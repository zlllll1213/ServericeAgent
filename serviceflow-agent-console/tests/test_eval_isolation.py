from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "serviceflow.db"


def file_fingerprint(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def test_eval_uses_temp_database_by_default(tmp_path):
    before = file_fingerprint(DEFAULT_DB)
    env = os.environ.copy()
    env.pop("SERVICEFLOW_DB_PATH", None)
    env["PYTHONPATH"] = str(ROOT)

    # 用最小 dataset 验证导入顺序和数据库隔离；完整 make eval 复用同一入口。
    result = subprocess.run(
        [sys.executable, "evals/run_eval.py", "--dataset", "intent"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert '"intent"' in result.stdout
    assert file_fingerprint(DEFAULT_DB) == before
