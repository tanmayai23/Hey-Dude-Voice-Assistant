"""Weather lookup using Open-Meteo (no key, free).

City resolution order:
1. Profile.city if set in HeyDude.db
2. IP geolocation via ipapi.co/json (no key, ~5 req/min limit)
3. Falls back to a polite "boss city set kar do" if neither works.

Designed to be cheap: imports `requests` lazily, 4-second timeouts everywhere,
small JSON payloads, no caching layer (Open-Meteo is fast enough that a per-
query call adds <500ms).
"""
import sqlite3
from datetime import datetime


_CONDITION_HI = {
    0: "saaf aasman",
    1: "thoda saaf, halki cloud",
    2: "thoda cloudy",
    3: "puri tarah cloudy",
    45: "kohra hai",
    48: "kohra aur frost",
    51: "halki phuhar",
    53: "phuhar",
    55: "tez phuhar",
    61: "halki baarish",
    63: "baarish",
    65: "tez baarish",
    66: "freezing rain — sambhal ke",
    67: "tez freezing rain",
    71: "halki snowfall",
    73: "snowfall",
    75: "tez snowfall",
    77: "snow grains",
    80: "baarish ki bauchhar",
    81: "baarish ki tez bauchhar",
    82: "bahut tez baarish",
    85: "snow shower",
    86: "tez snow shower",
    95: "thunderstorm — bahar mat ja",
    96: "thunderstorm with hail",
    99: "tez thunderstorm with hail",
}


def _profile_city():
    try:
        con = sqlite3.connect("HeyDude.db")
        cur = con.cursor()
        cur.execute("SELECT city FROM profile WHERE id=1")
        row = cur.fetchone()
        con.close()
        if row and row[0] and row[0].strip():
            return row[0].strip()
    except Exception:
        pass
    return None


def _resolve_city(city_hint=None):
    """Returns (lat, lon, label). Raises on full failure."""
    import requests

    # 1. Caller-supplied
    if city_hint:
        try:
            r = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city_hint, "count": 1, "language": "en"},
                timeout=4,
            )
            results = (r.json() or {}).get("results") or []
            if results:
                hit = results[0]
                return hit["latitude"], hit["longitude"], hit.get("name", city_hint)
        except Exception:
            pass

    # 2. Profile.city
    pc = _profile_city()
    if pc:
        try:
            r = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": pc, "count": 1, "language": "en"},
                timeout=4,
            )
            results = (r.json() or {}).get("results") or []
            if results:
                hit = results[0]
                return hit["latitude"], hit["longitude"], hit.get("name", pc)
        except Exception:
            pass

    # 3. IP geolocation
    try:
        r = requests.get("https://ipapi.co/json/", timeout=4)
        data = r.json() or {}
        if data.get("latitude") and data.get("longitude"):
            return data["latitude"], data["longitude"], data.get("city") or "your area"
    except Exception:
        pass

    raise RuntimeError("Could not resolve location for weather")


def _strip_city_words(query):
    """Pull a city name out of phrases like 'mausam in delhi' or 'delhi ka mausam'."""
    q = (query or "").lower()
    for stop in ("weather", "mausam", "temperature", "in", "ka", "kaisa", "kaisi", "hai", "today", "now", "boss", "hey"):
        q = q.replace(stop, " ")
    q = " ".join(q.split())
    return q.strip() or None


def get_weather(query=None):
    """Returns a Hinglish summary string. Never raises — always returns SOMETHING speakable."""
    try:
        import requests
    except Exception:
        return "Boss, requests library install nahi hai — weather check nahi ho payega."

    try:
        hint = _strip_city_words(query) if query else None
        lat, lon, label = _resolve_city(hint)
    except Exception:
        return "Boss, city set nahi hai — settings me city add kar do."

    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
            },
            timeout=5,
        )
        data = r.json()
    except Exception as e:
        return f"Boss, weather server tak pahunch nahi paya — {e}."

    try:
        cur = data["current"]
        daily = data["daily"]
        temp = round(cur["temperature_2m"])
        feels = round(cur["apparent_temperature"])
        humidity = cur["relative_humidity_2m"]
        code = cur["weather_code"]
        wind = cur["wind_speed_10m"]
        tmax = round(daily["temperature_2m_max"][0])
        tmin = round(daily["temperature_2m_min"][0])

        cond = _CONDITION_HI.get(code, "weather thoda mixed hai")

        return (
            f"Boss, {label} me abhi {temp}°C hai aur {cond}. "
            f"Feels like {feels}°C, humidity {humidity}%. "
            f"Aaj ka high {tmax}°C aur low {tmin}°C rahega. "
            f"Hawa {wind} km/h."
        )
    except Exception:
        return "Boss, data thoda gadbad aaya weather server se."
