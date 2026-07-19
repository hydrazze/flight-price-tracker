import json
import re
from pathlib import Path

try:
    from transliterate import translit
except ImportError:
    translit = None


class CityResolver:
    def __init__(self):
        path = Path(__file__).resolve().parents[1] / "data" / "airports.json"

        with path.open("r", encoding="utf-8") as file:
            self.airports = json.load(file)

        self.aliases = {
            "mow": "Москва",
            "dme": "Москва",
            "svo": "Москва",
            "vko": "Москва",
            "kzn": "Казань",
            "ufa": "Уфа",
            "led": "Санкт-Петербург",
            "ist": "Стамбул",
            "cdg": "Париж",
            "jfk": "Нью-Йорк",
            "lhr": "Лондон",
            "sin": "Сингапур",
            "pek": "Пекин",
            "del": "Дели",
            "svx": "Екатеринбург",
            "ovb": "Новосибирск",
            "nrt": "Токио",
            "fra": "Франкфурт",
            "ams": "Амстердам",
            "prg": "Прага",
            "vie": "Вена",
        }

        self.city_name_overrides = {
            "moscow": "Москва",
            "saint petersburg": "Санкт-Петербург",
            "st petersburg": "Санкт-Петербург",
            "kazan": "Казань",
            "ufa": "Уфа",
            "istanbul": "Стамбул",
            "yekaterinburg": "Екатеринбург",
            "novosibirsk": "Новосибирск",
            "tokyo": "Токио",
            "paris": "Париж",
            "london": "Лондон",
            "new york": "Нью-Йорк",
            "singapore": "Сингапур",
            "beijing": "Пекин",
            "delhi": "Дели",
            "prague": "Прага",
            "vienna": "Вена",
            "amsterdam": "Амстердам",
            "frankfurt": "Франкфурт",
        }

    def _looks_cyrillic(self, value: str) -> bool:
        return any(ord(ch) > 127 for ch in value)

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-zа-яё]+", " ", str(value).strip().lower()).strip()

    def _display_name(self, value: str) -> str:
        value = str(value).strip()
        if not value:
            return ""
        return value.title()

    def _to_cyrillic(self, value: str) -> str:
        value = str(value).strip()
        if not value:
            return ""

        if self._looks_cyrillic(value):
            return self._display_name(value)

        normalized = self._normalize(value)
        if normalized in self.city_name_overrides:
            return self._display_name(self.city_name_overrides[normalized])

        lowered = value.lower()
        if lowered in self.aliases:
            return self._display_name(self.aliases[lowered])

        if translit is not None:
            try:
                result = translit(value, "ru")
                if result and result != value:
                    return self._display_name(result)
            except Exception:
                pass

        return self._display_name(value)

    def _extract_names(self, entry):
        if isinstance(entry, dict):
            values = []
            for key in ("name", "city", "title", "english_name", "ru_name", "airport_name"):
                if key in entry:
                    values.append(str(entry[key]))
            if "codes" in entry:
                values.extend(str(x) for x in entry["codes"])
            if "aliases" in entry:
                values.extend(str(x) for x in entry["aliases"])
            return values

        if isinstance(entry, list):
            return [str(x) for x in entry if str(x)]

        return [str(entry)]

    def resolve(self, value: str) -> dict | None:
        if not value:
            return None

        raw = str(value).strip()
        normalized = self._normalize(raw)

        if isinstance(self.airports, dict):
            for code, entry in self.airports.items():
                code_str = str(code).strip().upper()

                if code_str == raw.upper():
                    names = self._extract_names(entry)
                    first_name = names[0] if names else code_str
                    return {
                        "city": self._to_cyrillic(first_name),
                        "code": code_str,
                    }

                for name in self._extract_names(entry):
                    if self._normalize(name) == normalized:
                        return {
                            "city": self._to_cyrillic(name),
                            "code": code_str,
                        }

        if raw.lower() in self.aliases:
            return {
                "city": self._display_name(self.aliases[raw.lower()]),
                "code": raw.upper(),
            }

        return None

    def format_city(self, airport: dict) -> str:
        return f"{airport['city']} ({airport['code']})"

    def get_city_name(self, value: str) -> str:
        if not value:
            return ""

        resolved = self.resolve(str(value))
        if resolved:
            return resolved["city"]

        return self._display_name(str(value).strip().upper())


resolver = CityResolver()