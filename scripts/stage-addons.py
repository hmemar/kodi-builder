#!/usr/bin/env python3
"""Stage python, binary and bundled add-ons into a Kodi source tree.

Usage:
  stage-addons.py <kodi-src> <kodi-config-dir> <platform>

platform: android-aarch64 | android-armv7 | windows-x86_64 | osx-arm64 | osx-x86_64 | linux | python-only
For linux/python-only, only python + bundled add-ons are staged (binary built separately).
"""
from __future__ import annotations

import base64
import io
import os
import re
import shutil
import sys
import urllib.request
import zipfile

MIRROR = "https://mirrors.kodi.tv/addons/omega"


def _log(msg: str) -> None:
    print(msg, flush=True)


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 HushamPlay/1.1"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read()


def _register(src: str, addon_id: str) -> None:
    inst = os.path.join(src, "cmake", "installdata", "common", "addons.txt")
    man = os.path.join(src, "system", "addon-manifest.xml")
    entry = f"addons/{addon_id}/*"
    if os.path.isfile(inst):
        text = open(inst, encoding="utf-8").read()
        if entry not in text:
            with open(inst, "a", encoding="utf-8") as fh:
                fh.write(f"\n{entry}\n")
    if os.path.isfile(man):
        text = open(man, encoding="utf-8").read()
        if f"<addon>{addon_id}</addon>" not in text:
            open(man, "w", encoding="utf-8").write(
                text.replace("</addons>", f"  <addon>{addon_id}</addon>\n</addons>")
            )


def _extract_zip(data: bytes, dest_addons: str) -> list[str]:
    z = zipfile.ZipFile(io.BytesIO(data))
    z.extractall(dest_addons)
    ids = sorted({n.split("/")[0] for n in z.namelist() if n and not n.startswith("__")})
    return [i for i in ids if i]


def install_python(src: str, cfg: str) -> list[str]:
    af = os.path.join(cfg, "addons.txt")
    installed: list[str] = []
    if not os.path.isfile(af):
        return installed
    dest = os.path.join(src, "addons")
    os.makedirs(dest, exist_ok=True)
    for line in open(af, encoding="utf-8"):
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        _log(f"python addon: {url}")
        data = _download(url)
        for aid in _extract_zip(data, dest):
            _register(src, aid)
            installed.append(aid)
            _log(f"  + {aid}")
    return installed


def install_bundled(src: str, cfg: str) -> list[str]:
    bundled = os.path.join(cfg, "bundled-addons")
    installed: list[str] = []
    if not os.path.isdir(bundled):
        return installed
    dest = os.path.join(src, "addons")
    for name in sorted(os.listdir(bundled)):
        path = os.path.join(bundled, name)
        if not os.path.isdir(path):
            continue
        target = os.path.join(dest, name)
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(path, target)
        # Decode any *.b64 assets shipped in git
        for dirpath, _, filenames in os.walk(target):
            for fn in filenames:
                if fn.endswith(".b64"):
                    raw = fn[:-4]
                    raw_path = os.path.join(dirpath, raw)
                    b64_path = os.path.join(dirpath, fn)
                    if not os.path.isfile(raw_path):
                        open(raw_path, "wb").write(base64.b64decode(open(b64_path, "rb").read()))
        _register(src, name)
        installed.append(name)
        _log(f"bundled addon: {name}")
    return installed


def install_binary(src: str, cfg: str, platform: str) -> list[str]:
    if platform in ("linux", "python-only", ""):
        _log(f"skip binary mirror install for platform={platform}")
        return []
    bf = os.path.join(cfg, "binary-addons.txt")
    if not os.path.isfile(bf):
        return []
    dest = os.path.join(src, "addons")
    os.makedirs(dest, exist_ok=True)
    installed: list[str] = []
    for line in open(bf, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        addon_id, version = parts[0], parts[1]
        url = f"{MIRROR}/{addon_id}+{platform}/{addon_id}-{version}.zip"
        _log(f"binary addon: {url}")
        try:
            data = _download(url)
        except Exception as exc:  # noqa: BLE001
            _log(f"  FAILED {addon_id}: {exc}")
            continue
        for aid in _extract_zip(data, dest):
            _register(src, aid)
            installed.append(aid)
            _log(f"  + {aid}")
    return installed


def decode_config_assets(cfg: str) -> None:
    for dirpath, _, filenames in os.walk(cfg):
        for fn in filenames:
            if not fn.endswith(".b64"):
                continue
            raw = fn[:-4]
            raw_path = os.path.join(dirpath, raw)
            b64_path = os.path.join(dirpath, fn)
            if not os.path.isfile(raw_path):
                open(raw_path, "wb").write(base64.b64decode(open(b64_path, "rb").read()))
                _log(f"decoded {raw}")


def copy_userdata(src: str, cfg: str) -> None:
    ud = os.path.join(src, "userdata")
    os.makedirs(ud, exist_ok=True)
    for f in ("sources.xml", "advancedsettings.xml", "favourites.xml", "guisettings.xml"):
        p = os.path.join(cfg, f)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(ud, f))
            _log(f"userdata {f}")


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    src, cfg, platform = sys.argv[1], sys.argv[2], sys.argv[3]
    _log(f"stage-addons src={src} platform={platform}")
    decode_config_assets(cfg)
    copy_userdata(src, cfg)
    all_ids = []
    all_ids += install_python(src, cfg)
    all_ids += install_bundled(src, cfg)
    all_ids += install_binary(src, cfg, platform)
    _log("staged: " + ", ".join(all_ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
