# FEAT-005 decisions

- Session business state is separate from per-artifact job state.
- Gate B locks activity and learning-objective versions before experience generation.
- Learning explanation resolution is reviewed-cache first, generation second.
- Video failure falls back to reviewed still+narration without changing the approved activity/objective.
- Ready packages must include the off-screen ActivityHandoff.
