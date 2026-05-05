# Jarvis Upgrade — "Hey Boss" Personal Assistant

## Context
Hey-Dude already has a solid base: working command router, persistent Gemini chat, WhatsApp/YouTube/open-app automation, lazy-loaded heavy modules, glass UI with arc-reactor centerpiece. Three things hold it back from being the "Jarvis with full laptop access" you described:

1. **No true wake word** — current `hotword_detection.py` polls Google Speech every few seconds. Always-on, network-heavy, can't run hands-free.
2. **No system control** — the assistant can't see your RAM, can't clean caches, can't take screenshots, can't change volume/brightness, can't drive Notepad. Half the "Jarvis" feel is missing.
3. **Half the suggestion chips are stubs** — `weather`, `surprise me`, `dinner ideas` fall through to generic Gemini; the dock status row (SYSTEM / VOICE / UPLINK / DATE / TIME) cramps on narrower windows.

Goal: ship a Hinglish "boss" personality, real offline wake word ("hey boss"), full system access with safe confirm-before-act cleanup, wire the dead chips, and fix the dock alignment — **without touching the iron-man aesthetic** you said is already perfect.

**Decisions locked from clarifying questions:**
- Wake word: **Picovoice Porcupine** (offline, custom-trainable "hey boss")
- High-RAM behavior: **Notify + ask "saaf kar dun?", then clean** on confirm
- Tone: **Hinglish always** — "Hey boss, kaiso ho aap" everywhere

---

## Phase 1 — Foundation (personality, wake word, dock fix)
Smallest visible win. Land this first, test, then move on.

### 1.1 Hinglish boss personality
- `Backend/gemini_ai.py:41` — replace system instruction with Hinglish boss persona:
  > "Tu mera personal assistant hai, mai tera boss hun. Hamesha 'boss' kehke address kar. Reply Hinglish me — Hindi Roman script + English mixed (jaise 'haan boss, woh kaam ho gaya'). Friendly, witty, thoda cocky — Iron Man ke Jarvis jaisa. Greetings: 'Hey boss, kaiso ho aap' / 'Ji boss, sun raha hun'. Errors: 'Sorry boss, samjha nahi'. Short replies — 2-3 sentences max unless boss explicitly asks long answer."
- Sweep hardcoded English in `Backend/command.py` (lines around 87-141: "Can you repeat?", greeting strings) and `Backend/features.py:24-76` (open/play confirmations) → Hinglish equivalents.
- Cache the pyttsx3 engine at module level (currently `command.py:9` creates new engine per call — slow).

