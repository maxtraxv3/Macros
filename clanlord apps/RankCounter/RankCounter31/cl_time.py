from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple, TypedDict, Optional, List, TypedDict
import time

# The game time multiplier is exactly 45.0 / 11.0 (time passes faster in-game)
IC_SPEED_MULTIPLIER = 45.0 / 11.0

# Base Puddleby Time epoch offset used internally by the client
IC_BASE_OFFSET = 24371635.0
IC_BASE_YEAR = 411  # The base calculation starts at the year 411

IC_SECONDS_PER_DAY = 86400
IC_SECONDS_PER_YEAR = 31104000  # 360 days * 86,400 seconds
IC_DAYS_PER_YEAR = 360
IC_DAYS_PER_SEASON = 90
IC_DAYS_PER_WEEK = 7
IC_MOON_CYCLE_DAYS = 28
IC_ZODIAC_SIGN_DAYS = 30
IC_ZODIAC_SIGNS_COUNT = 12

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
WEEKDAYS = ["Sombdi", "Gradi", "Tridi", "Quartidi", "Quintidi", "Sixdi", "Sevdi"]

ZODIAC_SIGNS = [
    "Ancients", "Centaur", "Fox", "Rat",
    "Rooster", "Runkee", "Shredder", "Cat",
    "Healer", "Mystic", "Orcipus the Pig", "Warrior",
]

class ZodiacData(TypedDict):
    name: str
    short_name: str
    gilded_sprite_id: int
    star_icon_id: int

ZODIAC_SIGNS_METADATA: list[ZodiacData] = [
    {
        "name": "Awjus & Hamusa the Shredders",
        "short_name": "Shredders",
        "gilded_sprite_id": 1908,
        "star_icon_id": 2378
    },
    {
        "name": "Ma'Taline the Mystic",
        "short_name": "Mystic",
        "gilded_sprite_id": 1911,
        "star_icon_id": 2379
    },
    {
        "name": "Josephus the Ancient",
        "short_name": "Josephus",
        "gilded_sprite_id": 1911,
        "star_icon_id": 2380
    },
    {
        "name": "Mump the Vermine",
        "short_name": "Mump",
        "gilded_sprite_id": 1909,
        "star_icon_id": 2381
    },
    {
        "name": "Elixus the Cat",
        "short_name": "Elixus",
        "gilded_sprite_id": 1910,
        "star_icon_id": 2382
    },
    {
        "name": "Sybill the Fox",
        "short_name": "Sybill",
        "gilded_sprite_id": 1912,
        "star_icon_id": 2383
    },
    {
        "name": "Eghorus the Rooster",
        "short_name": "Eghorus",
        "gilded_sprite_id": 1913,
        "star_icon_id": 2384
    },
    {
        "name": "Bgrr the Ogre",
        "short_name": "Bgrr",
        "gilded_sprite_id": 1914,
        "star_icon_id": 2385
    },
    {
        "name": "Boh the Pig",
        "short_name": "Boh",
        "gilded_sprite_id": 1915,
        "star_icon_id": 2386
    },
    {
        "name": "Detros the Ruknee",
        "short_name": "Detros",
        "gilded_sprite_id": 1916,
        "star_icon_id": 2387
    },
    {
        "name": "T’Karr the Monument",
        "short_name": "T’Karr",
        "gilded_sprite_id": 1917,
        "star_icon_id": 2388
    },
    {
        "name": "Nip the Dog",
        "short_name": "Nip",
        "gilded_sprite_id": 1918,
        "star_icon_id": 2389
    },
]

CELESTIAL_SKY_CATALOG = {
    "zodiacs": [
        {"name": "Awjus & Hamusa the Shredders", "sprite_id": 1908, "star_icon_id": 2378},
        {"name": "Ma'Taline the Mystic",      "sprite_id": 1911, "star_icon_id": 2379},
        {"name": "Josephus the Ancient",      "sprite_id": 1911, "star_icon_id": 2380},
        {"name": "Mump the Vermine",          "sprite_id": 1909, "star_icon_id": 2381},
        {"name": "Elixus the Cat",            "sprite_id": 1910, "star_icon_id": 2382},
        {"name": "Sybill the Fox",            "sprite_id": 1912, "star_icon_id": 2383},
        {"name": "Eghorus the Rooster",       "sprite_id": 1913, "star_icon_id": 2384},
        {"name": "Bgrr the Ogre",              "sprite_id": 1914, "star_icon_id": 2385},
        {"name": "Boh the Pig",               "sprite_id": 1915, "star_icon_id": 2386},
        {"name": "Detros the Ruknee",          "sprite_id": 1916, "star_icon_id": 2387},
        {"name": "T’Karr the Monument",        "sprite_id": 1917, "star_icon_id": 2388},
        {"name": "Nip the Dog",               "sprite_id": 1918, "star_icon_id": 2389},
    ],
    "extra_features": [
        {"name": "Fyr the Fish",     "sprite_id": 1919, "star_icon_id": 2390, "type": "Auxiliary Zodiac"},
        {"name": "D’moth the Egg",   "sprite_id": 1920, "star_icon_id": 2391, "type": "Auxiliary Zodiac"},
        {"name": "The Comet",        "sprite_id": None, "star_icon_id": 2392, "type": "Celestial Object"},
        {"name": "The Pole Star",    "sprite_id": None, "star_icon_id": 2393, "type": "Fixed Star"},
        {"name": "The Serpent",      "sprite_id": None, "star_icon_id": 2394, "type": "Sky Formation"},
    ]
}

