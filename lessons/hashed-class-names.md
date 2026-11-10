Hashed class names change when the app ships a release; its data-qa attributes and ids do not.

**What happened.** Early selectors used generated class names.

**Why it mattered.** A selector that breaks on release day fails silently, and the tenant's real content shows through.

**What to do.** In a browser pass, look for data-qa attributes and ids first. Fall back to a hashed class only when nothing else exists, and say so in the app map.
