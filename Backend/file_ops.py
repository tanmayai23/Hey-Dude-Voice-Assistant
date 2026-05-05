"""File operations for Hey Boss — download URLs, type into Notepad, find files.

Lazy imports throughout. Every function returns a structured dict so
the voice route handler can speak appropriate Hinglish.
"""
import os
import sys
import time
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote


def _is_windows():
    return sys.platform == "win32"


def _safe_filename_from_url(url, fallback="download.bin"):
    try:
        path = urlparse(url).path
        name = unquote(os.path.basename(path)) or fallback
        # strip illegal Windows path chars
        for ch in '<>:"/\\|?*':
            name = name.replace(ch, "_")
        return name.strip() or fallback
    except Exception:
        return fallback


def download_file(url, save_path=None, timeout=30):
    """Streams URL to disk. If save_path is omitted, writes into
    ~/Downloads using the URL's basename."""
    try:
        import requests
    except Exception as e:
        return {"ok": False, "error": f"requests missing: {e}"}

    try:
        if not save_path:
            downloads = Path.home() / "Downloads"
            downloads.mkdir(parents=True, exist_ok=True)
            save_path = str(downloads / _safe_filename_from_url(url))

        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total = 0
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
        return {
            "ok": True,
            "path": save_path,
            "size_mb": round(total / (1024 ** 2), 2),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def write_file_to_app(content, app="notepad"):
    """Opens Notepad (or another app) and types content via pyautogui.
    Notepad gets a brief sleep so the window has time to focus."""
    if not _is_windows() and app == "notepad":
        return {"ok": False, "error": "Notepad is Windows-only"}

    try:
        if app == "notepad":
            subprocess.Popen(["notepad.exe"])
            time.sleep(0.7)
        else:
            subprocess.Popen([app])
            time.sleep(0.9)

        try:
            import pyautogui
        except Exception as e:
            return {"ok": False, "error": f"pyautogui missing: {e}"}

        # Slow-ish per-char typing avoids dropped chars on slower hosts.
        pyautogui.write(content, interval=0.005)
        return {"ok": True, "app": app, "chars": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def find_file(name, root=None, max_results=50, timeout_s=30):
    """Case-insensitive file search. Walks ~ by default. Stops at
    timeout or max_results to avoid runaway scans."""
    if not name:
        return {"ok": False, "error": "name required"}
    name_lower = name.lower()
    root = root or str(Path.home())

    matches = []
    started = time.time()
    try:
        for cur_root, _dirs, files in os.walk(root):
            if (time.time() - started) > timeout_s:
                break
            for f in files:
                if name_lower in f.lower():
                    matches.append(os.path.join(cur_root, f))
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break
        return {
            "ok": True,
            "paths": matches,
            "count": len(matches),
            "truncated": len(matches) >= max_results,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
