# Stage contract

All stages keep an existing versioned `.blend` rollback checkpoint and its generated
`.blend.json` receipt. A checkpoint saves a copy without changing the active file path.
Approvals bind the submitted artifact hashes. Image, report and checkpoint geometry
fingerprints must agree. Context-dependent warnings require documented review.

| Stage | Entry | Deliverables | Validation and approval | Rollback |
| --- | --- | --- | --- | --- |
| RESEARCH | Scene inspected; scope/use identified | Inventory, brief, reference/dimension metadata, checkpoint/receipt | Uncertainty and existing-object classification reviewed; explicit user approval | Initial checkpoint |
| BLOCKOUT | Approved research | Envelope, proportions, report, four reviewed views, change log, checkpoint/receipt | Primary ratios and silhouette agree with available evidence; user approval | Pre-blockout checkpoint |
| PRIMARY_GEOMETRY | Approved blockout | Major forms with approved targets protected; standard evidence bundle | Scale, datums and major surfaces reviewed; user approval | Approved blockout |
| SECONDARY_GEOMETRY | Approved primary | Component separation/clearances and standard bundle | Construction and contact inspected; user approval | Approved primary |
| DETAILING | Approved secondary | Purposeful functional details and standard bundle | No primary silhouette regression or uncontrolled density; user approval | Approved secondary |
| TOPOLOGY_REVIEW | Approved detailing | Source/evaluated checks and standard bundle | Profile errors zero; warning decisions documented; edge flow/shading visually reviewed; user approval | Pre-cleanup checkpoint |
| MATERIALS | Approved topology | Materials in context plus neutral geometry evidence | Materials do not conceal defects; user approval | Approved untextured geometry |
| FINAL_VALIDATION | Approved materials | Final standard bundle and explicit limitations/export scope | No unavailable checks; images actually inspected; intended export tested when claimed; user approval | Last approved checkpoint |

Runtime technical gates check errors and coverage. Reference fidelity, functional logic,
warning acceptance and artistic acceptance are contextual user/agent responsibilities;
the state machine does not pretend to measure them automatically.

`Workflow.submit(artifacts)` requires these relative keys:

- Research: `inventory`, `brief`, `references`, `checkpoint`, `checkpoint_receipt`.
- Other stages: `report`, `views`, `change_log`, `checkpoint`, `checkpoint_receipt`.

Capture views with `artifact_root=workflow.root`; manifest image paths are relative
to that root. Set `reviewed`, `reviewer_role` (`agent` or `user`), a concrete `observation`
and `blocking_issues` only after looking at the actual image. Capture alone leaves review
false. `approve(authority_reference)` needs a redacted reference to an actual explicit
user decision. `advance()` never approves a stage.

Protected targets cannot be edited in later stages merely because a permit used to
cover them. `reopen(stage, targets, authority_reference)` invalidates that stage and
all later stage records and releases only named targets. Revalidate and resubmit.
Minor authorized corrections need a change log and fresh evidence too. Rejection
records result, problem, cause hypothesis, correction strategy and retry validation.

The journal is intended for a single writer. External concurrent edits need coordination;
source fingerprints are checked immediately before BMA operations. The local event
hash chain detects accidental event changes, not malicious authorship or state rewriting.
