import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# 필요한 모듈들 import
from src.data_provider import KoreanStockDataProvider
from src.pair_finder import PairFinder
from src.visualizer import PairTradingVisualizer
from src.utils import get_stock_name_mapping

# 페이지 설정
st.set_page_config(
    page_title="🇰🇷 한국 주식 페어 트레이딩 분석 시스템",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4ECDC4;
    }
    
    .pair-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-left: 20px;
        padding-right: 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4ECDC4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 제목
    st.markdown('<h1 class="main-header">🇰🇷 한국 주식 페어 트레이딩 분석 시스템</h1>', unsafe_allow_html=True)
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 분석 설정")
        
        # 기간 설정
        st.subheader("📅 분석 기간")
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "시작일",
                value=datetime.now() - timedelta(days=365),
                max_value=datetime.now()
            )
        
        with col2:
            end_date = st.date_input(
                "종료일",
                value=datetime.now(),
                max_value=datetime.now()
            )
        
        # 페어 트레이딩 파라미터
        st.subheader("📊 페어 트레이딩 파라미터")
        correlation_threshold = st.slider("상관계수 임계값", 0.5, 0.95, 0.8, 0.05)
        cointegration_pvalue = st.slider("공적분 p-value 임계값", 0.01, 0.1, 0.05, 0.01)
        entry_z_score = st.slider("진입 Z-Score", 1.0, 3.0, 2.0, 0.1)
        exit_z_score = st.slider("청산 Z-Score", 0.1, 1.5, 0.5, 0.1)
        
        # 종목 필터링
        st.subheader("🏢 종목 필터링")
        market_filter = st.selectbox(
            "시장 선택",
            ["전체", "KOSPI", "KOSDAQ"],
            index=0
        )
        
        min_market_cap = st.selectbox(
            "최소 시가총액 (억원)",
            [0, 1000, 5000, 10000, 50000],
            index=1
        )
        
        max_stocks = st.selectbox(
            "최대 분석 종목 수",
            [50, 100, 200, 500],
            index=1
        )
        
        # 분석 시작 버튼
        analyze_button = st.button("🚀 페어 분석 시작", type="primary", use_container_width=True)
    
    # 메인 컨텐츠 영역
    if analyze_button:
        with st.spinner("🔍 한국 주식 데이터를 수집하고 있습니다..."):
            # 데이터 제공자 초기화
            data_provider = KoreanStockDataProvider()
            
            # 주식 목록 가져오기
            stock_list = data_provider.get_stock_list(
                market=market_filter,
                min_market_cap=min_market_cap,
                max_count=max_stocks
            )
            
            if stock_list.empty:
                st.error("조건에 맞는 종목이 없습니다. 필터 조건을 완화해주세요.")
                return
            
            st.success(f"✅ {len(stock_list)}개 종목을 발견했습니다!")
            
            # 주식 데이터 다운로드
            with st.spinner("📈 주식 가격 데이터를 다운로드하고 있습니다..."):
                price_data = data_provider.download_stock_data(
                    stock_list['Symbol'].tolist(),
                    start_date,
                    end_date
                )
            
            if price_data.empty:
                st.error("가격 데이터를 가져올 수 없습니다.")
                return
            
            st.success(f"✅ {len(price_data.columns)}개 종목의 가격 데이터를 수집했습니다!")
        
        # 페어 찾기
        with st.spinner("🔍 통계적으로 유의한 페어를 찾고 있습니다..."):
            pair_finder = PairFinder(
                correlation_threshold=correlation_threshold,
                cointegration_pvalue=cointegration_pvalue
            )
            
            pairs_df = pair_finder.find_pairs(price_data)
        
        if pairs_df.empty:
            st.warning("⚠️ 조건에 맞는 페어를 찾지 못했습니다. 임계값을 조정해보세요.")
            return
        
        # 종목명 매핑
        name_mapping = get_stock_name_mapping(stock_list)
        pairs_df['Stock1_Name'] = pairs_df['Stock1'].map(name_mapping)
        pairs_df['Stock2_Name'] = pairs_df['Stock2'].map(name_mapping)
        
        # 결과 표시
        st.header("🎯 발견된 페어 트레이딩 기회")
        
        # 페어 목록 표시
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📋 총 {len(pairs_df)}개의 페어 발견")
            
            # 페어 테이블 표시
            display_df = pairs_df.copy()
            display_df['페어'] = display_df['Stock1_Name'] + ' ↔ ' + display_df['Stock2_Name']
            display_df['상관계수'] = display_df['Correlation'].round(3)
            display_df['공적분 p-value'] = display_df['Cointegration_PValue'].round(4)
            
            st.dataframe(
                display_df[['페어', '상관계수', '공적분 p-value']],
                use_container_width=True,
                height=400
            )
        
        with col2:
            st.subheader("📊 페어 분석 요약")
            st.metric("발견된 페어 수", len(pairs_df))
            st.metric("평균 상관계수", f"{pairs_df['Correlation'].mean():.3f}")
            st.metric("최고 상관계수", f"{pairs_df['Correlation'].max():.3f}")
            st.metric("분석 종목 수", len(price_data.columns))
        
        # 페어 선택 및 상세 분석
        if not pairs_df.empty:
            st.header("🔬 페어 상세 분석")
            
            # 페어 선택
            selected_idx = st.selectbox(
                "분석할 페어를 선택하세요:",
                range(len(pairs_df)),
                format_func=lambda x: f"{pairs_df.iloc[x]['Stock1_Name']} ↔ {pairs_df.iloc[x]['Stock2_Name']} "
                                      f"(상관계수: {pairs_df.iloc[x]['Correlation']:.3f})"
            )
            
            selected_pair = pairs_df.iloc[selected_idx]
            stock1_symbol = selected_pair['Stock1']
            stock2_symbol = selected_pair['Stock2']
            stock1_name = selected_pair['Stock1_Name']
            stock2_name = selected_pair['Stock2_Name']
            
            # 선택된 페어 정보 표시
            st.markdown(f"""
            <div class="pair-info">
                <h3>📈 {stock1_name} ({stock1_symbol}) ↔ {stock2_name} ({stock2_symbol})</h3>
                <p><strong>상관계수:</strong> {selected_pair['Correlation']:.3f}</p>
                <p><strong>공적분 p-value:</strong> {selected_pair['Cointegration_PValue']:.4f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 페어 트레이딩 백테스트
            with st.spinner("📊 페어 트레이딩 전략을 백테스트하고 있습니다..."):
                visualizer = PairTradingVisualizer()
                
                # 백테스트 실행
                backtest_results = visualizer.run_backtest(
                    price_data[[stock1_symbol, stock2_symbol]],
                    stock1_symbol,
                    stock2_symbol,
                    entry_z_score,
                    exit_z_score
                )
            
            # 탭으로 구분된 결과 표시
            tab1, tab2, tab3, tab4 = st.tabs(["📈 가격 차트", "📊 스프레드 분석", "💰 수익률 분석", "📋 거래 신호"])
            
            with tab1:
                st.subheader("정규화된 가격 비교")
                price_fig = visualizer.create_price_comparison_chart(
                    price_data[[stock1_symbol, stock2_symbol]],
                    stock1_name,
                    stock2_name
                )
                st.plotly_chart(price_fig, use_container_width=True)
            
            with tab2:
                st.subheader("스프레드 및 Z-Score 분석")
                spread_fig = visualizer.create_spread_analysis_chart(
                    backtest_results,
                    stock1_name,
                    stock2_name,
                    entry_z_score,
                    exit_z_score
                )
                st.plotly_chart(spread_fig, use_container_width=True)
            
            with tab3:
                st.subheader("누적 수익률 및 성과 지표")
                
                # 성과 지표 표시
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "총 수익률",
                        f"{backtest_results['total_return']:.2%}",
                        delta=f"{backtest_results['total_return']:.2%}"
                    )
                
                with col2:
                    st.metric(
                        "샤프 비율",
                        f"{backtest_results['sharpe_ratio']:.2f}",
                        delta=f"{backtest_results['sharpe_ratio']:.2f}"
                    )
                
                with col3:
                    st.metric(
                        "최대 손실",
                        f"{backtest_results['max_drawdown']:.2%}",
                        delta=f"{backtest_results['max_drawdown']:.2%}"
                    )
                
                with col4:
                    st.metric(
                        "승률",
                        f"{backtest_results['win_rate']:.1%}",
                        delta=f"{backtest_results['win_rate']:.1%}"
                    )
                
                # 누적 수익률 차트
                returns_fig = visualizer.create_returns_chart(
                    backtest_results,
                    stock1_name,
                    stock2_name
                )
                st.plotly_chart(returns_fig, use_container_width=True)
            
            with tab4:
                st.subheader("거래 신호 및 포지션")
                
                # 거래 신호 테이블
                signals_df = backtest_results['signals_df']
                if not signals_df.empty:
                    st.dataframe(signals_df.head(20), use_container_width=True)
                else:
                    st.info("해당 기간에 거래 신호가 없습니다.")
    
    else:
        # 초기 화면
        st.markdown("""
        ## 👋 환영합니다!
        
        이 시스템은 한국 주식 시장에서 **페어 트레이딩**이 가능한 종목 쌍을 찾아주는 고도화된 분석 도구입니다.
        
        ### 🔥 주요 기능
        - 📊 **전체 한국 주식 시장** 분석 (KOSPI + KOSDAQ)
        - 🔬 **공적분 검정**을 통한 통계적 페어 발견
        - 📈 **실시간 백테스팅** 및 성과 분석
        - 🎯 **사용자 정의 파라미터** 설정
        - 📱 **직관적인 탭 기반 UI**
        
        ### 🚀 시작하기
        1. 좌측 사이드바에서 **분석 조건**을 설정하세요
        2. **'페어 분석 시작'** 버튼을 클릭하세요
        3. 발견된 페어 중 원하는 것을 선택하여 **상세 분석**을 확인하세요
        
        ### ⚡ 기술적 특징
        - ✅ **FinanceDataReader** 기반 고품질 데이터
        - ✅ **Johansen 공적분 테스트** 적용
        - ✅ **최적화된 알고리즘**으로 빠른 분석
        - ✅ **실시간 시각화** 및 인터랙티브 차트
        """)
        
        # 샘플 차트 표시
        st.subheader("📊 분석 예시")
        
        # 더미 데이터로 샘플 차트 생성
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        sample_data = pd.DataFrame({
            'Date': dates,
            'Stock1': np.cumsum(np.random.randn(len(dates))) + 100,
            'Stock2': np.cumsum(np.random.randn(len(dates))) + 100
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sample_data['Date'], y=sample_data['Stock1'], name='종목 A'))
        fig.add_trace(go.Scatter(x=sample_data['Date'], y=sample_data['Stock2'], name='종목 B'))
        fig.update_layout(
            title="페어 트레이딩 예시 - 두 종목의 가격 움직임",
            xaxis_title="날짜",
            yaxis_title="주가",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
