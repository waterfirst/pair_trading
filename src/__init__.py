"""
한국 주식 페어 트레이딩 분석 시스템

이 패키지는 한국 주식 시장에서 페어 트레이딩이 가능한 종목 쌍을 찾고
분석하는 도구를 제공합니다.

주요 모듈:
- data_provider: 한국 주식 데이터 수집
- pair_finder: 공적분 기반 페어 발견
- visualizer: 차트 및 백테스팅 시각화
- utils: 유틸리티 함수들

사용법:
    from src.data_provider import KoreanStockDataProvider
    from src.pair_finder import PairFinder
    from src.visualizer import PairTradingVisualizer
    
    # 데이터 수집
    provider = KoreanStockDataProvider()
    stock_list = provider.get_stock_list(market="KOSPI", max_count=100)
    price_data = provider.download_stock_data(
        stock_list['Symbol'].tolist(),
        start_date,
        end_date
    )
    
    # 페어 찾기
    finder = PairFinder(correlation_threshold=0.8, cointegration_pvalue=0.05)
    pairs = finder.find_pairs(price_data)
    
    # 시각화
    visualizer = PairTradingVisualizer()
    chart = visualizer.create_price_comparison_chart(price_data, "종목1", "종목2")

작성자: Claude & waterfirst
버전: 1.0.0
라이선스: MIT
"""

__version__ = "1.0.0"
__author__ = "Claude & waterfirst"
__email__ = "waterfirst@github.com"

# 주요 클래스들을 패키지 레벨에서 import 가능하게 설정
from .data_provider import KoreanStockDataProvider
from .pair_finder import PairFinder
from .visualizer import PairTradingVisualizer
from .utils import (
    get_stock_name_mapping,
    clean_stock_name,
    format_percentage,
    format_number,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    clean_price_data,
    create_summary_table
)

__all__ = [
    'KoreanStockDataProvider',
    'PairFinder', 
    'PairTradingVisualizer',
    'get_stock_name_mapping',
    'clean_stock_name',
    'format_percentage',
    'format_number',
    'calculate_sharpe_ratio',
    'calculate_max_drawdown',
    'clean_price_data',
    'create_summary_table'
]
