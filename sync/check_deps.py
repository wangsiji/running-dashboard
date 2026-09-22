#!/usr/bin/env python3
"""核对 requirements.txt：多了什么、少了什么。

依赖应该是 sync/ 里真实 import 的结果，不是凭记忆列的。改完 import 跑一遍：

    python3 sync/check_deps.py

AST 只认顶层 import。装在 try/except 里的可选依赖会被漏报（tzfpy / timezonefinder
平台互斥就是这种），所以看输出人工判断，别直接拿它改写文件。
"""

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYNC = ROOT / "sync"

# 仓库内的本地模块，不是 pip 包
LOCAL = {
    "config",
    "coros",
    "generator",
    "gpx",
    "polyline_processor",
    "synced_data_file_logger",
    "tracks",
    "utils",
}


def real_imports():
    mods = set()
    for f in SYNC.rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            print(f"  ! 跳过无法解析的 {f.name}: {e}", file=sys.stderr)
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                mods.add(n.module.split(".")[0])
    return mods


def declared():
    lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return {
        line.split(";")[0].split("==")[0].split("[")[0].strip()
        for line in lines
        if line.strip() and not line.startswith("#")
    }


def main():
    # import 名下划线 → pip 包名横线
    have = {m.replace("_", "-") for m in real_imports() - LOCAL}
    stdlib = set(sys.stdlib_module_names)
    have = {m for m in have if m not in stdlib and m.replace("-", "_") not in stdlib}
    want = declared()

    print("requirements.txt 写着的:", sorted(want))
    print("sync/ 真实 import 的:", sorted(have))
    print()
    extra = sorted(want - have)
    missing = sorted(have - want)
    print("多余（可删）:", extra or "无")
    print("缺失（必须加）:", missing or "无")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
