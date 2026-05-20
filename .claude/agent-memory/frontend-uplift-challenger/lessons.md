# Frontend-Uplift Challenger lessons

- **QSettings persistence is routinely undercounted as "M" when it is "M+"**: the API surface looks small but the signal-cascade re-entrancy risk on restore (variety-changed → subtype-changed → render fires N times), schema versioning (namespace + integer version tag), and key-existence guard for renamed varieties (must check `if key not in VARIETIES`) together add 1–2 extra days beyond the QSettings API calls themselves. Size QSettings candidates at the upper-end of M, not lower-end.
