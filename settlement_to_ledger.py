"""Turn weekly trucking settlement lines into journal entries and check them.

For each settlement the script:
  1. adds the earnings, subtracts the deductions and compares the result with
     the total payment printed on the settlement, to the cent;
  2. finds the net payment on the bank deposits file (same amount, within
     3 days of the pay date);
  3. maps every line to an account from the mapping file and prints a
     balanced journal entry. A negative week goes to a settlement payable.

Nothing is written for a settlement that fails a check. Usage:
  python3 settlement_to_ledger.py settlement-mapping.csv sample-settlements.csv sample-bank-deposits.csv
Add --out journal.csv to save the journal lines. Python 3, standard library only.
"""
import csv
import sys
from collections import OrderedDict
from datetime import date
from decimal import Decimal

BANK = "Operating checking"
PAYABLE = "Settlement payable to carrier"
WINDOW_DAYS = 3


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    if out:
        args.remove(out)
    if len(args) != 3:
        print(__doc__)
        return 2
    mapping = {r["line_type"]: r for r in read(args[0])}
    deposits = read(args[2])
    used = set()

    settlements = OrderedDict()
    for r in read(args[1]):
        settlements.setdefault(r["settlement_id"], []).append(r)

    journal, problems = [], 0
    for sid, lines in settlements.items():
        head = lines[0]
        printed = [Decimal(l["amount"]) for l in lines if l["line_type"] == "printed_total"]
        body = [l for l in lines if l["line_type"] != "printed_total"]
        earned = sum(Decimal(l["amount"]) for l in body if Decimal(l["amount"]) > 0)
        deducted = -sum(Decimal(l["amount"]) for l in body if Decimal(l["amount"]) < 0)
        net = earned - deducted
        print(f"\n{sid}  {head['driver']}  truck {head['truck']}  paid {head['pay_date']}")
        print(f"  earned {earned:,.2f}  deducted {deducted:,.2f}  net {net:,.2f}")

        stop = []
        if len(printed) != 1:
            stop.append("no single printed total on the settlement")
        elif printed[0] != net:
            stop.append(f"printed total {printed[0]:,.2f} does not equal the lines ({net:,.2f}), off by {printed[0] - net:,.2f}")
        unknown = sorted({l["line_type"] for l in body if l["line_type"] not in mapping})
        if unknown:
            stop.append("no account mapped for: " + ", ".join(unknown))
        decide = sorted({l["line_type"] for l in body if mapping.get(l["line_type"], {}).get("decide_once") == "yes"})
        if decide:
            stop.append("needs a decision before posting: " + ", ".join(decide))

        match = None
        if net > 0 and not stop:
            pay = date.fromisoformat(head["pay_date"])
            for i, d in enumerate(deposits):
                if i in used or Decimal(d["amount"]) != net:
                    continue
                if abs((date.fromisoformat(d["date"]) - pay).days) <= WINDOW_DAYS:
                    match = i
                    break
            if match is None:
                stop.append(f"net {net:,.2f} not found on the bank deposits within {WINDOW_DAYS} days of {head['pay_date']}")

        if stop:
            problems += 1
            for s in stop:
                print("  WAIT: " + s)
            continue

        entry = []
        for l in body:
            amt = Decimal(l["amount"])
            acct = mapping[l["line_type"]]["account"]
            if amt > 0:
                entry.append((acct, Decimal("0"), amt, l["description"]))
            else:
                entry.append((acct, -amt, Decimal("0"), l["description"]))
        if net > 0:
            used.add(match)
            entry.append((BANK, net, Decimal("0"), "Net settlement deposit"))
            print(f"  deposit found: {deposits[match]['date']} {deposits[match]['description']}")
        elif net < 0:
            entry.append((PAYABLE, Decimal("0"), -net, "Negative week, carrier collects later"))

        dr = sum(e[1] for e in entry)
        cr = sum(e[2] for e in entry)
        assert dr == cr, f"{sid} does not balance"
        for acct, d, c, memo in entry:
            print(f"  {acct:<32}{(f'{d:,.2f}' if d else ''):>12}{(f'{c:,.2f}' if c else ''):>12}  {memo}")
            journal.append([head["pay_date"], sid, head["driver"], acct, f"{d:.2f}" if d else "", f"{c:.2f}" if c else "", memo])
        print(f"  {'Total':<32}{dr:>12,.2f}{cr:>12,.2f}")

    leftover = [d for i, d in enumerate(deposits) if i not in used]
    for d in leftover:
        print(f"\nDeposit with no settlement: {d['date']} {d['description']} {Decimal(d['amount']):,.2f}")

    if out:
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "settlement_id", "driver", "account", "debit", "credit", "memo"])
            w.writerows(journal)
        print(f"\nWrote {len(journal)} journal lines to {out}")

    print(f"\n{len(settlements) - problems} of {len(settlements)} settlements ready to post")
    return 1 if problems or leftover else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
