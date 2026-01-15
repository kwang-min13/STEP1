"""
Candidate Generation Module (Improved v2)

- Popularity candidates (deterministic + scored)
- Item-to-item co-purchase CF candidates (time decay + user-recent weighting + popularity penalty)
- Score-based deterministic merge (robust normalization, clear tie-break)
- DuckDB: transactions scanned ONCE (TEMP TABLE materialization)

Key fixes vs v1:
1) Avoid CSV re-scan by materializing CF window into TEMP TABLE
2) Switch CF to item-to-item co-occurrence (more stable + faster than similar-users overlap)
3) Apply user recent-item weights + time decay
4) Optional popularity penalty (rank-based, but isolated & tunable)
5) Normalize pop/cf scores before weighted merge
"""

from __future__ import annotations

import duckdb
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoredItem:
    item_id: str
    score: float
    source: str  # "pop" or "cf"


class CandidateGenerator:
    def __init__(
        self,
        db_path: str = "local_helix.db",
        transactions_path: str = "data/raw/transactions_train.csv",
        item_features_path: str = "data/features/item_features.parquet",
        memory_limit: str = "8GB",
        threads: int = 4,
        cf_window_days: int = 28,
        materialize_transactions: bool = True,
    ):
        self.db_path = db_path
        self.transactions_path = transactions_path
        self.item_features_path = item_features_path
        self.memory_limit = memory_limit
        self.threads = threads
        self.cf_window_days = cf_window_days
        self.materialize_transactions = materialize_transactions

        self.con: Optional[duckdb.DuckDBPyConnection] = None
        self._cache_ready = False

    def connect(self) -> duckdb.DuckDBPyConnection:
        if self.con is None:
            # Use in-memory database to avoid file locking
            self.con = duckdb.connect(":memory:")
            # Attach the file database in read-only mode for data access
            if self.db_path != ":memory:":
                try:
                    self.con.execute(f"ATTACH '{self.db_path}' AS filedb (READ_ONLY)")
                except Exception:
                    # If attach fails, continue with in-memory only
                    pass
            self.con.execute(f"SET memory_limit='{self.memory_limit}'")
            self.con.execute(f"SET threads TO {int(self.threads)}")
        if not self._cache_ready:
            self._prepare_cache()
        return self.con

    def _prepare_cache(self) -> None:
        con = self.con
        assert con is not None

        # item features view
        con.execute("DROP VIEW IF EXISTS v_item_features")
        con.execute(
            f"""
            CREATE VIEW v_item_features AS
            SELECT
                article_id::VARCHAR AS article_id,
                popularity_rank
            FROM read_parquet('{self.item_features_path}')
            """
        )

        # raw transactions view (will be materialized into temp table for CF window)
        con.execute("DROP VIEW IF EXISTS v_transactions_all")
        con.execute(
            f"""
            CREATE VIEW v_transactions_all AS
            SELECT
                customer_id::VARCHAR AS customer_id,
                article_id::VARCHAR  AS article_id,
                CAST(t_dat AS DATE)  AS t_dat
            FROM read_csv_auto('{self.transactions_path}', header=true)
            """
        )

        # materialize CF window
        con.execute("DROP TABLE IF EXISTS t_cf_transactions")
        con.execute("DROP VIEW IF EXISTS v_cf_transactions")

        if self.materialize_transactions:
            # IMPORTANT: force one-time scan + keep only window
            con.execute(
                f"""
                CREATE TEMP TABLE t_cf_transactions AS
                WITH mx AS (SELECT MAX(t_dat) AS dmax FROM v_transactions_all)
                SELECT *
                FROM v_transactions_all
                WHERE t_dat >= (SELECT dmax - INTERVAL '{int(self.cf_window_days)} days' FROM mx)
                """
            )
            # Helpful: order by (article_id, customer_id, t_dat) for join locality
            con.execute("DROP TABLE IF EXISTS t_cf_sorted")
            con.execute(
                """
                CREATE TEMP TABLE t_cf_sorted AS
                SELECT * FROM t_cf_transactions
                ORDER BY article_id, customer_id, t_dat
                """
            )
            con.execute("DROP TABLE IF EXISTS t_cf_transactions")
            con.execute("ALTER TABLE t_cf_sorted RENAME TO t_cf_transactions")

            con.execute("CREATE VIEW v_cf_transactions AS SELECT * FROM t_cf_transactions")
        else:
            con.execute(
                f"""
                CREATE VIEW v_cf_transactions AS
                WITH mx AS (SELECT MAX(t_dat) AS dmax FROM v_transactions_all)
                SELECT *
                FROM v_transactions_all
                WHERE t_dat >= (SELECT dmax - INTERVAL '{int(self.cf_window_days)} days' FROM mx)
                """
            )

        # cache max date for consistent time-decay
        con.execute("DROP VIEW IF EXISTS v_cf_max_date")
        con.execute(
            """
            CREATE VIEW v_cf_max_date AS
            SELECT MAX(t_dat) AS dmax
            FROM v_cf_transactions
            """
        )

        self._cache_ready = True
        logger.info("Cache ready: CF window materialized=%s", self.materialize_transactions)

    # ---------------------------
    # Popularity
    # ---------------------------
    def generate_popularity_candidates(self, top_k: int = 50) -> List[str]:
        con = self.connect()
        q = """
            SELECT article_id
            FROM v_item_features
            ORDER BY popularity_rank ASC NULLS LAST, article_id ASC
            LIMIT ?
        """
        rows = con.execute(q, [int(top_k)]).fetchall()
        return [r[0] for r in rows]

    def generate_popularity_scored(self, top_k: int = 50) -> List[ScoredItem]:
        """
        score_pop = 1 / (1 + popularity_rank)
        """
        con = self.connect()
        q = """
            SELECT article_id, popularity_rank
            FROM v_item_features
            ORDER BY popularity_rank ASC NULLS LAST, article_id ASC
            LIMIT ?
        """
        rows = con.execute(q, [int(top_k)]).fetchall()

        out: List[ScoredItem] = []
        for item_id, pop_rank in rows:
            r = float(pop_rank) if pop_rank is not None else 1e12
            r = max(r, 0.0)
            score = 1.0 / (1.0 + r)
            out.append(ScoredItem(item_id=str(item_id), score=float(score), source="pop"))
        return out

    # ---------------------------
    # CF: item-to-item co-purchase
    # ---------------------------
    def generate_cf_scored_item2item(
        self,
        user_id: str,
        top_k: int = 50,
        recent_items: int = 10,
        cooc_top_per_seed: int = 200,
        time_decay_half_life_days: int = 14,
        popularity_penalty_alpha: float = 0.20,
        exclude_already_purchased: bool = True,
    ) -> List[ScoredItem]:
        """
        CF score intuition:
        - Take user's recent items (seed set)
        - For each seed item, find co-purchased items in same window
        - Weight by:
            (a) seed recency weight
            (b) co-purchase count
            (c) time decay on co-purchase transactions
        - Apply popularity penalty optionally
        """
        con = self.connect()
        half_life = max(int(time_decay_half_life_days), 1)

        # NOTE:
        # - DuckDB doesn't have great indexing, but sorting temp table helps.
        # - Limit cooc candidates per seed to control blow-up.
        q = f"""
        WITH
        dmax AS (SELECT dmax FROM v_cf_max_date),
        user_recent AS (
            SELECT
                article_id AS seed_item,
                t_dat      AS seed_date,
                ROW_NUMBER() OVER (ORDER BY t_dat DESC, article_id ASC) AS rnk
            FROM v_cf_transactions
            WHERE customer_id = ?
            QUALIFY rnk <= ?
        ),
        seed_weighted AS (
            SELECT
                seed_item,
                seed_date,
                -- seed recency weight: 0.5^(age/half_life)
                POW(
                    0.5,
                    DATE_DIFF('day', seed_date, (SELECT dmax FROM dmax))::DOUBLE / {half_life}.0
                ) AS w_seed
            FROM user_recent
        ),
        user_purchased AS (
            SELECT DISTINCT article_id
            FROM v_cf_transactions
            WHERE customer_id = ?
        ),
        -- Co-purchase candidates: users who bought seed_item -> other items they bought
        cooc_raw AS (
            SELECT
                sw.seed_item,
                t2.article_id AS cand_item,
                -- weight each co-purchase event by seed weight and time-decay of t2
                SUM(
                    sw.w_seed
                    * POW(
                        0.5,
                        DATE_DIFF('day', t2.t_dat, (SELECT dmax FROM dmax))::DOUBLE / {half_life}.0
                    )
                ) AS raw_score
            FROM seed_weighted sw
            JOIN v_cf_transactions t1
              ON t1.article_id = sw.seed_item
            JOIN v_cf_transactions t2
              ON t2.customer_id = t1.customer_id
            WHERE t2.article_id <> sw.seed_item
            GROUP BY sw.seed_item, t2.article_id
        ),
        -- control explosion: take top per seed
        cooc_pruned AS (
            SELECT *
            FROM (
                SELECT
                    seed_item,
                    cand_item,
                    raw_score,
                    ROW_NUMBER() OVER (PARTITION BY seed_item ORDER BY raw_score DESC, cand_item ASC) AS rr
                FROM cooc_raw
            )
            WHERE rr <= ?
        ),
        -- aggregate across seeds
        cand_agg AS (
            SELECT
                cand_item AS article_id,
                SUM(raw_score) AS score_sum
            FROM cooc_pruned
            GROUP BY cand_item
        ),
        cand_join AS (
            SELECT
                ca.article_id,
                ca.score_sum,
                vf.popularity_rank
            FROM cand_agg ca
            LEFT JOIN v_item_features vf
              ON vf.article_id = ca.article_id
        ),
        cand_filtered AS (
            SELECT
                article_id,
                CASE
                    WHEN popularity_rank IS NULL THEN score_sum
                    ELSE score_sum / (1.0 + ? * LN(1.0 + CAST(popularity_rank AS DOUBLE)))
                END AS score_cf
            FROM cand_join
            {"WHERE article_id NOT IN (SELECT article_id FROM user_purchased)" if exclude_already_purchased else ""}
        )
        SELECT article_id, score_cf
        FROM cand_filtered
        ORDER BY score_cf DESC, article_id ASC
        LIMIT ?
        """

        params = [
            str(user_id),
            int(recent_items),
            str(user_id),
            int(cooc_top_per_seed),
            float(popularity_penalty_alpha),
            int(top_k),
        ]

        rows = con.execute(q, params).fetchall()
        return [ScoredItem(item_id=str(i), score=float(s), source="cf") for i, s in rows]

    # ---------------------------
    # Merge: robust normalization + deterministic ranking
    # ---------------------------
    @staticmethod
    def _normalize_scores(items: List[ScoredItem]) -> Dict[str, float]:
        """
        Robust normalization for merging:
        - apply log1p to reduce heavy-tail
        - min-max scale to [0,1] within the list
        """
        if not items:
            return {}

        raw = {it.item_id: float(it.score) for it in items}
        vals = [math.log1p(max(v, 0.0)) for v in raw.values()]
        vmin, vmax = min(vals), max(vals)

        if vmax <= vmin + 1e-12:
            # all same -> give 1.0 to all
            return {k: 1.0 for k in raw.keys()}

        out: Dict[str, float] = {}
        for (k, v), lv in zip(raw.items(), vals):
            out[k] = (lv - vmin) / (vmax - vmin)
        return out

    def merge_candidates(
        self,
        user_id: str,
        total_k: int = 100,
        pop_top: int = 200,
        cf_top: int = 300,
        w_pop: float = 0.30,
        w_cf: float = 0.70,
        recent_items: int = 10,
        cooc_top_per_seed: int = 200,
        time_decay_half_life_days: int = 14,
        popularity_penalty_alpha: float = 0.20,
        fallback_pop_expand: int = 1000,
    ) -> List[str]:
        total_k = int(total_k)
        if total_k <= 0:
            return []

        pop_scored = self.generate_popularity_scored(top_k=int(pop_top))
        cf_scored = self.generate_cf_scored_item2item(
            user_id=user_id,
            top_k=int(cf_top),
            recent_items=int(recent_items),
            cooc_top_per_seed=int(cooc_top_per_seed),
            time_decay_half_life_days=int(time_decay_half_life_days),
            popularity_penalty_alpha=float(popularity_penalty_alpha),
        )

        # normalize within each source
        pop_norm = self._normalize_scores(pop_scored)
        cf_norm = self._normalize_scores(cf_scored)

        # union
        all_ids = set(pop_norm.keys()) | set(cf_norm.keys())
        if len(all_ids) < total_k:
            # expand popularity to fill
            expanded = self.generate_popularity_scored(top_k=int(fallback_pop_expand))
            exp_norm = self._normalize_scores(expanded)
            for k, v in exp_norm.items():
                if len(all_ids) >= total_k:
                    break
                if k not in all_ids:
                    pop_norm[k] = v
                    all_ids.add(k)

        # deterministic ranking
        def key_fn(item_id: str) -> Tuple[float, float, float, str]:
            ps = float(pop_norm.get(item_id, 0.0))
            cs = float(cf_norm.get(item_id, 0.0))
            final = float(w_pop) * ps + float(w_cf) * cs
            return (final, cs, ps, item_id)

        ranked = sorted(all_ids, key=key_fn, reverse=True)
        return ranked[:total_k]

    def close(self) -> None:
        if self.con is not None:
            self.con.close()
            self.con = None
        self._cache_ready = False


def main():
    import time

    gen = CandidateGenerator(
        db_path="local_helix.db",
        transactions_path="data/raw/transactions_train.csv",
        item_features_path="data/features/item_features.parquet",
        cf_window_days=28,
        materialize_transactions=True,
    )

    try:
        con = gen.connect()
        sample_user = con.execute(
            """
            SELECT customer_id
            FROM read_parquet('data/features/user_features.parquet')
            LIMIT 1
            """
        ).fetchone()[0]

        logger.info("Sample user: %s", sample_user)

        t0 = time.time()
        pop = gen.generate_popularity_candidates(top_k=50)
        logger.info("Popularity: %d (%.1f ms)", len(pop), (time.time() - t0) * 1000)

        t0 = time.time()
        cf = gen.generate_cf_scored_item2item(sample_user, top_k=50)
        logger.info("CF(item2item): %d (%.1f ms)", len(cf), (time.time() - t0) * 1000)

        t0 = time.time()
        merged = gen.merge_candidates(sample_user, total_k=100)
        logger.info("Merged: %d (%.1f ms)", len(merged), (time.time() - t0) * 1000)
        logger.info("Top-10 merged: %s", merged[:10])

    finally:
        gen.close()


if __name__ == "__main__":
    main()
