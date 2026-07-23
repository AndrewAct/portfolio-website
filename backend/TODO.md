# Backend TODO

## Worker: add a no-op counter to TickResult

`apps/workers/horoscope_email.py` — `TickResult` currently tracks `due`, `sent`, `skipped`,
but `_claim_and_send()` has several "due but nothing to do" branches (already resolved
today, pending-not-yet-stale, failed-max-attempts, claim race lost) that fall through to
`return` at line ~141-144 without incrementing any counter. Result: `due != sent + skipped`,
which reads as unexplained missing sends in the `Tick complete` log even though it's benign.

Fix: add a counter (e.g. `no_op`) to `TickResult`, increment it right before that `return`,
and include it in the `Tick complete` log line so `due == sent + no_op` (skipped stays a
separate, unrelated bucket — see the `_is_due()` vs `_claim_and_send()` distinction).
