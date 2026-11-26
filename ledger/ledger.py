"""가계부 엑셀 관리 스크립트.

사용 예:
  python3 ledger/ledger.py add 지출 "점심" 12000 --cat 식비 --date 2026-11-26
  python3 ledger/ledger.py add 수입 "월급" 3000000 --cat 급여
  python3 ledger/ledger.py start 500000      # 시작 잔액 설정
  python3 ledger/ledger.py show              # 현재 잔액/요약 출력
"""
import argparse, datetime, os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "가계부.xlsx")
HEAD = ["날짜", "구분", "항목", "카테고리", "수입", "지출", "잔액", "메모"]
WON = '#,##0"원"'
thin = Side(style="thin", color="BBBBBB")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)


def new_book():
    wb = Workbook()
    ws = wb.active
    ws.title = "가계부"
    ws.append(HEAD)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(horizontal="center")
        c.border = BOX
    for col, w in zip("ABCDEFGH", [12, 7, 22, 12, 14, 14, 15, 24]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    # 2행: 시작 잔액
    ws.append([datetime.date.today(), "시작", "시작 잔액", "", 0, 0, "=E2-F2", ""])
    style_row(ws, 2)

    s = wb.create_sheet("요약")
    rows = [("총 수입", "=SUM(가계부!E3:E10000)"),
            ("총 지출", "=SUM(가계부!F3:F10000)"),
            ("시작 잔액", "=가계부!E2"),
            ("현재 잔액", "=가계부!E2+B1-B2")]
    for i, (k, f) in enumerate(rows, 1):
        s.cell(i, 1, k).font = Font(bold=True)
        c = s.cell(i, 2, f)
        c.number_format = WON
    s["A4"].font = Font(bold=True, size=13, color="C00000")
    s["B4"].font = Font(bold=True, size=13, color="C00000")
    s.column_dimensions["A"].width = 12
    s.column_dimensions["B"].width = 18
    s["A6"] = "카테고리별 지출"
    s["A6"].font = Font(bold=True)
    wb.save(PATH)


def style_row(ws, r):
    ws.cell(r, 1).number_format = "yyyy-mm-dd"
    for col in (5, 6, 7):
        ws.cell(r, col).number_format = WON
    ws.cell(r, 5).font = Font(color="2E7D32")
    ws.cell(r, 6).font = Font(color="C62828")
    ws.cell(r, 7).font = Font(bold=True)
    for col in range(1, 9):
        ws.cell(r, col).border = BOX


def refresh_categories(wb):
    ws, s = wb["가계부"], wb["요약"]
    for row in s.iter_rows(min_row=7):
        for c in row:
            c.value = None
    cats = sorted({ws.cell(r, 4).value for r in range(3, ws.max_row + 1)
                   if ws.cell(r, 2).value == "지출" and ws.cell(r, 4).value})
    for i, cat in enumerate(cats, 7):
        s.cell(i, 1, cat)
        c = s.cell(i, 2, f'=SUMIFS(가계부!F:F,가계부!D:D,A{i},가계부!B:B,"지출")')
        c.number_format = WON


def numbers(ws):
    """수식 대신 파이썬으로 계산한 값 (화면 출력용)."""
    start = ws["E2"].value or 0
    inc = sum(ws.cell(r, 5).value or 0 for r in range(3, ws.max_row + 1))
    exp = sum(ws.cell(r, 6).value or 0 for r in range(3, ws.max_row + 1))
    return start, inc, exp, start + inc - exp


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("kind", choices=["수입", "지출"])
    a.add_argument("item")
    a.add_argument("amount", type=int)
    a.add_argument("--cat", default="")
    a.add_argument("--date", default=None)
    a.add_argument("--memo", default="")
    st = sub.add_parser("start")
    st.add_argument("amount", type=int)
    sub.add_parser("show")
    args = p.parse_args()

    if not os.path.exists(PATH):
        new_book()
    wb = load_workbook(PATH)
    ws = wb["가계부"]

    if args.cmd == "add":
        d = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
        r = ws.max_row + 1
        inc = args.amount if args.kind == "수입" else 0
        exp = args.amount if args.kind == "지출" else 0
        ws.append([d, args.kind, args.item, args.cat, inc, exp,
                   f"=G{r-1}+E{r}-F{r}", args.memo])
        style_row(ws, r)
    elif args.cmd == "start":
        ws["E2"] = args.amount

    refresh_categories(wb)
    wb.save(PATH)
    start, inc, exp, bal = numbers(ws)
    print(f"시작 {start:,}원 | 총수입 {inc:,}원 | 총지출 {exp:,}원 | 현재 잔액 {bal:,}원")


if __name__ == "__main__":
    main()
