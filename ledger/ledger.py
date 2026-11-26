"""가계부 엑셀 관리 스크립트 (계좌별, 달러).

사용 예:
  python3 ledger/ledger.py start 개인 4267        # 계좌 시작 잔액
  python3 ledger/ledger.py add 지출 개인 "점심" 12.5 --cat 식비 --date 2026-11-26
  python3 ledger/ledger.py add 수입 공동 "월급" 3000 --cat 급여
  python3 ledger/ledger.py show
"""
import argparse, datetime, os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "가계부.xlsx")
HEAD = ["날짜", "구분", "계좌", "항목", "카테고리", "수입", "지출", "전체 잔액", "메모"]
USD = '"$"#,##0.00'
thin = Side(style="thin", color="BBBBBB")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
# 열 번호
DATE, KIND, ACCT, ITEM, CAT, INC, EXP, BAL, MEMO = range(1, 10)


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
    for col, w in zip("ABCDEFGHI", [12, 7, 8, 22, 12, 13, 13, 14, 24]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    wb.create_sheet("요약")
    return wb


def style_row(ws, r):
    ws.cell(r, DATE).number_format = "yyyy-mm-dd"
    for col in (INC, EXP, BAL):
        ws.cell(r, col).number_format = USD
    ws.cell(r, INC).font = Font(color="2E7D32")
    ws.cell(r, EXP).font = Font(color="C62828")
    ws.cell(r, BAL).font = Font(bold=True)
    for col in range(1, 10):
        ws.cell(r, col).border = BOX


def rows(ws):
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, KIND).value:
            yield r


def rebuild_summary(wb):
    ws = wb["가계부"]
    del wb["요약"]
    s = wb.create_sheet("요약")
    s.column_dimensions["A"].width = 14
    for col in "BCDE":
        s.column_dimensions[col].width = 14
    hdr = ["계좌", "시작 잔액", "수입", "지출", "현재 잔액"]
    for i, h in enumerate(hdr, 1):
        c = s.cell(1, i, h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(horizontal="center")
    accts = []
    for r in rows(ws):
        a = ws.cell(r, ACCT).value
        if a and a not in accts:
            accts.append(a)
    R = "가계부!{}:{}"
    F, G, B, C = R.format("F", "F"), R.format("G", "G"), R.format("B", "B"), R.format("C", "C")
    i = 2
    for i, a in enumerate(accts, 2):
        s.cell(i, 1, a)
        s.cell(i, 2, f'=SUMIFS({F},{C},A{i},{B},"시작")')
        s.cell(i, 3, f'=SUMIFS({F},{C},A{i},{B},"수입")')
        s.cell(i, 4, f'=SUMIFS({G},{C},A{i},{B},"지출")')
        s.cell(i, 5, f"=B{i}+C{i}-D{i}")
    t = len(accts) + 2
    s.cell(t, 1, "합계")
    for col in "BCDE":
        s[f"{col}{t}"] = f"=SUM({col}2:{col}{t-1})"
    for r in range(2, t + 1):
        for col in range(2, 6):
            s.cell(r, col).number_format = USD
        s.cell(r, 5).font = Font(bold=True)
    for col in range(1, 6):
        s.cell(t, col).font = Font(bold=True, size=12, color="C00000")
    # 카테고리별 지출
    k = t + 2
    s.cell(k, 1, "카테고리별 지출").font = Font(bold=True)
    cats = sorted({ws.cell(r, CAT).value for r in rows(ws)
                   if ws.cell(r, KIND).value == "지출" and ws.cell(r, CAT).value})
    E = R.format("E", "E")
    for j, cat in enumerate(cats, k + 1):
        s.cell(j, 1, cat)
        c = s.cell(j, 2, f'=SUMIFS({G},{E},A{j},{B},"지출")')
        c.number_format = USD


def totals(ws):
    acc = {}
    for r in rows(ws):
        a, k = ws.cell(r, ACCT).value, ws.cell(r, KIND).value
        inc, exp = ws.cell(r, INC).value or 0, ws.cell(r, EXP).value or 0
        acc[a] = acc.get(a, 0) + inc - exp
    return acc


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("kind", choices=["수입", "지출"])
    a.add_argument("acct")
    a.add_argument("item")
    a.add_argument("amount", type=float)
    a.add_argument("--cat", default="")
    a.add_argument("--date", default=None)
    a.add_argument("--memo", default="")
    st = sub.add_parser("start")
    st.add_argument("acct")
    st.add_argument("amount", type=float)
    st.add_argument("--date", default=None)
    sub.add_parser("show")
    args = p.parse_args()

    wb = load_workbook(PATH) if os.path.exists(PATH) else new_book()
    ws = wb["가계부"]

    if args.cmd in ("add", "start"):
        d = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
        r = max([x for x in rows(ws)] or [1]) + 1
        if args.cmd == "start":
            vals = [d, "시작", args.acct, "시작 잔액", "", args.amount, 0]
        else:
            inc = args.amount if args.kind == "수입" else 0
            exp = args.amount if args.kind == "지출" else 0
            vals = [d, args.kind, args.acct, args.item, args.cat, inc, exp]
        prev = f"H{r-1}+" if r > 2 else ""
        for col, v in enumerate(vals + [f"={prev}F{r}-G{r}", getattr(args, "memo", "")], 1):
            ws.cell(r, col, v)
        style_row(ws, r)

    rebuild_summary(wb)
    wb.save(PATH)
    acc = totals(ws)
    for k, v in acc.items():
        print(f"{k}: ${v:,.2f}")
    print(f"합계: ${sum(acc.values()):,.2f}")


if __name__ == "__main__":
    main()
