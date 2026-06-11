from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "app" / "web"


def module_paths(html: str) -> list[str]:
    return re.findall(r'<script\s+type="module"\s+src="([^"]+)"', html)


def test_module_entrypoints_exist_and_legacy_scripts_are_retired():
    pages = [WEB_DIR / "index.html", WEB_DIR / "admin.html", WEB_DIR / "login.html"]

    for page in pages:
        html = page.read_text(encoding="utf-8")
        assert "/static/app.js" not in html
        assert "/static/admin.js" not in html
        paths = module_paths(html)
        assert paths, f"{page.name} should load an ES module entrypoint"
        for path in paths:
            assert path.startswith("/static/")
            assert (WEB_DIR / path.removeprefix("/static/")).exists()


def test_legacy_monolith_files_are_removed():
    assert not (WEB_DIR / "app.js").exists()
    assert not (WEB_DIR / "admin.js").exists()


def test_browser_loaded_javascript_parses_with_node():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")

    scripts = sorted(path for path in WEB_DIR.rglob("*.js") if "vendor" not in path.parts)
    assert scripts
    for script in scripts:
        subprocess.run([node, "--check", str(script)], cwd=ROOT, check=True)
