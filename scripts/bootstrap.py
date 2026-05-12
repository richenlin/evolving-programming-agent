"""
bootstrap.py — Runtime Python resolver for evolving-agent (offline, detect-only).

This script detects an available Python interpreter for the skill runtime.
It does NOT download anything. It only checks for:
  1. Portable Python (bundled by IDE build pipeline at .runtime/python/)
  2. System Python (fallback, must meet min_version from runtime.json)

Usage:
    python3 bootstrap.py --resolve     # Resolve Python path, output JSON to stdout
    python3 bootstrap.py --doctor      # Output detailed diagnostic JSON to stdout

Output (stdout, strict JSON for IDE parsing):
    {"status":"ok","python":"/path/to/python3","python_version":"3.11.9","source":"portable|system","skill_root":"/path"}
    {"status":"error","code":"PYTHON_NOT_FOUND","message":"...","skill_root":"/path"}

Exit codes: 0 = success, 1 = failure
"""

import json
import os
import sys
import subprocess
import argparse
import platform


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_JSON = os.path.join(PROJECT_ROOT, "runtime.json")


def _load_runtime_config():
    try:
        with open(RUNTIME_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[bootstrap] WARNING: Cannot load runtime.json: {e}", file=sys.stderr)
        return None


def _get_python_version(python_path):
    try:
        out = subprocess.check_output(
            [python_path, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode().strip()
        return out
    except Exception:
        return None


def _version_ge(version_str, min_version_str):
    try:
        v = tuple(int(x) for x in version_str.split("."))
        m = tuple(int(x) for x in min_version_str.split("."))
        return v >= m
    except (ValueError, TypeError):
        return False


def detect_portable_python(skill_root):
    bin_paths = [
        os.path.join(skill_root, ".runtime", "python", "bin", "python3"),
        os.path.join(skill_root, ".runtime", "python", "python.exe"),
    ]
    for p in bin_paths:
        if os.path.isfile(p):
            ver = _get_python_version(p)
            if ver:
                return {"path": p, "version": ver, "source": "portable"}
    return None


def detect_system_python(min_version="3.8"):
    candidates = [
        "python3.13", "python3.12", "python3.11", "python3.10",
        "python3.9", "python3.8", "python3", "python",
    ]
    for cmd in candidates:
        ver = _get_python_version(cmd)
        if ver and _version_ge(ver, min_version):
            return {"path": cmd, "version": ver, "source": "system"}
    return None


def resolve():
    cfg = _load_runtime_config()
    min_version = "3.8"
    if cfg:
        min_version = cfg.get("python", {}).get("min_version", "3.8")

    py = detect_portable_python(PROJECT_ROOT)
    if not py:
        py = detect_system_python(min_version)

    if not py:
        return {
            "status": "error",
            "code": "PYTHON_NOT_FOUND",
            "message": (
                f"No Python >= {min_version} found. "
                "IDE installation may be corrupted or system Python is missing."
            ),
            "skill_root": PROJECT_ROOT,
        }

    return {
        "status": "ok",
        "python": py["path"],
        "python_version": py["version"],
        "source": py["source"],
        "skill_root": PROJECT_ROOT,
    }


def doctor():
    cfg = _load_runtime_config()
    min_version = "3.8"
    if cfg:
        min_version = cfg.get("python", {}).get("min_version", "3.8")

    portable = detect_portable_python(PROJECT_ROOT)

    system_candidates = []
    candidate_cmds = [
        "python3.13", "python3.12", "python3.11", "python3.10",
        "python3.9", "python3.8", "python3", "python",
    ]
    for cmd in candidate_cmds:
        ver = _get_python_version(cmd)
        if ver:
            system_candidates.append({
                "command": cmd,
                "version": ver,
                "meets_min": _version_ge(ver, min_version),
            })

    resolved = resolve()

    return {
        "status": "ok" if resolved.get("status") == "ok" else "error",
        "runtime_json_path": RUNTIME_JSON,
        "project_root": PROJECT_ROOT,
        "platform": platform.system().lower(),
        "machine": platform.machine().lower(),
        "min_python_version": min_version,
        "portable_python": portable,
        "system_python_candidates": system_candidates,
        "resolved_python": resolved,
    }


def main():
    parser = argparse.ArgumentParser(
        description="evolving-agent runtime Python resolver (offline, detect-only)"
    )
    parser.add_argument("--resolve", action="store_true",
                        help="Resolve Python path and output JSON to stdout")
    parser.add_argument("--doctor", action="store_true",
                        help="Output detailed diagnostic JSON to stdout")
    args = parser.parse_args()

    if args.doctor:
        result = doctor()
    else:
        result = resolve()

    json.dump(result, sys.stdout, indent=2)
    print()
    sys.exit(0 if result.get("status") == "ok" else 1)


if __name__ == "__main__":
    main()
