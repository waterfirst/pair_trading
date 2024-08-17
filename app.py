import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from itertools import product
from scipy import stats

# 페이지 설정
st.set_page_config(page_title="KOSPI와 S&P 200 페어트레이딩 분석", layout="wide")

# CSS 스타일
st.markdown("""
<style>
    .reportview-container .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5px;
        padding-right: 5px;
    }
    .stPlotlyChart {
        height: 70vh !important;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_process_data(start_date, end_date):
    tickers = {"KOSPI": "^KS11", "S&P 200": "^AXJO"}
    data = yf.download(list(tickers.values()), start=start_date, end=end_date)['Close']
    data.columns = tickers.keys()
    return data.dropna().replace([np.inf, -np.inf], np.nan).dropna()

# 상관관계 테스트 함수
def correlation_test(y0, y1):
    correlation, p_value = stats.pearsonr(y0, y1)
    return correlation, p_value

# Z-score 계산 함수 (0으로 나누는 문제 방지)
def calculate_zscore(spread):
    mean = np.mean(spread)
    std = np.std(spread)
    if std == 0:
        return np.zeros_like(spread)
    return (spread - mean) / std

# 페어트레이딩 분석 함수
def pair_trading_analysis(data, entry_threshold=2, exit_threshold=0):
    try:
        log_returns = np.log(data / data.shift(1)).dropna()
        correlation, p_value = correlation_test(data["KOSPI"], data["S&P 200"])
        spread = data["KOSPI"] - data["S&P 200"]
        z_score = calculate_zscore(spread)
        
        signals = pd.Series(index=z_score.index, data='neutral')
        signals[z_score < -entry_threshold] = 'buy'
        signals[z_score > entry_threshold] = 'sell'
        signals[(z_score >= -exit_threshold) & (z_score <= exit_threshold)] = 'neutral'
        
        position = pd.Series(np.where(z_score < -entry_threshold, 1, np.where(z_score > entry_threshold, -1, 0)), index=data.index)
        strategy_returns = (log_returns["KOSPI"] - log_returns["S&P 200"]) * position.shift(1).dropna()
        cumulative_returns = (1 + strategy_returns).cumprod()
        
        total_return = cumulative_returns.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
        sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std() if strategy_returns.std() != 0 else 0
        
        return {
            "correlation": correlation,
            "p_value": p_value,
            "z_score": z_score,
            "signals": signals,
            "cumulative_returns": cumulative_returns,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio
        }
    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
        return None

# Z-Score 최적화 함수
def optimize_z_score(data, z_scores):
    log_returns = np.log(data / data.shift(1)).dropna()
    spread = data["KOSPI"] - data["S&P 200"]
    z_score = calculate_zscore(spread)
    
    results = []
    for entry, exit in product(z_scores, repeat=2):
        if entry <= exit:
            continue
        
        position = pd.Series(0, index=z_score.index)
        position[z_score < -entry] = 1  # 매수 신호
        position[z_score > entry] = -1  # 매도 신호
        position[(z_score >= -exit) & (z_score <= exit)] = 0  # 청산 신호
        
        strategy_returns = (log_returns["KOSPI"] - log_returns["S&P 200"]) * position.shift(1)
        cumulative_returns = (1 + strategy_returns).cumprod()
        total_return = cumulative_returns.iloc[-1] - 1
        std_dev = strategy_returns.std()
        sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / std_dev if std_dev != 0 else 0
        
        results.append({
            "entry": entry,
            "exit": exit,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio
        })
    
    return pd.DataFrame(results)

# 메인 앱 함수
def main():
    st.title("KOSPI와 S&P 200 페어트레이딩 분석 및 Z-Score 최적화")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작 날짜", value=datetime(2020, 1, 1))
    with col2:
        end_date = st.date_input("종료 날짜", value=datetime.now())
    
    data = load_and_process_data(start_date, end_date)
    
    if data.empty:
        st.warning("선택한 기간에 대한 데이터가 없습니다. 다른 기간을 선택해주세요.")
        return
    
    analysis_results = pair_trading_analysis(data)
    
    if analysis_results is None:
        return
    
    st.subheader("페어트레이딩 분석 결과")
    
    st.write(f"상관계수: {analysis_results['correlation']:.4f}")
    st.write(f"p-값: {analysis_results['p_value']:.4f}")
    if analysis_results['p_value'] < 0.05:
        st.write("KOSPI와 S&P 200은 통계적으로 유의한 상관관계를 가지고 있어 페어트레이딩에 적합할 수 있습니다.")
    else:
        st.write("KOSPI와 S&P 200의 상관관계가 약하여 페어트레이딩에 주의가 필요합니다.")

    # Z-Score 최적화
    st.subheader("Z-Score 최적화")
    z_scores = np.arange(0.5, 3.1, 0.1)
    optimization_results = optimize_z_score(data, z_scores)
    
    if optimization_results.empty:
        st.warning("최적화 결과를 얻을 수 없습니다. 데이터를 확인해 주세요.")
        return
    
    best_result = optimization_results.loc[optimization_results['sharpe_ratio'].idxmax()]
    st.write(f"최적 Z-Score 진입 지점: {best_result['entry']:.2f}")
    st.write(f"최적 Z-Score 퇴출 지점: {best_result['exit']:.2f}")
    st.write(f"최대 샤프 비율: {best_result['sharpe_ratio']:.2f}")
    st.write(f"총 수익률: {best_result['total_return']:.2%}")

    # 최적화된 성과 지표
    optimized_results = pair_trading_analysis(data, entry_threshold=best_result['entry'], exit_threshold=best_result['exit'])
    st.subheader("최적화된 전략 성과")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 수익률", f"{optimized_results['total_return']:.2%}")
    col2.metric("연간화 수익률", f"{optimized_results['annualized_return']:.2%}")
    col3.metric("샤프 비율", f"{optimized_results['sharpe_ratio']:.2f}")
    
    
    # 이중축 그래프 생성
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("KOSPI vs S&P 200", "Z-Score 및 신호등", "누적 수익률"),
                        specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]])
    
    # KOSPI vs S&P 200 (이중축)
    fig.add_trace(go.Scatter(x=data.index, y=data["KOSPI"], name="KOSPI"), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=data.index, y=data["S&P 200"], name="S&P 200"), row=1, col=1, secondary_y=True)
    
    # Z-Score 및 신호등
    fig.add_trace(go.Scatter(x=optimized_results['z_score'].index, y=optimized_results['z_score'], name="Z-Score"), row=2, col=1)
    fig.add_hline(y=best_result['entry'], line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=-best_result['entry'], line_dash="dash", line_color="green", row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    
    # 신호등 표시
    buy_signals = optimized_results['signals'] == 'buy'
    sell_signals = optimized_results['signals'] == 'sell'
    
    fig.add_trace(go.Scatter(x=data.index[buy_signals], y=data["KOSPI"][buy_signals],
                             mode='markers', marker=dict(color='green', symbol='triangle-up', size=10),
                             name='매수 신호'), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=data.index[sell_signals], y=data["KOSPI"][sell_signals],
                             mode='markers', marker=dict(color='red', symbol='triangle-down', size=10),
                             name='매도 신호'), row=1, col=1, secondary_y=False)
    
    # 누적 수익률
    fig.add_trace(go.Scatter(x=optimized_results['cumulative_returns'].index, 
                             y=optimized_results['cumulative_returns'], name="누적 수익률"), row=3, col=1)
    
    # 레이아웃 업데이트
    fig.update_layout(
        height=900,
        title_text="KOSPI와 S&P 200 페어트레이딩 분석 (최적화된 Z-Score 사용)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    # Y축 레이블 설정
    fig.update_yaxes(title_text="KOSPI", secondary_y=False, row=1, col=1)
    fig.update_yaxes(title_text="S&P 200", secondary_y=True, row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    fig.update_yaxes(title_text="누적 수익률", row=3, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 최적화 결과 히트맵
    pivot_table = optimization_results.pivot(index="entry", columns="exit", values="sharpe_ratio")
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale='Viridis',
        colorbar=dict(title='Sharpe Ratio')
    ))
    fig_heatmap.update_layout(
        title='Z-Score 최적화 결과 (Sharpe Ratio)',
        xaxis_title='퇴출 Z-Score',
        yaxis_title='진입 Z-Score'
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

if __name__ == "__main__":
    main()