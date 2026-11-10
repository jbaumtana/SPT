Assigning values by page order breaks as soon as the page redraws.

**What happened.** Captions were handed out by a counter. When the list redrew, every caption moved, and copies of the same post got different captions.

**Why it mattered.** The story on screen changed between two looks at the same calendar.

**What to do.** Key each value to a stable attribute on the post's container, so the same post always gets the same value (fix E3). Tie date-specific copy to its date with a scoped rule instead of relying on order (fix E4).
