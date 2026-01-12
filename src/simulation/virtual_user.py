"""
Virtual User Module

LLM 기반 가상 유저 페르소나 생성
"""

import random
from typing import Dict, Any, List
import logging
from .ollama_client import OllamaClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VirtualUser:
    """가상 유저 클래스"""
    
    def __init__(self, ollama_client: OllamaClient = None):
        """
        초기화
        
        Args:
            ollama_client: Ollama 클라이언트 (선택사항)
        """
        self.ollama_client = ollama_client or OllamaClient()
        self.persona: Dict[str, Any] = {}
    
    def generate_persona(self) -> Dict[str, Any]:
        """
        가상 유저 페르소나 생성
        
        Returns:
            페르소나 정보 딕셔너리
        """
        # 기본 속성 랜덤 생성
        age = random.randint(18, 65)
        gender = random.choice(['Male', 'Female', 'Non-binary'])
        
        # LLM으로 상세 페르소나 생성
        prompt = f"""Generate a realistic shopping persona for a {age}-year-old {gender} customer.
Include:
- Style preference (e.g., casual, formal, sporty, trendy)
- Shopping frequency (e.g., weekly, monthly, occasionally)
- Budget range (e.g., low, medium, high)
- Favorite fashion categories (2-3 items)

Format as JSON with keys: style, frequency, budget, categories.
Keep it concise and realistic."""
        
        response = self.ollama_client.generate(prompt, temperature=0.8)
        
        if response:
            # LLM 응답 파싱 시도
            try:
                import json
                # JSON 부분만 추출
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    persona_details = json.loads(response[start:end])
                else:
                    persona_details = self._fallback_persona()
            except:
                persona_details = self._fallback_persona()
        else:
            persona_details = self._fallback_persona()
        
        self.persona = {
            'age': age,
            'gender': gender,
            **persona_details
        }
        
        return self.persona
    
    def _fallback_persona(self) -> Dict[str, Any]:
        """LLM 실패 시 대체 페르소나"""
        styles = ['casual', 'formal', 'sporty', 'trendy', 'vintage']
        frequencies = ['weekly', 'monthly', 'occasionally']
        budgets = ['low', 'medium', 'high']
        categories = ['tops', 'bottoms', 'dresses', 'shoes', 'accessories', 'outerwear']
        
        return {
            'style': random.choice(styles),
            'frequency': random.choice(frequencies),
            'budget': random.choice(budgets),
            'categories': random.sample(categories, 2)
        }
    
    def evaluate_recommendations(self, recommendations: List[str]) -> Dict[str, Any]:
        """
        추천 상품 평가
        
        Args:
            recommendations: 추천 상품 ID 리스트
            
        Returns:
            평가 결과
        """
        if not self.persona:
            self.generate_persona()
        
        # LLM으로 추천 평가
        prompt = f"""You are a {self.persona['age']}-year-old {self.persona['gender']} shopper.
Your style: {self.persona.get('style', 'casual')}
Your budget: {self.persona.get('budget', 'medium')}
Your favorite categories: {', '.join(self.persona.get('categories', ['general']))}

You received {len(recommendations)} product recommendations.
How many would you likely purchase? (Give a number between 0 and {len(recommendations)})
Also rate your satisfaction (1-5).

Format: "Purchase: X, Satisfaction: Y" """
        
        response = self.ollama_client.generate(prompt, temperature=0.5)
        
        # 응답 파싱
        purchase_count = 0
        satisfaction = 3
        
        if response:
            try:
                # 숫자 추출
                import re
                purchase_match = re.search(r'Purchase:\s*(\d+)', response)
                satisfaction_match = re.search(r'Satisfaction:\s*(\d+)', response)
                
                if purchase_match:
                    purchase_count = min(int(purchase_match.group(1)), len(recommendations))
                if satisfaction_match:
                    satisfaction = min(int(satisfaction_match.group(1)), 5)
            except:
                # 랜덤 대체값
                purchase_count = random.randint(0, min(3, len(recommendations)))
                satisfaction = random.randint(2, 5)
        else:
            # Ollama 없을 때 랜덤
            purchase_count = random.randint(0, min(3, len(recommendations)))
            satisfaction = random.randint(2, 5)
        
        return {
            'purchase_count': purchase_count,
            'satisfaction': satisfaction,
            'acceptance_rate': purchase_count / len(recommendations) if recommendations else 0
        }


if __name__ == "__main__":
    # 테스트
    user = VirtualUser()
    
    logger.info("가상 유저 페르소나 생성 중...")
    persona = user.generate_persona()
    
    logger.info("=" * 60)
    logger.info("생성된 페르소나:")
    for key, value in persona.items():
        logger.info(f"  {key}: {value}")
    
    # 추천 평가 테스트
    logger.info("\n추천 평가 테스트...")
    test_recs = ['item1', 'item2', 'item3', 'item4', 'item5']
    evaluation = user.evaluate_recommendations(test_recs)
    
    logger.info("평가 결과:")
    logger.info(f"  구매 예상: {evaluation['purchase_count']}/{len(test_recs)}")
    logger.info(f"  만족도: {evaluation['satisfaction']}/5")
    logger.info(f"  수용률: {evaluation['acceptance_rate']:.1%}")
    logger.info("=" * 60)
