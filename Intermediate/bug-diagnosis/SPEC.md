# Orders Service — Business Rules (Spec)

This spec defines the **expected behavior**. The diagnosis in
`docs/agent-analysis/I6_bug_diagnosis.md` is graded against these rules.

1. An **order** contains one or more **line items**. Each line item has a `price` (> 0) and a
   `qty` (integer ≥ 1).
2. **Line total** = `price × qty`.
3. **Bulk discount:** a line item qualifies for a **10% discount** when its **quantity is 10 or
   more** (i.e. `qty >= 10`). The discount applies to that line item only.
4. **Order total** = sum of all line totals (after any per-line discount), rounded to 2 decimals.

### Worked examples
| Line item | Qualifies for bulk discount? | Line total |
|---|---|---|
| 100 × 9  | No (`9 < 10`)   | 900.00 |
| 100 × 10 | **Yes** (`10 >= 10`) | **900.00** (1000 − 10%) |
| 100 × 11 | Yes (`11 >= 10`) | 990.00 (1100 − 10%) |
| 50 × 10  | Yes | 450.00 (500 − 10%) |

The boundary case **qty = 10** is the key rule: it MUST receive the discount.
