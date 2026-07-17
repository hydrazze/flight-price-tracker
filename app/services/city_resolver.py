import json
from pathlib import Path


class CityResolver:

    def __init__(self):
        path = Path("app/data/airports.json")

        with open(path, "r", encoding="utf-8") as file:
            self.airports = json.load(file)


    def resolve(self, value: str) -> str | None:

        value = value.strip()

        # 1. Сначала ищем город/алиас
        for code, names in self.airports.items():
            for name in names:
                if value.lower() == name.lower():
                    return code

        # 2. Потом проверяем код аэропорта
        value = value.upper()

        if value in self.airports:
            return value

        return None

resolver = CityResolver()