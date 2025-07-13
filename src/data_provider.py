import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import yfinance as yf
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

class KoreanStockDataProvider:
    """
    한국 주식 데이터 제공 클래스
    FinanceDataReader를 주로 사용하고 yfinance를 백업으로 활용
    """
    
    def __init__(self):
        self.stock_list_cache = None
        self.cache_timestamp = None
        self.cache_duration = 3600  # 1시간 캐시
    
    def get_stock_list(self, market="전체", min_market_cap=0, max_count=200):
        """
        한국 주식 종목 리스트를 가져옵니다.
        
        Args:
            market (str): "전체", "KOSPI", "KOSDAQ" 중 선택
            min_market_cap (int): 최소 시가총액 (억원)
            max_count (int): 최대 종목 수
            
        Returns:
            pd.DataFrame: 종목 정보 (Symbol, Name, Market, MarketCap 등)
        """
        
        # 캐시 확인
        current_time = datetime.now()
        if (self.stock_list_cache is not None and 
            self.cache_timestamp is not None and
            (current_time - self.cache_timestamp).seconds < self.cache_duration):
            stocks = self.stock_list_cache.copy()
        else:
            # 새로 데이터 가져오기
            try:
                if market == "KOSPI":
                    stocks = fdr.StockListing('KOSPI')
                elif market == "KOSDAQ":
                    stocks = fdr.StockListing('KOSDAQ')
                else:  # 전체
                    kospi = fdr.StockListing('KOSPI')
                    kosdaq = fdr.StockListing('KOSDAQ')
                    stocks = pd.concat([kospi, kosdaq], ignore_index=True)
                
                # 캐시 업데이트
                self.stock_list_cache = stocks.copy()
                self.cache_timestamp = current_time
                
            except Exception as e:
                print(f"주식 리스트 가져오기 실패: {e}")
                return pd.DataFrame()
        
        # 데이터 정리
        if stocks.empty:
            return stocks
        
        # 필요한 컬럼만 선택하고 정리
        required_columns = ['Symbol', 'Name', 'Market']
        available_columns = [col for col in required_columns if col in stocks.columns]
        
        if 'Code' in stocks.columns and 'Symbol' not in stocks.columns:
            stocks['Symbol'] = stocks['Code']
            available_columns = ['Symbol'] + [col for col in required_columns[1:] if col in stocks.columns]
        
        stocks = stocks[available_columns].copy()
        
        # MarketCap 컬럼이 있다면 시가총액 필터링
        if 'MarketCap' in stocks.columns and min_market_cap > 0:
            stocks = stocks[stocks['MarketCap'] >= min_market_cap * 100000000]  # 억원을 원으로 변환
        
        # ETF, SPAC, 우선주 등 제외
        if 'Name' in stocks.columns:
            exclude_keywords = ['ETF', 'ETN', 'SPAC', '우선', '1우', '2우', '3우', 'REIT']
            for keyword in exclude_keywords:
                stocks = stocks[~stocks['Name'].str.contains(keyword, na=False)]
        
        # 상위 종목만 선택 (시가총액 순 또는 가나다순)
        if len(stocks) > max_count:
            if 'MarketCap' in stocks.columns:
                stocks = stocks.nlargest(max_count, 'MarketCap')
            else:
                stocks = stocks.head(max_count)
        
        return stocks.reset_index(drop=True)
    
    def download_stock_data(self, symbols, start_date, end_date, retry_count=3):
        """
        주식 가격 데이터를 다운로드합니다.
        
        Args:
            symbols (list): 종목 코드 리스트
            start_date (datetime): 시작 날짜
            end_date (datetime): 종료 날짜
            retry_count (int): 재시도 횟수
            
        Returns:
            pd.DataFrame: 종가 데이터
        """
        
        price_data = pd.DataFrame()
        successful_symbols = []
        failed_symbols = []
        
        for i, symbol in enumerate(symbols):
            if i % 10 == 0:  # 진행상황 표시
                print(f"진행률: {i}/{len(symbols)} ({i/len(symbols)*100:.1f}%)")
            
            # FinanceDataReader 시도
            data = self._download_with_fdr(symbol, start_date, end_date, retry_count)
            
            # 실패 시 yfinance 시도
            if data is None or data.empty:
                data = self._download_with_yfinance(symbol, start_date, end_date, retry_count)
            
            if data is not None and not data.empty and len(data) > 20:  # 최소 20일 데이터
                price_data[symbol] = data['Close']
                successful_symbols.append(symbol)
            else:
                failed_symbols.append(symbol)
            
            # API 호출 제한 방지
            time.sleep(0.1)
        
        print(f"성공: {len(successful_symbols)}개, 실패: {len(failed_symbols)}개")
        
        # 결측치 처리
        if not price_data.empty:
            # 80% 이상 데이터가 있는 종목만 유지
            valid_threshold = len(price_data) * 0.8
            price_data = price_data.loc[:, price_data.count() >= valid_threshold]
            
            # 전체 기간에서 20% 이상 결측치가 있는 날짜 제거
            valid_date_threshold = len(price_data.columns) * 0.8
            price_data = price_data.loc[price_data.count(axis=1) >= valid_date_threshold]
            
            # 앞뒤 채우기
            price_data = price_data.fillna(method='ffill').fillna(method='bfill')
            
        return price_data.dropna()
    
    def _download_with_fdr(self, symbol, start_date, end_date, retry_count):
        """FinanceDataReader로 데이터 다운로드"""
        for attempt in range(retry_count):
            try:
                data = fdr.DataReader(symbol, start_date, end_date)
                if not data.empty:
                    return data
            except Exception as e:
                if attempt == retry_count - 1:
                    print(f"FDR 실패 - {symbol}: {e}")
                time.sleep(1)
        return None
    
    def _download_with_yfinance(self, symbol, start_date, end_date, retry_count):
        """yfinance로 데이터 다운로드 (백업)"""
        # 한국 주식 티커 형식으로 변환
        if not symbol.endswith('.KS') and not symbol.endswith('.KQ'):
            if len(symbol) == 6:  # 6자리 코드
                yf_symbol = f"{symbol}.KS"  # 일단 KS로 시도
            else:
                return None
        else:
            yf_symbol = symbol
        
        for attempt in range(retry_count):
            try:
                data = yf.download(yf_symbol, start=start_date, end=end_date, progress=False)
                if not data.empty:
                    return data
                
                # KS가 실패하면 KQ로 시도
                if yf_symbol.endswith('.KS'):
                    yf_symbol = yf_symbol.replace('.KS', '.KQ')
                    data = yf.download(yf_symbol, start=start_date, end=end_date, progress=False)
                    if not data.empty:
                        return data
                        
            except Exception as e:
                if attempt == retry_count - 1:
                    print(f"yfinance 실패 - {symbol}: {e}")
                time.sleep(1)
        return None
    
    def get_stock_info(self, symbol):
        """개별 종목 정보 가져오기"""
        try:
            # FinanceDataReader로 기본 정보
            info = fdr.SnapDataReader(symbol)
            return info
        except:
            return None
    
    def validate_symbols(self, symbols):
        """
        종목 코드 유효성 검사
        
        Args:
            symbols (list): 검사할 종목 코드 리스트
            
        Returns:
            list: 유효한 종목 코드 리스트
        """
        valid_symbols = []
        
        for symbol in symbols:
            try:
                # 최근 5일 데이터로 간단히 테스트
                test_data = fdr.DataReader(symbol, 
                                         datetime.now() - timedelta(days=10), 
                                         datetime.now())
                if not test_data.empty:
                    valid_symbols.append(symbol)
            except:
                continue
        
        return valid_symbols
    
    def search_stock(self, query, market="전체"):
        """
        종목 검색 기능
        
        Args:
            query (str): 검색어 (종목명 또는 코드)
            market (str): 시장 구분
            
        Returns:
            pd.DataFrame: 검색 결과
        """
        stock_list = self.get_stock_list(market=market, max_count=3000)
        
        if stock_list.empty:
            return stock_list
        
        # 종목 코드나 이름으로 검색
        mask = (stock_list['Symbol'].str.contains(query, case=False, na=False) |
                stock_list['Name'].str.contains(query, case=False, na=False))
        
        return stock_list[mask].reset_index(drop=True)
