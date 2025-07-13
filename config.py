"""
한국 주식 페어 트레이딩 시스템 설정 파일

이 파일에는 시스템의 기본 설정값들이 정의되어 있습니다.
필요에 따라 값을 수정하여 사용하세요.
"""

# 앱 기본 설정
APP_CONFIG = {
    'title': '🇰🇷 한국 주식 페어 트레이딩 분석 시스템',
    'page_icon': '📈',
    'layout': 'wide',
    'version': '1.0.0',
    'author': 'Claude & waterfirst',
    'description': '한국 주식 시장에서 페어 트레이딩 가능한 종목 쌍을 찾는 고도화된 분석 시스템'
}

# 데이터 수집 설정
DATA_CONFIG = {
    # 기본 분석 기간 (일)
    'default_period_days': 365,
    
    # 최소 데이터 포인트 수
    'min_data_points': 30,
    
    # 최대 분석 종목 수
    'max_stocks_default': 200,
    'max_stocks_limit': 1000,
    
    # 데이터 품질 임계값
    'data_quality_threshold': 0.8,  # 80% 이상 데이터가 있어야 유효
    
    # API 호출 제한 (초)
    'api_delay': 0.1,
    'retry_count': 3,
    'timeout': 30,
    
    # 캐시 설정 (초)
    'cache_duration': 3600,  # 1시간
    'stock_list_cache_duration': 86400  # 24시간
}

# 페어 분석 설정
PAIR_ANALYSIS_CONFIG = {
    # 기본 임계값
    'default_correlation_threshold': 0.8,
    'default_cointegration_pvalue': 0.05,
    'default_entry_z_score': 2.0,
    'default_exit_z_score': 0.5,
    
    # 임계값 범위
    'correlation_range': (0.5, 0.95),
    'pvalue_range': (0.01, 0.1),
    'z_score_range': (0.5, 3.0),
    
    # 통계 분석 설정
    'rolling_window_days': 60,
    'min_half_life_days': 1,
    'max_half_life_days': 252,
    
    # 백테스팅 설정
    'transaction_cost': 0.0015,  # 0.15% (편도)
    'slippage': 0.001,  # 0.1%
    'risk_free_rate': 0.02  # 2% 연율
}

# 시각화 설정
VISUALIZATION_CONFIG = {
    # 색상 팔레트
    'color_palette': {
        'primary': '#4ECDC4',
        'secondary': '#FF6B6B',
        'success': '#2ECC71',
        'warning': '#F39C12',
        'danger': '#E74C3C',
        'info': '#3498DB',
        'dark': '#2C3E50',
        'light': '#ECF0F1'
    },
    
    # 차트 기본 설정
    'chart_height': 500,
    'chart_template': 'plotly_white',
    'show_logo': False,
    'show_toolbar': True,
    
    # 테이블 설정
    'table_page_size': 50,
    'table_height': 400
}

# 성능 최적화 설정
PERFORMANCE_CONFIG = {
    # 병렬 처리
    'enable_parallel_processing': True,
    'max_workers': 4,
    'chunk_size': 50,
    
    # 메모리 관리
    'memory_limit_gb': 4,
    'enable_memory_optimization': True,
    
    # 진행률 표시
    'show_progress': True,
    'progress_update_interval': 10
}

# 한국 주식 시장 특성
KOREAN_MARKET_CONFIG = {
    # 거래 시간 (KST)
    'market_open': '09:00',
    'market_close': '15:30',
    'lunch_break_start': '12:00',
    'lunch_break_end': '13:00',
    
    # 거래일 설정
    'trading_days_per_year': 252,
    'weekend_days': [5, 6],  # 토요일, 일요일
    
    # 주요 휴장일 (예시)
    'holidays': [
        '2024-01-01',  # 신정
        '2024-02-09',  # 설날 연휴 시작
        '2024-02-10',  # 설날
        '2024-02-11',  # 설날 연휴 끝
        '2024-02-12',  # 설날 대체공휴일
        '2024-03-01',  # 삼일절
        '2024-04-10',  # 국회의원 선거
        '2024-05-05',  # 어린이날
        '2024-05-06',  # 어린이날 대체공휴일
        '2024-05-15',  # 부처님 오신 날
        '2024-06-06',  # 현충일
        '2024-08-15',  # 광복절
        '2024-09-16',  # 추석 연휴 시작
        '2024-09-17',  # 추석
        '2024-09-18',  # 추석 연휴 끝
        '2024-10-03',  # 개천절
        '2024-10-09',  # 한글날
        '2024-12-25'   # 성탄절
    ],
    
    # 섹터 분류
    'major_sectors': {
        '기술/IT': ['005930', '000660', '035420', '035720'],  # 삼성전자, SK하이닉스, NAVER, 카카오
        '자동차': ['005380', '000270', '012330'],  # 현대차, 기아, 현대모비스
        '금융': ['105560', '055550', '086790'],  # KB금융, 신한지주, 하나금융지주
        '화학/소재': ['051910', '096770', '009830'],  # LG화학, SK이노베이션, 한화솔루션
        '바이오/제약': ['068270', '207940', '000100']  # 셀트리온, 삼성바이오로직스, 유한양행
    }
}

