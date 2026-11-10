# Iterative correction

Create a prioritized plan containing the problem, its actual numeric/image evidence,
target names, correction strategy, required permission and retry validation. Restore
or save a versioned checkpoint before edits. Use a new one-use permit per attempt.

`correction_loop(inspect, propose, apply, max_iterations=3)` stops at its limit or
when no evidenced plan exists. The caller obtains permissions and supplies the operations.
Failures propagate; a timeout is not evidence that nothing changed. Inspect real state
before retrying a mutation. Repeatedly adding topology without evidence is not a correction.

An unreviewed visual result remains `needs_visual_review` even when technical checks pass.
Record changes and remaining issues. A user rejection creates a structured failure
record with rejected result, problem, likely cause (labeled as hypothesis when unverified),
strategy and required retry evidence. Reopen approved stages only with explicit authority.
