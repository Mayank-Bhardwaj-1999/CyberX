#!/usr/bin/env python3
"""Lightweight health / readiness checks.
Run: python health_check.py --all
Exits non-zero if a critical check fails.
"""
from __future__ import annotations
import argparse, os, sys, json, socket, shutil, time
from pathlib import Path

def check_python(min_major=3, min_minor=9):
    v = sys.version_info
    if v.major > min_major or (v.major == min_major and v.minor >= min_minor):
        return True, f"Python {v.major}.{v.minor}.{v.micro} OK"
    return False, f"Python {v.major}.{v.minor}.{v.micro} < {min_major}.{min_minor}"

def check_dirs():
    required = ["data", "logs", "config", "src"]
    missing = [d for d in required if not Path(d).exists()]
    return (len(missing)==0, f"Directories OK" if not missing else f"Missing: {', '.join(missing)}")

def check_write(path: str):
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write('{}')
        p.unlink(missing_ok=True)
        return True, f"Writable: {path}"
    except Exception as e:
        return False, f"Write fail {path}: {e}"

def check_network(host="api-inference.huggingface.co", port=443, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"Network OK to {host}:{port}"
    except Exception as e:
        return False, f"Network fail {host}:{port} - {e}"

def check_disk(min_free_mb=200):
    total, used, free = shutil.disk_usage('.')
    free_mb = free/1024/1024
    if free_mb < min_free_mb:
        return False, f"Low disk {free_mb:.1f}MB < {min_free_mb}MB"
    return True, f"Disk free {free_mb:.1f}MB"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()

    results = {}

    ok, msg = check_python()
    results['python'] = {"ok": ok, "msg": msg}

    for name, fn in {
        'dirs': check_dirs,
        'disk': check_disk,
        'write_logs': lambda: check_write('logs/.write_test'),
        'write_data': lambda: check_write('data/.write_test'),
        'network_hf': check_network,
    }.items():
        ok, msg = fn()
        results[name] = {"ok": ok, "msg": msg}

    exit_code = 0 if all(r['ok'] for r in results.values()) else 1

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for k, v in results.items():
            print(f"{k:15} {'OK' if v['ok'] else 'FAIL'} - {v['msg']}")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
