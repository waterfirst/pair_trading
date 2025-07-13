import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import itertools
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class PairFinder:
    """
    페어 트레이딩 가능한 종목 쌍을 찾는 클래스
    상관관계 분석과 공적분 검정을 통해 통계적으로 유의한 페어를 선별
    """
    
    def __init__(self, correlation_threshold=0.8, cointegration_pvalue=0.05):
        """
        초기화
        
        Args:
            correlation_threshold (float): 상관계수 임계값 (0.5-0.95)
            cointegration_pvalue (float): 공적분 검정 p-value 임계값 (0.01-0.1)
        """
        self.correlation_threshold = correlation_threshold
        self.cointegration_pvalue = cointegration_pvalue
        
    def find_pairs(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        주어진 가격 데이터에서 페어 트레이딩 가능한 종목 쌍을 찾습니다.
        
        Args:
            price_data (pd.DataFrame): 종목별 가격 데이터 (컬럼: 종목코드, 인덱스: 날짜)
            
        Returns:
            pd.DataFrame: 발견된 페어 정보 (Stock1, Stock2, Correlation, Cointegration_PValue 등)
        """
        
        if price_data.empty or len(price_data.columns) < 2:
            return pd.DataFrame()
        
        print(f"📊 {len(price_data.columns)}개 종목에서 페어를 찾는 중...")
        
        # 1단계: 상관관계 기반 사전 필터링
        high_corr_pairs = self._find_high_correlation_pairs(price_data)
        
        if not high_corr_pairs:
            print("⚠️ 높은 상관관계를 가진 페어가 없습니다.")
            return pd.DataFrame()
        
        print(f"🔍 {len(high_corr_pairs)}개의 높은 상관관계 페어 발견")
        
        # 2단계: 공적분 검정
        cointegrated_pairs = self._test_cointegration(price_data, high_corr_pairs)
        
        if not cointegrated_pairs:
            print("⚠️ 공적분 관계를 가진 페어가 없습니다.")
            return pd.DataFrame()
        
        print(f"✅ {len(cointegrated_pairs)}개의 공적분 페어 발견")
        
        # 결과를 DataFrame으로 변환
        pairs_df = pd.DataFrame(cointegrated_pairs)
        
        # 정렬 및 정리
        pairs_df = pairs_df.sort_values(['Cointegration_PValue', 'Correlation'], 
                                      ascending=[True, False]).reset_index(drop=True)
        
        return pairs_df
    
    def _find_high_correlation_pairs(self, price_data: pd.DataFrame) -> List[Tuple[str, str, float]]:
        """
        높은 상관관계를 가진 종목 쌍을 찾습니다.
        
        Args:
            price_data (pd.DataFrame): 가격 데이터
            
        Returns:
            List[Tuple]: (stock1, stock2, correlation) 형태의 리스트
        """
        
        # 로그 수익률 계산 (상관관계 분석용)
        log_returns = np.log(price_data / price_data.shift(1)).dropna()
        
        if log_returns.empty:
            return []
        
        # 상관계수 행렬 계산
        correlation_matrix = log_returns.corr()
        
        high_corr_pairs = []
        symbols = correlation_matrix.columns
        
        # 상삼각행렬만 검사 (중복 제거)
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                correlation = correlation_matrix.iloc[i, j]
                
                # 유효한 상관계수이고 임계값을 넘는 경우
                if (not np.isnan(correlation) and 
                    abs(correlation) >= self.correlation_threshold):
                    
                    high_corr_pairs.append((symbols[i], symbols[j], correlation))
        
        return high_corr_pairs
    
    def _test_cointegration(self, price_data: pd.DataFrame, 
                          candidate_pairs: List[Tuple[str, str, float]]) -> List[Dict]:
        """
        후보 페어들에 대해 공적분 검정을 실행합니다.
        
        Args:
            price_data (pd.DataFrame): 가격 데이터
            candidate_pairs (List): 후보 페어 리스트
            
        Returns:
            List[Dict]: 공적분 관계가 있는 페어들의 상세 정보
        """
        
        cointegrated_pairs = []
        
        for i, (stock1, stock2, correlation) in enumerate(candidate_pairs):
            if i % 10 == 0:
                print(f"공적분 검정 진행률: {i}/{len(candidate_pairs)}")
            
            try:
                # 가격 데이터 추출
                s1_prices = price_data[stock1].dropna()
                s2_prices = price_data[stock2].dropna()
                
                # 공통 기간 데이터만 사용
                common_dates = s1_prices.index.intersection(s2_prices.index)
                if len(common_dates) < 30:  # 최소 30일 데이터 필요
                    continue
                
                s1_common = s1_prices[common_dates]
                s2_common = s2_prices[common_dates]
                
                # Engle-Granger 공적분 검정
                coint_result = self._engle_granger_test(s1_common, s2_common)
                
                # Johansen 공적분 검정 (더 정확)
                johansen_result = self._johansen_test(s1_common, s2_common)
                
                # 두 검정 중 하나라도 통과하면 공적분으로 판단
                is_cointegrated = (coint_result['p_value'] < self.cointegration_pvalue or
                                 johansen_result['is_cointegrated'])
                
                if is_cointegrated:
                    # 추가 통계 정보 계산
                    spread_stats = self._calculate_spread_statistics(s1_common, s2_common)
                    
                    pair_info = {
                        'Stock1': stock1,
                        'Stock2': stock2,
                        'Correlation': correlation,
                        'Cointegration_PValue': min(coint_result['p_value'], 
                                                  johansen_result.get('p_value', 1.0)),
                        'EG_PValue': coint_result['p_value'],
                        'EG_Statistic': coint_result['statistic'],
                        'Johansen_Cointegrated': johansen_result['is_cointegrated'],
                        'Spread_Mean': spread_stats['mean'],
                        'Spread_Std': spread_stats['std'],
                        'Spread_StationarityScore': spread_stats['stationarity_score'],
                        'HalfLife': spread_stats['half_life']
                    }
                    
                    cointegrated_pairs.append(pair_info)
                    
            except Exception as e:
                print(f"공적분 검정 오류 ({stock1}-{stock2}): {e}")
                continue
        
        return cointegrated_pairs
    
    def _engle_granger_test(self, s1: pd.Series, s2: pd.Series) -> Dict:
        """
        Engle-Granger 공적분 검정을 실행합니다.
        
        Args:
            s1, s2 (pd.Series): 두 시계열 데이터
            
        Returns:
            Dict: 검정 결과 (statistic, p_value)
        """
        try:
            # 공적분 검정 실행
            score, p_value, _ = coint(s1, s2)
            
            return {
                'statistic': score,
                'p_value': p_value,
                'is_cointegrated': p_value < self.cointegration_pvalue
            }
        except:
            return {
                'statistic': np.nan,
                'p_value': 1.0,
                'is_cointegrated': False
            }
    
    def _johansen_test(self, s1: pd.Series, s2: pd.Series) -> Dict:
        """
        Johansen 공적분 검정을 실행합니다.
        
        Args:
            s1, s2 (pd.Series): 두 시계열 데이터
            
        Returns:
            Dict: 검정 결과
        """
        try:
            # 로그 변환
            log_data = np.log(np.column_stack([s1, s2]))
            
            # Johansen 검정 실행
            result = coint_johansen(log_data, det_order=0, k_ar_diff=1)
            
            # trace 통계량과 임계값 비교 (5% 유의수준)
            trace_stat = result.lr1[0]  # 첫 번째 trace 통계량
            critical_value = result.cvt[0, 1]  # 5% 임계값
            
            is_cointegrated = trace_stat > critical_value
            
            return {
                'trace_statistic': trace_stat,
                'critical_value': critical_value,
                'is_cointegrated': is_cointegrated,
                'p_value': 0.05 if not is_cointegrated else 0.01  # 근사치
            }
        except:
            return {
                'trace_statistic': np.nan,
                'critical_value': np.nan,
                'is_cointegrated': False,
                'p_value': 1.0
            }
    
    def _calculate_spread_statistics(self, s1: pd.Series, s2: pd.Series) -> Dict:
        """
        스프레드의 통계적 특성을 계산합니다.
        
        Args:
            s1, s2 (pd.Series): 두 시계열 데이터
            
        Returns:
            Dict: 스프레드 통계 정보
        """
        try:
            # 로그 가격으로 변환
            log_s1 = np.log(s1)
            log_s2 = np.log(s2)
            
            # 회귀분석으로 헤지 비율 계산
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(log_s2.values.reshape(-1, 1), log_s1.values)
            hedge_ratio = model.coef_[0]
            
            # 스프레드 계산
            spread = log_s1 - hedge_ratio * log_s2
            
            # 기본 통계량
            spread_mean = spread.mean()
            spread_std = spread.std()
            
            # 평균 회귀 반감기 계산
            half_life = self._calculate_half_life(spread)
            
            # 정상성 점수 (ADF 검정 기반)
            stationarity_score = self._calculate_stationarity_score(spread)
            
            return {
                'mean': spread_mean,
                'std': spread_std,
                'hedge_ratio': hedge_ratio,
                'half_life': half_life,
                'stationarity_score': stationarity_score
            }
        except:
            return {
                'mean': np.nan,
                'std': np.nan,
                'hedge_ratio': 1.0,
                'half_life': np.nan,
                'stationarity_score': 0.0
            }
    
    def _calculate_half_life(self, spread: pd.Series) -> float:
        """
        평균 회귀의 반감기를 계산합니다.
        
        Args:
            spread (pd.Series): 스프레드 시계열
            
        Returns:
            float: 반감기 (일 단위)
        """
        try:
            from sklearn.linear_model import LinearRegression
            
            # 스프레드 차분 계산
            spread_lag = spread.shift(1).dropna()
            spread_diff = spread.diff().dropna()
            
            # 공통 인덱스
            common_idx = spread_lag.index.intersection(spread_diff.index)
            spread_lag = spread_lag[common_idx]
            spread_diff = spread_diff[common_idx]
            
            if len(spread_lag) < 10:
                return np.nan
            
            # 회귀분석: Δspread = α + β * spread_{t-1}
            model = LinearRegression()
            model.fit(spread_lag.values.reshape(-1, 1), spread_diff.values)
            beta = model.coef_[0]
            
            # 반감기 = ln(2) / (-β)
            if beta < 0:
                half_life = np.log(2) / (-beta)
                return min(half_life, 252)  # 최대 1년으로 제한
            else:
                return np.nan
        except:
            return np.nan
    
    def _calculate_stationarity_score(self, spread: pd.Series) -> float:
        """
        스프레드의 정상성 점수를 계산합니다 (0-1 범위).
        
        Args:
            spread (pd.Series): 스프레드 시계열
            
        Returns:
            float: 정상성 점수 (1에 가까울수록 정상)
        """
        try:
            from statsmodels.tsa.stattools import adfuller
            
            # ADF 검정
            adf_result = adfuller(spread.dropna())
            adf_pvalue = adf_result[1]
            
            # p-value를 0-1 점수로 변환 (p-value가 낮을수록 높은 점수)
            stationarity_score = max(0, 1 - adf_pvalue)
            
            return stationarity_score
        except:
            return 0.0
    
    def filter_pairs_by_criteria(self, pairs_df: pd.DataFrame, 
                                min_correlation=None,
                                max_pvalue=None,
                                min_stationarity=None,
                                max_half_life=None) -> pd.DataFrame:
        """
        추가 기준으로 페어를 필터링합니다.
        
        Args:
            pairs_df (pd.DataFrame): 페어 데이터프레임
            min_correlation (float): 최소 상관계수
            max_pvalue (float): 최대 p-value
            min_stationarity (float): 최소 정상성 점수
            max_half_life (float): 최대 반감기
            
        Returns:
            pd.DataFrame: 필터링된 페어 데이터프레임
        """
        filtered_df = pairs_df.copy()
        
        if min_correlation is not None:
            filtered_df = filtered_df[abs(filtered_df['Correlation']) >= min_correlation]
        
        if max_pvalue is not None:
            filtered_df = filtered_df[filtered_df['Cointegration_PValue'] <= max_pvalue]
        
        if min_stationarity is not None and 'Spread_StationarityScore' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Spread_StationarityScore'] >= min_stationarity]
        
        if max_half_life is not None and 'HalfLife' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['HalfLife'] <= max_half_life) | 
                (filtered_df['HalfLife'].isna())
            ]
        
        return filtered_df.reset_index(drop=True)
    
    def get_pair_summary(self, pairs_df: pd.DataFrame) -> Dict:
        """
        페어 분석 결과 요약을 제공합니다.
        
        Args:
            pairs_df (pd.DataFrame): 페어 데이터프레임
            
        Returns:
            Dict: 요약 통계
        """
        if pairs_df.empty:
            return {}
        
        summary = {
            'total_pairs': len(pairs_df),
            'avg_correlation': pairs_df['Correlation'].mean(),
            'avg_pvalue': pairs_df['Cointegration_PValue'].mean(),
            'correlation_range': (pairs_df['Correlation'].min(), pairs_df['Correlation'].max()),
            'pvalue_range': (pairs_df['Cointegration_PValue'].min(), pairs_df['Cointegration_PValue'].max())
        }
        
        if 'HalfLife' in pairs_df.columns:
            valid_half_life = pairs_df['HalfLife'].dropna()
            if not valid_half_life.empty:
                summary['avg_half_life'] = valid_half_life.mean()
                summary['half_life_range'] = (valid_half_life.min(), valid_half_life.max())
        
        if 'Spread_StationarityScore' in pairs_df.columns:
            summary['avg_stationarity'] = pairs_df['Spread_StationarityScore'].mean()
        
        return summary
