"""가계부 관리 스크립트 (달러).

기록은 ledger/data.json 에 저장하고, 실행할 때마다 ledger/가계부.xlsx 를 새로 만든다.
엑셀 구성: 계좌마다 시트 하나 (왼쪽 = 수입, 오른쪽 = 지출) + 요약 시트.

사용 예:
  python3 ledger/ledger.py start 개인 4267
  python3 ledger/ledger.py add 지출 개인 "점심" 12.5 --cat 식비 --date 2026-11-26
  python3 ledger/ledger.py add 수입 공동 "월급" 3000 --cat 급여
  python3 ledger/ledger.py show
"""
import argparse, datetime, json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(DIR, "data.json")
XLSX = os.path.join(DIR, "가계부.xlsx")
USD = '"$"#,##0.00'
thin = Side(style="thin", color="BBBBBB")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
GREEN, RED, BLUE = "2E7D32", "C62828", "305496"
HDR = ["날짜", "항목", "카테고리", "금액", "메모"]
LAST = 2000  # 합계 수식 범위


def load():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    return {"accounts": {}}


def save(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def acct(d, name):
    return d["accounts"].setdefault(name, {"start": 0, "수입": [], "지출": []})


def fill(c, color, white=True):
    c.fill = PatternFill("solid", fgColor=color)
    c.font = Font(bold=True, color="FFFFFF" if white else "000000")
    c.alignment = Alignment(horizontal="center")


def account_sheet(wb, name, a):
    ws = wb.create_sheet(name)
    ws["A1"] = f"{name} 계좌 가계부"
    ws["A1"].font = Font(bold=True, size=14)
    # 잔액 상자
    box = [("A2", "시작 잔액", "B2", a["start"]),
           ("C2", "총 수입", "D2", f"=SUM(D6:D{LAST})"),
           ("G2", "총 지출", "H2", f"=SUM(J6:J{LAST})"),
           ("I2", "현재 잔액", "J2", "=B2+D2-H2")]
    for lc, label, vc, val in box:
        ws[lc] = label
        ws[lc].font = Font(bold=True)
        ws[vc] = val
        ws[vc].number_format = USD
        ws[vc].font = Font(bold=True)
    ws["D2"].font = Font(bold=True, color=GREEN)
    ws["H2"].font = Font(bold=True, color=RED)
    ws["I2"].font = ws["J2"].font = Font(bold=True, size=12, color="C00000")
    # 두 표
    for kind, col0, color in (("수입", 1, GREEN), ("지출", 7, RED)):
        ws.merge_cells(start_row=4, start_column=col0, end_row=4, end_column=col0 + 4)
        c = ws.cell(4, col0, kind)
        fill(c, color)
        for i, h in enumerate(HDR):
            c = ws.cell(5, col0 + i, h)
            fill(c, BLUE)
            c.border = BOX
        for r, e in enumerate(sorted(a[kind], key=lambda e: e["date"]), 6):
            vals = [datetime.date.fromisoformat(e["date"]), e["item"], e.get("cat", ""),
                    e["amount"], e.get("memo", "")]
            for i, v in enumerate(vals):
                c = ws.cell(r, col0 + i, v)
                c.border = BOX
            ws.cell(r, col0).number_format = "yyyy-mm-dd"
            m = ws.cell(r, col0 + 3)
            m.number_format = USD
            m.font = Font(color=color)
    for col, w in zip("ABCDEFGHIJK", [12, 22, 12, 13, 18, 3, 12, 22, 12, 13, 18]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A6"


def build(d):
    wb = Workbook()
    s = wb.active
    s.title = "요약"
    names = list(d["accounts"])
    for n in names:
        account_sheet(wb, n, d["accounts"][n])

    s["A1"] = "전체 요약"
    s["A1"].font = Font(bold=True, size=14)
    for i, h in enumerate(["계좌", "시작 잔액", "수입", "지출", "현재 잔액"], 1):
        fill(s.cell(3, i, h), BLUE)
    r = 3
    for r, n in enumerate(names, 4):
        s.cell(r, 1, n)
        for col, ref in zip(range(2, 6), ["B2", "D2", "H2", "J2"]):
            s.cell(r, col, f"='{n}'!{ref}")
    t = r + 1
    s.cell(t, 1, "합계")
    for col in "BCDE":
        s[f"{col}{t}"] = f"=SUM({col}4:{col}{t-1})"
    for row in range(4, t + 1):
        for col in range(2, 6):
            s.cell(row, col).number_format = USD
    for col in range(1, 6):
        s.cell(t, col).font = Font(bold=True, size=12, color="C00000")

    # 카테고리별 (두 계좌 합산)
    k = t + 2
    for kind, col0, color, amt in (("수입", 1, GREEN, "D"), ("지출", 4, RED, "J")):
        fill(s.cell(k, col0, f"카테고리별 {kind}"), color)
        s.merge_cells(start_row=k, start_column=col0, end_row=k, end_column=col0 + 1)
        cc = "C" if kind == "수입" else "I"
        cats = sorted({e.get("cat") or "기타" for a in d["accounts"].values() for e in a[kind]})
        for j, cat in enumerate(cats, k + 1):
            s.cell(j, col0, cat)
            f = "+".join(f"SUMIF('{n}'!{cc}6:{cc}{LAST},{'A' if col0 == 1 else 'D'}{j},'{n}'!{amt}6:{amt}{LAST})"
                         for n in names)
            c = s.cell(j, col0 + 1, "=" + f)
            c.number_format = USD
    for col, w in zip("ABCDE", [14, 14, 14, 14, 14]):
        s.column_dimensions[col].width = w
    wb.save(XLSX)


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
    sub.add_parser("show")
    args = p.parse_args()

    d = load()
    if args.cmd == "add":
        if args.cat == "":
            args.cat = "기타"
        acct(d, args.acct)[args.kind].append({
            "date": args.date or datetime.date.today().isoformat(),
            "item": args.item, "cat": args.cat, "amount": args.amount, "memo": args.memo})
    elif args.cmd == "start":
        acct(d, args.acct)["start"] = args.amount
    save(d)
    build(d)
    tot = 0
    for n, a in d["accounts"].items():
        inc = sum(e["amount"] for e in a["수입"])
        exp = sum(e["amount"] for e in a["지출"])
        bal = a["start"] + inc - exp
        tot += bal
        print(f"{n}: 시작 ${a['start']:,.2f} | 수입 ${inc:,.2f} | 지출 ${exp:,.2f} | 잔액 ${bal:,.2f}")
    print(f"합계 잔액: ${tot:,.2f}")


if __name__ == "__main__":
    main()
