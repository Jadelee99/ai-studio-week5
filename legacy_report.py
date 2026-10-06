import os
import sqlite3
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY")
DB_URL = os.getenv("DB_URL")
MODEL = os.getenv("MODEL", "claude-sonnet-4-5")
REPORT_MONTH = os.getenv("REPORT_MONTH", "2026-09")

if not API_KEY or not DB_URL:
    raise ValueError("필수 환경 변수(API_KEY, DB_URL)가 설정되지 않았습니다. .env 파일을 확인하세요.")

def connect_db(db_url):
    info = urlparse(db_url)
    print(f"[INFO] DB 접속 시도: 호스트 {info.hostname}:{info.port} / DB {info.path.lstrip('/')}")
    print("[데모] 실제 DB 대신 내장 샘플 데이터를 사용합니다.")

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sales (sold_on TEXT, category TEXT, amount INTEGER)")
    sample = [
        ("2026-09-01", "음료", 4500), ("2026-09-01", "음료", 5000),
        ("2026-09-02", "디저트", 6500), ("2026-09-03", "음료", 4500),
        ("2026-09-05", "원두", 18000), ("2026-09-07", "디저트", 5500),
        ("2026-09-10", "음료", 5500), ("2026-09-12", "원두", 22000),
        ("2026-09-15", "음료", 4500), ("2026-09-18", "디저트", 7000),
        ("2026-09-21", "음료", 5000), ("2026-09-25", "원두", 18000),
        ("2026-08-30", "음료", 4500),
    ]
    conn.executemany("INSERT INTO sales VALUES (?, ?, ?)", sample)
    return conn

def monthly_summary(conn, month):
    rows = conn.execute(
        """SELECT category, COUNT(*), SUM(amount)
           FROM sales
           WHERE substr(sold_on, 1, 7) = ?
           GROUP BY category
           ORDER BY SUM(amount) DESC""",
        (month,),
    ).fetchall()
    return [{"category": c, "count": n, "total": t} for c, n, t in rows]

def request_llm_comment(summary, api_key):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    masked_key = api_key[:7] + "..." if api_key else "None"
    print(f"[DEBUG] LLM 요청 준비 완료 (API Key: {masked_key})")
    
    top = summary[0]["category"] if summary else "없음"
    print(f"[데모] {MODEL} 호출을 생략하고 모의 응답을 사용합니다.")
    return f"[MOCK] 이번 달 매출 1위 카테고리는 '{top}'입니다. 상위 품목 재고를 점검하세요."

def print_report(month, summary, comment):
    total = sum(r["total"] for r in summary)
    print("\n" + "=" * 46)
    print(f"  서강카페 월간 매출 리포트 ({month})")
    print("=" * 46)
    for r in summary:
        share = r["total"] / total * 100 if total else 0
        print(f"  {r['category']:<6} {r['count']:>3}건  {r['total']:>8,}원  ({share:4.1f}%)")
    print("-" * 46)
    print(f"  합계            {total:>8,}원")
    print(f"\n  AI 코멘트: {comment}")
    print("=" * 46)


def main():
    conn = connect_db(DB_URL)
    summary = monthly_summary(conn, REPORT_MONTH)
    comment = request_llm_comment(summary, API_KEY)
    print_report(REPORT_MONTH, summary, comment)
    conn.close()

if __name__ == "__main__":
    main()