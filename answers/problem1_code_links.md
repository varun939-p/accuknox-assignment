# Problem Statement 1 - Q4 and Q5

## Q4. Most complex Python code

https://github.com/varun939-p/Keka-Resume-Intelligence-ATS-Platform/blob/main/pipeline.py

`pipeline.py` orchestrates batch resume screening for Keka Resume Intelligence: every file is parsed, deduplicated, scored against a job description, routed to a pipeline stage, persisted, and written to an audit log. Files arrive one request at a time to stay under serverless request-body limits, and each one is isolated: the filename is reduced to a safe basename, extension and size are checked before parsing, and any unexpected parser or scorer exception is recorded as a per-file failure instead of killing the batch. The duplicate check and the registry insert run under one lock, so two concurrent uploads of the same resume cannot both register as originals, and a thread-safe event bus with per-batch sequence numbers feeds the server-sent events stream that shows live progress. `rescore_batch` re-ranks a finished batch against another job description by reusing the stored profile and dedup trace instead of re-parsing, and it keeps any stage a recruiter set by hand.

## Q5. Most complex database code

https://github.com/varun939-p/habotconnect-lsa-booking/blob/main/bookings/migrations/0002_booking_exclusion_constraint.py

This Django migration adds two PostgreSQL `EXCLUDE USING gist` constraints to the booking table: one rejects two active bookings for the same LSA whose `tstzrange(scheduled_start, scheduled_end, '[)')` ranges overlap (`=` on the LSA key, `&&` on the range, with `btree_gist` enabled so the integer equality can sit in the same GiST index), and the other applies the same rule per parent. The keys are `CASE` expressions that return NULL unless the status is `pending` or `confirmed`, and because an exclusion constraint never matches NULL, cancelled, failed and completed bookings never block a rebooking, while the half-open `[)` range lets a session start exactly when the previous one ends. An application-level check is a read followed by a write, so under READ COMMITTED two concurrent requests can both see a free slot and both insert; the constraint is checked against the index at insert time, so the second transaction waits for the first to commit and then fails with an exclusion violation (SQLSTATE 23P01). The booking view already serializes requests with `SELECT ... FOR UPDATE`, so this migration is the last layer: it still holds for raw SQL, admin edits, scripts, or a future code path that skips the lock, and it is a no-op on SQLite, which has no GiST.
