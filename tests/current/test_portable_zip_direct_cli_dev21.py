"""Windows build_exe.cmd executes the packager as a standalone script."""
import os
from pathlib import Path
import subprocess
import sys
import zipfile


def test_portable_zip_script_direct_invocation_from_foreign_cwd(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = tmp_path / "fake-install"
    source.mkdir()
    (source / "QuietWriter.exe").write_bytes(b"non-executable packaging fixture")
    internal = source / "_internal"
    internal.mkdir()
    (internal / "sample.dat").write_bytes(b"hello")
    out = tmp_path / "portable.zip"
    foreign = tmp_path / "other-working-directory"
    foreign.mkdir()
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(root / "tools" / "create_portable_zip.py"),
         "--source", str(source), "--output", str(out)],
        cwd=foreign, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(out) as archive:
        assert sorted(archive.namelist()) == ["QuietWriter.exe", "_internal/sample.dat"]
