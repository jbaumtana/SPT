The app rewrites text inside existing elements, so watching only for added and removed elements lets old names come back.

**What happened.** In the first pre-flight, a topic page title returned to its tenant name after the overlay had replaced it. The page had changed the text of an element that was already there.

**Why it mattered.** A seed name reappearing mid-demo is the exact failure the overlay exists to prevent.

**What to do.** Watch for in-place text changes as well as added and removed elements, and pause watching while the engine writes so it doesn't trigger itself. The engine does this since v1.1.0-spt (fix E1). Any new observer should follow the same pattern.
