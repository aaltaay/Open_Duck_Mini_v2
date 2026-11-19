"""Weather from Open-Meteo. No key. No account.

Geocoding: https://open-meteo.com/en/docs/geocoding-api
Forecast: https://open-meteo.com/en/docs
The weather_code words are the WMO codes on that forecast page.
A failed fetch raises WeatherOffline. The caller says the network is needed.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

# Cited, Open-Meteo forecast docs, WMO weather interpretation codes.
WMO = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "foggy",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "a thunderstorm",
    96: "a thunderstorm",
    99: "a thunderstorm",
}

_UA = "open-duck-mini-companion"


class WeatherOffline(OSError):
    """The weather service did not answer. No body is stored."""


class WeatherClient:
    def __init__(self, fetch=None, timeout=8.0):
        self.fetch = fetch or self._fetch
        self.timeout = float(timeout)

    def _fetch(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise WeatherOffline("weather needs the network") from exc

    def report(self, city):
        city = " ".join(str(city).split())
        if not city:
            raise ValueError("city required")
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?count=1&language=en&format=json&name="
            + urllib.parse.quote(city)
        )
        geo = self.fetch(geo_url) or {}
        results = geo.get("results") or []
        if not results:
            return ""
        hit = results[0]
        lat = hit.get("latitude")
        lon = hit.get("longitude")
        if lat is None or lon is None:
            raise WeatherOffline("weather needs the network")
        name = hit.get("name") or city
        country = hit.get("country") or ""
        place = name if not country else "%s, %s" % (name, country)
        cast_url = (
            "https://api.open-meteo.com/v1/forecast?current=temperature_2m,weather_code"
            "&temperature_unit=fahrenheit&latitude=%s&longitude=%s" % (lat, lon)
        )
        cast = self.fetch(cast_url) or {}
        current = cast.get("current") or {}
        temp = current.get("temperature_2m")
        code = current.get("weather_code")
        if temp is None or code is None:
            raise WeatherOffline("weather needs the network")
        words = WMO.get(int(code), "weather code %s" % int(code))
        return "%s is %d F and %s." % (place, int(round(float(temp))), words)
