A whole-word match built on \b fails when the name starts or ends with punctuation.

**What happened.** A label ending in a bracket, followed by a hyphen, never matched, because \b needs a letter or digit on one side.

**Why it mattered.** The label stayed on screen and had to be patched by hand.

**What to do.** Use lookarounds on letters, digits and underscore with the unicode flag, as the engine does since fix E2. When adding a find string, test it with trailing punctuation, a leading @ or #, and at the start and end of a text node.
