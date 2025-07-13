# 🇰🇷 한국 주식 페어 트레이딩 분석 시스템

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Korean](https://img.shields.io/badge/Language-Korean-brightgreen.svg)](README.md)

> **한국 주식 시장에 특화된 고도화된 페어 트레이딩 분석 도구**  
> 공적분 검정과 통계적 분석을 통해 수익성 있는 종목 쌍을 발견하고 백테스팅까지 한 번에!

![시스템 스크린샷](https://via.placeholder.com/800x400/4ECDC4/FFFFFF?text=Korean+Stock+Pair+Trading+System)

## 🎯 주요 특징

### 📊 **전체 한국 주식 시장 분석**
- **2,600개 이상의 KOSPI + KOSDAQ 종목** 실시간 분석
- **CSV 파일 업로드** 지원으로 사용자 정의 종목 리스트 분석
- **FinanceDataReader** 기반 고품질 데이터 수집
- **자동 데이터 검증** 및 이상치 처리

### 🔬 **고급 통계 분석**
- **Johansen 공적분 검정**: Engle-Granger보다 정확한 페어 탐지
- **상관관계 + 공적분** 2단계 필터링으로 신뢰성 높은 페어 선별
- **Z-Score 기반 평균 회귀** 전략 자동 생성

### 📈 **기간별 종합 분석 (신규!)**
- **6개월, 1년, 2년, 5년** 기간별 페어 분석
- **투자가치 점수** 기반 페어 랭킹 시스템
- **HTML 보고서** 자동 생성 및 다운로드
- **커맨드라인 독립 실행** 지원

### 📈 **실시간 백테스팅 & 시각화**
- **인터랙티브 차트**: Plotly 기반 전문가급 시각화
- **성과 지표**: 샤프 비율, 최대 손실, 승률 등 종합 분석
- **거래 신호**: 진입/청산 타이밍 시각적 표시
- **탭 기반 UI**: 직관적인 사용자 경험

### ⚡ **최적화된 성능**
- **캐싱 시스템**: 중복 계산 방지로 빠른 응답
- **병렬 처리**: 대용량 데이터 효율적 처리
- **메모리 최적화**: 수천 개 종목도 안정적 분석

## 🚀 빠른 시작

### 1️⃣ 설치

```bash
# 저장소 클론
git clone https://github.com/waterfirst/pair_trading.git
cd pair_trading

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2️⃣ 실행 방법

#### 🖥️ **웹 인터페이스 실행**
```bash
# Streamlit 앱 실행
streamlit run main.py

# 또는 모듈로 실행
python -m streamlit run main.py
```

#### 📊 **기간별 분석 (커맨드라인)**
```bash
# 기본 설정으로 실행
python run_period_analysis.py

# 사용자 정의 설정
python run_period_analysis.py --csv data/kospi_stock.csv --stocks 100 --pairs 20

# 도움말 보기
python run_period_analysis.py --help
```

### 3️⃣ 접속

브라우저에서 `http://localhost:8501` 접속하여 분석을 시작하세요!

## 📋 사용 방법

### 🎮 **웹 인터페이스 사용법**

#### 🔍 **실시간 페어 분석**

1. **⚙️ 분석 설정**
   - 📅 분석 기간 선택 (최근 1년 권장)
   - 📊 상관계수 임계값 설정 (0.8 이상 권장)
   - 🔬 공적분 p-value 설정 (0.05 이하)
   - 📈 Z-Score 진입/청산 기준 설정

2. **🏢 종목 필터링**
   - 시장 선택: KOSPI, KOSDAQ, 또는 전체
   - 최소 시가총액 설정으로 우량주 선별
   - 분석 종목 수 제한 (성능 최적화)

3. **🚀 분석 실행**
   - "실시간 페어 분석 시작" 버튼 클릭
   - 실시간 진행상황 모니터링
   - 발견된 페어 목록 확인

#### 📊 **기간별 종합 분석 (신규!)**

1. **📁 종목 데이터 선택**
   - CSV 파일 업로드 또는 시스템 기본 종목 사용
   - KOSPI 종목 정보 (종목코드, 종목명 필수)

2. **⚙️ 분석 설정**
   - 최대 분석 종목 수: 30-200개
   - 기간별 최대 페어 수: 10-30개
   - 상관계수 및 공적분 임계값 설정

3. **📅 분석 기간**
   - **6개월**: 단기 트렌드 분석
   - **1년**: 연간 패턴 및 계절성 분석
   - **2년**: 중기 시장 사이클 분석
   - **5년**: 장기 구조적 관계 분석

4. **🎯 결과 확인**
   - 기간별 페어 수 및 평균 투자점수
   - 전체 최고 투자가치 페어 순위
   - **HTML 보고서 다운로드** 및 상세 분석

### 🐍 **프로그래밍 인터페이스**

#### 실시간 분석
```python
from src.data_provider import KoreanStockDataProvider
from src.pair_finder import PairFinder
from src.visualizer import PairTradingVisualizer

# 1. 데이터 수집
provider = KoreanStockDataProvider()
stock_list = provider.get_stock_list(market="KOSPI", max_count=100)
price_data = provider.download_stock_data(
    stock_list['Symbol'].tolist(),
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# 2. 페어 찾기
finder = PairFinder(correlation_threshold=0.8, cointegration_pvalue=0.05)
pairs = finder.find_pairs(price_data)

# 3. 백테스팅 및 시각화
visualizer = PairTradingVisualizer()
backtest_results = visualizer.run_backtest(
    price_data[['005930', '000660']], # 삼성전자, SK하이닉스
    '005930', '000660',
    entry_z_score=2.0, exit_z_score=0.5
)
```

#### 기간별 분석
```python
from src.period_analyzer import PeriodAnalyzer

# 분석기 초기화
analyzer = PeriodAnalyzer("data/kospi_stock.csv")

# 전체 기간 분석 실행
results = analyzer.run_full_analysis(
    max_stocks=100,
    max_pairs_per_period=20
)

# HTML 보고서 생성
html_file = analyzer.generate_html_report(results)
```

## 🏗️ 시스템 아키텍처

```
📦 pair_trading/
├── 🎯 main.py                     # Streamlit 메인 애플리케이션
├── 🚀 run_period_analysis.py      # 기간별 분석 독립 실행 스크립트
├── 📊 src/
│   ├── 🏪 data_provider.py        # 한국 주식 데이터 수집
│   ├── 🔍 pair_finder.py          # 공적분 기반 페어 탐지
│   ├── 📈 visualizer.py           # 차트 & 백테스팅 시각화  
│   ├── 📊 period_analyzer.py      # 기간별 분석 & HTML 보고서 생성
│   ├── 🛠️ utils.py                # 유틸리티 함수들
│   └── 📋 __init__.py             # 패키지 초기화
├── 📁 data/
│   └── 📄 kospi_stock.csv         # KOSPI 종목 데이터 (업로드됨)
├── 📊 reports/                    # 생성된 HTML 보고서들
├── 📄 requirements.txt            # 의존성 패키지 목록
├── ⚙️ config.py                   # 시스템 설정 파일
├── 📖 README.md                   # 프로젝트 설명서 (이 파일)
├── 📜 LICENSE                     # MIT 라이선스
└── 🗂️ .gitignore                 # Git 무시 파일 목록
```

### 🔧 **핵심 모듈 설명**

#### 📡 **data_provider.py**
- **FinanceDataReader** 주 엔진, **yfinance** 백업
- 한국 주식 시장 전체 종목 리스트 수집
- 자동 재시도 및 오류 처리
- 데이터 품질 검증 및 정제

#### 🎯 **pair_finder.py**  
- **2단계 페어 선별**: 상관관계 → 공적분 검정
- **Johansen 테스트**: 다변량 공적분 분석
- **통계적 지표**: 반감기, 정상성 점수 등
- **효율적 알고리즘**: 대용량 데이터 최적화

#### 🎨 **visualizer.py**
- **Plotly 기반** 인터랙티브 차트
- **실시간 백테스팅**: Z-Score 전략 구현
- **성과 분석**: 샤프 비율, MDD, 승률 계산
- **거래 신호**: 매수/매도 타이밍 시각화

#### 📊 **period_analyzer.py (신규!)**
- **기간별 종합 분석**: 6개월, 1년, 2년, 5년
- **투자가치 평가**: 다중 지표 기반 점수 산정
- **HTML 보고서**: 전문적인 분석 보고서 생성
- **CSV 파일 지원**: 사용자 정의 종목 리스트

## 📊 분석 예시

### 🏆 **대표적인 페어 발견 사례**

| 페어 | 상관계수 | 공적분 p-value | 연 수익률 | 샤프 비율 | 투자점수 |
|------|----------|----------------|-----------|-----------|----------|
| 삼성전자 ↔ SK하이닉스 | 0.891 | 0.023 | 15.2% | 1.34 | 87.5 |
| 현대차 ↔ 기아 | 0.934 | 0.008 | 22.7% | 1.67 | 92.1 |
| KB금융 ↔ 신한지주 | 0.847 | 0.041 | 11.8% | 1.12 | 78.3 |

### 📈 **기간별 분석 결과 예시**

**기간별 발견 페어 수:**
- 6개월: 12개 페어 (평균 점수: 74.2)
- 1년: 18개 페어 (평균 점수: 71.8)
- 2년: 25개 페어 (평균 점수: 69.5)
- 5년: 31개 페어 (평균 점수: 68.1)

## 🆕 신규 기능 가이드

### 📊 **기간별 종합 분석**

이 시스템의 가장 강력한 기능으로, **여러 기간에 걸쳐 종합적인 페어 분석**을 수행합니다.

#### 🎯 **투자가치 점수 산정**

각 페어의 투자 매력도를 객관적으로 평가하기 위해 다음 5개 지표를 종합합니다:

| 지표 | 가중치 | 설명 |
|------|--------|------|
| 총 수익률 | 30% | 백테스팅 기간 동안의 누적 수익률 |
| 샤프 비율 | 25% | 위험 대비 수익률 (높을수록 좋음) |
| 최대 손실 | 20% | 최대 낙폭 (낮을수록 좋음) |
| 승률 | 15% | 수익을 낸 거래의 비율 |
| 상관계수 | 10% | 두 종목 간 상관관계의 강도 |

#### 📄 **HTML 보고서 특징**

생성되는 HTML 보고서는 다음과 같은 전문적인 기능을 제공합니다:

- 📊 **인터랙티브 테이블**: 정렬, 필터링 가능
- 🎨 **반응형 디자인**: 모바일에서도 최적화된 화면
- 📈 **시각적 지표**: 색상 코딩된 성과 표시
- 📱 **다운로드 가능**: 오프라인에서도 확인 가능
- 🔍 **상세 분석**: 페어별 구체적인 거래 정보

### 📁 **CSV 파일 업로드 기능**

사용자가 직접 준비한 종목 리스트로 분석할 수 있습니다:

#### 📋 **CSV 파일 형식**
```csv
종목코드,종목명,시가총액
005930,삼성전자,500000000000
000660,SK하이닉스,80000000000
035420,NAVER,50000000000
```

#### 🔧 **지원 인코딩**
- UTF-8, CP949, EUC-KR, CP1252, Latin1 자동 감지

#### ✅ **필수 컬럼**
- `종목코드`: 6자리 숫자
- `종목명`: 한글 종목명
- `시가총액` (선택): 종목 우선순위 결정에 사용

## ⚙️ 고급 설정

### 🎛️ **파라미터 튜닝 가이드**

| 파라미터 | 권장값 | 설명 |
|----------|--------|------|
| 상관계수 임계값 | 0.7-0.9 | 높을수록 안정적, 낮을수록 다양한 페어 |
| 공적분 p-value | 0.01-0.05 | 낮을수록 통계적으로 신뢰성 높음 |
| 진입 Z-Score | 1.5-2.5 | 높을수록 보수적, 낮을수록 적극적 |
| 청산 Z-Score | 0.3-0.8 | 낮을수록 빠른 청산 |

### 🔧 **성능 최적화 팁**

```python
# 1. 캐싱 활용
@st.cache_data(ttl=3600)  # 1시간 캐시
def cached_analysis():
    # 무거운 계산 작업
    pass

# 2. 배치 처리
chunk_size = 50  # 한 번에 50개씩 처리
for chunk in chunks(stock_list, chunk_size):
    process_chunk(chunk)

# 3. 메모리 최적화
price_data = price_data.astype('float32')  # 메모리 절약
```

### 📊 **커맨드라인 옵션**

```bash
# 상세 옵션 설명
python run_period_analysis.py \
    --csv data/kospi_stock.csv \     # CSV 파일 경로
    --stocks 100 \                   # 최대 종목 수
    --pairs 20 \                     # 기간별 최대 페어 수
    --correlation 0.8 \              # 상관계수 임계값
    --pvalue 0.05 \                  # 공적분 p-value
    --output reports/my_report.html \ # 출력 파일 경로
    --verbose                        # 상세 진행상황 출력
```

## 🚨 주의사항 및 리스크

### ⚠️ **투자 위험 고지**
- 본 시스템은 **교육 및 연구 목적**으로 개발되었습니다
- **실제 투자 결정**에는 추가적인 분석과 전문가 조언이 필요합니다
- **과거 성과가 미래 수익을 보장하지 않습니다**
- **페어 트레이딩도 손실 위험**이 있는 투자 전략입니다

### 🛡️ **시스템 제한사항**
- **데이터 지연**: 실시간이 아닌 일봉 데이터 기반
- **거래비용 미반영**: 수수료, 세금 등 실제 비용 제외
- **유동성 가정**: 모든 종목이 즉시 거래 가능하다고 가정
- **모델 위험**: 통계 모델의 한계 존재

## 🤝 기여하기

프로젝트 개선에 참여해주세요!

### 🐛 **버그 리포트**
[Issues](https://github.com/waterfirst/pair_trading/issues)에서 버그를 신고해주세요.

### 💡 **기능 제안**
새로운 기능 아이디어가 있다면 [Discussions](https://github.com/waterfirst/pair_trading/discussions)에서 논의해주세요.

### 🔧 **코드 기여**
1. Fork 프로젝트
2. Feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 제출

## 📞 문의 및 지원

- 📧 **이메일**: waterfirst@github.com
- 🐙 **GitHub**: [@waterfirst](https://github.com/waterfirst)
- 💬 **이슈**: [GitHub Issues](https://github.com/waterfirst/pair_trading/issues)

## 📄 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

## 🙏 감사의 말

- **FinanceDataReader**: 한국 주식 데이터 제공
- **Streamlit**: 훌륭한 웹 앱 프레임워크
- **Plotly**: 아름다운 인터랙티브 차트
- **한국 투자자 커뮤니티**: 지속적인 피드백과 지원

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요! ⭐**

</div>

---

## 🔗 관련 링크

- [페어 트레이딩 이론](https://en.wikipedia.org/wiki/Pairs_trade)
- [공적분 검정 설명](https://en.wikipedia.org/wiki/Cointegration)
- [FinanceDataReader 문서](https://financedata.github.io/)
- [Streamlit 문서](https://docs.streamlit.io/)

*마지막 업데이트: 2025년 7월 13일*
