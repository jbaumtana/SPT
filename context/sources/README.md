# context/sources/

A drop-in folder for existing demo material, so the context layer doesn't
depend on any connector.

**Put here:** exported pages (Markdown, HTML, PDF, DOCX), screenshots of the
demo tenant, copy-pasted notes, or demo recordings' transcripts.

**Then ask an agent:** "Fill in `context/tenant-baseline.md` from
`context/sources/`." It should cite which source file each fact came from and
leave `TODO` for anything the sources don't cover.

**In here now:** `sprout-api-docs-2026-10.txt`, a text copy of the official
Sprout API docs (Oct 2026), so agents can read it without network access.

**Don't put here:** prospect- or customer-specific material (that goes in
`runs/`), credentials, or anything Security hasn't cleared for the repo.
