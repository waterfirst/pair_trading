import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import warnings
import os
warnings.filterwarnings('ignore')

# 필요한 모듈들 import
from src.data_provider import KoreanStockDataProvider
from src.pair_finder import PairFinder
from src.visualizer import PairTradingVisualizer
from src.period_analyzer import PeriodAnalyzer
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
    
    .upload-section {
        border: 2px dashed #4ECDC4;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 제목
    st.markdown('<h1 class="main-header">🇰🇷 한국 주식 페어 트레이딩 분석 시스템</h1>', unsafe_allow_html=True)
    
    # 메인 탭 구성
    main_tab1, main_tab2 = st.tabs(["🔍 실시간 페어 분석", "📊 기간별 종합 분석"])
    
    with main_tab1:
        # 기존 실시간 분석 기능
        real_time_analysis()
    
    with main_tab2:
        # 새로운 기간별 분석 기능
        period_analysis()

def real_time_analysis():
    """실시간 페어 분석 기능"""
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 실시간 분석 설정")
        
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
        analyze_button = st.button("🚀 실시간 페어 분석 시작", type="primary", use_container_width=True)
    
    # 메인 컨텐츠 영역 (기존 로직)
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
        ## 👋 실시간 페어 분석에 오신 것을 환영합니다!
        
        이 기능을 통해 **실시간으로 한국 주식 시장**에서 페어 트레이딩 기회를 찾을 수 있습니다.
        
        ### 🔥 주요 기능
        - 📊 **KOSPI/KOSDAQ 종목** 실시간 분석
        - 🔬 **공적분 검정**을 통한 통계적 페어 발견
        - 📈 **즉시 백테스팅** 및 성과 분석
        - 🎯 **사용자 정의 파라미터** 설정
        
        ### 🚀 시작하기
        1. 좌측 사이드바에서 **분석 조건**을 설정하세요
        2. **'실시간 페어 분석 시작'** 버튼을 클릭하세요
        3. 발견된 페어 중 원하는 것을 선택하여 **상세 분석**을 확인하세요
        """)

def period_analysis():
    """기간별 종합 분석 기능"""
    
    st.header("📊 KOSPI 종목 기간별 종합 분석")
    
    st.markdown("""
    이 기능을 사용하면 **KOSPI 전체 종목**을 대상으로 **6개월, 1년, 2년, 5년** 기간별 페어 분석을 수행하고,
    **투자가치가 높은 페어**들을 종합적으로 비교 분석할 수 있습니다.
    """)
    
    # CSV 파일 업로드 또는 기본 종목 사용 선택
    st.subheader("1️⃣ 종목 데이터 선택")
    
    data_source = st.radio(
        "분석할 종목 데이터를 선택하세요:",
        ["📁 KOSPI CSV 파일 업로드", "🔄 시스템 기본 종목 사용"],
        index=0
    )
    
    csv_file_path = None
    
    if data_source == "📁 KOSPI CSV 파일 업로드":
        st.markdown("""
        <div class="upload-section">
            <h4>📁 KOSPI 종목 CSV 파일 업로드</h4>
            <p>KOSPI 종목 정보가 담긴 CSV 파일을 업로드하세요.</p>
            <p><small>필수 컬럼: 종목코드, 종목명 (시가총액 컬럼이 있으면 더 정확한 분석 가능)</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "CSV 파일을 선택하세요",
            type=['csv'],
            help="종목코드와 종목명이 포함된 CSV 파일을 업로드하세요"
        )
        
        if uploaded_file is not None:
            # 임시 파일 저장
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            csv_file_path = temp_file_path
            
            # 파일 미리보기
            try:
                preview_df = pd.read_csv(temp_file_path, encoding='utf-8', nrows=5)
                st.success(f"✅ 파일 업로드 성공! (미리보기 - 상위 5행)")
                st.dataframe(preview_df)
            except:
                try:
                    preview_df = pd.read_csv(temp_file_path, encoding='cp949', nrows=5)
                    st.success(f"✅ 파일 업로드 성공! (미리보기 - 상위 5행)")
                    st.dataframe(preview_df)
                except:
                    st.error("파일을 읽을 수 없습니다. CSV 파일 형식을 확인해주세요.")
    
    else:
        st.info("💡 시스템 기본 KOSPI 종목 리스트를 사용합니다.")
        csv_file_path = "data/kospi_stock.csv"  # 기본 CSV 파일 경로
    
    # 분석 설정
    st.subheader("2️⃣ 분석 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_stocks = st.selectbox(
            "최대 분석 종목 수",
            [30, 50, 100, 200],
            index=1,
            help="너무 많은 종목을 선택하면 분석 시간이 오래 걸립니다"
        )
        
        max_pairs_per_period = st.selectbox(
            "기간별 최대 페어 수",
            [10, 15, 20, 30],
            index=1,
            help="기간별로 분석할 최대 페어 수입니다"
        )
    
    with col2:
        correlation_threshold = st.slider("상관계수 임계값", 0.6, 0.9, 0.7, 0.05)
        cointegration_pvalue = st.slider("공적분 p-value 임계값", 0.01, 0.1, 0.05, 0.01)
    
    # 분석 기간 표시
    st.subheader("3️⃣ 분석 기간")
    
    periods_info = {
        "6개월": "최근 6개월간의 단기 트렌드 분석",
        "1년": "연간 패턴 및 계절성 분석", 
        "2년": "중기 시장 사이클 분석",
        "5년": "장기 구조적 관계 분석"
    }
    
    cols = st.columns(4)
    for i, (period, description) in enumerate(periods_info.items()):
        with cols[i]:
            st.info(f"**{period}**\n\n{description}")
    
    # 분석 실행 버튼
    st.subheader("4️⃣ 분석 실행")
    
    if csv_file_path and (os.path.exists(csv_file_path) or data_source == "📁 KOSPI CSV 파일 업로드"):
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            analyze_period_button = st.button(
                "🚀 기간별 분석 시작",
                type="primary",
                use_container_width=True,
                help="모든 기간에 대해 종합 분석을 수행합니다 (시간이 소요될 수 있습니다)"
            )
        
        if analyze_period_button:
            
            # 진행률 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # PeriodAnalyzer 초기화
                analyzer = PeriodAnalyzer(csv_file_path)
                
                status_text.text("📊 분석을 시작합니다...")
                progress_bar.progress(10)
                
                # 전체 분석 실행
                with st.spinner("🔍 기간별 페어 분석을 수행하고 있습니다... (수 분이 소요될 수 있습니다)"):
                    results = analyzer.run_full_analysis(
                        max_stocks=max_stocks,
                        max_pairs_per_period=max_pairs_per_period
                    )
                
                progress_bar.progress(80)
                status_text.text("📄 HTML 보고서를 생성하고 있습니다...")
                
                if "error" in results:
                    st.error(f"❌ 분석 실패: {results['error']}")
                    return
                
                # HTML 보고서 생성
                html_file = analyzer.generate_html_report(results)
                
                progress_bar.progress(100)
                status_text.text("✅ 분석 완료!")
                
                # 결과 표시
                st.success("🎉 기간별 페어 분석이 완료되었습니다!")
                
                # 요약 정보 표시
                if "summary" in results:
                    summary = results["summary"]
                    
                    st.subheader("📊 분석 결과 요약")
                    
                    # 기간별 페어 수
                    if "total_pairs_by_period" in summary:
                        cols = st.columns(4)
                        for i, (period, count) in enumerate(summary["total_pairs_by_period"].items()):
                            with cols[i]:
                                st.metric(f"{period} 기간", f"{count}개 페어")
                    
                    # 전체 최고 페어들
                    if "overall_best_pairs" in summary and summary["overall_best_pairs"]:
                        st.subheader("🏆 전체 최고 투자가치 페어 (상위 5개)")
                        
                        best_pairs_data = []
                        for i, pair in enumerate(summary["overall_best_pairs"][:5], 1):
                            best_pairs_data.append({
                                "순위": i,
                                "페어": f"{pair['stock1_name']} - {pair['stock2_name']}",
                                "기간": pair['period'],
                                "투자점수": f"{pair['investment_score']:.1f}",
                                "수익률": f"{pair['total_return']:.2%}",
                                "샤프비율": f"{pair['sharpe_ratio']:.2f}"
                            })
                        
                        st.dataframe(
                            pd.DataFrame(best_pairs_data),
                            use_container_width=True,
                            hide_index=True
                        )
                
                # HTML 파일 다운로드 링크
                st.subheader("📄 상세 보고서 다운로드")
                
                if os.path.exists(html_file):
                    with open(html_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    st.download_button(
                        label="📥 HTML 보고서 다운로드",
                        data=html_content,
                        file_name=f"kospi_pair_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        help="상세한 기간별 분석 결과가 포함된 HTML 보고서를 다운로드합니다"
                    )
                    
                    st.info("💡 다운로드한 HTML 파일을 브라우저에서 열면 더 자세한 분석 결과를 확인할 수 있습니다.")
                
                # 임시 파일 정리
                if data_source == "📁 KOSPI CSV 파일 업로드" and os.path.exists(csv_file_path):
                    os.remove(csv_file_path)
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                progress_bar.progress(0)
                status_text.text("❌ 분석 실패")
    
    else:
        st.warning("⚠️ 먼저 분석할 종목 데이터를 선택해주세요.")
    
    # 기간별 분석 가이드
    with st.expander("📖 기간별 분석 가이드"):
        st.markdown("""
        ### 🎯 투자가치 점수 산정 기준
        
        각 페어의 투자가치는 다음 요소들을 종합하여 0-100점으로 평가됩니다:
        
        - **총 수익률 (30%)**: 백테스팅 기간 동안의 누적 수익률
        - **샤프 비율 (25%)**: 위험 대비 수익률 (높을수록 좋음)
        - **최대 손실 (20%)**: 최대 낙폭 (낮을수록 좋음) 
        - **승률 (15%)**: 수익을 낸 거래의 비율
        - **상관계수 (10%)**: 두 종목 간 상관관계의 강도
        
        ### 📅 기간별 특성
        
        - **6개월**: 단기 변동성과 최근 트렌드 반영
        - **1년**: 계절성과 연간 사이클 포함
        - **2년**: 중기 시장 사이클과 구조적 변화 반영
        - **5년**: 장기적 구조적 관계와 안정성 확인
        
        ### ⚠️ 주의사항
        
        - 과거 성과가 미래 수익을 보장하지 않습니다
        - 실제 투자 전에는 전문가 조언을 구하세요
        - 거래비용과 세금이 실제 수익률에 영향을 줄 수 있습니다
        """)

if __name__ == "__main__":
    main()
