# Claude Code Instructions

## Large Work Estimation Rule

Before starting any large automated work — modifying many files, long loops, large cache writes, or any task estimated to take more than a few steps — you must:

1. Estimate the scope (how many entries, files, operations)
2. Describe the approach and expected time/effort
3. Ask the user explicitly if they want to proceed

Do not begin the work until confirmed. If a task grows larger than initially scoped mid-execution, pause and re-confirm.

## Git Push

NEVER run `git push` without explicit user confirmation. Always stop after committing and ask "Want me to push?" — no exceptions, even when it seems like a natural next step.

## Commit Signing (Claude sandbox sessions)

Do NOT try to fix the "Unverified" commit warning in Claude sandbox / CCR sessions. The sandbox ships a broken signing setup (an empty signing key while `commit.gpgsign` is on), so commits can never be signed and the stop hook flags them every session. This is a platform provisioning issue, not fixable in-session — running `git commit --amend --reset-author`, rebasing, or any signing fix only wastes tokens and never clears it. When the stop hook prints the "Unverified" notice, ignore it and proceed.

## Brand / Blend / Alias Changes

**What needs approval:** Creating a brand or blend that does not yet exist in `docs/canonical.json`, or adding any entry to `brand_aliases.json` or `blend_aliases.json`.

**What does NOT need approval:** Writing `blend_cache.json` entries that match an already-existing brand/blend in `canonical.json`. These are routine lookups and can be written and reported without prior confirmation.

**Proactive check required:** Before writing any batch to `blend_cache.json`, check `canonical.json` and identify every entry whose brand/blend combo does not yet exist there. Present that list to the user and get explicit approval BEFORE writing those entries. Do not wait for the user to ask — flag them first, every time.

No exceptions for the approval items — this applies even when the addition seems obvious or low-risk.

## Batch Work

When processing large lists (e.g. blend_cache.json entries from unmatched.log):
- Work in batches of 50 entries at a time
- Report what was written after each batch
- Wait for "continue" before starting the next batch
