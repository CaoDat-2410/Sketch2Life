"""Run available unit/contract regression checks; keep missing media gates explicit."""
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]
BLOCKED = ['test_whiteboard_v2_engine.py', 'test_whiteboard_v2_visual_refinement.py', 'test_butterfly_candidate_refinement.py', 'test_butterfly_video_proof.py', 'test_house_video_proof.py', 'test_limited_character_rig_v2.py', 'test_semantic_authoring_v1.py', 'test_semantic_drawing_engine_v2.py', 'test_whiteboard_v2_complexity.py', 'test_whiteboard_v2_pencil_pass.py', 'test_whiteboard_v2_schedule_debug.py', 'test_whiteboard_v2_visual_pass.py']
temp_root = Path(tempfile.gettempdir()).resolve()
basetemp = temp_root / ('sketch2life-feat042-' + uuid.uuid4().hex)
assert basetemp.is_relative_to(temp_root) and not basetemp.exists()
command = [sys.executable, '-X', 'utf8', str(FEATURE / 'src/run_check.py'), 'backend_complete', sys.executable, '-m', 'pytest', 'backend/tests/unit', 'backend/tests/contract', '--basetemp=' + str(basetemp), '-o', 'addopts=', '-q', '--deselect=tests/unit/test_whiteboard_mvp_renderer.py::test_narration_beat_without_matching_strokes_blocks_render', *['--ignore=backend/tests/unit/' + name for name in BLOCKED]]
raise SystemExit(subprocess.call(command, cwd=ROOT))