# 알림 및 로깅 설정
NOTIFICATION_CONFIG = {
    # 로그 레벨
    'log_level': 'INFO',
    'enable_debug': False,
    
    # 경고 메시지
    'show_warnings': True,
    'show_risk_disclaimer': True,
    
    # 성공/실패 메시지
    'show_success_messages': True,
    'show_error_details': True
}

# 보안 설정
SECURITY_CONFIG = {
    # API 키 보호
    'mask_api_keys': True,
    
    # 데이터 보호
    'anonymize_user_data': True,
    
    # 세션 관리
    'session_timeout_minutes': 60,
    'max_concurrent_sessions': 5
}

# 고급 기능 설정
ADVANCED_CONFIG = {
    # 실험적 기능
    'enable_experimental_features': False,
    
    # 머신러닝 기능
    'enable_ml_features': False,
    'ml_model_path': 'models/',
    
    # 실시간 데이터
    'enable_realtime_data': False,
    'websocket_url': None,
    
    # 백테스팅 고급 옵션
    'enable_portfolio_optimization': False,
    'enable_risk_management': True,
    'enable_dynamic_hedging': False
}

# 환경별 설정 오버라이드
import os

# 개발 환경
if os.getenv('ENV') == 'development':
    DATA_CONFIG['cache_duration'] = 300  # 5분으로 단축
    NOTIFICATION_CONFIG['enable_debug'] = True
    ADVANCED_CONFIG['enable_experimental_features'] = True

# 프로덕션 환경
elif os.getenv('ENV') == 'production':
    PERFORMANCE_CONFIG['max_workers'] = 2  # 서버 리소스 고려
    SECURITY_CONFIG['anonymize_user_data'] = True
    NOTIFICATION_CONFIG['show_error_details'] = False

# 설정 검증 함수
def validate_config():
    """설정값의 유효성을 검증합니다."""
    
    # 상관계수 범위 검증
    min_corr, max_corr = PAIR_ANALYSIS_CONFIG['correlation_range']
    if not (0 <= min_corr <= max_corr <= 1):
        raise ValueError("상관계수 범위가 올바르지 않습니다.")
    
    # p-value 범위 검증
    min_p, max_p = PAIR_ANALYSIS_CONFIG['pvalue_range']
    if not (0 < min_p <= max_p <= 1):
        raise ValueError("p-value 범위가 올바르지 않습니다.")
    
    # Z-Score 범위 검증
    min_z, max_z = PAIR_ANALYSIS_CONFIG['z_score_range']
    if not (0 < min_z <= max_z):
        raise ValueError("Z-Score 범위가 올바르지 않습니다.")
    
    print("✅ 모든 설정값이 유효합니다.")

# 설정 정보 출력 함수
def print_config_summary():
    """주요 설정 정보를 출력합니다."""
    
    print("🔧 한국 주식 페어 트레이딩 시스템 설정")
    print("=" * 50)
    print(f"📱 앱 버전: {APP_CONFIG['version']}")
    print(f"📊 기본 분석 기간: {DATA_CONFIG['default_period_days']}일")
    print(f"🏢 최대 분석 종목: {DATA_CONFIG['max_stocks_default']}개")
    print(f"🔗 상관계수 임계값: {PAIR_ANALYSIS_CONFIG['default_correlation_threshold']}")
    print(f"📈 진입 Z-Score: {PAIR_ANALYSIS_CONFIG['default_entry_z_score']}")
    print(f"⚡ 병렬 처리: {'활성화' if PERFORMANCE_CONFIG['enable_parallel_processing'] else '비활성화'}")
    print("=" * 50)

if __name__ == "__main__":
    validate_config()
    print_config_summary()
