# Reviewable technical knowledge

Use `bma.knowledge.KnowledgeRecord` with category, asset types, symptoms, root cause and
verification flag, recommended correction, validation, confidence, evidence type/reference,
status and limitations. Save immutable content-hashed JSON revisions; review a new revision
before selecting it. Reverting means selecting the prior record, not rewriting history.

Statuses: `verified_success`, `user_approved`, `proposed_untested`, `rejected`, `recommendation`.
Only executed tests or actually inspected images support `verified_success`; user approval
alone is a different status. Unknown root causes remain hypotheses. A rejected approach
keeps its applicable scope and must not become a universal prohibition.

Use generic technical descriptions and relative public evidence identifiers. Do not include
private conversations, names, private images, absolute personal paths or credentials.
The runtime validates structural provenance, not the truth of assertions; peer review and
the publication privacy audit remain necessary. No private project history is imported.
