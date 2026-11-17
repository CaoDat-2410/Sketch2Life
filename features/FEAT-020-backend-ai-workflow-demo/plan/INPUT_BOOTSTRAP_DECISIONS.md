# FEAT-020 Input Bootstrap Decisions

These are pending decisions added after the initial plan. They must be resolved before the plan is marked approved.

1. Which image-generation provider/model should create the child-drawing-style image?
2. Does “Google audio” mean Google AI Studio/Gemini text-to-speech or Google Cloud Text-to-Speech?
3. What language, locale, voice, and speaking style should the generated narration use?
4. Should every default demo run generate both image and WAV, or should WAV generation be enabled only when `MULTIMODAL` is explicitly selected?
5. Should the narration script be generated automatically from the same image scenario prompt, or supplied as a separate operator prompt?
6. Should the default generated drawing use a fixed reproducible seed for evidence, or a new random seed for every run?
