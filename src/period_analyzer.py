import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from src.data_provider import KoreanStockDataProvider
from src.pair_finder import PairFinder
from src.visualizer import PairTradingVisualizer
from src.utils import get_stock_name_mapping, format_percentage, format_number

class PeriodAnalyzer:
    """
    기간별 페어 트레이딩 분석 및 HTML 보고서 생성 클래스
    KOSPI 종목 CSV 파일을 기반으로 여러 기간에 대해 분석 수행
    """
    
    def __init__(self, csv_file_path: str = "data/kospi_stock.csv"):
        self.csv_file_path = csv_file_path
        self.data_provider = KoreanStockDataProvider()
        self.visualizer = PairTradingVisualizer()
        
        # 분석 기간 설정 (월 단위)
        self.periods = {
            "6개월": 6,
            "1년": 12,
            "2년": 24,
            "5년": 60
        }
        
        # 투자가치 평가 가중치
        self.evaluation_weights = {
            'total_return': 0.3,     # 총 수익률
            'sharpe_ratio': 0.25,    # 샤프 비율
            'max_drawdown': 0.2,     # 최대 손실 (음수이므로 역가중)
            'win_rate': 0.15,        # 승률
            'correlation': 0.1       # 상관계수
        }
    
    def load_kospi_stocks(self) -> pd.DataFrame:
        """
        KOSPI 종목 CSV 파일을 읽어서 DataFrame으로 반환합니다.
        인코딩 문제를 해결하고 필요한 컬럼만 추출합니다.
        """
        try:
            # 여러 인코딩으로 시도
            encodings = ['utf-8', 'cp949', 'euc-kr', 'cp1252', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(self.csv_file_path, encoding=encoding)
                    print(f"✅ 파일 로드 성공 (인코딩: {encoding})")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("지원하는 인코딩으로 파일을 읽을 수 없습니다.")
            
            # 컬럼명 정리 (한글 깨짐 문제 해결)
            if len(df.columns) >= 2:
                df.columns = [
                    '종목코드', '종목명', '종가', '대비', '등락률', '시가', 
                    '고가', '저가', '거래량', '거래대금', '시가총액', '상장주식수'
                ][:len(df.columns)]
            
            # 필요한 컬럼만 선택
            required_columns = ['종목코드', '종목명']
            if '시가총액' in df.columns:
                required_columns.append('시가총액')
            
            kospi_stocks = df[required_columns].copy()
            
            # 종목코드 정리 (6자리 숫자로 맞춤)
            kospi_stocks['종목코드'] = kospi_stocks['종목코드'].astype(str).str.zfill(6)
            
            # 결측치 제거
            kospi_stocks = kospi_stocks.dropna(subset=['종목코드', '종목명'])
            
            # 시가총액이 있다면 상위 종목들로 필터링
            if '시가총액' in kospi_stocks.columns:
                kospi_stocks = kospi_stocks.sort_values('시가총액', ascending=False)
            
            print(f"📊 KOSPI 종목 {len(kospi_stocks)}개 로드 완료")
            return kospi_stocks
            
        except Exception as e:
            print(f"❌ CSV 파일 로드 실패: {e}")
            return pd.DataFrame()
    
    def analyze_period(self, period_name: str, period_months: int, 
                      stock_symbols: List[str], stock_names: Dict[str, str],
                      max_pairs: int = 20) -> Dict:
        """
        특정 기간에 대해 페어 분석을 수행합니다.
        
        Args:
            period_name (str): 기간명 (예: "1년")
            period_months (int): 기간 (월 단위)
            stock_symbols (List[str]): 분석할 종목 코드 리스트
            stock_names (Dict[str, str]): 종목 코드 -> 종목명 매핑
            max_pairs (int): 최대 분석할 페어 수
            
        Returns:
            Dict: 분석 결과
        """
        print(f"\n🔍 {period_name} 기간 분석 시작...")
        
        # 날짜 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_months * 30)
        
        try:
            # 가격 데이터 다운로드
            print(f"📈 {len(stock_symbols)}개 종목의 가격 데이터 수집 중...")
            price_data = self.data_provider.download_stock_data(
                stock_symbols, start_date, end_date
            )
            
            if price_data.empty:
                print(f"❌ {period_name}: 가격 데이터가 없습니다.")
                return {"period": period_name, "pairs": [], "error": "데이터 없음"}
            
            print(f"✅ {len(price_data.columns)}개 종목 데이터 수집 완료")
            
            # 페어 찾기
            pair_finder = PairFinder(
                correlation_threshold=0.7,  # 기간이 길수록 더 관대한 기준
                cointegration_pvalue=0.05
            )
            
            pairs_df = pair_finder.find_pairs(price_data)
            
            if pairs_df.empty:
                print(f"⚠️ {period_name}: 유효한 페어가 없습니다.")
                return {"period": period_name, "pairs": [], "error": "페어 없음"}
            
            print(f"🎯 {len(pairs_df)}개 페어 발견")
            
            # 상위 페어들에 대해 백테스팅 수행
            analyzed_pairs = []
            
            for idx, row in pairs_df.head(max_pairs).iterrows():
                stock1 = row['Stock1']
                stock2 = row['Stock2']
                
                # 백테스팅 수행
                backtest_results = self.visualizer.run_backtest(
                    price_data[[stock1, stock2]],
                    stock1, stock2,
                    entry_z_score=2.0,
                    exit_z_score=0.5
                )
                
                # 투자가치 점수 계산
                investment_score = self._calculate_investment_score(
                    backtest_results, row['Correlation']
                )
                
                pair_result = {
                    'stock1_code': stock1,
                    'stock2_code': stock2,
                    'stock1_name': stock_names.get(stock1, stock1),
                    'stock2_name': stock_names.get(stock2, stock2),
                    'correlation': row['Correlation'],
                    'cointegration_pvalue': row['Cointegration_PValue'],
                    'total_return': backtest_results['total_return'],
                    'sharpe_ratio': backtest_results['sharpe_ratio'],
                    'max_drawdown': backtest_results['max_drawdown'],
                    'win_rate': backtest_results['win_rate'],
                    'investment_score': investment_score
                }
                
                analyzed_pairs.append(pair_result)
            
            # 투자가치 점수로 정렬
            analyzed_pairs.sort(key=lambda x: x['investment_score'], reverse=True)
            
            print(f"✅ {period_name} 분석 완료: {len(analyzed_pairs)}개 페어")
            
            return {
                "period": period_name,
                "pairs": analyzed_pairs,
                "total_pairs_found": len(pairs_df),
                "total_stocks_analyzed": len(price_data.columns)
            }
            
        except Exception as e:
            print(f"❌ {period_name} 분석 실패: {e}")
            return {"period": period_name, "pairs": [], "error": str(e)}
    
    def _calculate_investment_score(self, backtest_results: Dict, correlation: float) -> float:
        """
        백테스팅 결과를 바탕으로 투자가치 점수를 계산합니다.
        
        Args:
            backtest_results (Dict): 백테스팅 결과
            correlation (float): 상관계수
            
        Returns:
            float: 투자가치 점수 (0-100)
        """
        
        # 각 지표를 0-100 점수로 정규화
        scores = {}
        
        # 총 수익률 점수 (0% = 50점, 20% = 100점, -10% = 0점)
        total_return = backtest_results['total_return']
        scores['total_return'] = max(0, min(100, 50 + total_return * 250))
        
        # 샤프 비율 점수 (0 = 50점, 2 = 100점, -1 = 0점)
        sharpe_ratio = backtest_results['sharpe_ratio']
        scores['sharpe_ratio'] = max(0, min(100, 50 + sharpe_ratio * 25))
        
        # 최대 손실 점수 (0% = 100점, -10% = 50점, -20% = 0점)
        max_drawdown = abs(backtest_results['max_drawdown'])
        scores['max_drawdown'] = max(0, min(100, 100 - max_drawdown * 500))
        
        # 승률 점수 (50% = 50점, 70% = 100점, 30% = 0점)
        win_rate = backtest_results['win_rate']
        scores['win_rate'] = max(0, min(100, win_rate * 100))
        
        # 상관계수 점수 (0.7 = 70점, 0.9 = 100점, 0.5 = 50점)
        scores['correlation'] = max(0, min(100, abs(correlation) * 100))
        
        # 가중 평균으로 최종 점수 계산
        final_score = sum(
            scores[metric] * weight 
            for metric, weight in self.evaluation_weights.items()
        )
        
        return round(final_score, 2)
    
    def run_full_analysis(self, max_stocks: int = 100, max_pairs_per_period: int = 15) -> Dict:
        """
        전체 기간에 대해 페어 분석을 수행합니다.
        
        Args:
            max_stocks (int): 최대 분석할 종목 수
            max_pairs_per_period (int): 기간별 최대 페어 수
            
        Returns:
            Dict: 전체 분석 결과
        """
        
        print("🚀 KOSPI 종목 기간별 페어 트레이딩 분석 시작")
        print("=" * 60)
        
        # KOSPI 종목 로드
        kospi_stocks = self.load_kospi_stocks()
        
        if kospi_stocks.empty:
            return {"error": "KOSPI 종목 데이터를 로드할 수 없습니다."}
        
        # 상위 종목들 선택
        selected_stocks = kospi_stocks.head(max_stocks)
        stock_symbols = selected_stocks['종목코드'].tolist()
        stock_names = dict(zip(selected_stocks['종목코드'], selected_stocks['종목명']))
        
        print(f"📊 분석 대상: {len(stock_symbols)}개 종목")
        print(f"📅 분석 기간: {', '.join(self.periods.keys())}")
        
        # 기간별 분석 수행
        all_results = {}
        
        for period_name, period_months in self.periods.items():
            result = self.analyze_period(
                period_name, period_months, 
                stock_symbols, stock_names,
                max_pairs_per_period
            )
            all_results[period_name] = result
        
        # 전체 요약 통계
        summary = self._generate_summary(all_results)
        
        return {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_stocks_analyzed": len(stock_symbols),
            "periods_analyzed": list(self.periods.keys()),
            "results": all_results,
            "summary": summary
        }
    
    def _generate_summary(self, all_results: Dict) -> Dict:
        """전체 분석 결과 요약을 생성합니다."""
        
        summary = {
            "total_pairs_by_period": {},
            "avg_investment_score_by_period": {},
            "best_pair_by_period": {},
            "overall_best_pairs": []
        }
        
        all_pairs = []
        
        for period_name, result in all_results.items():
            if "pairs" in result and result["pairs"]:
                pairs = result["pairs"]
                
                # 기간별 통계
                summary["total_pairs_by_period"][period_name] = len(pairs)
                summary["avg_investment_score_by_period"][period_name] = (
                    sum(p["investment_score"] for p in pairs) / len(pairs)
                )
                
                # 기간별 최고 페어
                best_pair = pairs[0] if pairs else None
                if best_pair:
                    summary["best_pair_by_period"][period_name] = {
                        "pair": f"{best_pair['stock1_name']} - {best_pair['stock2_name']}",
                        "score": best_pair["investment_score"],
                        "return": best_pair["total_return"]
                    }
                
                # 전체 페어 수집 (기간 정보 추가)
                for pair in pairs:
                    pair_with_period = pair.copy()
                    pair_with_period["period"] = period_name
                    all_pairs.append(pair_with_period)
        
        # 전체 최고 페어들 (투자가치 기준 상위 10개)
        all_pairs.sort(key=lambda x: x["investment_score"], reverse=True)
        summary["overall_best_pairs"] = all_pairs[:10]
        
        return summary
    
    def generate_html_report(self, analysis_results: Dict, output_file: str = "reports/kospi_pair_analysis_report.html") -> str:
        """
        분석 결과를 HTML 보고서로 생성합니다.
        
        Args:
            analysis_results (Dict): 분석 결과
            output_file (str): 출력 파일 경로
            
        Returns:
            str: 생성된 HTML 파일 경로
        """
        
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # HTML 생성
        html_content = self._generate_html_content(analysis_results)
        
        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML 보고서 생성 완료: {output_file}")
        return output_file
    
    def _generate_html_content(self, results: Dict) -> str:
        """HTML 보고서 내용을 생성합니다."""
        
        # CSS 스타일
        css_style = """
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; padding: 20px; 
                background-color: #f5f5f5; 
                color: #333;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }
            .header { 
                text-align: center; 
                color: #2c3e50; 
                border-bottom: 3px solid #3498db; 
                padding-bottom: 20px; 
                margin-bottom: 30px;
            }
            .summary { 
                background: #ecf0f1; 
                padding: 20px; 
                border-radius: 8px; 
                margin-bottom: 30px;
            }
            .period-section { 
                margin-bottom: 40px; 
                border: 1px solid #ddd; 
                border-radius: 8px; 
                overflow: hidden;
            }
            .period-header { 
                background: linear-gradient(135deg, #3498db, #2980b9); 
                color: white; 
                padding: 15px; 
                font-size: 1.2em; 
                font-weight: bold;
            }
            .period-content { 
                padding: 20px; 
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 15px;
            }
            th, td { 
                padding: 12px; 
                text-align: left; 
                border-bottom: 1px solid #ddd;
            }
            th { 
                background-color: #34495e; 
                color: white; 
                font-weight: bold;
            }
            tr:nth-child(even) { 
                background-color: #f8f9fa; 
            }
            tr:hover { 
                background-color: #e8f4f8; 
            }
            .score-high { 
                color: #27ae60; 
                font-weight: bold; 
            }
            .score-medium { 
                color: #f39c12; 
                font-weight: bold; 
            }
            .score-low { 
                color: #e74c3c; 
                font-weight: bold; 
            }
            .positive { 
                color: #27ae60; 
            }
            .negative { 
                color: #e74c3c; 
            }
            .footer { 
                text-align: center; 
                margin-top: 40px; 
                padding-top: 20px; 
                border-top: 1px solid #ddd; 
                color: #7f8c8d;
            }
            .best-pairs { 
                background: #fff3cd; 
                border: 1px solid #ffeaa7; 
                border-radius: 8px; 
                padding: 20px; 
                margin-bottom: 30px;
            }
            .metric { 
                display: inline-block; 
                margin: 5px 15px 5px 0; 
                padding: 5px 10px; 
                background: #3498db; 
                color: white; 
                border-radius: 15px; 
                font-size: 0.9em;
            }
        </style>
        """
        
        # HTML 헤더
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>KOSPI 종목 페어 트레이딩 분석 보고서</title>
            {css_style}
        </head>
        <body>
        <div class="container">
            <div class="header">
                <h1>🇰🇷 KOSPI 종목 페어 트레이딩 분석 보고서</h1>
                <p>분석 일시: {results.get('analysis_date', 'N/A')}</p>
                <p>분석 종목 수: {results.get('total_stocks_analyzed', 'N/A')}개</p>
            </div>
        """
        
        # 전체 요약
        if "summary" in results:
            html += self._generate_summary_section(results["summary"])
        
        # 전체 최고 페어들
        if "summary" in results and "overall_best_pairs" in results["summary"]:
            html += self._generate_best_pairs_section(results["summary"]["overall_best_pairs"])
        
        # 기간별 분석 결과
        if "results" in results:
            for period_name in ["6개월", "1년", "2년", "5년"]:
                if period_name in results["results"]:
                    html += self._generate_period_section(period_name, results["results"][period_name])
        
        # HTML 푸터
        html += """
            <div class="footer">
                <p>⚠️ <strong>주의사항:</strong> 이 보고서는 교육 및 연구 목적으로 작성되었습니다.</p>
                <p>실제 투자 결정 시에는 전문가의 조언을 구하시기 바랍니다.</p>
                <p>과거 성과가 미래 수익을 보장하지 않습니다.</p>
                <hr>
                <p>Generated by 한국 주식 페어 트레이딩 분석 시스템 v1.0</p>
            </div>
        </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_summary_section(self, summary: Dict) -> str:
        """전체 요약 섹션을 생성합니다."""
        
        html = """
        <div class="summary">
            <h2>📊 분석 요약</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        """
        
        # 기간별 페어 수
        if "total_pairs_by_period" in summary:
            html += "<div><h4>기간별 발견 페어 수</h4><ul>"
            for period, count in summary["total_pairs_by_period"].items():
                html += f"<li>{period}: <strong>{count}개</strong></li>"
            html += "</ul></div>"
        
        # 기간별 평균 투자점수
        if "avg_investment_score_by_period" in summary:
            html += "<div><h4>기간별 평균 투자가치 점수</h4><ul>"
            for period, score in summary["avg_investment_score_by_period"].items():
                html += f"<li>{period}: <strong>{score:.1f}점</strong></li>"
            html += "</ul></div>"
        
        # 기간별 최고 페어
        if "best_pair_by_period" in summary:
            html += "<div><h4>기간별 최고 페어</h4><ul>"
            for period, best in summary["best_pair_by_period"].items():
                html += f"<li>{period}: <strong>{best['pair']}</strong> (점수: {best['score']:.1f})</li>"
            html += "</ul></div>"
        
        html += "</div></div>"
        return html
    
    def _generate_best_pairs_section(self, best_pairs: List[Dict]) -> str:
        """전체 최고 페어 섹션을 생성합니다."""
        
        html = """
        <div class="best-pairs">
            <h2>🏆 전체 최고 투자가치 페어 (상위 10개)</h2>
            <table>
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>페어</th>
                        <th>기간</th>
                        <th>투자점수</th>
                        <th>수익률</th>
                        <th>샤프비율</th>
                        <th>최대손실</th>
                        <th>승률</th>
                        <th>상관계수</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, pair in enumerate(best_pairs, 1):
            score_class = self._get_score_class(pair["investment_score"])
            return_class = "positive" if pair["total_return"] >= 0 else "negative"
            
            html += f"""
                <tr>
                    <td><strong>{i}</strong></td>
                    <td><strong>{pair['stock1_name']} - {pair['stock2_name']}</strong></td>
                    <td>{pair['period']}</td>
                    <td class="{score_class}">{pair['investment_score']:.1f}</td>
                    <td class="{return_class}">{format_percentage(pair['total_return'])}</td>
                    <td>{pair['sharpe_ratio']:.2f}</td>
                    <td class="negative">{format_percentage(pair['max_drawdown'])}</td>
                    <td>{format_percentage(pair['win_rate'])}</td>
                    <td>{pair['correlation']:.3f}</td>
                </tr>
            """
        
        html += "</tbody></table></div>"
        return html
    
    def _generate_period_section(self, period_name: str, period_result: Dict) -> str:
        """기간별 분석 결과 섹션을 생성합니다."""
        
        html = f"""
        <div class="period-section">
            <div class="period-header">
                📅 {period_name} 기간 분석 결과
            </div>
            <div class="period-content">
        """
        
        if "error" in period_result:
            html += f"<p>❌ 분석 실패: {period_result['error']}</p>"
        elif not period_result.get("pairs"):
            html += "<p>⚠️ 이 기간에서는 유효한 페어를 찾지 못했습니다.</p>"
        else:
            pairs = period_result["pairs"]
            
            # 기간별 요약 정보
            html += f"""
            <div style="margin-bottom: 20px;">
                <span class="metric">발견 페어: {len(pairs)}개</span>
                <span class="metric">분석 종목: {period_result.get('total_stocks_analyzed', 'N/A')}개</span>
                <span class="metric">전체 페어: {period_result.get('total_pairs_found', 'N/A')}개</span>
            </div>
            """
            
            # 페어 테이블
            html += """
            <table>
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>페어 (종목명)</th>
                        <th>종목코드</th>
                        <th>투자점수</th>
                        <th>수익률</th>
                        <th>샤프비율</th>
                        <th>최대손실</th>
                        <th>승률</th>
                        <th>상관계수</th>
                        <th>공적분 p-value</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for i, pair in enumerate(pairs, 1):
                score_class = self._get_score_class(pair["investment_score"])
                return_class = "positive" if pair["total_return"] >= 0 else "negative"
                
                html += f"""
                    <tr>
                        <td><strong>{i}</strong></td>
                        <td><strong>{pair['stock1_name']} - {pair['stock2_name']}</strong></td>
                        <td>{pair['stock1_code']} - {pair['stock2_code']}</td>
                        <td class="{score_class}">{pair['investment_score']:.1f}</td>
                        <td class="{return_class}">{format_percentage(pair['total_return'])}</td>
                        <td>{pair['sharpe_ratio']:.2f}</td>
                        <td class="negative">{format_percentage(pair['max_drawdown'])}</td>
                        <td>{format_percentage(pair['win_rate'])}</td>
                        <td>{pair['correlation']:.3f}</td>
                        <td>{pair['cointegration_pvalue']:.4f}</td>
                    </tr>
                """
            
            html += "</tbody></table>"
        
        html += "</div></div>"
        return html
    
    def _get_score_class(self, score: float) -> str:
        """투자점수에 따른 CSS 클래스를 반환합니다."""
        if score >= 70:
            return "score-high"
        elif score >= 50:
            return "score-medium"
        else:
            return "score-low"

# 메인 실행 함수
def main():
    """기간별 페어 분석을 실행하고 HTML 보고서를 생성합니다."""
    
    analyzer = PeriodAnalyzer()
    
    # 전체 분석 실행
    print("🚀 KOSPI 종목 기간별 페어 트레이딩 분석을 시작합니다...")
    
    results = analyzer.run_full_analysis(
        max_stocks=50,  # 분석할 종목 수 (너무 많으면 시간이 오래 걸림)
        max_pairs_per_period=15  # 기간별 최대 페어 수
    )
    
    if "error" in results:
        print(f"❌ 분석 실패: {results['error']}")
        return
    
    # HTML 보고서 생성
    html_file = analyzer.generate_html_report(results)
    
    print(f"\n✅ 분석 완료!")
    print(f"📄 HTML 보고서: {html_file}")
    print("\n📊 분석 요약:")
    
    if "summary" in results:
        summary = results["summary"]
        
        # 기간별 페어 수 출력
        if "total_pairs_by_period" in summary:
            for period, count in summary["total_pairs_by_period"].items():
                print(f"  - {period}: {count}개 페어")
        
        # 전체 최고 페어
        if "overall_best_pairs" in summary and summary["overall_best_pairs"]:
            best = summary["overall_best_pairs"][0]
            print(f"\n🏆 최고 페어: {best['stock1_name']} - {best['stock2_name']}")
            print(f"   투자점수: {best['investment_score']:.1f}점")
            print(f"   수익률: {format_percentage(best['total_return'])}")
            print(f"   기간: {best['period']}")

if __name__ == "__main__":
    main()
