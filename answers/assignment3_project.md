# Assignment 3

AetherOps: https://github.com/varun939-p/aetherops

Live demo: https://aetherops-xi.vercel.app (browser mode only; writing patches to disk needs a local run)

It finds security and reliability bugs in a local repo with a rule engine plus Gemini, then writes reviewed fixes to disk.

## Why it's hard

1. Full-file rewrites from Gemini could break or truncate code, so I forced a strict JSON schema and small line-range patches.
2. Disk, database and model can drift apart, so I added SHA-256 checks that block a patch if the file changed mid-review.
3. I write files with atomic temp-file renames, re-check paths after symlinks resolve, and never send credential files to the LLM.
