import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Optional
import re
import warnings
warnings.filterwarnings('ignore')

def get_stock_name_mapping(stock_list: pd.DataFrame) -> Dict[str, str]:
    """
    종목 코드와 종목명 매핑 딕셔너리를 생성합니다.
    
    Args:
        stock_list (pd.DataFrame): 종목 정보 DataFrame
        
    Returns:
        Dict[str, str]: {종목코드: 종목명} 형태의 매핑
    """
    if stock_list.empty or 'Symbol' not in stock_list.columns or 'Name' not in stock_list.columns:
        return {}
    
    return dict(zip(stock_list['Symbol'], stock_list['Name']))

def clean_stock_name(name: str) -> str:
    """
    종목명을 정리합니다 (특수문자 제거, 길이 제한 등).
    
    Args:
        name (str): 원본 종목명
        
    Returns:
        str: 정리된 종목명
    """
    if not isinstance(name, str):
        return str(name)
    
    # 특수문자 제거 및 공백 정리
    cleaned = re.sub(r'[^\w\s가-힣]', '', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 길이 제한 (30자)
    if len(cleaned) > 30:
        cleaned = cleaned[:27] + '...'
    
    return cleaned

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    백분율을 포맷팅합니다.
    
    Args:
        value (float): 소수점 형태의 값 (0.1 = 10%)
        decimals (int): 소수점 자릿수
        
    Returns:
        str: 포맷팅된 백분율 문자열
    """
    if pd.isna(value):
        return "N/A"
    
    return f"{value * 100:.{decimals}f}%"

def format_number(value: float, decimals: int = 2) -> str:
    """
    숫자를 포맷팅합니다.
    
    Args:
        value (float): 숫자 값
        decimals (int): 소수점 자릿수
        
    Returns:
        str: 포맷팅된 숫자 문자열
    """
    if pd.isna(value):
        return "N/A"
    
    return f"{value:.{decimals}f}"

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    샤프 비율을 계산합니다.
    
    Args:
        returns (pd.Series): 수익률 시계열
        risk_free_rate (float): 무위험 수익률 (연율)
        
    Returns:
        float: 샤프 비율
    """
    if returns.empty or returns.std() == 0:
        return 0.0
    
    excess_returns = returns - risk_free_rate / 252  # 일일 무위험 수익률
    sharpe = excess_returns.mean() / returns.std() * np.sqrt(252)
    
    return sharpe

def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
    """
    최대 손실(Maximum Drawdown)을 계산합니다.
    
    Args:
        cumulative_returns (pd.Series): 누적 수익률 시계열
        
    Returns:
        float: 최대 손실 (음수)
    """
    if cumulative_returns.empty:
        return 0.0
    
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns / peak) - 1
    
    return drawdown.min()

def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """
    변동성을 계산합니다.
    
    Args:
        returns (pd.Series): 수익률 시계열
        annualize (bool): 연율화 여부
        
    Returns:
        float: 변동성
    """
    if returns.empty:
        return 0.0
    
    volatility = returns.std()
    
    if annualize:
        volatility *= np.sqrt(252)
    
    return volatility

def detect_outliers(data: pd.Series, method: str = 'iqr', threshold: float = 1.5) -> pd.Series:
    """
    이상치를 탐지합니다.
    
    Args:
        data (pd.Series): 데이터 시계열
        method (str): 탐지 방법 ('iqr', 'zscore')
        threshold (float): 임계값
        
    Returns:
        pd.Series: 이상치 여부 (True/False)
    """
    if data.empty:
        return pd.Series(dtype=bool)
    
    if method == 'iqr':
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        outliers = (data < lower_bound) | (data > upper_bound)
        
    elif method == 'zscore':
        z_scores = np.abs((data - data.mean()) / data.std())
        outliers = z_scores > threshold
        
    else:
        raise ValueError("method는 'iqr' 또는 'zscore'여야 합니다.")
    
    return outliers

