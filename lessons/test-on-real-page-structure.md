A test page built from your own selectors proves nothing about the real page.

**What happened.** The headless selector test passed, then the first pre-flight on the real app found seven engine problems. The test page had none of the app's real structure.

**Why it mattered.** Passing tests gave false confidence right before a live run.

**What to do.** During a browser pass, save a cleaned copy of each screen: structure kept, text replaced with filler. Run engine and payload tests against those copies. Until they exist, treat a green test run as covering the engine's logic only, and say so in any status report.