class SkyFeatureData(TypedDict):
    name: str
    sprite_id: Optional[int]
    star_icon_id: int
    type: str


CELESTIAL_EXTRA_FEATURES: list[SkyFeatureData] = [
    {
        "name": "Fyr the Fish",
        "sprite_id": 1919,
        "star_icon_id": 2390,
        "type": "Auxiliary Zodiac",
    },
    {
        "name": "D'moth the Egg",
        "sprite_id": 1920,
        "star_icon_id": 2391,
        "type": "Auxiliary Zodiac",
    },
    {
        "name": "The Comet",
        "sprite_id": None,
        "star_icon_id": 2392,
        "type": "Celestial Object",
    },
    {
        "name": "The Pole Star",
        "sprite_id": None,
        "star_icon_id": 2393,
        "type": "Fixed Star",
    },
    {
        "name": "The Serpent",
        "sprite_id": None,
        "star_icon_id": 2394,
        "type": "Sky Formation",
    },
]

MOON_PHASE_NAMES = [
    "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
    "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
]

@dataclass
class CLTimeStruct:
    ic_seconds: int
    ic_day: int
    ic_hour: int
    ic_minute: int
    ic_second: int
    year: int
    day_of_year: int
    season_index: int
    season_day: int
    weekday_index: int
    lunar_day: int
    zodiac_day: int
    zodiac_index: int

    @property
    def season_name(self) -> str:
        return SEASONS[self.season_index]

    @property
    def weekday_name(self) -> str:
        return WEEKDAYS[self.weekday_index]

    @property
    def zodiac_info(self) -> ZodiacData:
        return ZODIAC_SIGNS_METADATA[self.zodiac_index]

    @property
    def zodiac_name(self) -> str:
        return self.zodiac_info["name"]

    @property
    def zodiac_sprite_filename(self) -> str:
        """Returns image filename for the Gilded Sprite, e.g. '1909.png'"""
        return f"{self.zodiac_info['gilded_sprite_id']}.png"

    @property
    def zodiac_stars_filename(self) -> str:
        """Returns image filename for the Constellation Icon, e.g. '2381.png'"""
        return f"{self.zodiac_info['star_icon_id']}.png"

    @property
    def is_night(self) -> bool:
        """True if the in-game hour is during nighttime (before 6 AM or after 6 PM)."""
        return self.ic_hour < 6 or self.ic_hour >= 18

    @property
    def visible_night_features(self) -> List[SkyFeatureData]:
        """Returns additional sky objects visible during night hours."""
        if not self.is_night:
            return []
        visible = [f for f in CELESTIAL_EXTRA_FEATURES if f["name"] == "The Pole Star"]
        return visible

    @property
    def moon_phase_name(self) -> str:
        idx = (self.lunar_day * len(MOON_PHASE_NAMES)) // IC_MOON_CYCLE_DAYS
        return MOON_PHASE_NAMES[idx]


def _to_unix(dt_or_unix) -> float:
    if isinstance(dt_or_unix, (int, float)):
        return float(dt_or_unix)
    if isinstance(dt_or_unix, datetime):
        return dt_or_unix.astimezone(timezone.utc).timestamp()
    raise TypeError("real_to_cl expects datetime or unix timestamp")


