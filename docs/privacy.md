# Privacy and pre-publication audit

The publication tree must contain no private conversations, names/account information,
absolute personal paths, credentials, private photos/references, proprietary models,
private project names or identifying metadata. Technical research uses public upstream
repository identifiers only. Knowledge is generic technical guidance, not chat history.

Runtime outputs go into ignored `outputs/`; private inputs belong outside the checkout
or in ignored `private/`. JSON inventories omit external file paths/custom properties,
but object names can still identify a project. A `.blend` checkpoint saves the whole
open project and may include linked paths and metadata. Never publish a user project's
checkpoint. Run the synthetic example with `--factory-startup` in a separate process.

Before review/publication:

```sh
python scripts/privacy_audit.py . --output outputs/privacy-audit.json
```

In a Git checkout the script inspects tracked files, including tracked files in ignored
directories, plus untracked files allowed by `.gitignore`. Without Git it scans source
files while excluding runtime directories. It flags secret patterns, personal absolute
paths, email addresses, sensitive filenames, symlinks and binary/media assets needing
manual license/metadata review. Findings never echo matched secret values.

For a local storage audit, `--all-files` also scans ignored outputs/private data
(runtime caches and VCS internals remain excluded). This will deliberately flag generated
images and `.blend` files; those need provenance and metadata review, not an allow-all rule.
No scanner proves privacy or detects every secret/name/proprietary asset. Review the
candidate file list, text, links, licenses and binary metadata manually too. Do not
publish or push until explicitly authorized.
