# Test design techniques — pick by what changed

Read this only when the right technique for a change is not obvious. Use the ones the change
calls for; never run the whole catalog.

## By kind of change

| The change touches… | Technique | Cases it produces |
|---|---|---|
| A numeric, length, date or count limit | Equivalence classes + boundary values | just below, on, just above each limit; empty; the type's extreme |
| Several conditions combined (`if a and (b or c)`) | Decision table | one case per rule that changes the outcome; drop combinations with the same result |
| A status field or workflow | State transitions | every allowed transition, the forbidden ones from each state, the same transition twice |
| Three or more independent factors (role × currency × channel) | Pairwise | each pair of values appears in at least one case, not the full product |
| Anything that can run twice (submit, job, webhook, retry) | Idempotency | the same input twice in a row; twice concurrently; after a timeout of the first |
| Money, prices, discounts, taxes | Rounding and currency | amounts with 3+ decimals, zero, negative, currency change, totals equal to the sum of lines |
| Dates and times | Time zones and calendar | day change across zones, month/year end, leap day, DST change, server vs user zone |
| Permissions, roles, tenants, companies | Isolation | the allowed role; the role just below; a user of another tenant/company reading the same record by id |
| An external call (API, gateway, queue) | Failure injection | timeout, 4xx, 5xx, malformed body, slow response, retry after partial success |
| A form or UI flow | Exploratory charter + states | loading, empty, success, error, partial success; double click; back/forward; reload; expired session |
| A list, search or filter | Partitions | no results, one, many, paging limit, special characters, the filter that should exclude |
| Translations or locale-dependent output | Locale | each supported language, a long string, number and date formats |
| No simple expected result (ranking, pricing engine, search relevance) | Metamorphic relations | a change to the input with a known effect on the output: add a filter → results ⊆ before; double the quantity → total doubles; reorder input → same result |

## Exploratory charters

When the change is a user flow, write each exploratory session as one line:

> Explore **<area>** with **<data or resource>** to discover **<risk>**.

Example: *Explore the checkout payment step with an expired card and a slow gateway to
discover double charges or a stuck order.* Note what was tried and what was observed; a
charter without notes counts as not run.

## Error guessing — check history first

Before inventing failures, look for real ones in the area: `git log -S <symbol>` or
`git log --oneline -- <file>` for past fixes, and existing tests named after bugs. A bug that
happened once in this code is the best predictor of the next one.

## Layer choice

| Risk | Lowest faithful layer |
|---|---|
| A calculation, a rule, a parser | unit |
| A query, a transaction, an ORM rule, a migration | integration with a real test database |
| A request/response contract, auth on an endpoint | API test |
| What the user sees and does across pages | end-to-end, only for the critical journey |
| Visual layout, wording, accessibility judgment | manual, stated as manual |

Automated accessibility checks (axe, lint rules) find some issues; they do not prove
conformance. Say which one ran.