def real_to_cl(dt_or_unix) -> CLTimeStruct:
    unix_time = _to_unix(dt_or_unix)

    ic_seconds_total = unix_time * IC_SPEED_MULTIPLIER + IC_BASE_OFFSET

    year = int(ic_seconds_total / IC_SECONDS_PER_YEAR) + IC_BASE_YEAR

    seconds_in_year = ic_seconds_total - (year - IC_BASE_YEAR) * IC_SECONDS_PER_YEAR

    day_of_year = int(seconds_in_year / IC_SECONDS_PER_DAY)

    seconds_in_day = seconds_in_year - (day_of_year * IC_SECONDS_PER_DAY)

    ic_hour = int(seconds_in_day / 3600.0)
    seconds_in_hour = seconds_in_day - (ic_hour * 3600.0)
    ic_minute = int(seconds_in_hour / 60.0)
    ic_second = int(seconds_in_hour - (ic_minute * 60.0))

    weekday_index = int(ic_seconds_total / IC_SECONDS_PER_DAY) % 7

    if day_of_year == 0:
        day_of_year_out = 360
        season_day = 90
        year_out = year - 1
        season_index = 3
    else:
        day_of_year_out = day_of_year
        season_day = (day_of_year - 1) % IC_DAYS_PER_SEASON + 1
        season_index = (day_of_year - 1) // IC_DAYS_PER_SEASON
        year_out = year

    ic_day = int(ic_seconds_total / IC_SECONDS_PER_DAY)

    lunar_day = ic_day % IC_MOON_CYCLE_DAYS
    zodiac_day = ic_day % IC_ZODIAC_SIGN_DAYS
    zodiac_index = (ic_day // IC_ZODIAC_SIGN_DAYS) % IC_ZODIAC_SIGNS_COUNT

    return CLTimeStruct(
        ic_seconds=int(ic_seconds_total),
        ic_day=ic_day,
        ic_hour=ic_hour,
        ic_minute=ic_minute,
        ic_second=ic_second,
        year=year_out,
        day_of_year=day_of_year_out - 1,
        season_index=season_index,
        season_day=season_day - 1,
        weekday_index=weekday_index,
        lunar_day=lunar_day,
        zodiac_day=zodiac_day,
        zodiac_index=zodiac_index,
    )


def cl_to_real(ic_day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    ic_seconds_total = ic_day * IC_SECONDS_PER_DAY + hour * 3600 + minute * 60 + second
    real_seconds = (ic_seconds_total - IC_BASE_OFFSET) / IC_SPEED_MULTIPLIER
    return datetime.fromtimestamp(real_seconds, tz=timezone.utc)


def moon_phase_for_day(ic_day: int) -> Tuple[int, str]:
    lunar_day = ic_day % IC_MOON_CYCLE_DAYS
    idx = (lunar_day * len(MOON_PHASE_NAMES)) // IC_MOON_CYCLE_DAYS
    return lunar_day, MOON_PHASE_NAMES[idx]


def zodiac_for_day(ic_day: int) -> Tuple[str, int, int]:
    zodiac_day = ic_day % IC_ZODIAC_SIGN_DAYS
    zodiac_index = (ic_day // IC_ZODIAC_SIGN_DAYS) % IC_ZODIAC_SIGNS_COUNT
    sign = ZODIAC_SIGNS_METADATA[zodiac_index]["name"]
    days_until_next = IC_ZODIAC_SIGN_DAYS - zodiac_day
    return sign, zodiac_day, days_until_next


def dawn_dusk_for_day(ic_day: int) -> Tuple[datetime, datetime]:
    sunrise = cl_to_real(ic_day, 6, 0, 0)
    sunset = cl_to_real(ic_day, 18, 0, 0)
    return sunrise, sunset


def next_full_moon(ic_day: int, search_days: int = IC_DAYS_PER_YEAR * 3):
    for offset in range(search_days):
        test_day = ic_day + offset
        lunar_day, phase_name = moon_phase_for_day(test_day)
        if phase_name == "Full Moon":
            start = cl_to_real(test_day, 0, 0, 0)
            noon = cl_to_real(test_day, 12, 0, 0)
            end = cl_to_real(test_day, 23, 59, 40)
            return test_day, start, noon, end
    return None, None, None, None


def fmt_real(dt: datetime) -> str:
    return dt.astimezone().strftime("%a %b %d %H:%M:%S %Y")


def fmt_cl_header(cl: CLTimeStruct) -> str:
    hour_12 = ((cl.ic_hour + 11) % 12) + 1
    ampm = "AM" if cl.ic_hour < 12 else "PM"
    return (
        f"{cl.weekday_name} {hour_12}:{cl.ic_minute:02d}:{cl.ic_second:02d} {ampm}, "
        f"day {cl.season_day + 1} of {cl.season_name}, "
        f"day {cl.day_of_year + 1} of the year {cl.year}"
    )


def get_extra_feature_by_name(name: str) -> Optional[SkyFeatureData]:
    """Helper to fetch image IDs for auxiliary features (Fyr, D'moth, Comet, etc.)"""
    for feat in CELESTIAL_EXTRA_FEATURES:
        if feat["name"].lower() == name.lower():
            return feat
    return None


def cl_now() -> CLTimeStruct:
    return real_to_cl(datetime.now(timezone.utc))

if __name__ == "__main__":
    now_cl = cl_now()
    print("Current Puddleby Time:")
    print(fmt_cl_header(now_cl))
    print(f"Zodiac: {now_cl.zodiac_name}")
    print(f"Moon: {now_cl.moon_phase_name}")
