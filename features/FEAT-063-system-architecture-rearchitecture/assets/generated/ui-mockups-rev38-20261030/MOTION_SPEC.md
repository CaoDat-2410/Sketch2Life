# Motion and interaction proposal — Rev38 screens

These notes describe suggested transitions for a later implementation. They are not executable animations and do not authorize frontend implementation.

## Shared rules

- Respect reduced-motion preferences and replace movement with immediate state updates.
- Use motion only for a real state change. Never invent progress, percentage, ETA, or completion.
- Keep focus, selected state, status text and error copy visible; color alone must not carry meaning.
- Parent and Teacher flows remain separate. Optional sketch generation creates no job while disabled.
- Story scenes are read-only; adult suggestions request an AI rewrite. Video safety runs automatically.
- Keep destructive actions confirmable, and scope feedback to the lesson.

## Per-screen notes

See each role screen's MOTION.md for the specific proposed behavior: P01–P12, T01–T07, M01–M02, A01–A02.
