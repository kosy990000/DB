"""Shared download utilities for stage 1 (1_download).

Robust streaming download with progress, resume, and skip-if-exists,
plus gzip/tar helpers. Used by the per-source download scripts.
"""
import gzip
import shutil
import tarfile
import time
from pathlib import Path

import requests

CHUNK = 1024 * 1024  # 1 MiB


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def download_file(url, dest, *, skip_if_exists=True, resume=True, timeout=60):
    """Stream a URL to ``dest`` with progress bar, resume, and skip-if-exists.

    Downloads to ``dest.part`` first, then renames on success so an
    interrupted run never leaves a truncated file at the final path.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if skip_if_exists and dest.exists():
        print(f"  [skip] {dest.name} already exists ({human(dest.stat().st_size)})")
        return dest

    tmp = dest.with_name(dest.name + ".part")
    headers = {}
    mode = "wb"
    existing = 0
    if resume and tmp.exists():
        existing = tmp.stat().st_size
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"

    print(f"  [get ] {url}")
    with requests.get(url, stream=True, headers=headers, timeout=timeout) as r:
        # Server ignored our Range request -> start over from scratch.
        if existing and r.status_code == 200:
            existing = 0
            mode = "wb"
        r.raise_for_status()

        total = int(r.headers.get("Content-Length", 0)) + existing
        done = existing
        last = 0.0
        with open(tmp, mode) as f:
            for chunk in r.iter_content(chunk_size=CHUNK):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                now = time.time()
                if now - last > 1.0:
                    pct = f"{done / total * 100:5.1f}%" if total else "  ?  "
                    tail = f" / {human(total)}" if total else ""
                    print(f"\r  [....] {pct}  {human(done)}{tail}   ", end="", flush=True)
                    last = now

    print(f"\r  [done] {dest.name}  {human(done)}                              ")
    tmp.replace(dest)
    return dest


def gunzip(src, dest, *, keep=False, skip_if_exists=True):
    """Decompress a .gz file to ``dest``."""
    src = Path(src)
    dest = Path(dest)
    if skip_if_exists and dest.exists():
        print(f"  [skip] {dest.name} already decompressed")
        if not keep and src.exists():
            src.unlink()
        return dest
    print(f"  [gzip] {src.name} -> {dest.name}")
    with gzip.open(src, "rb") as fi, open(dest, "wb") as fo:
        shutil.copyfileobj(fi, fo, length=CHUNK)
    if not keep:
        src.unlink()
    return dest


def download_gz(url, dest, *, skip_if_exists=True, **kw):
    """Download a gzipped URL and decompress it to ``dest`` (the plain file)."""
    dest = Path(dest)
    if skip_if_exists and dest.exists():
        print(f"  [skip] {dest.name} already exists ({human(dest.stat().st_size)})")
        return dest
    gz_tmp = dest.with_name(dest.name + ".gz")
    download_file(url, gz_tmp, skip_if_exists=False, **kw)
    return gunzip(gz_tmp, dest, keep=False, skip_if_exists=False)


def extract_tar(src, dest_dir, *, skip_marker=None):
    """Extract a tar(.gz) archive into ``dest_dir``.

    If ``skip_marker`` (a path) already exists, extraction is skipped.
    """
    src = Path(src)
    dest_dir = Path(dest_dir)
    if skip_marker and Path(skip_marker).exists():
        print(f"  [skip] already extracted ({Path(skip_marker).name} present)")
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"  [tar ] extracting {src.name} -> {dest_dir}")
    with tarfile.open(src, "r:*") as tf:
        try:
            tf.extractall(dest_dir, filter="data")  # py>=3.12
        except TypeError:
            tf.extractall(dest_dir)