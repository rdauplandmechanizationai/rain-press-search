"""3부처 보도자료 검색 도구 — solution.py

사용법:
    python solution.py <키워드>      예) python solution.py "1,820"
    python solution.py              (인수가 없으면 키워드를 직접 물어봄)

같은 폴더의 보도자료데이터.json 을 읽어 본문에 키워드가 들어 있는 보도자료만 골라
결과_<키워드>.csv (UTF-8, 헤더: 번호·부처·제목·본문) 로 저장하고,
찾은 건수를 화면에 출력한다.

표준 라이브러리(csv · json · sys · pathlib)만 사용한다.
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "보도자료데이터.json"
FIELDS = ["번호", "부처", "제목", "본문"]
# 파일명에 쓸 수 없는 문자 (Windows 기준). 키워드에 섞여 있으면 '_' 로 바꾼다.
UNSAFE_CHARS = '\\/:*?"<>|'


def get_keyword():
    """명령행 인수 또는 프롬프트에서 키워드 1개를 받는다."""
    if len(sys.argv) >= 2:
        keyword = " ".join(sys.argv[1:])  # 따옴표 없이 띄어 쓴 키워드도 하나로 묶는다
    else:
        try:
            keyword = input("검색할 키워드를 입력하세요: ")
        except EOFError:
            keyword = ""
    keyword = keyword.strip()
    if not keyword:
        print("사용법: python solution.py <키워드>")
        sys.exit(1)
    return keyword


def load_articles():
    """보도자료데이터.json 을 읽어 보도자료 목록을 돌려준다."""
    try:
        text = DATA.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"[오류] 데이터 파일이 없습니다: {DATA}")
        sys.exit(1)
    try:
        articles = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 형식이 잘못되었습니다: {e}")
        sys.exit(1)
    if not isinstance(articles, list):
        print("[오류] JSON 최상위는 보도자료 목록(배열)이어야 합니다.")
        sys.exit(1)
    return articles


def plain_text(body):
    """본문에서 마크다운 기호(**, #, ---)를 걷어낸 순수 텍스트.

    원문이 "**1,820명**의" 처럼 굵게 표시돼 있어도 "1,820명의" 로 검색되게 한다.
    """
    lines = []
    for line in body.replace("**", "").splitlines():
        stripped = line.strip()
        if stripped == "---":
            continue
        lines.append(stripped.lstrip("#").strip())
    return "\n".join(lines)


def contains_keyword(article, keyword):
    """본문(원문 또는 마크다운을 걷어낸 본문)에 키워드가 들어 있는지 — 대소문자 무시."""
    body = str(article.get("본문", ""))
    key = keyword.casefold()
    return key in body.casefold() or key in plain_text(body).casefold()


def safe_filename(keyword):
    """키워드를 파일명에 넣을 수 있게 위험 문자를 '_' 로 바꾼다."""
    return "".join("_" if ch in UNSAFE_CHARS else ch for ch in keyword)


def main():
    keyword = get_keyword()
    articles = load_articles()
    filtered = [a for a in articles if contains_keyword(a, keyword)]

    out = HERE / f"결과_{safe_filename(keyword)}.csv"
    # utf-8-sig: BOM 이 붙은 UTF-8. 엑셀에서 바로 열어도 한글이 깨지지 않는다.
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for a in filtered:
            writer.writerow({k: a.get(k, "") for k in FIELDS})

    print(f"[OK] '{keyword}' 포함 보도자료 {len(filtered)}건 저장 → {out.name}")
    for a in filtered:
        print(f"  - [{a.get('번호', '')}] {a.get('부처', '')} | {a.get('제목', '')}")


if __name__ == "__main__":
    main()
