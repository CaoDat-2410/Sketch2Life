"""Audit Wan imports together; optionally install missing allowlisted packages."""
import argparse
import ast
import importlib.metadata as metadata
import importlib.util
import subprocess
import sys
from pathlib import Path

PACKAGES = {
    'easydict': 'easydict', 'ftfy': 'ftfy', 'einops': 'einops',
    'decord': 'decord', 'dashscope': 'dashscope', 'imageio': 'imageio',
    'imageio_ffmpeg': 'imageio-ffmpeg', 'cv2': 'opencv-python',
    'librosa': 'librosa', 'soundfile': 'soundfile', 'scipy': 'scipy',
    'sentencepiece': 'sentencepiece', 'regex': 'regex', 'tqdm': 'tqdm',
    'safetensors': 'safetensors', 'PIL': 'Pillow', 'accelerate': 'accelerate',
    'huggingface_hub': 'huggingface-hub', 'numpy': 'numpy',
    'torch': 'torch', 'torchvision': 'torchvision', 'torchaudio': 'torchaudio',
    'transformers': 'transformers', 'diffusers': 'diffusers',
}
PROTECTED = {'torch', 'torchvision', 'torchaudio', 'numpy', 'transformers', 'diffusers'}


def available(name):
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path,
                        default=Path('/teamspace/studios/this_studio/Wan2.2'))
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not (repo / 'generate.py').is_file():
        raise SystemExit(f'Wan source not found: {repo}')
    imports = set()
    files = [repo / 'generate.py', *sorted((repo / 'wan').rglob('*.py'))]
    for file in files:
        tree = ast.parse(file.read_text(encoding='utf-8-sig'), filename=str(file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(item.name.split('.')[0] for item in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module.split('.')[0])
    local = {p.stem for p in repo.glob('*.py')}
    local.update(p.name for p in repo.iterdir() if p.is_dir())
    external = imports - set(sys.stdlib_module_names) - local
    absent = sorted(name for name in external if not available(name))
    known = [name for name in absent if name in PACKAGES]
    unknown = [name for name in absent if name not in PACKAGES]
    print('Python:', sys.executable, flush=True)
    print('Missing mapped imports:', known, flush=True)
    print('Other missing imports (may be optional/preprocessing):', unknown, flush=True)
    print('No automatic installation of unknown imports or flash-attention.', flush=True)
    blocked = sorted(set(known) & PROTECTED)
    installable = [name for name in known if name not in PROTECTED]
    if args.install and installable:
        out = Path.cwd() / '.runtime' / 'wan-dependencies'
        out.mkdir(parents=True, exist_ok=True)
        constraints = out / 'installed-constraints.txt'
        pins = sorted({f"{dist.metadata['Name']}=={dist.version}"
                       for dist in metadata.distributions() if dist.metadata['Name']})
        constraints.write_text('\n'.join(pins) + '\n', encoding='utf-8')
        print('Installing missing mapped packages in ONE pip transaction;',
              'existing versions are constrained:', constraints, flush=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-c', str(constraints),
                        *[PACKAGES[name] for name in installable]], check=True)
    elif installable:
        print('Audit only. Rerun with --install to install the mapped missing packages.')
        return
    if blocked:
        print('Core environment needs separate review:', blocked, flush=True)
        for name in ('torch', 'torchvision', 'torchaudio'):
            try:
                print(name, metadata.version(name), flush=True)
            except metadata.PackageNotFoundError:
                print(name, 'NOT_INSTALLED', flush=True)
        torch_check = subprocess.run(
            [sys.executable, '-c',
             'import torch; print("TORCH_BUILD", torch.__version__); '
             'print("CUDA_BUILD", torch.version.cuda)'],
            capture_output=True, text=True)
        print(torch_check.stdout, flush=True)
        print(torch_check.stderr, flush=True)
        raise SystemExit('Ordinary dependency installation finished; core packages were NOT changed. '
                         'Share the version lines above before installing torchaudio.')
    print('Checking real Wan CLI imports (up to 180 seconds)...', flush=True)
    try:
        result = subprocess.run([sys.executable, str(repo / 'generate.py'), '--help'],
                                cwd=repo, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        raise SystemExit('CLI import timed out; no weights downloaded.')
    if result.returncode:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit('CLI import failed. Review this output and the complete missing-import list above.')
    print('WAN_CLI_IMPORT_OK. No model weights downloaded.')


if __name__ == '__main__':
    main()
