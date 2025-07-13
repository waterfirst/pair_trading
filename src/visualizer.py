import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

class PairTradingVisualizer:
    """
    페어 트레이딩 분석 결과를 시각화하는 클래스
    차트 생성, 백테스팅, 성과 분석 등의 기능 제공
    """
    
    def __init__(self):
        self.color_palette = {
            'primary': '#4ECDC4',
            'secondary': '#FF6B6B', 
            'success': '#2ECC71',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'info': '#3498DB',
            'dark': '#2C3E50',
            'light': '#ECF0F1'
        }
    
    def create_price_comparison_chart(self, price_data: pd.DataFrame, 
                                    stock1_name: str, stock2_name: str) -> go.Figure:
        """
        두 종목의 정규화된 가격 비교 차트를 생성합니다.
        
        Args:
            price_data (pd.DataFrame): 가격 데이터
            stock1_name, stock2_name (str): 종목명
            
        Returns:
            go.Figure: Plotly 차트 객체
        """
        
        # 정규화 (시작점을 100으로)
        normalized_data = price_data.div(price_data.iloc[0]) * 100
        
        fig = go.Figure()
        
        # 첫 번째 종목
        fig.add_trace(go.Scatter(
            x=normalized_data.index,
            y=normalized_data.iloc[:, 0],
            mode='lines',
            name=stock1_name,
            line=dict(color=self.color_palette['primary'], width=2),
            hovertemplate=f'<b>{stock1_name}</b><br>날짜: %{{x}}<br>정규화 가격: %{{y:.2f}}<extra></extra>'
        ))
        
        # 두 번째 종목
        fig.add_trace(go.Scatter(
            x=normalized_data.index,
            y=normalized_data.iloc[:, 1],
            mode='lines',
            name=stock2_name,
            line=dict(color=self.color_palette['secondary'], width=2),
            hovertemplate=f'<b>{stock2_name}</b><br>날짜: %{{x}}<br>정규화 가격: %{{y:.2f}}<extra></extra>'
        ))
        
        # 레이아웃 설정
        fig.update_layout(
            title=f'📈 {stock1_name} vs {stock2_name} 가격 비교 (정규화)',
            xaxis_title='날짜',
            yaxis_title='정규화 가격 (시작점 = 100)',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_spread_analysis_chart(self, backtest_results: Dict, 
                                   stock1_name: str, stock2_name: str,
                                   entry_threshold: float, exit_threshold: float) -> go.Figure:
        """
        스프레드 분석 차트를 생성합니다 (스프레드, Z-Score, 거래 신호).
        
        Args:
            backtest_results (Dict): 백테스트 결과
            stock1_name, stock2_name (str): 종목명
            entry_threshold, exit_threshold (float): 진입/청산 임계값
            
        Returns:
            go.Figure: Plotly 차트 객체
        """
        
        df = backtest_results['data']
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(
                f'📊 {stock1_name} - {stock2_name} 가격 비율',
                '📈 Z-Score 및 거래 신호'
            ),
            row_heights=[0.4, 0.6]
        )
        
        # 가격 비율
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['ratio'],
                mode='lines',
                name='가격 비율',
                line=dict(color=self.color_palette['info'], width=1.5),
                hovertemplate='날짜: %{x}<br>비율: %{y:.4f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Z-Score
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['z_score'],
                mode='lines',
                name='Z-Score',
                line=dict(color=self.color_palette['dark'], width=2),
                hovertemplate='날짜: %{x}<br>Z-Score: %{y:.3f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 임계값 라인
        fig.add_hline(y=entry_threshold, line_dash="dash", line_color=self.color_palette['danger'], 
                     annotation_text=f"진입선 (+{entry_threshold})", row=2, col=1)
        fig.add_hline(y=-entry_threshold, line_dash="dash", line_color=self.color_palette['success'], 
                     annotation_text=f"진입선 (-{entry_threshold})", row=2, col=1)
        fig.add_hline(y=exit_threshold, line_dash="dot", line_color=self.color_palette['warning'], 
                     annotation_text=f"청산선 (+{exit_threshold})", row=2, col=1)
        fig.add_hline(y=-exit_threshold, line_dash="dot", line_color=self.color_palette['warning'], 
                     annotation_text=f"청산선 (-{exit_threshold})", row=2, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1, row=2, col=1)
        
        # 거래 신호 표시
        buy_signals = df[df['signal'] == 'buy']
        sell_signals = df[df['signal'] == 'sell']
        
        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['z_score'],
                    mode='markers',
                    name=f'{stock1_name} 매수 신호',
                    marker=dict(
                        color=self.color_palette['success'],
                        symbol='triangle-up',
                        size=12,
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate='매수 신호<br>날짜: %{x}<br>Z-Score: %{y:.3f}<extra></extra>'
                ),
                row=2, col=1
            )
        
        if not sell_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=sell_signals.index,
                    y=sell_signals['z_score'],
                    mode='markers',
                    name=f'{stock1_name} 매도 신호',
                    marker=dict(
                        color=self.color_palette['danger'],
                        symbol='triangle-down',
                        size=12,
                        line=dict(color='white', width=1)
                    ),
                    hovertemplate='매도 신호<br>날짜: %{x}<br>Z-Score: %{y:.3f}<extra></extra>'
                ),
                row=2, col=1
            )
        
        # 레이아웃 업데이트
        fig.update_layout(
            height=700,
            hovermode='x unified',
            template='plotly_white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(title_text="가격 비율", row=1, col=1)
        fig.update_yaxes(title_text="Z-Score", row=2, col=1)
        fig.update_xaxes(title_text="날짜", row=2, col=1)
        
        return fig
    
    def create_returns_chart(self, backtest_results: Dict, 
                           stock1_name: str, stock2_name: str) -> go.Figure:
        """
        누적 수익률 차트를 생성합니다.
        
        Args:
            backtest_results (Dict): 백테스트 결과
            stock1_name, stock2_name (str): 종목명
            
        Returns:
            go.Figure: Plotly 차트 객체
        """
        
        df = backtest_results['data']
        
        fig = go.Figure()
        
        # 페어 트레이딩 수익률
        fig.add_trace(go.Scatter(
            x=df.index,
            y=(df['cumulative_returns'] - 1) * 100,
            mode='lines',
            name='페어 트레이딩 전략',
            line=dict(color=self.color_palette['primary'], width=3),
            fill='tonexty',
            fillcolor=f'rgba(78, 205, 196, 0.1)',
            hovertemplate='날짜: %{x}<br>누적 수익률: %{y:.2f}%<extra></extra>'
        ))
        
        # 개별 종목 수익률 (정규화)
        stock1_returns = ((df.iloc[:, 0] / df.iloc[0, 0]) - 1) * 100
        stock2_returns = ((df.iloc[:, 1] / df.iloc[0, 1]) - 1) * 100
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=stock1_returns,
            mode='lines',
            name=f'{stock1_name} (개별)',
            line=dict(color=self.color_palette['info'], width=1, dash='dash'),
            hovertemplate=f'{stock1_name}<br>날짜: %{{x}}<br>수익률: %{{y:.2f}}%<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=stock2_returns,
            mode='lines',
            name=f'{stock2_name} (개별)',
            line=dict(color=self.color_palette['warning'], width=1, dash='dash'),
            hovertemplate=f'{stock2_name}<br>날짜: %{{x}}<br>수익률: %{{y:.2f}}%<extra></extra>'
        ))
        
        # 0% 라인
        fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1)
        
        # 레이아웃 설정
        fig.update_layout(
            title=f'💰 누적 수익률 비교: 페어 트레이딩 vs 개별 종목',
            xaxis_title='날짜',
            yaxis_title='누적 수익률 (%)',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def run_backtest(self, price_data: pd.DataFrame, stock1_symbol: str, stock2_symbol: str,
                    entry_z_score: float = 2.0, exit_z_score: float = 0.5) -> Dict:
        """
        페어 트레이딩 백테스트를 실행합니다.
        
        Args:
            price_data (pd.DataFrame): 가격 데이터
            stock1_symbol, stock2_symbol (str): 종목 코드
            entry_z_score (float): 진입 Z-Score 임계값
            exit_z_score (float): 청산 Z-Score 임계값
            
        Returns:
            Dict: 백테스트 결과
        """
        
        df = price_data[[stock1_symbol, stock2_symbol]].copy().dropna()
        
        if len(df) < 30:
            return {
                'data': df,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'signals_df': pd.DataFrame()
            }
        
        # 가격 비율 계산
        df['ratio'] = df[stock1_symbol] / df[stock2_symbol]
        
        # Z-Score 계산 (60일 이동평균/표준편차 사용)
        rolling_window = min(60, len(df) // 4)
        df['ratio_mean'] = df['ratio'].rolling(window=rolling_window).mean()
        df['ratio_std'] = df['ratio'].rolling(window=rolling_window).std()
        df['z_score'] = (df['ratio'] - df['ratio_mean']) / df['ratio_std']
        
        # 거래 신호 생성
        df['signal'] = 'hold'
        df['position'] = 0
        
        # 진입 신호
        df.loc[df['z_score'] > entry_z_score, 'signal'] = 'sell'  # stock1 매도, stock2 매수
        df.loc[df['z_score'] < -entry_z_score, 'signal'] = 'buy'  # stock1 매수, stock2 매도
        
        # 청산 신호
        df.loc[abs(df['z_score']) < exit_z_score, 'signal'] = 'exit'
        
        # 포지션 계산
        current_position = 0
        positions = []
        
        for i, row in df.iterrows():
            if row['signal'] == 'buy' and current_position <= 0:
                current_position = 1
            elif row['signal'] == 'sell' and current_position >= 0:
                current_position = -1
            elif row['signal'] == 'exit':
                current_position = 0
            
            positions.append(current_position)
        
        df['position'] = positions
        
        # 수익률 계산
        df['stock1_returns'] = df[stock1_symbol].pct_change()
        df['stock2_returns'] = df[stock2_symbol].pct_change()
        
        # 전략 수익률 (헤지 비율 고려)
        hedge_ratio = 1.0  # 단순화를 위해 1:1 비율 사용
        df['strategy_returns'] = (
            df['position'].shift(1) * df['stock1_returns'] - 
            df['position'].shift(1) * hedge_ratio * df['stock2_returns']
        )
        
        # 누적 수익률
        df['cumulative_returns'] = (1 + df['strategy_returns'].fillna(0)).cumprod()
        
        # 성과 지표 계산
        total_return = df['cumulative_returns'].iloc[-1] - 1
        
        # 샤프 비율 (연율화)
        strategy_returns_clean = df['strategy_returns'].dropna()
        if len(strategy_returns_clean) > 0 and strategy_returns_clean.std() > 0:
            sharpe_ratio = (strategy_returns_clean.mean() / strategy_returns_clean.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 최대 손실 (MDD)
        peak = df['cumulative_returns'].expanding(min_periods=1).max()
        drawdown = (df['cumulative_returns'] / peak) - 1
        max_drawdown = drawdown.min()
        
        # 승률 계산
        winning_trades = (df['strategy_returns'] > 0).sum()
        total_trades = (df['strategy_returns'] != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 거래 신호 DataFrame 생성
        signals_df = df[df['signal'].isin(['buy', 'sell', 'exit'])].copy()
        signals_df = signals_df[['signal', 'z_score', 'position']].reset_index()
        signals_df.columns = ['날짜', '신호', 'Z-Score', '포지션']
        
        return {
            'data': df,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'signals_df': signals_df
        }
    
    def create_correlation_heatmap(self, price_data: pd.DataFrame, stock_names: Dict = None) -> go.Figure:
        """
        상관관계 히트맵을 생성합니다.
        
        Args:
            price_data (pd.DataFrame): 가격 데이터
            stock_names (Dict): 종목 코드 -> 종목명 매핑
            
        Returns:
            go.Figure: Plotly 히트맵
        """
        
        # 수익률 계산
        returns = price_data.pct_change().dropna()
        
        # 상관관계 행렬
        correlation_matrix = returns.corr()
        
        # 종목명 매핑
        if stock_names:
            symbols = correlation_matrix.columns
            names = [stock_names.get(symbol, symbol) for symbol in symbols]
            correlation_matrix.index = names
            correlation_matrix.columns = names
        
        # 히트맵 생성
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=correlation_matrix.round(3).values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hovertemplate='%{y} vs %{x}<br>상관계수: %{z:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='📊 종목간 상관관계 히트맵',
            xaxis_title='종목',
            yaxis_title='종목',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    def create_performance_summary_chart(self, backtest_results: Dict) -> go.Figure:
        """
        성과 요약 차트를 생성합니다.
        
        Args:
            backtest_results (Dict): 백테스트 결과
            
        Returns:
            go.Figure: Plotly 차트
        """
        
        # 성과 지표
        metrics = [
            '총 수익률 (%)',
            '샤프 비율',
            '최대 손실 (%)',
            '승률 (%)'
        ]
        
        values = [
            backtest_results['total_return'] * 100,
            backtest_results['sharpe_ratio'],
            backtest_results['max_drawdown'] * 100,
            backtest_results['win_rate'] * 100
        ]
        
        colors = [
            self.color_palette['success'] if v >= 0 else self.color_palette['danger'] 
            for v in values
        ]
        
        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=values,
                marker_color=colors,
                text=[f'{v:.2f}' for v in values],
                textposition='auto',
                hovertemplate='%{x}: %{y:.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='📊 페어 트레이딩 성과 요약',
            xaxis_title='성과 지표',
            yaxis_title='값',
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        return fig
