# Problem Statement 1 - Q4 and Q5

## Q4. Most complex Python code

https://github.com/varun939-p/Keka-Resume-Intelligence-ATS-Platform/blob/main/pipeline.py

This runs batch resume screening for my Keka ATS project. Each file is parsed, checked for duplicates under a lock, and scored against the job description. An event bus streams live progress to the UI, and one bad file fails on its own without stopping the batch.

## Q5. Most complex database code

https://github.com/varun939-p/habotconnect-lsa-booking/blob/main/bookings/migrations/0002_booking_exclusion_constraint.py

This migration adds PostgreSQL GiST exclusion constraints so two active bookings for the same LSA cannot overlap in time. An app-level check can race when two requests land together, so the database enforces the rule instead. Cancelled and completed bookings are left out, so they never block a rebooking.
