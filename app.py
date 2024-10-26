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
st.set_page_config(page_title="KOSPI와 S&P 500 페어트레이딩 분석", layout="wide")

# CSS 스타일
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_and_process_data(start_date, end_date):
    tickers = {"S&P 500": "^GSPC", "KOSPI": "^KS11"}
    data = yf.download(list(tickers.values()), start=start_date, end=end_date)["Close"]
    data.columns = tickers.keys()
    return data.dropna().replace([np.inf, -np.inf], np.nan).dropna()


def correlation_test(y0, y1):
    correlation, p_value = stats.pearsonr(y0, y1)
    return correlation, p_value


def calculate_zscore(spread):
    mean = np.mean(spread)
    std = np.std(spread)
    if std == 0:
        return np.zeros_like(spread)
    return (spread - mean) / std


def normalize_data(data):
    """데이터 정규화 함수"""
    normalized = {}
    for col in data.columns:
        normalized[col] = (
            100 * (data[col] - data[col].min()) / (data[col].max() - data[col].min())
        )
    return pd.DataFrame(normalized)


def create_pair_trading_figure(data, results, best_result, base_asset, normalized_data):
    """페어트레이딩 분석 그래프 생성 함수"""
    other_asset = "KOSPI" if base_asset == "S&P 500" else "S&P 500"

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            f"{base_asset} vs {other_asset}",
            f"Z-Score 및 신호등 ({base_asset} 기반)",
            f"누적 수익률 ({base_asset} 기반)",
        ),
        specs=[
            [{"secondary_y": True}],
            [{"secondary_y": False}],
            [{"secondary_y": False}],
        ],
    )

    # 가격 차트
    fig.add_trace(
        go.Scatter(x=data.index, y=normalized_data[base_asset], name=base_asset),
        row=1,
        col=1,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=data.index, y=normalized_data[other_asset], name=other_asset),
        row=1,
        col=1,
        secondary_y=True,
    )

    # 축 범위 설정
    fig.update_yaxes(
        title_text=base_asset, range=[-5, 105], secondary_y=False, row=1, col=1
    )
    fig.update_yaxes(
        title_text=other_asset, range=[-5, 105], secondary_y=True, row=1, col=1
    )

    # Z-Score
    fig.add_trace(
        go.Scatter(x=results["z_score"].index, y=results["z_score"], name="Z-Score"),
        row=2,
        col=1,
    )
    fig.add_hline(
        y=best_result["entry"], line_dash="dash", line_color="red", row=2, col=1
    )
    fig.add_hline(
        y=-best_result["entry"], line_dash="dash", line_color="green", row=2, col=1
    )
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)

    # 매수/매도 신호
    buy_signals = results["signals"] == "buy"
    sell_signals = results["signals"] == "sell"

    # 매수/매도 신호 표시
    fig.add_trace(
        go.Scatter(
            x=data.index[buy_signals],
            y=normalized_data[base_asset][buy_signals],
            mode="markers",
            marker=dict(color="green", symbol="triangle-up", size=10),
            name="매수 신호",
        ),
        row=1,
        col=1,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index[sell_signals],
            y=normalized_data[base_asset][sell_signals],
            mode="markers",
            marker=dict(color="red", symbol="triangle-down", size=10),
            name="매도 신호",
        ),
        row=1,
        col=1,
        secondary_y=False,
    )

    # 누적 수익률
    fig.add_trace(
        go.Scatter(
            x=results["cumulative_returns"].index,
            y=results["cumulative_returns"],
            name="누적 수익률",
        ),
        row=3,
        col=1,
    )

    # 레이아웃 업데이트
    fig.update_layout(
        height=900,
        title_text=f"{base_asset} 기반 페어트레이딩 분석 (최적화된 Z-Score 사용)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=100, b=50, l=50, r=50),
    )

    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    fig.update_yaxes(title_text="누적 수익률", row=3, col=1)

    return fig


def pair_trading_analysis(data, entry_threshold=2, exit_threshold=0, base_asset="KOSPI"):
    try:
        log_returns = np.log(data / data.shift(1)).dropna()
        correlation, p_value = correlation_test(data["KOSPI"], data["S&P 500"])
        
        # spread 계산 로직 수정 - base_asset에 따라 다르게 계산
        if base_asset == "KOSPI":
            spread = data["KOSPI"] - data["S&P 500"]
        else:  # S&P 500 기반
            spread = data["S&P 500"] - data["KOSPI"]
            
        z_score = calculate_zscore(spread)

        # 신호 생성 로직은 동일하게 유지
        signals = pd.Series(index=z_score.index, data="neutral")
        signals[z_score < -entry_threshold] = "buy"
        signals[z_score > entry_threshold] = "sell"
        signals[(z_score >= -exit_threshold) & (z_score <= exit_threshold)] = "neutral"

        position = pd.Series(
            np.where(
                z_score < -entry_threshold,
                1,
                np.where(z_score > entry_threshold, -1, 0),
            ),
            index=data.index,
        )

        # 수익률 계산 로직
        if base_asset == "KOSPI":
            strategy_returns = (
                log_returns["KOSPI"] - log_returns["S&P 500"]
            ) * position.shift(1).dropna()
        else:  # S&P 500 기반
            strategy_returns = (
                log_returns["S&P 500"] - log_returns["KOSPI"]
            ) * position.shift(1).dropna()

        cumulative_returns = (1 + strategy_returns).cumprod()
        total_return = cumulative_returns.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
        sharpe_ratio = (
            np.sqrt(252) * strategy_returns.mean() / strategy_returns.std()
            if strategy_returns.std() != 0
            else 0
        )

        return {
            "correlation": correlation,
            "p_value": p_value,
            "z_score": z_score,
            "signals": signals,
            "cumulative_returns": cumulative_returns,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio,
            "strategy_returns": strategy_returns,
        }
    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
        return None

