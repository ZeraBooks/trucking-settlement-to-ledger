# Trucking settlement to ledger

To automate a trucking client's books, read each driver's weekly settlement,
add the loads, subtract the deductions and check the result against the total
payment printed on the settlement before anything posts. Then map every line
to the driver's accounts, match the net to the bank deposit and post one
balanced entry on the pay date.

This repository is that routine as files: a mapping table from settlement
lines to accounts, two fictional weekly settlements and a script that turns
them into journal entries and refuses to post a week that doesn't tie.

## Files

| File | What it is |
|---|---|
| `settlement-mapping.csv` | 15 common settlement line types (linehaul, fuel surcharge, fuel advances, insurance, escrow, 2290 savings, tolls, truck payments and more) with the account, debit or credit side, and a note on how to book each one. `decide_once` marks lines a person should look at before they post. |
| `sample-settlements.csv` | Two fictional weeks for one owner-operator, Northline Hauling: a normal week that nets 5,775.00 and a short week that nets minus 475.00. One row per settlement line plus the printed total. |
| `sample-bank-deposits.csv` | The fictional bank deposit the first settlement should match. |
| `settlement_to_ledger.py` | Checks each settlement and prints the journal entry. Python 3, standard library only. |

## How to use it

1. Run the sample:

   ```
   python3 settlement_to_ledger.py settlement-mapping.csv sample-settlements.csv sample-bank-deposits.csv
   ```

   Add `--out journal.csv` to save the journal lines for import into your
   general ledger.
2. Edit `settlement-mapping.csv` so the account names match your client's
   chart. Add a row for every deduction type your carriers use.
3. Type or export each week's settlement in the same layout as
   `sample-settlements.csv`: earnings as positive amounts, deductions as
   negative amounts, and one `printed_total` row copied from the settlement.
4. Export the bank deposits for the same weeks and run the script again.

## What makes a settlement wait

The script posts nothing for a settlement when:

- the printed total does not equal earnings minus deductions (it shows the
  difference);
- a line type has no account in the mapping file;
- a line is marked `decide_once`, such as a truck payment that still needs
  splitting into interest and principal;
- the net is positive and no bank deposit of that amount is within 3 days of
  the pay date.

A deposit left over with no settlement is listed at the end. It usually
means a settlement is missing from the folder.

## Worked example

Northline Hauling's settlement for the week ending October 9, 2026:

| Settlement line | Amount | Account |
|---|---|---|
| Linehaul, 4 loads | 8,400.00 | Freight revenue |
| Fuel surcharge | 1,260.00 | Freight revenue |
| Fuel card advances | (3,180.00) | Fuel expense |
| Cargo and liability insurance | (420.00) | Insurance expense |
| Escrow held by the carrier | (250.00) | Escrow receivable |
| ELD fee | (35.00) | Software and subscriptions |
| Net deposit to checking | 5,775.00 | Operating checking |

9,660.00 earned less 3,885.00 deducted is 5,775.00, the amount on the bank
statement. The next week earns 1,210.00 against 1,685.00 of deductions, so
nothing reaches the bank and 475.00 goes to a settlement payable until the
carrier collects it.

All figures are fictional.

## FAQ

### Why book the settlement gross instead of just the deposit?

Booking only the deposit hides most of the revenue and every cost the carrier
took out: fuel, insurance and escrow never reach the books, and the fuel
figures for IFTA are missing.

### Is escrow an expense?

No. The carrier is holding the driver's money. It builds up as a receivable
and comes back when the lease ends, less any charges. The same goes for Form
2290 savings and maintenance reserves.

### How should a negative settlement be booked?

When deductions are bigger than the loads, book every line as usual and put
the shortfall on a payable to the carrier. It clears when the carrier
collects it from a later week.

For a full trucking chart of accounts, see
[chart-of-accounts-templates/trucking](https://github.com/ZeraBooks/chart-of-accounts-templates/tree/main/trucking).

## Learn more

[Trucking bookkeeping automation](https://www.zerabooks.com/trucking-bookkeeping-automation)
on zerabooks.com, and the guide to
[bookkeeping for trucking](https://www.zerabooks.com/bookkeeping-for-trucking).

## License

The content and data in this repository are licensed under
[CC BY 4.0](LICENSE). The code (`*.py`) is licensed under [MIT](LICENSE-CODE).

Maintained by [ZeraBooks](https://www.zerabooks.com).
