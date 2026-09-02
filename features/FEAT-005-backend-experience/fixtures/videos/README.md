# Video fixtures

Generate synthetic MP4 fixtures with FFmpeg:

```bash
python features/FEAT-005-backend-experience/scripts/generate_video_fixtures.py \
  --output-dir features/FEAT-005-backend-experience/fixtures/videos/generated
```

The script creates `valid.mp4` (8 seconds), `short.mp4` (3 seconds), `long.mp4` (11 seconds), and `corrupt.mp4`. These are synthetic media only and contain no child data.