### 1.2 Picovoice wake word — `Backend/wake_word.py` (NEW)
- Wraps `pvporcupine` + `pvrecorder`. Daemon thread, on-detect calls `eel.activateMicFromHotword()` then `start_listen()` once.
- Reads `PICOVOICE_ACCESS_KEY` and optional `WAKE_WORD_PPN_PATH` from `.env`.
- If no custom `.ppn`, falls back to a built-in keyword (e.g. `jarvis` or `hey google`) so it works the second the user pastes their AccessKey, before they train custom "hey boss" on picovoice.ai console.
- `main.py:86-95` — when `ENABLE_HOTWORD=true`, prefer Porcupine. If `pvporcupine` import fails, fall back to existing `hotword_detection.py` (don't delete it).
- `requirements.txt` — add `pvporcupine`, `pvrecorder` (~10 MB combined, near-zero CPU at idle).
- `.env.example` — add `PICOVOICE_ACCESS_KEY=`, `WAKE_WORD_PPN_PATH=` with comments linking to picovoice.ai.

### 1.3 Dock alignment fix (`Frontend/index.html:259-283`, `Frontend/style.css:948-984`)
Current dock is a flat 6-element row using per-cluster `margin-left: auto`. Cramps below ~900px and the value text truncates inside chips. Fix:
- HTML: wrap into two groups —
  ```html
  <footer class="dock">
    <div class="dock__group dock__group--status"> SYSTEM/VOICE/UPLINK clusters </div>
    <div class="dock__group dock__group--meta"> DATE/TIME/RESET </div>
  </footer>
  ```
- CSS: `.dock { justify-content: space-between; flex-wrap: wrap; row-gap: 10px; }` and `.dock__group { display: flex; align-items: center; gap: 28px; }`. Drop the `--right` margin-auto hack.
- Below 720px (`@media`): meta group drops to its own line cleanly instead of overlapping.
- Optional Pencil mockup of the new dock if a `.pen` design file already exists for the project; otherwise skip — pure CSS is enough.

---

## Phase 2 — Wire up the dead chips
### 2.1 Weather — `Backend/weather.py` (NEW)
- Open-Meteo API (no key, free). City from `profile` table (already has `city` column — `config.py:14-52`); fallback to IP geolocation via `https://ipapi.co/json/`.
- Response: "Boss, abhi {temp}°C hai {city} me, {condition}. Max aaj {max}°C tak jayega."
- Route in `command.py:execute_command` — match `weather|mausam|temperature` BEFORE Gemini fallback.

### 2.2 "Surprise me" / "Dinner ideas"
- Already work via Gemini fallback. Just nudge prompts in `index.html:222-229` data-cmd → Hinglish-flavored ("kuch interesting batao boss", "aaj khane me kya banaun") so Gemini replies in tone.

### 2.3 Chip relabeling
- Visible labels → Hinglish: `weather` → `mausam`, `surprise me` → `kuch sunao`, `dinner ideas` → `khana ideas`. Underlying `data-cmd` strings unchanged so backend matching still works.

---

## Phase 3 — Full laptop control (the real Jarvis bit)
All Windows-specific. All lazy-imported. All gated behind explicit voice or button trigger except the proactive monitor.

### 3.1 `Backend/system_control.py` (NEW)
Single class wrapping:

| Capability | Library / Approach |
|---|---|
| RAM / CPU / Disk | `psutil.virtual_memory()`, `cpu_percent()`, `disk_usage('C:')` |
| Battery | `psutil.sensors_battery()` — proactive alerts at ≤20%, ≤10%, full |
| Top memory hogs | `psutil.process_iter(['name','memory_info'])` sorted by RSS |
| Kill process | `psutil.Process(pid).terminate()` — confirm-only |
| Cache cleanup | sweep `%TEMP%`, `%LOCALAPPDATA%\Temp`, `EmptyWorkingSet` via ctypes for non-critical PIDs |
| Volume | `pycaw` (COM audio) |
| Brightness | `screen-brightness-control` |
| Screenshot | `mss` → `~/Pictures/JarvisShots/{ts}.png` |
| Lock / sleep / shutdown | `ctypes.windll.user32.LockWorkStation()` etc. — always confirm |

### 3.2 Proactive monitor (daemon thread)
- Spawned from `main.py:start()` if `ENABLE_SYSTEM_MONITOR=true` (default true).
- Polls psutil every 60s (microsecond cost).
- Trigger: RAM > 85% OR CPU > 90% sustained 30s.
- Calls `eel.systemAlert({type:'ram', value:87, top:[…]})`. Frontend shows a small toast inside the dock area: "Boss, RAM 87% — saaf kar dun?" with **Haan** / **Nahi** buttons.
- On Haan → `system_control.cleanup()` runs, frontend hears `eel.systemAlertResolved({freed_mb: 1240})`, speaks "Saaf ho gaya boss, 1.2 GB free kar diya."

### 3.3 Voice routes (extend `command.py:execute_command`)
- `ram check` / `memory kitni hai` → speak %, show top 5 hogs
- `saaf kar` / `clean cache` → cleanup with confirm
- `screenshot lo` / `screenshot le` → save + announce path
- `volume 50` / `volume up/down/mute` → pycaw
- `brightness 70` → screen-brightness-control
- `battery kitni` → psutil.sensors_battery
- `lock kar de` / `lock screen` → user32.LockWorkStation

### 3.4 File operations — `Backend/file_ops.py` (NEW)
- `download_file(url, save_path)` — `requests` (already pulled in by pywhatkit), lazy import.
- `write_file_to_app(content, app='notepad')` — opens Notepad, types via `pyautogui` (already a dep). For "boss notepad me likho hello world" use case.
- `find_file(name, root='C:\\Users\\tanma')` — `os.walk` with name filter.
- Voice: `download {url}`, `notepad kholo aur likho {content}`, `dhundo {filename}`.

### 3.5 System stats overlay (frontend)
- Small live mini-panel in the dock or hover popover: RAM/CPU/Battery mini-bars, refreshed every 5s via new `eel.expose def get_system_stats()` → `eel.updateSystemStats(payload)`.
- Use **Pencil MCP** here to mock placement and styling so it sits inside the iron-man aesthetic — call `find_empty_space_on_canvas` + `batch_design` only if a project `.pen` exists; otherwise place it inline with current style tokens (`--red`, `--paper-fade`, `--f-mono`).

---

## Phase 4 — Polish & robustness
- `gemini_ai.py:41` — model fallback list `['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']`, pick first that initializes. Protects against model retirement.
- `helper.py:32` — delete dead `remove_words()` (undefined `input_string`).
- `@eel.expose def health()` — return per-subsystem status (mic / gemini / porcupine / system_control). Dock shows a colored dot.
- Chat history → also persist to new SQLite `chat_log` table (browser localStorage stays as primary; SQLite is backup).

---

## Critical files

**Modify**
- `Backend/gemini_ai.py` — line 41 (Hinglish prompt + model fallback list)
- `Backend/command.py` — lines 9-17 (cache pyttsx3 engine), 32-83 (add weather/system/file routes), 87-141 (Hinglish strings)
- `Backend/features.py` — Hinglish confirmations
- `Backend/helper.py` — delete `remove_words()`
- `main.py` — lines 86-95 (Porcupine swap), add monitor thread
- `Frontend/index.html` — lines 222-229 (chip labels), 259-283 (dock restructure), add stats overlay
- `Frontend/style.css` — lines 948-984 (dock flex restructure + media query), new system-alert toast & stats overlay styles
- `Frontend/main.js` — handlers for `systemAlert`, `updateSystemStats`
- `requirements.txt` — add pvporcupine, pvrecorder, psutil, pycaw, screen-brightness-control, mss
- `.env.example` — add PICOVOICE_ACCESS_KEY, WAKE_WORD_PPN_PATH, ENABLE_SYSTEM_MONITOR

**New**
- `Backend/wake_word.py` (Porcupine wrapper)
- `Backend/weather.py`
- `Backend/system_control.py`
- `Backend/file_ops.py`

**Keep as fallback (don't delete)**
- `hotword_detection.py` — used if `pvporcupine` import fails

---

## Reuse (don't reinvent)
- `Backend/command.py:execute_command` routing pattern — extend with new prefixes, don't replace
- `Backend/config.py` profile table — already has `city` field for weather
- `Backend/features.py:opencommand` — handles "open X" generically; system_control hooks into the same router
- `eel.expose` decorator pattern across all new handlers
- Lazy-import pattern from `main.py` docstring — keep for psutil/pycaw/mss/pvporcupine

---

## Verification
1. `python run.py` — starts without errors, UI loads at localhost:8006
2. **Dock alignment** — resize browser to 720px wide, status row stays clean, meta group drops to row 2 instead of overlapping
3. **Wake word** — set `PICOVOICE_ACCESS_KEY` and `ENABLE_HOTWORD=true`, say built-in keyword (or trained "hey boss") → UI mic activates. CPU stays <2% at idle
4. **Personality** — type "hello" → response starts with "Hey boss" / "Ji boss". Type "what's weather" → Hinglish reply
5. **Weather chip** — click `mausam` → "Boss, abhi X°C hai {city} me…"
6. **System control** —
   - "ram check" → speaks RAM%, shows top 5 hogs in chat
   - Open many apps to push RAM > 85% → toast appears, click Haan → cleanup runs, MB freed announced
   - "screenshot lo" → file appears in `~/Pictures/JarvisShots/`
   - "volume 50", "brightness 70" → system actually changes
7. **File ops** — "notepad kholo aur likho hello world" → Notepad opens with that text
8. **Memory footprint** — `psutil` self-check shows resident <250 MB at idle (current baseline ~50-80 MB; psutil + pvporcupine add ~30-50 MB)
9. **Health** — `eel.health()` returns all subsystems green; dock dot is green

---

## Phasing recommendation
Ship in order — **don't try to land everything at once.**
- **Phase 1**: 3-5h. Biggest perceptual win. Test thoroughly.
- **Phase 2**: 1-2h. Quick chip cleanup.
- **Phase 3**: 4-6h. The big new surface area; needs careful testing per capability.
- **Phase 4**: 2h. Polish.

Total ~12h of work. After Phase 1 the assistant already feels different.