def clean_price_data(price_data: pd.DataFrame, 
                    outlier_method: str = 'iqr',
                    outlier_threshold: float = 3.0,
                    min_data_points: int = 30) -> pd.DataFrame:
    """
    가격 데이터를 정리합니다.
    
    Args:
        price_data (pd.DataFrame): 가격 데이터
        outlier_method (str): 이상치 탐지 방법
        outlier_threshold (float): 이상치 탐지 임계값
        min_data_points (int): 최소 데이터 포인트 수
        
    Returns:
        pd.DataFrame: 정리된 가격 데이터
    """
    if price_data.empty:
        return price_data
    
    cleaned_data = price_data.copy()
    
    # 1. 무한값과 NaN 제거
    cleaned_data = cleaned_data.replace([np.inf, -np.inf], np.nan)
    
    # 2. 0 또는 음수 가격 제거
    cleaned_data = cleaned_data.where(cleaned_data > 0)
    
    # 3. 이상치 탐지 및 제거 (수익률 기준)
    returns = cleaned_data.pct_change()
    
    for column in returns.columns:
        outliers = detect_outliers(returns[column].dropna(), 
                                 method=outlier_method, 
                                 threshold=outlier_threshold)
        
        if outliers.any():
            # 이상치를 이전 값으로 대체
            outlier_dates = outliers[outliers].index
            for date in outlier_dates:
                if date in cleaned_data.index:
                    prev_date = cleaned_data.index[cleaned_data.index < date]
                    if len(prev_date) > 0:
                        cleaned_data.loc[date, column] = cleaned_data.loc[prev_date[-1], column]
    
    # 4. 데이터 포인트가 부족한 종목 제거
    valid_columns = []
    for column in cleaned_data.columns:
        if cleaned_data[column].count() >= min_data_points:
            valid_columns.append(column)
    
    cleaned_data = cleaned_data[valid_columns]
    
    # 5. 결측치 처리 (앞뒤 채우기)
    cleaned_data = cleaned_data.fillna(method='ffill').fillna(method='bfill')
    
    # 6. 여전히 NaN이 있는 행 제거
    cleaned_data = cleaned_data.dropna()
    
    return cleaned_data

@st.cache_data(ttl=3600)  # 1시간 캐시
def cached_correlation_calculation(price_data: pd.DataFrame) -> pd.DataFrame:
    """
    상관관계 계산을 캐시합니다.
    
    Args:
        price_data (pd.DataFrame): 가격 데이터
        
    Returns:
        pd.DataFrame: 상관관계 행렬
    """
    returns = price_data.pct_change().dropna()
    return returns.corr()

def validate_date_range(start_date, end_date) -> tuple:
    """
    날짜 범위의 유효성을 검사합니다.
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        
    Returns:
        tuple: (유효한 시작날짜, 유효한 종료날짜)
    """
    from datetime import datetime, timedelta
    
    # 문자열을 datetime으로 변환
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 날짜 순서 확인
    if start_date >= end_date:
        end_date = start_date + timedelta(days=1)
    
    # 미래 날짜 확인
    today = datetime.now().date()
    if end_date.date() > today:
        end_date = datetime.combine(today, datetime.min.time())
    
    # 최소 기간 확인 (30일)
    if (end_date - start_date).days < 30:
        start_date = end_date - timedelta(days=365)  # 1년으로 설정
    
    return start_date, end_date

def create_sector_mapping() -> Dict[str, List[str]]:
    """
    한국 주식 섹터 매핑을 생성합니다.
    
    Returns:
        Dict[str, List[str]]: {섹터명: [종목명 키워드 리스트]} 형태
    """
    sector_mapping = {
        '기술/IT': ['삼성전자', 'LG전자', 'SK하이닉스', 'NAVER', '카카오', 'NCSoft', '셀바스AI'],
        '화학/소재': ['LG화학', 'SK이노베이션', '한화솔루션', '롯데케미칼', 'LG생활건강'],
        '자동차': ['현대차', '기아', '현대모비스', '한온시스템', '만도'],
        '금융': ['KB금융', '신한지주', '하나금융지주', '우리금융그룹', '삼성생명'],
        '바이오/제약': ['셀트리온', '삼성바이오로직스', '유한양행', '종근당', '대웅제약'],
        '건설/부동산': ['삼성물산', '현대건설', 'GS건설', '대림산업'],
        '철강/조선': ['POSCO', '현대중공업', '삼성중공업', '대우조선해양'],
        '유통/소비': ['롯데쇼핑', '신세계', '이마트', 'GS리테일'],
        '에너지': ['SK에너지', 'GS칼텍스', '한국전력', 'S-Oil'],
        '통신': ['SK텔레콤', 'KT', 'LG유플러스']
    }
    
    return sector_mapping

def get_stock_sector(stock_name: str, sector_mapping: Dict[str, List[str]] = None) -> str:
    """
    종목명을 기반으로 섹터를 추정합니다.
    
    Args:
        stock_name (str): 종목명
        sector_mapping (Dict): 섹터 매핑 정보
        
    Returns:
        str: 섹터명
    """
    if sector_mapping is None:
        sector_mapping = create_sector_mapping()
    
    for sector, keywords in sector_mapping.items():
        for keyword in keywords:
            if keyword in stock_name:
                return sector
    
    return '기타'

