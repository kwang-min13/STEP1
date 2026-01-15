"""
Local-Helix Dashboard

Streamlit 대시보드로 A/B 테스트 결과 및 모델 성능 시각화
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.analysis.statistical_tests import analyze_ab_test


# 페이지 설정
st.set_page_config(
    page_title="Local-Helix Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 타이틀
st.title("🎯 Local-Helix Recommendation System Dashboard")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("📊 Navigation")
    page = st.radio(
        "Select Page",
        ["Overview", "A/B Test Results", "Statistical Analysis", "Detailed Metrics"]
    )
    
    st.markdown("---")
    st.markdown("### 📁 Data Info")
    
    # 데이터 로드 (절대 경로 사용)
    data_path = project_root / 'logs' / 'ab_test_results.csv'
    
    try:
        if data_path.exists():
            df = pd.read_csv(data_path)
            st.success(f"✅ Data Loaded")
            st.info(f"Total Users: {len(df)}")
            st.info(f"Date: {pd.to_datetime(df['timestamp']).dt.date.iloc[0]}")
        else:
            st.error(f"❌ File not found: {data_path}")
            df = None
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.error(f"Attempted path: {data_path}")
        df = None


# 메인 컨텐츠
if df is not None:
    
    # Overview 페이지
    if page == "Overview":
        st.header("📈 Overview")
        
        # 전체 분석 실행 (절대 경로 사용)
        results = analyze_ab_test(str(data_path))
        stats = results['basic_stats']
        
        # 주요 지표
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Users",
                f"{stats['total_users']:,}",
                help="Total number of users in the simulation"
            )
        
        with col2:
            st.metric(
                "Group A CTR",
                f"{stats['group_a_ctr']:.2%}",
                help="Click-through rate for Group A (Popular items + Random time)"
            )
        
        with col3:
            st.metric(
                "Group B CTR",
                f"{stats['group_b_ctr']:.2%}",
                delta=f"{stats['ctr_difference']:.2%}",
                help="Click-through rate for Group B (ML recommendations + Optimal time)"
            )
        
        with col4:
            st.metric(
                "CTR Lift",
                f"{stats['ctr_lift']:.2f}%",
                help="Percentage improvement of Group B over Group A"
            )
        
        st.markdown("---")
        
        # 그룹별 비교 차트
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 CTR Comparison")
            
            # CTR 비교 바 차트
            ctr_data = pd.DataFrame({
                'Group': ['Group A', 'Group B'],
                'CTR': [stats['group_a_ctr'], stats['group_b_ctr']]
            })
            
            fig = px.bar(
                ctr_data,
                x='Group',
                y='CTR',
                color='Group',
                color_discrete_map={'Group A': '#FF6B6B', 'Group B': '#4ECDC4'},
                text='CTR'
            )
            fig.update_traces(texttemplate='%{text:.2%}', textposition='outside')
            fig.update_layout(showlegend=False, yaxis_title="Click-Through Rate")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⭐ Satisfaction Comparison")
            
            # 만족도 비교 바 차트
            sat_data = pd.DataFrame({
                'Group': ['Group A', 'Group B'],
                'Satisfaction': [stats['group_a_avg_satisfaction'], stats['group_b_avg_satisfaction']]
            })
            
            fig = px.bar(
                sat_data,
                x='Group',
                y='Satisfaction',
                color='Group',
                color_discrete_map={'Group A': '#FF6B6B', 'Group B': '#4ECDC4'},
                text='Satisfaction'
            )
            fig.update_traces(texttemplate='%{text:.2f}/5', textposition='outside')
            fig.update_layout(showlegend=False, yaxis_title="Average Satisfaction", yaxis_range=[0, 5])
            st.plotly_chart(fig, use_container_width=True)
        
        # 구매 수 비교
        st.subheader("🛒 Purchase Count Comparison")
        
        purchase_data = pd.DataFrame({
            'Group': ['Group A', 'Group B'],
            'Avg Purchases': [stats['group_a_avg_purchases'], stats['group_b_avg_purchases']]
        })
        
        fig = px.bar(
            purchase_data,
            x='Group',
            y='Avg Purchases',
            color='Group',
            color_discrete_map={'Group A': '#FF6B6B', 'Group B': '#4ECDC4'},
            text='Avg Purchases'
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(showlegend=False, yaxis_title="Average Purchase Count")
        st.plotly_chart(fig, use_container_width=True)
    
    
    # A/B Test Results 페이지
    elif page == "A/B Test Results":
        st.header("🧪 A/B Test Results")
        
        # 그룹별 분포
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Group Distribution")
            group_counts = df['group'].value_counts()
            
            fig = px.pie(
                values=group_counts.values,
                names=group_counts.index,
                color=group_counts.index,
                color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Click Distribution")
            click_counts = df['clicked'].value_counts()
            
            fig = px.pie(
                values=click_counts.values,
                names=['Clicked' if x else 'Not Clicked' for x in click_counts.index],
                color_discrete_sequence=['#4ECDC4', '#FF6B6B']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 그룹별 클릭률
        st.subheader("Click Rate by Group")
        
        click_by_group = df.groupby('group')['clicked'].agg(['sum', 'count', 'mean']).reset_index()
        click_by_group.columns = ['Group', 'Clicks', 'Total', 'CTR']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=click_by_group['Group'],
            y=click_by_group['Clicks'],
            name='Clicks',
            marker_color='#4ECDC4'
        ))
        fig.add_trace(go.Bar(
            x=click_by_group['Group'],
            y=click_by_group['Total'] - click_by_group['Clicks'],
            name='No Clicks',
            marker_color='#FF6B6B'
        ))
        fig.update_layout(barmode='stack', yaxis_title="Number of Users")
        st.plotly_chart(fig, use_container_width=True)
        
        # 데이터 테이블
        st.subheader("📋 Sample Data")
        st.dataframe(df.head(20), use_container_width=True)
    
    
    # Statistical Analysis 페이지
    elif page == "Statistical Analysis":
        st.header("🔬 Statistical Analysis")
        
        results = analyze_ab_test(str(data_path))
        
        # 카이제곱 검정
        st.subheader("Chi-Square Test (CTR)")
        chi2 = results['chi_square_test']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("χ² Statistic", f"{chi2['chi2_statistic']:.4f}")
        with col2:
            st.metric("p-value", f"{chi2['p_value']:.4f}")
        with col3:
            if chi2['significant']:
                st.success("✅ Statistically Significant (p < 0.05)")
            else:
                st.warning("❌ Not Significant (p ≥ 0.05)")
        
        st.info("""
        **Interpretation**: The chi-square test evaluates whether there is a statistically significant 
        difference in click-through rates between Group A and Group B.
        """)
        
        st.markdown("---")
        
        # T-검정 (만족도)
        st.subheader("T-Test: Satisfaction")
        t_sat = results['t_test_satisfaction']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("t-statistic", f"{t_sat['t_statistic']:.4f}")
        with col2:
            st.metric("p-value", f"{t_sat['p_value']:.4f}")
        with col3:
            if t_sat['significant']:
                st.success("✅ Statistically Significant (p < 0.05)")
            else:
                st.warning("❌ Not Significant (p ≥ 0.05)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Group A Mean", f"{t_sat['group_a_mean']:.2f}/5")
        with col2:
            st.metric("Group B Mean", f"{t_sat['group_b_mean']:.2f}/5")
        with col3:
            st.metric("Difference", f"{t_sat['difference']:.2f}")
        
        st.markdown("---")
        
        # T-검정 (구매)
        st.subheader("T-Test: Purchase Count")
        t_pur = results['t_test_purchases']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("t-statistic", f"{t_pur['t_statistic']:.4f}")
        with col2:
            st.metric("p-value", f"{t_pur['p_value']:.4f}")
        with col3:
            if t_pur['significant']:
                st.success("✅ Statistically Significant (p < 0.05)")
            else:
                st.warning("❌ Not Significant (p ≥ 0.05)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Group A Mean", f"{t_pur['group_a_mean']:.2f}")
        with col2:
            st.metric("Group B Mean", f"{t_pur['group_b_mean']:.2f}")
        with col3:
            st.metric("Difference", f"{t_pur['difference']:.2f}")
    
    
    # Detailed Metrics 페이지
    elif page == "Detailed Metrics":
        st.header("📊 Detailed Metrics")
        
        # 페르소나별 분석
        st.subheader("Analysis by Persona Budget")
        
        budget_analysis = df.groupby(['group', 'persona_budget'])['clicked'].agg(['sum', 'count', 'mean']).reset_index()
        budget_analysis.columns = ['Group', 'Budget', 'Clicks', 'Total', 'CTR']
        
        fig = px.bar(
            budget_analysis,
            x='Budget',
            y='CTR',
            color='Group',
            barmode='group',
            color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4'},
            text='CTR'
        )
        fig.update_traces(texttemplate='%{text:.2%}', textposition='outside')
        fig.update_layout(yaxis_title="Click-Through Rate")
        st.plotly_chart(fig, use_container_width=True)
        
        # 나이대별 분석
        st.subheader("Analysis by Persona Age")
        
        # 나이대 구간 생성
        df['age_group'] = pd.cut(df['persona_age'], bins=[0, 25, 35, 45, 55, 100], labels=['18-25', '26-35', '36-45', '46-55', '56+'])
        
        age_analysis = df.groupby(['group', 'age_group'])['clicked'].agg(['sum', 'count', 'mean']).reset_index()
        age_analysis.columns = ['Group', 'Age Group', 'Clicks', 'Total', 'CTR']
        
        fig = px.line(
            age_analysis,
            x='Age Group',
            y='CTR',
            color='Group',
            markers=True,
            color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4'}
        )
        fig.update_layout(yaxis_title="Click-Through Rate")
        st.plotly_chart(fig, use_container_width=True)
        
        # 만족도 분포
        st.subheader("Satisfaction Distribution")
        
        fig = px.histogram(
            df,
            x='satisfaction',
            color='group',
            barmode='overlay',
            color_discrete_map={'A': '#FF6B6B', 'B': '#4ECDC4'},
            opacity=0.7,
            nbins=5
        )
        fig.update_layout(xaxis_title="Satisfaction Score", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("❌ No data available. Please run the A/B test simulation first.")
    st.info("Run: `python scripts/run_simulation.py --ab-test --users 1000`")


# 푸터
st.markdown("---")
st.markdown("**Local-Helix Recommendation System** | Built with Streamlit 🎈")
