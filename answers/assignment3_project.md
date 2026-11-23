# Assignment 3

## Project link

AetherOps: https://github.com/varun939-p/aetherops

Live demo: https://aetherops-xi.vercel.app (the hosted build runs in browser mode; writing patches to disk and git commits need a local run in server mode)

AetherOps links a local repository, finds security and reliability defects with a deterministic rule engine plus Gemini, and writes reviewed line-range patches back to disk, optionally as a git commit.

## Why it's hard

1. LLM output had to be safe to write into real files: Gemini returns schema-constrained JSON that is re-validated with zod, files are split into token-budgeted chunks with absolute line numbers, and fixes come back as non-overlapping line-range edits, so a patch can never truncate code the model did not see.
2. Disk, database and model can disagree at any moment, so every step is a SHA-256 compare-and-swap: analysis results are saved only if the file hash is unchanged, a lease column stops two analyses of the same file, and a commit is refused with `DISK_DRIFT` if the file changed after review.
3. Writing into someone's repo had to be safe: atomic temp file + fsync + rename with a post-write hash check, path containment re-checked after symlink resolution against an allow-list, credential files never ingested or sent to the model, and filesystem routes that only answer on loopback.
