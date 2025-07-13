#!/usr/bin/env python3
"""
KOSPI 종목 기간별 페어 트레이딩 분석 실행 스크립트

이 스크립트는 커맨드라인에서 독립적으로 실행하여
KOSPI 종목들의 기간별 페어 트레이딩 분석을 수행하고
HTML 보고서를 생성합니다.

사용법:
    python run_period_analysis.py [옵션]

예시:
    python run_period_analysis.py --csv data/kospi_stock.csv --stocks 100 --pairs 20
    python run_period_analysis.py --help
"""

import argparse
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.period_analyzer import PeriodAnalyzer

def parse_arguments():
    """명령행 인수를 파싱합니다."""
    
    parser = argparse.ArgumentParser(
        description="KOSPI 종목 기간별 페어 트레이딩 분석",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--csv",
        type=str,
        default="data/kospi_stock.csv",
        help="KOSPI 종목 CSV 파일 경로"
    )
    
    parser.add_argument(
        "--stocks",
        type=int,
        default=50,
        help="분석할 최대 종목 수"
    )
    
    parser.add_argument(
        "--pairs",
        type=int,
        default=15,
        help="기간별 최대 페어 수"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="출력 HTML 파일 경로 (기본값: reports/kospi_pair_analysis_YYYYMMDD_HHMMSS.html)"
    )
    
    parser.add_argument(
        "--correlation",
        type=float,
        default=0.7,
        help="상관계수 임계값 (0.5-0.95)"
    )
    
    parser.add_argument(
        "--pvalue",
        type=float,
        default=0.05,
        help="공적분 p-value 임계값 (0.01-0.1)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세한 진행 상황 출력"
    )
    
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="HTML 보고서 생성하지 않음 (콘솔 출력만)"
    )
    
    return parser.parse_args()

def validate_arguments(args):
    """인수의 유효성을 검사합니다."""
    
    errors = []
    
    # CSV 파일 존재 확인
    if not os.path.exists(args.csv):
        errors.append(f"CSV 파일을 찾을 수 없습니다: {args.csv}")
    
    # 숫자 범위 확인
    if not (1 <= args.stocks <= 1000):
        errors.append("종목 수는 1-1000 범위여야 합니다")
    
    if not (1 <= args.pairs <= 100):
        errors.append("페어 수는 1-100 범위여야 합니다")
    
    if not (0.5 <= args.correlation <= 0.95):
        errors.append("상관계수는 0.5-0.95 범위여야 합니다")
    
    if not (0.01 <= args.pvalue <= 0.1):
        errors.append("p-value는 0.01-0.1 범위여야 합니다")
    
    if errors:
        print("❌ 인수 오류:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

def print_analysis_config(args):
    """분석 설정 정보를 출력합니다."""
    
    print("🔧 분석 설정")
    print("=" * 50)
    print(f"📁 CSV 파일: {args.csv}")
    print(f"📊 최대 종목 수: {args.stocks}개")
    print(f"🔗 기간별 최대 페어 수: {args.pairs}개")
    print(f"📈 상관계수 임계값: {args.correlation}")
    print(f"📉 공적분 p-value: {args.pvalue}")
    print(f"📄 HTML 생성: {'아니오' if args.no_html else '예'}")
    print(f"📝 상세 출력: {'예' if args.verbose else '아니오'}")
    print("=" * 50)

def print_summary(results):
    """분석 결과 요약을 출력합니다."""
    
    if "error" in results:
        print(f"❌ 분석 실패: {results['error']}")
        return
    
    print("\n📊 분석 결과 요약")
    print("=" * 50)
    
    if "summary" in results:
        summary = results["summary"]
        
        # 기간별 페어 수
        if "total_pairs_by_period" in summary:
            print("📅 기간별 발견 페어 수:")
            for period, count in summary["total_pairs_by_period"].items():
                print(f"  - {period}: {count}개")
        
        # 기간별 평균 점수
        if "avg_investment_score_by_period" in summary:
            print("\n📈 기간별 평균 투자가치 점수:")
            for period, score in summary["avg_investment_score_by_period"].items():
                print(f"  - {period}: {score:.1f}점")
        
        # 전체 최고 페어
        if "overall_best_pairs" in summary and summary["overall_best_pairs"]:
            print("\n🏆 전체 최고 투자가치 페어 (상위 5개):")
            for i, pair in enumerate(summary["overall_best_pairs"][:5], 1):
                print(f"  {i}. {pair['stock1_name']} - {pair['stock2_name']}")
                print(f"     기간: {pair['period']}, 점수: {pair['investment_score']:.1f}, "
                      f"수익률: {pair['total_return']:.2%}")

def main():
    """메인 실행 함수"""
    
    # 인수 파싱 및 검증
    args = parse_arguments()
    validate_arguments(args)
    
    # 시작 메시지
    print("🚀 KOSPI 종목 기간별 페어 트레이딩 분석 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 설정 정보 출력
    if args.verbose:
        print_analysis_config(args)
    
    try:
        # PeriodAnalyzer 초기화
        analyzer = PeriodAnalyzer(args.csv)
        
        # 상관계수와 p-value 설정 업데이트
        analyzer.correlation_threshold = args.correlation
        analyzer.cointegration_pvalue = args.pvalue
        
        # 전체 분석 실행
        print("\n🔍 기간별 페어 분석을 수행하고 있습니다...")
        print("⏳ 이 작업은 수 분이 소요될 수 있습니다...\n")
        
        results = analyzer.run_full_analysis(
            max_stocks=args.stocks,
            max_pairs_per_period=args.pairs
        )
        
        # 결과 요약 출력
        print_summary(results)
        
        # HTML 보고서 생성
        if not args.no_html and "error" not in results:
            print("\n📄 HTML 보고서를 생성하고 있습니다...")
            
            # 출력 파일명 설정
            if args.output:
                output_file = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"reports/kospi_pair_analysis_{timestamp}.html"
            
            # 보고서 생성
            html_file = analyzer.generate_html_report(results, output_file)
            
            print(f"✅ HTML 보고서 생성 완료: {html_file}")
            
            # 파일 크기 확인
            if os.path.exists(html_file):
                file_size = os.path.getsize(html_file) / 1024  # KB
                print(f"📁 파일 크기: {file_size:.1f} KB")
        
        print(f"\n🎉 분석 완료! 총 소요 시간: {datetime.now().strftime('%H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 분석이 중단되었습니다.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
