# How AI was used

The assessment asks for an AI-assisted build and a record of the decisions. The working instruction was to complete the salary-management brief with test-driven development, production-minded edge cases, and a responsive HR interface.

AI drafted the service, tests, and interface from that brief. The tests were the acceptance criteria, not a summary written afterward. A change was kept only when pytest or Vitest described the behavior and then passed. Examples of rules the tests pin down:

- Salaries reject zero, negatives, booleans, non-finite numbers, and more than two decimal places.
- Country insights never average a second country or a second currency.
- Terminated employees are omitted from pay figures unless requested.
- Search treats `%` and `_` as literals.
- A country change switches currency and does not pretend to convert the amount.
- Seeded names are exactly one token from each name file, and 10,000 rows insert in one bulk transaction.

AI did not get to choose the product rules above in order to make the code shorter. Where the model suggested a single global average, that was rejected because it mixes currencies. Where it suggested row-by-row inserts, the seed uses executemany because the brief says the script is run regularly.
