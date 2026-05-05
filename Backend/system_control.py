"""Full Windows control for Hey Boss.

Every heavy library (psutil, pycaw, screen_brightness_control, mss, ctypes
COM) is imported lazily inside the function that needs it. That way the
module imports clean on any host — including the rare cases where one of
the optional deps fails to install — and idle RAM stays low.

Every function returns a structured dict (`ok` always present) so the
frontend handler can be dumb. Destructive ops accept `confirm=False` and
no-op until the caller passes True. The proactive monitor in
`start_system_monitor()` runs in its own daemon thread spawned from
main.py.
"""
import os
import sys
import time
import threading


_PROTECTED_PIDS = {0, 4}
_PROTECTED_NAMES = {
    "system", "system idle process", "csrss.exe", "winlogon.exe",
    "services.exe", "lsass.exe", "svchost.exe", "explorer.exe",
    "dwm.exe", "wininit.exe", "smss.exe", "registry", "memcompression",
}


def _is_windows():
    return sys.platform == "win32"


# ===================================================================
# Stats — RAM / CPU / Disk / Battery / Volume
# ===================================================================

def get_stats():
    """Returns a snapshot of system vitals. Used by the dock overlay
    (every 5s from the frontend) and the proactive monitor."""
    try:
        import psutil
    except Exception as e:
        return {"ok": False, "error": f"psutil missing: {e}"}

    try:
        vm = psutil.virtual_memory()
        # interval=None gives a non-blocking value based on the cached
        # baseline — accurate enough for dock UI, ~free.
        cpu = psutil.cpu_percent(interval=None)
        try:
            disk = psutil.disk_usage("C:" if _is_windows() else "/").percent
        except Exception:
            disk = None
        battery_pct = None
        plugged = False
        try:
            bat = psutil.sensors_battery()
            if bat is not None:
                battery_pct = round(bat.percent)
                plugged = bool(bat.power_plugged)
        except Exception:
            pass

        volume = None
        try:
            volume = _read_volume_pct()
        except Exception:
            pass

        return {
            "ok": True,
            "ram": round(vm.percent),
            "ram_used_gb": round(vm.used / (1024 ** 3), 1),
            "ram_total_gb": round(vm.total / (1024 ** 3), 1),
            "cpu": round(cpu),
            "disk": disk,
            "battery": battery_pct,
            "plugged": plugged,
            "volume": volume,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def top_hogs(n=5):
    """Top-N processes by RSS. Skips protected/system processes."""
    try:
        import psutil
    except Exception:
        return []
    rows = []
    for p in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            info = p.info
            if info["pid"] in _PROTECTED_PIDS:
                continue
            name = (info.get("name") or "").lower()
            if name in _PROTECTED_NAMES:
                continue
            rss = info["memory_info"].rss if info.get("memory_info") else 0
            rows.append({
                "pid": info["pid"],
                "name": info.get("name") or f"pid {info['pid']}",
                "rss_mb": round(rss / (1024 ** 2)),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    rows.sort(key=lambda r: r["rss_mb"], reverse=True)
    return rows[:n]


def kill_process(pid, confirm=False):
    if not confirm:
        return {"ok": False, "error": "confirm required"}
    try:
        import psutil
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if int(pid) in _PROTECTED_PIDS:
        return {"ok": False, "error": "protected process"}
    try:
        p = psutil.Process(int(pid))
        if (p.name() or "").lower() in _PROTECTED_NAMES:
            return {"ok": False, "error": "protected process"}
        p.terminate()
        p.wait(timeout=3)
        return {"ok": True, "pid": int(pid)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ===================================================================
# Cleanup — temp files + EmptyWorkingSet on non-critical PIDs
# ===================================================================

def cleanup_caches(confirm=False):
    """Sweep %TEMP% + %LOCALAPPDATA%\\Temp and trim working sets.
    Returns {ok, freed_mb, files_removed, errors}."""
    if not confirm:
        return {"ok": False, "error": "confirm required"}

    freed_bytes = 0
    files_removed = 0
    errors = 0

    temp_dirs = []
    if _is_windows():
        for env in ("TEMP", "TMP"):
            v = os.environ.get(env)
            if v and os.path.isdir(v):
                temp_dirs.append(v)
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            cand = os.path.join(local_app, "Temp")
            if os.path.isdir(cand):
                temp_dirs.append(cand)
    else:
        if os.path.isdir("/tmp"):
            temp_dirs.append("/tmp")

    seen = set()
    for d in temp_dirs:
        real = os.path.realpath(d)
        if real in seen:
            continue
        seen.add(real)
        for root, _dirs, files in os.walk(real):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    sz = os.path.getsize(fp)
                    os.remove(fp)
                    freed_bytes += sz
                    files_removed += 1
                except Exception:
                    errors += 1

    # Trim working sets of non-critical processes (Windows only).
    # EmptyWorkingSet pages out unused memory; processes pull pages back
    # as needed. Visible RAM drops noticeably right after.
    if _is_windows():
        try:
            import ctypes
            import psutil
            psapi = ctypes.WinDLL("psapi.dll")
            kernel32 = ctypes.WinDLL("kernel32.dll")
            PROCESS_SET_QUOTA = 0x0100
            PROCESS_QUERY_INFORMATION = 0x0400
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    name = (p.info.get("name") or "").lower()
                    if name in _PROTECTED_NAMES or p.info["pid"] in _PROTECTED_PIDS:
                        continue
                    h = kernel32.OpenProcess(
                        PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION,
                        False,
                        p.info["pid"],
                    )
                    if h:
                        try:
                            psapi.EmptyWorkingSet(h)
                        finally:
                            kernel32.CloseHandle(h)
                except Exception:
                    pass
        except Exception:
            pass

    return {
        "ok": True,
        "freed_mb": round(freed_bytes / (1024 ** 2)),
        "files_removed": files_removed,
        "errors": errors,
    }


# ===================================================================
# Volume — pycaw
# ===================================================================

def _audio_endpoint():
    """Returns the IAudioEndpointVolume interface. Caller is responsible
    for calling CoInitialize on the current thread before this if not on
    the main thread."""
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def _read_volume_pct():
    if not _is_windows():
        return None
    try:
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass
    try:
        v = _audio_endpoint()
        return round(v.GetMasterVolumeLevelScalar() * 100)
    except Exception:
        return None


def set_volume(pct):
    if not _is_windows():
        return {"ok": False, "error": "Windows only"}
    pct = max(0, min(100, int(pct)))
    try:
        import comtypes
        try: comtypes.CoInitialize()
        except Exception: pass
        v = _audio_endpoint()
        v.SetMasterVolumeLevelScalar(pct / 100.0, None)
        return {"ok": True, "volume": pct}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def mute_volume(state=None):
    """state=True mute, False unmute, None toggle."""
    if not _is_windows():
        return {"ok": False, "error": "Windows only"}
    try:
        import comtypes
        try: comtypes.CoInitialize()
        except Exception: pass
        v = _audio_endpoint()
        if state is None:
            current = v.GetMute()
            v.SetMute(0 if current else 1, None)
            return {"ok": True, "muted": not bool(current)}
        v.SetMute(1 if state else 0, None)
        return {"ok": True, "muted": bool(state)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ===================================================================
# Brightness — screen-brightness-control
# ===================================================================

def set_brightness(pct):
    pct = max(0, min(100, int(pct)))
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(pct)
        return {"ok": True, "brightness": pct}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_brightness():
    try:
        import screen_brightness_control as sbc
        vals = sbc.get_brightness()
        if isinstance(vals, list) and vals:
            return {"ok": True, "brightness": int(vals[0])}
        return {"ok": True, "brightness": int(vals)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ===================================================================
# Screenshot — mss
# ===================================================================

def take_screenshot():
    try:
        from pathlib import Path
        import mss
    except Exception as e:
        return {"ok": False, "error": str(e)}

    try:
        out_dir = Path.home() / "Pictures" / "JarvisShots"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = str(out_dir / f"jarvis_{ts}.png")
        with mss.mss() as sct:
            sct.shot(mon=-1, output=path)
        return {"ok": True, "path": path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ===================================================================
# Power — lock / sleep / shutdown
# ===================================================================

def lock_screen():
    if not _is_windows():
        return {"ok": False, "error": "Windows only"}
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def sleep_pc(confirm=False):
    if not confirm:
        return {"ok": False, "error": "confirm required"}
    if not _is_windows():
        return {"ok": False, "error": "Windows only"}
    try:
        import ctypes
        ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def shutdown_pc(confirm=False, restart=False, delay_s=60):
    """Schedules a shutdown/restart with a grace period so the user can
    abort with `shutdown /a` if voice command was misheard."""
    if not confirm:
        return {"ok": False, "error": "confirm required"}
    if not _is_windows():
        return {"ok": False, "error": "Windows only"}
    try:
        import subprocess
        flag = "/r" if restart else "/s"
        subprocess.run(
            ["shutdown", flag, "/t", str(int(delay_s))],
            check=False, capture_output=True,
        )
        return {"ok": True, "delay_s": int(delay_s), "abort": "shutdown /a"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ===================================================================
# Proactive monitor — daemon thread
# ===================================================================

_monitor_thread = None
_monitor_stop = threading.Event()


def _ram_alert_payload():
    s = get_stats()
    return {
        "type": "ram",
        "value": s.get("ram", 0),
        "used_gb": s.get("ram_used_gb", 0),
        "total_gb": s.get("ram_total_gb", 0),
        "top": top_hogs(5),
    }


def _cpu_alert_payload():
    s = get_stats()
    return {
        "type": "cpu",
        "value": s.get("cpu", 0),
        "top": top_hogs(5),
    }


def _battery_alert_payload(level):
    return {"type": "battery", "value": level}


def _monitor_loop(eel_instance):
    """Polls every 60s; on threshold trip, samples 6× over 30s and
    requires 4/6 hits before alerting. 5-min cooldown after each fire."""
    try:
        import psutil  # noqa: F401
    except Exception:
        print("⚠️  psutil missing — system monitor disabled.")
        return

    BASELINE_S = 60
    SAMPLE_INTERVAL_S = 5
    SAMPLES = 6
    SAMPLE_THRESHOLD = 4
    COOLDOWN_S = 5 * 60

    last_fire_ts = 0.0
    battery_warned_20 = False
    battery_warned_10 = False

    def _emit(payload):
        try:
            eel_instance.systemAlert(payload)()
        except Exception as e:
            print(f"⚠️  systemAlert push failed: {e}")

    while not _monitor_stop.is_set():
        try:
            s = get_stats()
            now = time.time()

            # Battery alerts — fire once per discharge cycle
            bat = s.get("battery")
            plugged = s.get("plugged", False)
            if plugged:
                battery_warned_20 = False
                battery_warned_10 = False
            elif bat is not None:
                if bat <= 10 and not battery_warned_10:
                    _emit(_battery_alert_payload(bat))
                    battery_warned_10 = True
                elif bat <= 20 and not battery_warned_20:
                    _emit(_battery_alert_payload(bat))
                    battery_warned_20 = True

            # RAM / CPU sustained-spike check — gated by cooldown
            if (now - last_fire_ts) >= COOLDOWN_S:
                ram_hot = s.get("ram", 0) > 85
                cpu_hot = s.get("cpu", 0) > 90
                if ram_hot or cpu_hot:
                    hits_ram = 0
                    hits_cpu = 0
                    for _ in range(SAMPLES):
                        if _monitor_stop.is_set():
                            break
                        time.sleep(SAMPLE_INTERVAL_S)
                        s2 = get_stats()
                        if s2.get("ram", 0) > 85: hits_ram += 1
                        if s2.get("cpu", 0) > 90: hits_cpu += 1
                    if hits_ram >= SAMPLE_THRESHOLD:
                        _emit(_ram_alert_payload())
                        last_fire_ts = time.time()
                    elif hits_cpu >= SAMPLE_THRESHOLD:
                        _emit(_cpu_alert_payload())
                        last_fire_ts = time.time()
        except Exception as e:
            print(f"⚠️  monitor loop error: {e}")

        # Sleep in small chunks so stop() reacts quickly
        slept = 0
        while slept < BASELINE_S and not _monitor_stop.is_set():
            time.sleep(1)
            slept += 1


def start_system_monitor(eel_instance):
    """Spawns the proactive monitor in a daemon thread. Idempotent."""
    global _monitor_thread
    if _monitor_thread is not None and _monitor_thread.is_alive():
        return False
    _monitor_stop.clear()
    _monitor_thread = threading.Thread(
        target=_monitor_loop, args=(eel_instance,), daemon=True,
        name="JarvisSystemMonitor",
    )
    _monitor_thread.start()
    return True


def stop_system_monitor():
    _monitor_stop.set()
