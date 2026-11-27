# FEAT-098 decisions

Rulings made while building plan Rev 1.

| # | Decision | Why | Cost if wrong |
|---|---|---|---|
| D1 | The smaller render size is 960x576 (not 960x544), cropped to 960x540 and scaled to 720p | the two-stage pipeline accepts only multiples of 64 (`assert_resolution`, LTX v1.6.2) | about 6% more pixels than planned, so a smaller saving |
| D2 | `natten` needs no code change | v1.6.2 uses it as the default attention backend once installed | none; the measurement shows whether decoding is faster |
| D3 | Review-time pictures are cached by the hash of the preparation request and the plate model revision, kept 2 h, AI backgrounds only | an unchanged scene of a rewritten script is not painted again; a paper fallback gets another try | a derived picture of the child's drawing stays up to 2 h on the private scratch volume (expired entries are removed at the next preparation, so an idle volume keeps them longer) |
| D4 | The preparation warm-up does nothing while a renderer is loaded | unloading it would cost the model load again after review-time priming | the next uncached preparation unloads it anyway, as before |
| D5 | Review-time preparation runs from the API process, as the warm-up does, and only for a Parent's learning script | both story routes know when a revision is ready | GPU time is spent when the script is abandoned |
| D6 | Learning speech rate for planning is 14 to 18 letters a second | the longer narration did not fit the age-band check with the earlier range | scene lengths follow the real voice anyway (D7) |
| D7 | Narration is synthesised before rendering for learning scripts | the motion must be as long as the voice | the first render starts after the voice is ready (CPU work that already ran in parallel with preparation) |
| D8 | `natten` is installed with a second `uv sync --frozen --package ltx-core --extra natten --inexact`, then imported once in the build | plan Rev 1 named the extra on `ltx-pipelines`, which does not define it (the first image build failed there); the extra belongs to `ltx-core` | none: same committed lock, same torch |
| D9 | The accepted options (`conv_vae,small`) are the deploy default (`render_options.ACCEPTED`); `SKETCH2LIFE_VIDEO_OPTIONS=none` switches them off | a later redeploy must not silently drop the owner's choice | a new workspace must stage the convolution VAE first, or the render fails with `LTX_CONV_VAE_NOT_STAGED` |
| D10 | The spoken-text filter matches whole words with their accents; only a text with no accent at all is compared without them | accent-free comparison refused ordinary words | a listed word written with partly wrong accents (for example "chet" inside an accented sentence) now passes |
| D11 | The learning request is added to the Parent first story (`story_first_start.py`); the stored `prompt_version` keeps its pinned value | without it the app never produced a learning script; existing tests pin the identifier | the revision row does not say which prompt family wrote it (the stored `learning` block does) |