def calculate_portfolio_metrics(returns: pd.DataFrame, weights: Dict[str, float] = None) -> Dict:
    """
    포트폴리오 성과 지표를 계산합니다.
    
    Args:
        returns (pd.DataFrame): 종목별 수익률 데이터
        weights (Dict): 종목별 가중치 (없으면 동일 가중)
        
    Returns:
        Dict: 포트폴리오 성과 지표
    """
    if returns.empty:
        return {}
    
    # 가중치 설정
    if weights is None:
        weights = {col: 1/len(returns.columns) for col in returns.columns}
    
    # 포트폴리오 수익률 계산
    portfolio_returns = sum(returns[stock] * weight for stock, weight in weights.items())
    
    # 성과 지표 계산
    metrics = {
        'total_return': (1 + portfolio_returns).prod() - 1,
        'annualized_return': (1 + portfolio_returns.mean()) ** 252 - 1,
        'volatility': portfolio_returns.std() * np.sqrt(252),
        'sharpe_ratio': calculate_sharpe_ratio(portfolio_returns),
        'max_drawdown': calculate_max_drawdown((1 + portfolio_returns).cumprod()),
        'calmar_ratio': (portfolio_returns.mean() * 252) / abs(calculate_max_drawdown((1 + portfolio_returns).cumprod()))
    }
    
    return metrics

def create_summary_table(pairs_df: pd.DataFrame, stock_names: Dict[str, str] = None) -> pd.DataFrame:
    """
    페어 분석 결과 요약 테이블을 생성합니다.
    
    Args:
        pairs_df (pd.DataFrame): 페어 데이터프레임
        stock_names (Dict): 종목명 매핑
        
    Returns:
        pd.DataFrame: 요약 테이블
    """
    if pairs_df.empty:
        return pd.DataFrame()
    
    summary_df = pairs_df.copy()
    
    # 종목명 추가
    if stock_names:
        summary_df['Stock1_Name'] = summary_df['Stock1'].map(stock_names)
        summary_df['Stock2_Name'] = summary_df['Stock2'].map(stock_names)
        summary_df['페어'] = (summary_df['Stock1_Name'].fillna(summary_df['Stock1']) + 
                           ' ↔ ' + 
                           summary_df['Stock2_Name'].fillna(summary_df['Stock2']))
    else:
        summary_df['페어'] = summary_df['Stock1'] + ' ↔ ' + summary_df['Stock2']
    
    # 필요한 컬럼만 선택하고 포맷팅
    display_columns = ['페어', 'Correlation', 'Cointegration_PValue']
    
    if 'HalfLife' in summary_df.columns:
        display_columns.append('HalfLife')
    
    if 'Spread_StationarityScore' in summary_df.columns:
        display_columns.append('Spread_StationarityScore')
    
    summary_table = summary_df[display_columns].copy()
    
    # 컬럼명 한글화
    column_mapping = {
        'Correlation': '상관계수',
        'Cointegration_PValue': '공적분 p-value',
        'HalfLife': '반감기(일)',
        'Spread_StationarityScore': '정상성 점수'
    }
    
    summary_table = summary_table.rename(columns=column_mapping)
    
    # 수치 포맷팅
    if '상관계수' in summary_table.columns:
        summary_table['상관계수'] = summary_table['상관계수'].apply(lambda x: f"{x:.3f}")
    
    if '공적분 p-value' in summary_table.columns:
        summary_table['공적분 p-value'] = summary_table['공적분 p-value'].apply(lambda x: f"{x:.4f}")
    
    if '반감기(일)' in summary_table.columns:
        summary_table['반감기(일)'] = summary_table['반감기(일)'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )
    
    if '정상성 점수' in summary_table.columns:
        summary_table['정상성 점수'] = summary_table['정상성 점수'].apply(
            lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
        )
    
    return summary_table

def log_analysis_info(message: str, level: str = "INFO"):
    """
    분석 정보를 로깅합니다.
    
    Args:
        message (str): 로그 메시지
        level (str): 로그 레벨
    """
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def estimate_processing_time(num_stocks: int, num_pairs: int = None) -> str:
    """
    처리 시간을 추정합니다.
    
    Args:
        num_stocks (int): 종목 수
        num_pairs (int): 페어 수 (없으면 자동 계산)
        
    Returns:
        str: 예상 처리 시간 메시지
    """
    if num_pairs is None:
        num_pairs = num_stocks * (num_stocks - 1) // 2
    
    # 경험적 추정 (초 단위)
    data_download_time = num_stocks * 0.2  # 종목당 0.2초
    correlation_time = num_pairs * 0.001   # 페어당 0.001초
    cointegration_time = min(num_pairs * 0.1, 500)  # 페어당 0.1초, 최대 500초
    
    total_time = data_download_time + correlation_time + cointegration_time
    
    if total_time < 60:
        return f"예상 처리 시간: 약 {total_time:.0f}초"
    elif total_time < 3600:
        return f"예상 처리 시간: 약 {total_time/60:.1f}분"
    else:
        return f"예상 처리 시간: 약 {total_time/3600:.1f}시간"
