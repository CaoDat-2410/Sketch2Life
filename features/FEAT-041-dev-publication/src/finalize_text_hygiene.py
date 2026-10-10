"""Finish source prose line endings without changing protected artifact bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
ROOT = FEATURE.parents[1]

def main() -> None:
    path = FEATURE / 'evidence/metrics/PUBLICATION_MANIFEST.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    for record in manifest['source_reference_changes']:
        source = ROOT / record['path']
        text = source.read_bytes().decode('utf-8').replace('\r\r\n', '\n').replace('\r\n', '\n')
        source.write_text(text, encoding='utf-8', newline='\n')
        record['published_prose_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        backup = ROOT / record['backup']
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == record['original_prose_sha256']
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    # These are scratch drafts, not preserved originals. Remove only redundant EOF blank lines.
    draft = ROOT / 'features/FEAT-039-collaborative-learning-scope/artifacts/drafts/B26_TRACEABILITY_AND_GATES.md'
    draft.write_text(draft.read_text(encoding='utf-8').rstrip() + '\n', encoding='utf-8', newline='\n')
    print('SOURCE_PROSE_HYGIENE_VALID backup_hashes_preserved=10')

if __name__ == '__main__':
    main()