def optimize_z_score(data, z_scores, base_asset="KOSPI"):
    log_returns = np.log(data / data.shift(1)).dropna()
    
    # spread 계산 로직 수정
    if base_asset == "KOSPI":
        spread = data["KOSPI"] - data["S&P 500"]
    else:  # S&P 500 기반
        spread = data["S&P 500"] - data["KOSPI"]
        
    z_score = calculate_zscore(spread)

    results = []
    for entry, exit in product(z_scores, repeat=2):
        if entry <= exit:
            continue

        position = pd.Series(0, index=z_score.index)
        position[z_score < -entry] = 1  # 매수 신호
        position[z_score > entry] = -1  # 매도 신호
        position[(z_score >= -exit) & (z_score <= exit)] = 0  # 청산 신호

        if base_asset == "KOSPI":
            strategy_returns = (
                log_returns["KOSPI"] - log_returns["S&P 500"]
            ) * position.shift(1)
        else:  # S&P 500 기반
            strategy_returns = (
                log_returns["S&P 500"] - log_returns["KOSPI"]
            ) * position.shift(1)

        cumulative_returns = (1 + strategy_returns).cumprod()
        total_return = cumulative_returns.iloc[-1] - 1
        std_dev = strategy_returns.std()
        sharpe_ratio = (
            np.sqrt(252) * strategy_returns.mean() / std_dev if std_dev != 0 else 0
        )

        results.append({
            "entry": entry,
            "exit": exit,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
        })

    return pd.DataFrame(results)


def create_heatmap(optimization_results, base_asset):
    """히트맵 생성 함수"""
    pivot_table = optimization_results.pivot(
        index="entry", columns="exit", values="sharpe_ratio"
    )
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale="Viridis",
            colorbar=dict(title="Sharpe Ratio"),
        )
    )
    fig.update_layout(
        title=f"{base_asset} 기반 전략 Z-Score 최적화 결과 (Sharpe Ratio)",
        xaxis_title="퇴출 Z-Score",
        yaxis_title="진입 Z-Score",
    )
    return fig


def main():
    st.title("KOSPI와 S&P 500 페어트레이딩 분석 및 전략 비교")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작 날짜", value=datetime(2023, 1, 1))
    with col2:
        end_date = st.date_input("종료 날짜", value=datetime.now())

    data = load_and_process_data(start_date, end_date)
    if data.empty:
        st.warning("선택한 기간에 대한 데이터가 없습니다. 다른 기간을 선택해주세요.")
        return

    # 데이터 정규화
    normalized_data = normalize_data(data)

    # Z-Score 최적화
    st.subheader("Z-Score 최적화")
    z_scores = np.arange(0.5, 3.1, 0.1)

    # 전략 최적화 및 분석
    strategies = ["KOSPI", "S&P 500"]
    optimizations = {}
    results = {}
    best_results = {}

    for asset in strategies:
        optimizations[asset] = optimize_z_score(data, z_scores, base_asset=asset)
        best_results[asset] = optimizations[asset].loc[
            optimizations[asset]["sharpe_ratio"].idxmax()
        ]
        results[asset] = pair_trading_analysis(
            data,
            entry_threshold=best_results[asset]["entry"],
            exit_threshold=best_results[asset]["exit"],
            base_asset=asset,
        )

    if any(result is None for result in results.values()):
        return

    # 결과 표시
    st.subheader("최적화된 전략 비교 결과")
    cols = st.columns(2)
    for idx, asset in enumerate(strategies):
        with cols[idx]:
            st.write(f"{asset} 기반 전략 (최적화)")
            st.write(f"최적 진입 Z-Score: {best_results[asset]['entry']:.2f}")
            st.write(f"최적 퇴출 Z-Score: {best_results[asset]['exit']:.2f}")
            st.write(f"총 수익률: {results[asset]['total_return']:.2%}")
            st.write(f"연간화 수익률: {results[asset]['annualized_return']:.2%}")
            st.write(f"샤프 비율: {results[asset]['sharpe_ratio']:.2f}")

    # 누적 수익률 비교 그래프
    fig = go.Figure()
    for asset in strategies:
        fig.add_trace(
            go.Scatter(
                x=results[asset]["cumulative_returns"].index,
                y=results[asset]["cumulative_returns"],
                name=f"{asset} 기반 전략",
            )
        )
    fig.update_layout(
        title="누적 수익률 비교", xaxis_title="날짜", yaxis_title="누적 수익률"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 각 전략별 상세 분석 그래프
    for asset in strategies:
        fig = create_pair_trading_figure(
            data, results[asset], best_results[asset], asset, normalized_data
        )
        st.plotly_chart(fig, use_container_width=True)

        # 히트맵
        fig_heatmap = create_heatmap(optimizations[asset], asset)
        st.plotly_chart(fig_heatmap, use_container_width=True)


if __name__ == "__main__":
    main()
