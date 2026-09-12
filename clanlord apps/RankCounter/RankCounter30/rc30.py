from __future__ import annotations
import os
import sys
import traceback
import codecs
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import concurrent.futures
import re
import threading
import json
import time
import csv
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Tuple

# ----------------------------------------------------------------------
# ---------------------- GLOBAL DATA / CONSTANTS -----------------------
# ----------------------------------------------------------------------

# Stage helpers (module scope)
STAGE_PHRASES = ["movements", "ways", "essence"]

def _build_stage_index():
    idx = {}
    for phrase in STAGE_PHRASES:
        if "movements" in phrase:
            idx[phrase] = 0
        elif "ways" in phrase:
            idx[phrase] = 1
        elif "essence" in phrase:
            idx[phrase] = 2
        else:
            idx[phrase] = 0
    return idx

_STAGE_INDEX = _build_stage_index()

def _get_stage_index_for_template(template_text: str) -> int:
    t = template_text.lower()
    if "movements" in t:
        return 0
    if "ways" in t:
        return 1
    if "essence" in t:
        return 2
    for phrase, i in _STAGE_INDEX.items():
        if phrase in t:
            return i
    return 0

kills_to_next = {
    "almost nothing": {1:2, 2:2, 3:2, 4:2, 5:4},
    "a few": {1:3, 2:3, 3:3, 4:3, 5:3},
    "more than a few": {1:8, 2:7, 3:7, 4:7, 5:7},
    "some things": {1:9, 2:12, 3:12, 4:12, 5:12, 6:12, 7:12},
    "many things": {1:16, 2:20, 3:20, 4:20, 5:20, 6:20, 7:20},
    "much to learn": {1:20, 2:30, 3:30, 4:30, 5:30, 6:30, 7:30},
    "a lot to learn": {1:30, 2:30, 3:30, 4:30, 5:100},
    "a vast amount": {1:100, 2:100, 3:100, 4:100, 5:100, 6:100},
}

kills_table = [
    (1,  "almost nothing", 2),
    (2,  "almost nothing", 2),
    (3,  "almost nothing", 2),
    (4,  "almost nothing", 2),
    (5,  "almost nothing", 4),

    (6,  "a few", 3),
    (7,  "a few", 3),
    (8,  "a few", 3),
    (9,  "a few", 3),
    (10, "a few", 3),

    (11, "more than a few", 8),
    (12, "more than a few", 7),
    (13, "more than a few", 7),
    (14, "more than a few", 7),
    (15, "more than a few", 7),

    (16, "some things", 9),
    (17, "some things", 12),
    (18, "some things", 12),
    (19, "some things", 12),
    (20, "some things", 12),
    (21, "some things", 12),
    (23, "some things", 12),

    (24, "many things", 16),
    (25, "many things", 20),
    (26, "many things", 20),
    (27, "many things", 20),
    (28, "many things", 20),
    (29, "many things", 20),
    (30, "many things", 20),

    (31, "much to learn", 20),
    (32, "much to learn", 30),
    (33, "much to learn", 30),
    (34, "much to learn", 30),
    (35, "much to learn", 30),
    (36, "much to learn", 30),
    (37, "much to learn", 30),

    (38, "a lot to learn", 30),
    (39, "a lot to learn", 30),
    (40, "a lot to learn", 30),
    (41, "a lot to learn", 30),
    (42, "a lot to learn", 100),

    (43, "a vast amount", 100),
    (44, "a vast amount", 100),
    (45, "a vast amount", 100),
    (46, "a vast amount", 100),
    (47, "a vast amount", 100),
    (48, "a vast amount", 100),
]

CHAR_FILE = "characters.json"
character_ranks = {}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# -- Exception Logging --------------------------------------------------------

def exception_hook(exctype, value, tb):
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write("Unhandled exception:\n")
        traceback.print_exception(exctype, value, tb, file=f)
        f.write("\n")
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exception_hook

# -- Smart File Reader --------------------------------------------------------

def smart_read_file(path, encodings=('utf-8', 'mac_roman')):
    last_exc = None
    for enc in encodings:
        try:
            with codecs.open(path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError as e:
            last_exc = e
    raise last_exc

# -- Paths & Globals ---------------------------------------------------------

words_file_path       = resource_path('rankmessages.txt')
replacement_file_path = resource_path('trainers.txt')
special_file_path     = resource_path('specialphrases.txt')


merged_counts      = {}
merged_creatures   = {}
character_folders  = {}
character_ranks    = {}     # Stores rank data
character_creatures= {}     # Stores creature data
character_ignored  = {}     # Stores ignored creatures
current_folder_name= None
executor           = concurrent.futures.ThreadPoolExecutor(max_workers=4)

moon_icons = {
    "New Moon": "img/nm.gif",
    "Full Moon": "img/fm.gif",
    "Last Quarter": "img/lq.gif",
    "First Quarter": "img/fq.gif",
}
# -- Coins counter -----------------------------------------------------------

merged_skinned = 0
merged_share = 0
merged_coin_events = []

def save_characters():
    data = {}
    for name in character_folders:
        data[name] = {
            "folders": character_folders.get(name, []),
            "ranks": character_ranks.get(name, {}),
            "creatures": character_creatures.get(name, {}),
            "ignored": character_ignored.get(name, []),
            "kills_table": kills_to_next,
            "last_scan_time": time.time(),
        }
    with open(CHAR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_characters():
    if not os.path.exists(CHAR_FILE):
        return
    try:
        with open(CHAR_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for name, info in data.items():
            character_folders[name] = info.get("folders", [])
            character_ranks[name] = info.get("ranks", {})
            character_creatures[name] = info.get("creatures", {})
            character_ignored[name] = info.get("ignored", [])
    except Exception as e:
        print(f"Error loading JSON: {e}")

# -- Shared Exclusion Helper -------------------------------------------------

def is_excluded(line: str) -> bool:
    """Return True if the line should be skipped."""
    low = line.lower().strip()
    excluded = ["says,", "growls,", "yells,", "ponders,", "thinks,"]
    if any(exc in low for exc in excluded):
        return True
    if low.startswith("(") and low.endswith(")"):
        return True
    if "):" in low:
        return True
    return False

def search_word_in_file(file_path, word):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return word in f.read()
    except:
        return False

def scan_directory(directory, word):
    found_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.txt'):
                full_path = os.path.join(root, filename)
                if search_word_in_file(full_path, word):
                    found_files.append(full_path)
    return found_files

def open_file_with_default_app(file_path):
    try:
        if sys.platform.startswith('win'):
            os.startfile(file_path)
        elif sys.platform.startswith('darwin'):
            from subprocess import Popen
            Popen(['open', file_path])
        else:
            from subprocess import Popen
            Popen(['xdg-open', file_path])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open file: {e}")

def get_min_time_from_filter(filter_value):
    now = time.time()
    mapping = {
        "Last 5 minutes": 5 * 60,
        "Last 10 minutes": 10 * 60,
        "Last 30 minutes": 30 * 60,
        "Last 1 hour": 60 * 60,
        "Last 3 hours": 3 * 60 * 60,
        "Last 6 hours": 6 * 60 * 60,
        "Last 12 hours": 12 * 60 * 60,
        "Last 24 hours": 24 * 60 * 60
    }
    if filter_value in mapping:
        return now - mapping[filter_value]
    return None  # "All logs" or unknown

# -- File / Folder Readers ---------------------------------------------------

def read_words_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    lines = [line.strip() for line in smart_read_file(file_path).splitlines()]
    return [l for l in lines if l]

def read_text_files(folder_path):
    texts = []
    files = sorted(
        os.listdir(folder_path),
        key=lambda f: os.path.getmtime(os.path.join(folder_path, f))
    )

    for fname in files:
        fpath = os.path.join(folder_path, fname)
        if not os.path.isfile(fpath):
            continue

        try:
            content = smart_read_file(fpath)
            file_time = os.path.getmtime(fpath)
            texts.append((content, file_time))
        except UnicodeDecodeError:
            continue

    return texts

def count_word_occurrences(texts, words):
    counts = {w: 0 for w in words}
    for content, _ in texts:
        for line in content.splitlines():
            if is_excluded(line):
                continue
            for w in words:
                counts[w] += line.count(w)
    return counts

# -----------------------------
# Clan Lord Time Engine (Updated)
# -----------------------------
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

# The game time multiplier is exactly 45.0 / 11.0 (time passes faster in-game)[cite: 1]
IC_SPEED_MULTIPLIER = 45.0 / 11.0

# Base Puddleby Time epoch offset used internally by the client[cite: 1]
IC_BASE_OFFSET = 24371635.0
IC_BASE_YEAR = 411  # The base calculation starts at the year 411[cite: 1]

IC_SECONDS_PER_DAY = 86400
IC_SECONDS_PER_YEAR = 31104000  # 360 days * 86,400 seconds[cite: 1]
IC_DAYS_PER_YEAR = 360
IC_DAYS_PER_SEASON = 90
IC_DAYS_PER_WEEK = 7
IC_MOON_CYCLE_DAYS = 28
IC_ZODIAC_SIGN_DAYS = 30
IC_ZODIAC_SIGNS_COUNT = 12

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
WEEKDAYS = ["Sombdi", "Gradi", "Tridi", "Quartidi", "Quintidi", "Sixdi", "Sevdi"]

# Replaced the A-L placeholders with known Clan Lord zodiac entities.
# Note: The exact calendar order needs to be arranged based on in-game observation.
ZODIAC_SIGNS = [
    "Ancients", "Centaur", "Fox", "Rat",
    "Rooster", "Runkee", "Shredder", "Cat",
    "Healer", "Mystic", "Orcipus the Pig", "Warrior",
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
    def zodiac_name(self) -> str:
        return ZODIAC_SIGNS[self.zodiac_index]

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

    # Accurate Puddleby time conversion[cite: 1]
    ic_seconds_total = unix_time * IC_SPEED_MULTIPLIER + IC_BASE_OFFSET

    # Year calculation starting from base year 411[cite: 1]
    year = int(ic_seconds_total / IC_SECONDS_PER_YEAR) + IC_BASE_YEAR

    # Remaining seconds in the current year[cite: 1]
    seconds_in_year = ic_seconds_total - (year - IC_BASE_YEAR) * IC_SECONDS_PER_YEAR

    # Day of the year (0-indexed internally initially)[cite: 1]
    day_of_year = int(seconds_in_year / IC_SECONDS_PER_DAY)

    # Remaining seconds in the day[cite: 1]
    seconds_in_day = seconds_in_year - (day_of_year * IC_SECONDS_PER_DAY)

    ic_hour = int(seconds_in_day / 3600.0)
    seconds_in_hour = seconds_in_day - (ic_hour * 3600.0)
    ic_minute = int(seconds_in_hour / 60.0)
    ic_second = int(seconds_in_hour - (ic_minute * 60.0))

    # Weekday calculation[cite: 1]
    weekday_index = int(ic_seconds_total / IC_SECONDS_PER_DAY) % 7

    # If day_of_year is 0, it wraps around to the last day of the previous year[cite: 1]
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

    # Total IC days passed (useful for zodiac/moon phases)
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
        day_of_year=day_of_year_out - 1, # 0-indexed for external formatting parity
        season_index=season_index,
        season_day=season_day - 1,       # 0-indexed for external formatting parity
        weekday_index=weekday_index,
        lunar_day=lunar_day,
        zodiac_day=zodiac_day,
        zodiac_index=zodiac_index,
    )


def cl_to_real(ic_day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    ic_seconds_total = ic_day * IC_SECONDS_PER_DAY + hour * 3600 + minute * 60 + second
    # Reverse the exact logic
    real_seconds = (ic_seconds_total - IC_BASE_OFFSET) / IC_SPEED_MULTIPLIER
    return datetime.fromtimestamp(real_seconds, tz=timezone.utc)


def moon_phase_for_day(ic_day: int) -> Tuple[int, str]:
    lunar_day = ic_day % IC_MOON_CYCLE_DAYS
    idx = (lunar_day * len(MOON_PHASE_NAMES)) // IC_MOON_CYCLE_DAYS
    return lunar_day, MOON_PHASE_NAMES[idx]


def zodiac_for_day(ic_day: int) -> Tuple[str, int, int]:
    zodiac_day = ic_day % IC_ZODIAC_SIGN_DAYS
    zodiac_index = (ic_day // IC_ZODIAC_SIGN_DAYS) % IC_ZODIAC_SIGNS_COUNT
    sign = ZODIAC_SIGNS[zodiac_index]
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


def cl_now() -> CLTimeStruct:
    return real_to_cl(datetime.now(timezone.utc))

# Example usage check for testing:
if __name__ == "__main__":
    now_cl = cl_now()
    print("Current Puddleby Time:")
    print(fmt_cl_header(now_cl))
    print(f"Zodiac: {now_cl.zodiac_name}")
    print(f"Moon: {now_cl.moon_phase_name}")
# ----------------------------------------------------------------------
# ---------------------- CORE PARSING / COUNTS ------------------------
# ----------------------------------------------------------------------


def count_special_lines(texts):
    """
    Extracts all study-related lines and returns:
        special_occ: { "creature|function": entry, ... }
        exclude: set()

    Each entry contains:
        phrase_group, function, creature, msg_num, timestamp,
        kills_since_start, count, display_label

    Kill counting: only kills since study started (first study message).
    Abandon: movements abandon forgets all 3 functions;
             ways/essence abandon forgets that function only.
    """
    import re
    from datetime import datetime

    special_occ = {}
    exclude = set()

    ts_re = re.compile(r"^(\d+/\d+/\d+ \d+:\d+:\d+[ap])\s*[•>:-]*\s*(.*)$")
    study_re = re.compile(
        r"You have (almost nothing(?:\s+left)?|a few(?:\s+things)?|more than a few(?:\s+things)?|some things|many things|much to learn|a lot to learn|a vast amount)"
        r"(?:\s+to learn)?\s+about the (movements|ways|essence) of the (.+?)\.",
        re.IGNORECASE
    )
    # Map captured phrase text -> canonical phrase_group key in kills_table
    _phrase_norm = {
        "almost nothing left": "almost nothing",
        "a few things": "a few",
        "more than a few things": "more than a few",
    }
    kill_re = re.compile(
        r"(?:you|you helped)\s+(?:slaughter|dispatch|kill|vanquish)(?:ed|s|ing)?\s+(?:a|an|the)\s+(.+?)\.",
        re.IGNORECASE
    )
    abandon_re = re.compile(r"you abandon your study of the (.+?)\.", re.IGNORECASE)
    complete_re = re.compile(
        r"You learn to (fight the) (.+?) more effectively\.|"
        r"You learn to (befriend the|assume the form of the) (.+?)\.",
        re.IGNORECASE
    )
    complete_fn_map = {
        "fight the": "movements",
        "befriend the": "ways",
        "assume the form of the": "essence",
    }

    # Build lookup: (phrase_group, function) -> msg_num
    phrase_fn_to_msg = {}
    for msg_num, phrase_group, _ktn in kills_table:
        for fn in ("movements", "ways", "essence"):
            key = (phrase_group, fn)
            if key not in phrase_fn_to_msg or msg_num < phrase_fn_to_msg[key]:
                phrase_fn_to_msg[key] = msg_num

    # Collect all events chronologically
    all_events = []
    for content, _ in texts:
        for raw_line in content.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            m = ts_re.match(raw_line)
            if not m:
                continue
            ts_raw, msg = m.groups()
            try:
                # CL logs use single-letter a/p, strptime %p expects AM/PM
                normalized = ts_raw[:-1] + ("AM" if ts_raw[-1].lower() == "a" else "PM")
                timestamp = datetime.strptime(normalized, "%m/%d/%y %I:%M:%S%p")
            except Exception:
                timestamp = None
            low = msg.lower()

            m_ab = abandon_re.search(low)
            if m_ab:
                all_events.append(("abandon", timestamp, m_ab.group(1).strip().lower(), None))
                continue

            m_comp = complete_re.search(msg)
            if m_comp:
                fn_key = (m_comp.group(1) or m_comp.group(3) or "").lower()
                creature_name = (m_comp.group(2) or m_comp.group(4) or "").strip().lower()
                function = complete_fn_map.get(fn_key)
                if function and creature_name:
                    all_events.append(("complete", timestamp, creature_name, function))
                continue

            m_kill = kill_re.search(low)
            if m_kill:
                all_events.append(("kill", timestamp, m_kill.group(1).strip().lower(), None))
                continue

            m_study = study_re.search(msg)
            if m_study:
                phrase_raw = m_study.group(1).lower()
                phrase_group = _phrase_norm.get(phrase_raw, phrase_raw)
                all_events.append(("study", timestamp,
                    m_study.group(3).strip().lower(),
                    (phrase_group, m_study.group(2).lower())))
                continue

    all_events.sort(key=lambda e: e[1] or datetime.min)

    # Process chronologically
    study_starts = {}
    study_abandon = {}
    study_last_fn = {}
    study_active = {}
    kill_counts = {}

    for etype, ts, creature, data in all_events:
        if etype == "study":
            phrase_group, function = data
            key = (creature, function)
            if key not in study_starts:
                study_starts[key] = ts
                study_active[key] = True
            study_last_fn[creature] = function
            if ts:
                kill_counts.setdefault(creature, [])
                kill_counts[creature].append(("study", ts, function))

        elif etype == "abandon":
            last_fn = study_last_fn.get(creature)
            if last_fn == "movements":
                for fn in ("movements", "ways", "essence"):
                    key = (creature, fn)
                    if key in study_active and study_active[key]:
                        study_abandon[key] = ts
                        study_active[key] = False
            elif last_fn in ("ways", "essence"):
                key = (creature, last_fn)
                if key in study_active and study_active[key]:
                    study_abandon[key] = ts
                    study_active[key] = False
            kill_counts.setdefault(creature, [])
            kill_counts[creature].append(("abandon", ts, last_fn))

        elif etype == "kill":
            kill_counts.setdefault(creature, [])
            kill_counts[creature].append(("kill", ts, None))

        elif etype == "complete":
            function = data
            key = (creature, function)
            if key in study_active and study_active[key]:
                study_active[key] = False
            kill_counts.setdefault(creature, [])
            kill_counts[creature].append(("complete", ts, function))

    # Build results
    for (creature, function), start_ts in study_starts.items():
        is_active = study_active.get((creature, function), False)
        if not is_active:
            continue

        abandon_ts = study_abandon.get((creature, function))

        kills_since = 0
        events = kill_counts.get(creature, [])
        for ev_type, ev_ts, ev_fn in events:
            if ev_ts is None or ev_ts < start_ts:
                continue
            if abandon_ts and ev_ts > abandon_ts:
                continue
            if ev_type == "kill":
                kills_since += 1

        # Find the LATEST study message for this creature+function (most recent progress)
        phrase_group = None
        msg_num = None
        for e_type, e_ts, e_creature, e_data in all_events:
            if e_type == "study" and e_creature == creature and e_data and e_data[1] == function:
                phrase_group = e_data[0]
                msg_num = phrase_fn_to_msg.get(e_data)

        if phrase_group is None:
            continue

        entry_key = f"{creature}|{function}"
        display_label = f"You have {phrase_group} to learn about the {function} of the {creature}."
        display_label += f" \u2014 {kills_since} kills counted"

        special_occ[entry_key] = {
            "phrase_group": phrase_group,
            "function": function,
            "creature": creature,
            "msg_num": msg_num,
            "timestamp": start_ts,
            "kills_since_start": kills_since,
            "count": 1,
            "display_label": display_label,
            "active": is_active,
        }

    return special_occ, exclude

# -- Coin Scanning -----------------------------------------------------------

def count_coins(texts, character_name, min_time=None):
    skinned_total = 0
    share_total = 0
    events = []

    coin_rx = re.compile(
        r"\*\s*(You|.+?) recover[s]? the (.+?) (?:fur|blood|mandibles), worth (\d+)c\. Your share is (\d+)c",
        re.IGNORECASE
    )

    for content, file_time in texts:
        if min_time and file_time < min_time:
            continue

        for line in content.splitlines():
            m = coin_rx.search(line)
            if not m:
                continue

            groups = m.groups()
            if len(groups) != 4:
                continue
            player, monster, worth, share = groups
            did_skin = (player == "You" or player == character_name)

            worth = int(worth)
            share = int(share)

            if did_skin:
                skinned_total += worth
            share_total += share

            events.append({
                "monster": monster,
                "worth": worth,
                "share": share,
                "skinned": did_skin,
                "file_time": file_time
            })

    return skinned_total, share_total, events

# -- Background Task ---------------------------------------------------------

def scan_and_aggregate(folder_path, character_name):
    import re

    # --------------------------------------------------------------
    # Load mapping for normal ranks
    # --------------------------------------------------------------
    words        = read_words_from_file(words_file_path)
    replacements = read_words_from_file(replacement_file_path)

    if len(words) != len(replacements):
        raise ValueError(
            f"File Alignment Error: rankmessages.txt ({len(words)} lines) and "
            f"trainers.txt ({len(replacements)} lines) must match exactly."
        )

    mapping = dict(zip(words, replacements))

    # --------------------------------------------------------------
    # Load text logs
    # --------------------------------------------------------------
    texts = read_text_files(folder_path)
    word_occ = count_word_occurrences(texts, words)

    # NEW: extract study messages
    special_occ, exclude = count_special_lines(texts)

    # --------------------------------------------------------------
    # Coin counting
    # --------------------------------------------------------------
    filter_value = time_filter_var.get()
    min_time = get_min_time_from_filter(filter_value)
    skinned, share, coin_events = count_coins(texts, character_name, min_time)

    # --------------------------------------------------------------
    # NORMAL RANKS
    # --------------------------------------------------------------
    normal_ranks = {}
    for w, c in word_occ.items():
        if c:
            t = mapping.get(w, "Unknown")
            if isinstance(t, str):
                normal_ranks[t] = normal_ranks.get(t, 0) + c

    # --------------------------------------------------------------
    # SPECIAL CREATURE PROCESSING
    # New format: special_occ has keys "creature|function" with single entries
    # Show ALL active studies per creature (not just highest stage)
    # --------------------------------------------------------------
    STAGE_ORDER = {"movements": 0, "ways": 1, "essence": 2}

    # Group by creature
    creature_entries = {}
    for key, e in special_occ.items():
        creature = e["creature"]
        creature_entries.setdefault(creature, []).append(e)

    # --------------------------------------------------------------
    # Convert to UI format — one row per active study
    # --------------------------------------------------------------
    special_creatures = {}

    for creature, entries in creature_entries.items():
        for e in entries:
            lbl = e["display_label"]
            msg_num = e["msg_num"]
            ks = e.get("kills_since_start", 0)
            fn = e["function"]
            active = e.get("active", False)

            if not active:
                continue

            special_creatures[lbl] = (msg_num, str(ks))

    return normal_ranks, special_creatures, skinned, share, coin_events, os.path.basename(folder_path)

# -- Helpers for merging / parsing counts ------------------------------------

def parse_creature_count(count_str):
    """Helper to split '5 (1)' into base=5, bonus=1"""
    import re
    clean = str(count_str).strip()
    match = re.match(r'(\d+)(?:\s*\((\d+)\))?', clean)
    if match:
        base = int(match.group(1))
        bonus = int(match.group(2)) if match.group(2) else 0
        return base, bonus
    return 0, 0

def summarize_coin_events(events):
    summary = {}
    for ev in events:
        monster = ev["monster"]
        if monster not in summary:
            summary[monster] = {
                "total_worth": 0,
                "total_share": 0,
                "your_skins": 0
            }
        summary[monster]["total_worth"] += ev["worth"]
        summary[monster]["total_share"] += ev["share"]
        if ev["skinned"]:
            summary[monster]["your_skins"] += 1
    return summary



# ----------------------------------------------------------------------
# ------------------------- GUI / CALLBACKS ----------------------------
# ----------------------------------------------------------------------

def on_scan_done(fut):
    try:
        normal_ranks, special_creatures_data, skinned, share, coin_events, new_folder = fut.result()
    except Exception as e:
        import traceback
        print("FUTURE EXCEPTION (on_scan_done):", repr(e))
        traceback.print_exc()
        # Also try to print the future's exception object if available
        try:
            exc = fut.exception()
            if exc is not None:
                print("fut.exception():", repr(exc))
        except Exception:
            pass
        # Show the same messagebox so UI behavior is unchanged
        messagebox.showerror("Scan Error", str(e))
        return

    global merged_counts, merged_creatures, merged_skinned, merged_share, merged_coin_events

    # Merge coin totals with diagnostics
    try:
        if not isinstance(skinned, int):
            print("DIAG: skinned is not int:", repr(skinned)[:200], type(skinned))
        if not isinstance(merged_skinned, int):
            print("DIAG: merged_skinned is not int before add:", repr(merged_skinned)[:200], type(merged_skinned))
        merged_skinned += skinned
    except Exception:
        print("FATAL: exception merging skinned")
        _tb.print_exc()
        raise

    try:
        if not isinstance(share, int):
            print("DIAG: share is not int:", repr(share)[:200], type(share))
        if not isinstance(merged_share, int):
            print("DIAG: merged_share is not int before add:", repr(merged_share)[:200], type(merged_share))
        merged_share += share
    except Exception:
        print("FATAL: exception merging share")
        _tb.print_exc()
        raise

    # Merge detailed coin events
    merged_coin_events.extend(coin_events)

    # Merge normal ranks (defensive: log types and stack trace on unexpected types)
    import traceback as _tb
    for name, count in normal_ranks.items():
        try:
            # Print types before attempting arithmetic
            cur_val = merged_counts.get(name, 0)
            if not isinstance(cur_val, int) or not isinstance(count, int):
                print("DIAGNOSTIC: about to add values for:", repr(name))
                print("  merged_counts.get(name):", repr(cur_val), "type:", type(cur_val))
                print("  normal_ranks[name]:", repr(count), "type:", type(count))
                _tb.print_stack(limit=8)

            # Try to coerce numeric-like strings
            if not isinstance(count, int):
                try:
                    count = int(count)
                    print("DIAGNOSTIC: coerced count to int for", repr(name), "->", count)
                except Exception:
                    print("DIAGNOSTIC: cannot coerce count to int, skipping:", repr(name), repr(count), type(count))
                    continue

            if not isinstance(cur_val, int):
                print("DIAGNOSTIC: merged_counts has non-int for", repr(name), "resetting to 0 (was type: {})".format(type(cur_val)))
                _tb.print_stack(limit=8)
                cur_val = 0

            merged_counts[name] = cur_val + count

        except Exception as ex:
            print("FATAL: exception while merging normal_ranks for", repr(name))
            print("  count:", repr(count), "type:", type(count))
            print("  merged_counts.get(name):", repr(merged_counts.get(name)), "type:", type(merged_counts.get(name)))
            _tb.print_exc()
            raise

    # Merge special creatures (no arithmetic on dicts)
    for name, count_kills in special_creatures_data.items():
        # count_kills may be:
        #   - tuple: (count, kills_str)
        #   - dict:  {"count": ..., "kills": ...}
        #   - legacy: plain string/int
        if isinstance(count_kills, tuple):
            count_val, kills_str = count_kills
        elif isinstance(count_kills, dict):
            count_val = count_kills.get("count", 0)
            kills_str = count_kills.get("kills", "")
        else:
            count_val = count_kills
            kills_str = ""

        merged_creatures[name] = {
            "count": str(count_val),
            "kills": str(kills_str),
        }


    # Save to character
    char_name = get_selected_character()
    if char_name:
        character_ranks[char_name] = merged_counts
        character_creatures[char_name] = merged_creatures
        save_characters()

    # Update ranks table
    for item in table.get_children():
        table.delete(item)
    for name, cnt in merged_counts.items():
        table.insert("", "end", values=(name, cnt))

    # Update creatures table
    for item in creature_table.get_children():
        creature_table.delete(item)

    ignored_list = character_ignored.get(char_name, [])

    for name, data in merged_creatures.items():
        if name in ignored_list:
            continue

        if isinstance(data, dict):
            count_val = data.get("count", "")
            kills_val = data.get("kills", "")
        else:
            count_val = str(data)
            kills_val = ""

        creature_table.insert("", "end", values=(name, count_val, kills_val))

    # Update coins table
    for item in coins_table.get_children():
        coins_table.delete(item)

    # Diagnostic before computing total coins
    try:
        print("DIAG: before total coins: merged_skinned type/value:", type(merged_skinned), repr(merged_skinned)[:200])
        print("DIAG: before total coins: merged_share type/value:", type(merged_share), repr(merged_share)[:200])
        total_coins = merged_skinned + merged_share
        print("DIAG: computed total_coins:", total_coins, type(total_coins))
    except Exception:
        print("FATAL: exception computing total_coins")
        _tb.print_exc()
        raise

    coins_table.insert("", "end", values=("Total Skinned", merged_skinned))
    coins_table.insert("", "end", values=("Total Share", merged_share))
    coins_table.insert("", "end", values=("Total Coins", merged_skinned + merged_share))
    coins_table.insert("", "end", values=("", ""))  # spacer
    coins_table.insert("", "end", values=("Monster", "Details"))

    summary = summarize_coin_events(merged_coin_events)
    for monster, data in summary.items():
        label = monster
        details = f"Total {data['total_worth']}c, share {data['total_share']}c, you skinned {data['your_skins']}"
        coins_table.insert("", "end", values=(label, details))


def load_files_and_count_words():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return

    # Character has no folders at all
    if name not in character_folders or not character_folders[name]:
        messagebox.showerror("Error", "This character has no folders assigned.")
        return

    # --- NEW: Normalize and validate folders safely ---
    valid_folders = []
    invalid_folders = []

    for folder in character_folders[name]:
        # Normalize path (handles spaces, slashes, unicode, symlinks)
        norm = os.path.normpath(os.path.expanduser(folder.strip()))

        # If the normalized path exists, accept it
        if os.path.isdir(norm):
            valid_folders.append(norm)
            continue

        # If the original path exists exactly as stored, accept it
        if os.path.isdir(folder):
            valid_folders.append(folder)
            continue

        # Otherwise mark as invalid
        invalid_folders.append(folder)

    if invalid_folders:
        messagebox.showerror(
            "Invalid Folder",
            "These folders could not be accessed:\n\n" +
            "\n".join(invalid_folders) +
            "\n\nCheck spelling, case, or mount point."
        )
        return

    character_folders[name] = valid_folders

    global merged_counts, merged_creatures, merged_skinned, merged_share, merged_coin_events
    merged_counts.clear()
    merged_creatures.clear()
    merged_skinned = 0
    merged_share = 0
    merged_coin_events = []

    for folder in character_folders[name]:
        if not os.path.isdir(folder):
            continue

        fut = executor.submit(scan_and_aggregate, folder, name)
        fut.add_done_callback(lambda f: root.after(0, on_scan_done, f))


def rescan_all_logs():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return
    load_files_and_count_words()


def save_output():
    if not merged_counts:
        messagebox.showinfo("Info", "There is no data to save.")
        return

    path = filedialog.asksaveasfilename(
        title="Save Merged Results",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"),
                   ("Text files", "*.txt"),
                   ("All files", "*.*")]
    )
    if not path:
        return

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("Trainer,Ranks\n")
            for n, c in merged_counts.items():
                f.write(f"{n},{c}\n")
        messagebox.showinfo("Success", f"Saved to {path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save:\n{e}")


def ignore_selected_creature():
    selected_item = creature_table.selection()
    if not selected_item:
        return

    creature_name = creature_table.item(selected_item)['values'][0]
    char_name = get_selected_character()

    if not char_name:
        return

    if char_name not in character_ignored:
        character_ignored[char_name] = []

    if creature_name not in character_ignored[char_name]:
        character_ignored[char_name].append(creature_name)
        save_characters()
        creature_table.delete(selected_item)
        print(f"Ignored: {creature_name}")


def on_character_selected_simple():
    """Refresh tables from saved character data (used after ignore restore)."""
    name = get_selected_character()
    if not name:
        return

    # Ranks
    for item in table.get_children():
        table.delete(item)
    for n, c in character_ranks.get(name, {}).items():
        table.insert("", "end", values=(n, c))

    # Creatures
    for item in creature_table.get_children():
        creature_table.delete(item)
    ignored = character_ignored.get(name, [])
    for n, data in character_creatures.get(name, {}).items():
        if n in ignored:
            continue
        if isinstance(data, dict):
            count_val = data.get("count", "")
            kills_val = data.get("kills", "")
        else:
            count_val = str(data)
            kills_val = ""
        creature_table.insert("", "end", values=(n, count_val, kills_val))


def open_ignore_manager():
    char_name = get_selected_character()
    if not char_name:
        messagebox.showerror("Error", "Select a character first.")
        return

    win = tk.Toplevel(root)
    win.title(f"Ignored Creatures for {char_name}")
    win.geometry("400x300")

    lbl = tk.Label(win, text="Select Creatures to restore:")
    lbl.pack(pady=5)

    lb = tk.Listbox(win, selectmode=tk.MULTIPLE)
    lb.pack(fill="both", expand=True, padx=10, pady=5)

    ignored = character_ignored.get(char_name, [])
    for item in ignored:
        lb.insert(tk.END, item)

    def restore_selected():
        selections = lb.curselection()
        if not selections:
            return

        to_restore = [lb.get(i) for i in selections]

        for item in to_restore:
            if item in character_ignored[char_name]:
                character_ignored[char_name].remove(item)

        save_characters()
        win.destroy()
        on_character_selected_simple()

    btn_restore_selected = ttk.Button(
        win,
        text="Restore Selected",
        command=restore_selected
    )
    btn_restore_selected.pack(pady=10)

def open_kills_to_next_table():
    """Display the full kills-to-next table (48 messages) in a spreadsheet-like window."""
    win = tk.Toplevel()
    win.title("Kills‑to‑Next Message Table")
    win.geometry("1000x650")

    frame = ttk.Frame(win)
    frame.pack(fill="both", expand=True)

    # Scrollbars
    yscroll = ttk.Scrollbar(frame, orient="vertical")
    xscroll = ttk.Scrollbar(frame, orient="horizontal")

    cols = ("msg_num", "message", "kills_to_next", "kills_left")
    tree = ttk.Treeview(
        frame,
        columns=cols,
        show="headings",
        yscrollcommand=yscroll.set,
        xscrollcommand=xscroll.set,
    )

    tree.heading("msg_num", text="Message #")
    tree.heading("message", text="Message")
    tree.heading("kills_to_next", text="Kills to Next")
    tree.heading("kills_left", text="Kills Left")

    tree.column("msg_num", width=80, anchor="center")
    tree.column("message", width=600, anchor="w")
    tree.column("kills_to_next", width=120, anchor="center")
    tree.column("kills_left", width=120, anchor="center")

    yscroll.config(command=tree.yview)
    xscroll.config(command=tree.xview)

    tree.grid(row=0, column=0, sticky="nsew")
    yscroll.grid(row=0, column=1, sticky="ns")
    xscroll.grid(row=1, column=0, sticky="ew")

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Compute cumulative kills_left for each message
    # (kills_left = total kills from this msg through message 48)
    # ------------------------------------------------------------------
    total_all = sum(ktn for _, _, ktn in kills_table)

    running = 0
    for msg_num, stage, ktn in kills_table:
        msg = f"You have {stage} to learn about the <function> of the <creature>."
        kills_left = total_all - running
        tree.insert("", "end", values=(msg_num, msg, ktn, kills_left))
        running += ktn

    return win

class CLTime:
    def __init__(self, parent):
        self.parent = parent

        # Main container
        self.main = ttk.Frame(parent, padding=10)
        self.main.grid(row=0, column=0, sticky="nsew")

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # Styles
        style = ttk.Style()
        style.configure("Header.TLabel", font=("KIN668", 14, "bold"))
        style.configure("Body.TLabel", font=("KIN668", 11))

        self.build_layout()
        self.update_all()

    # -----------------------------
    # Helpers
    # -----------------------------
    def header(self, text):
        return ttk.Label(self.main, text=text, style="Header.TLabel")

    def body(self, text):
        return ttk.Label(self.main, text=text, style="Body.TLabel", justify="left")

    # -----------------------------
    # Layout
    # -----------------------------
    def build_layout(self):
        # Top header
        self.lbl_header = self.header("")
        self.lbl_header.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="n")

        # Dawn/Dusk
        self.header("Dawn/Dusk").grid(row=1, column=0, sticky="n")
        self.lbl_dawn = self.body("")
        self.lbl_dawn.grid(row=2, column=0, sticky="n", pady=(0, 20))

        # Lunar
        self.header("Lunar cycle").grid(row=1, column=1, sticky="n")
        self.lbl_lunar = self.body("")
        self.lbl_lunar.grid(row=2, column=1, sticky="n", pady=(0, 20))

        # Zodiac
        self.header("Zodiac cycle").grid(row=3, column=0, sticky="n")
        self.lbl_zodiac = self.body("")
        self.lbl_zodiac.grid(row=4, column=0, sticky="n", pady=(0, 20))

        # Coliseum
        self.header("Coliseum").grid(row=3, column=1, sticky="n")
        self.lbl_coliseum = self.body("")
        self.lbl_coliseum.grid(row=4, column=1, sticky="n", pady=(0, 20))

        # OOC → IC
        self.header("ooc → ic").grid(row=5, column=0, sticky="n")
        frame1 = ttk.Frame(self.main)
        frame1.grid(row=6, column=0, sticky="n", pady=(0, 5))
        self.entry_ooc = ttk.Entry(frame1, width=30)
        self.entry_ooc.pack(side="left", padx=(0, 5))
        ttk.Button(frame1, text="Convert", command=self.convert_ooc_to_ic).pack(side="left")
        self.lbl_ooc_result = self.body("")
        self.lbl_ooc_result.grid(row=7, column=0, sticky="n", pady=(0, 20))

        # IC → OOC
        self.header("ic → ooc").grid(row=5, column=1, sticky="n")
        frame2 = ttk.Frame(self.main)
        frame2.grid(row=6, column=1, sticky="n", pady=(0, 5))
        self.entry_ic = ttk.Entry(frame2, width=30)
        self.entry_ic.pack(side="left", padx=(0, 5))
        ttk.Button(frame2, text="Convert", command=self.convert_ic_to_ooc).pack(side="left")
        self.lbl_ic_result = self.body("")
        self.lbl_ic_result.grid(row=7, column=1, sticky="n", pady=(0, 20))

        self.main.columnconfigure(0, weight=1)
        self.main.columnconfigure(1, weight=1)

    # -----------------------------
    # Update Loop
    # -----------------------------
    def update_all(self):
        cl = cl_now()

        # Header
        self.lbl_header.config(text=fmt_cl_header(cl))

        # Dawn/Dusk
        sunrise, sunset = dawn_dusk_for_day(cl.ic_day)
        sunrise2, sunset2 = dawn_dusk_for_day(cl.ic_day + 1)
        self.lbl_dawn.config(text=(
            "Today:\n"
            f"  Sunrise at: {fmt_real(sunrise)}\n"
            f"  Sunset at:  {fmt_real(sunset)}\n\n"
            "Tomorrow:\n"
            f"  Next sunrise at: {fmt_real(sunrise2)}\n"
            f"  Next sunset at:  {fmt_real(sunset2)}"
        ))

        # Lunar
        moon_day, moon_name = moon_phase_for_day(cl.ic_day)
        next_day, start, noon, end = next_full_moon(cl.ic_day)
        lunar = f"{moon_name}, day {moon_day}\n\n"
        if start:
            lunar += (
                "Next Full Moon:\n"
                f"  Starts at: {fmt_real(start)}\n"
                f"  Noon is at: {fmt_real(noon)}\n"
                f"  Ends at:   {fmt_real(end)}"
            )
        self.lbl_lunar.config(text=lunar)

        # Zodiac
        sign, day_in_sign, days_until_next = zodiac_for_day(cl.ic_day)
        self.lbl_zodiac.config(text=(
            f"Day {day_in_sign} of {sign}\n"
            f"Next sign rises in {days_until_next} days"
        ))

        # Coliseum (simple example)
        next_col = cl_to_real(cl.ic_day + 1, 23, 10)
        self.lbl_coliseum.config(text=f"Coliseum opens at {fmt_real(next_col)}")

        self.parent.after(1000, self.update_all)

    # -----------------------------
    # Converters
    # -----------------------------
    def convert_ooc_to_ic(self):
        try:
            dt = datetime.strptime(self.entry_ooc.get(), "%H:%M %m-%d-%Y").replace(tzinfo=timezone.utc)
        except:
            messagebox.showerror("Error", "Format must be: HH:MM M-D-YYYY")
            return

        cl = real_to_cl(dt)
        result = (
            f"{cl.ic_hour:02d}:{cl.ic_minute:02d} "
            f"{cl.season_name}-{cl.season_day + 1}-{cl.year}"
        )
        self.lbl_ooc_result.config(text=result)

    def convert_ic_to_ooc(self):
        try:
            time_part, date_part = self.entry_ic.get().split()
            hour, minute = map(int, time_part.split(":"))
            season, day, year = date_part.split("-")
            season = season.capitalize()
            day = int(day)
            year = int(year)
            season_index = SEASONS.index(season)
        except:
            messagebox.showerror("Error", "Format must be: HH:MM Season-day-year")
            return

        ic_day = year * IC_DAYS_PER_YEAR + season_index * IC_DAYS_PER_SEASON + (day - 1)
        dt = cl_to_real(ic_day, hour, minute)
        self.lbl_ic_result.config(text=fmt_real(dt))

# ----------------------------------------------------------------------
# ------------------------- MAIN GUI SETUP -----------------------------
# ----------------------------------------------------------------------

root = tk.Tk()
root.title("Rank Counter 29")
# -----------------------------
# Global Font Override (KIN668.TTF)
# -----------------------------
font_path = os.path.join(os.path.dirname(__file__), "KIN668.TTF")
IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
from tkinter.font import Font
custom_font = ("KIN668", 10)

try:
    root.tk.call("font", "create", "KIN668", "-family", "KIN668",
                 "-size", "11", "-weight", "normal")
    root.tk.call("font", "configure", "KIN668", "-family", "KIN668")
except:
    pass  # font already registered or unavailable

# Apply globally
root.option_add("*Font", "KIN668 11")

try:
    icon_path = resource_path('phoenix.png')
    icon_img = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon_img)
except Exception as e:
    print(f"Could not load icon: {e}")

# Top bar: time display + character selector + scan button
top_bar = ttk.Frame(root)
top_bar.pack(fill="x", padx=10, pady=(5,0))

cl_time_label = tk.Label(top_bar, text="", font=("KIN668", 12))
cl_time_label.pack(side="top", pady=(0,4))

def _update_top_time():
    try:
        cl = cl_now()
        cl_time_label.config(text=fmt_cl_header(cl))
    except:
        pass
    root.after(1000, _update_top_time)
_update_top_time()

char_scan_frame = ttk.Frame(top_bar)
char_scan_frame.pack(side="top", fill="x")

character_list = tk.Listbox(char_scan_frame, height=1, width=30, exportselection=False)
character_list.pack(side="left", padx=(0,5))

ttk.Button(char_scan_frame, text="Scan", command=rescan_all_logs)\
    .pack(side="left", padx=5)

# Notebook
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

frame_characters = ttk.Frame(notebook)
frame_ranks = ttk.Frame(notebook)
frame_creatures = ttk.Frame(notebook)
frame_logsearch = ttk.Frame(notebook)
frame_coins = ttk.Frame(notebook)
frame_CLTime = ttk.Frame(notebook)
frame_moon = ttk.Frame(notebook)
frame_fighter = ttk.Frame(notebook)
frame_healer = ttk.Frame(notebook)

notebook.add(frame_characters, text="Characters")
notebook.add(frame_ranks, text="Ranks")
notebook.add(frame_creatures, text="Creatures")
notebook.add(frame_logsearch, text="Log Search")
notebook.add(frame_coins, text="Coins")
notebook.add(frame_CLTime, text="Time")
notebook.add(frame_moon, text="Moon Calendar")
notebook.add(frame_fighter, text="Fighter")
notebook.add(frame_healer, text="Healer")

CLTime(frame_CLTime)

# Time filter in Coins tab
time_filter_var = tk.StringVar()
time_filter_var.set("All logs")
time_filter_box = ttk.Combobox(
    frame_coins,
    textvariable=time_filter_var,
    values=[
        "All logs",
        "Last 5 minutes",
        "Last 10 minutes",
        "Last 30 minutes",
        "Last 1 hour",
        "Last 3 hours",
        "Last 6 hours",
        "Last 12 hours",
        "Last 24 hours"
    ],
    state="readonly"
)
time_filter_box.pack(pady=5)

def get_moon_icon(phase_name):
    # Mapping phase names to your filenames (update if your names differ)
    mapping = {
        "New Moon": "new.gif",
        "Full Moon": "full.gif",
        "Last Quarter": "lq.gif",
        # Add the rest of your 8 phases here
    }
    filename = mapping.get(phase_name, "default.gif")
    path = os.path.join(IMG_DIR, filename)
    if os.path.exists(path):
        return tk.PhotoImage(file=path)
    return None

def refresh_coins_table():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return

    global merged_skinned, merged_share, merged_coin_events
    merged_skinned = 0
    merged_share = 0
    merged_coin_events = []

    all_texts = []
    for folder in character_folders.get(name, []):
        if os.path.isdir(folder):
            all_texts.extend(read_text_files(folder))

    min_time = get_min_time_from_filter(time_filter_var.get())
    skinned, share, coin_events = count_coins(all_texts, name, min_time)
    merged_skinned = skinned
    merged_share = share
    merged_coin_events = coin_events

    for item in coins_table.get_children():
        coins_table.delete(item)

    coins_table.insert("", "end", values=("Total Skinned", merged_skinned))
    coins_table.insert("", "end", values=("Total Share", merged_share))
    coins_table.insert("", "end", values=("Total Coins", merged_skinned + merged_share))
    coins_table.insert("", "end", values=("", ""))
    coins_table.insert("", "end", values=("Monster", "Details"))

    summary = summarize_coin_events(merged_coin_events)
    for monster, data in summary.items():
        label = monster
        details = f"Total {data['total_worth']}c, share {data['total_share']}c, you skinned {data['your_skins']}"
        coins_table.insert("", "end", values=(label, details))

tk.Button(frame_coins, text="Refresh Coins", command=refresh_coins_table).pack(pady=5)

# Characters tab
load_characters()

char_area = ttk.Frame(frame_characters)
char_area.pack(fill="both", expand=True, pady=5)

def on_character_selected(event):
    sel = event.widget.curselection()
    if not sel:
        return
    name = event.widget.get(sel[0])

    merged_counts.clear()
    merged_creatures.clear()

    if name in character_ranks:
        for item in table.get_children():
            table.delete(item)
        for n, c in character_ranks[name].items():
            table.insert("", "end", values=(n, c))

    if name in character_creatures:
        for item in creature_table.get_children():
            creature_table.delete(item)
        ignored = character_ignored.get(name, [])
        for n, data in character_creatures[name].items():
            if n in ignored:
                continue
            if isinstance(data, dict):
                count_val = data.get("count", "")
                kills_val = data.get("kills", "")
            else:
                count_val = str(data)
                kills_val = ""
            creature_table.insert("", "end", values=(n, count_val, kills_val))

for name in character_folders.keys():
    character_list.insert(tk.END, name)
character_list.bind("<<ListboxSelect>>", on_character_selected)

def get_selected_character():
    sel = character_list.curselection()
    if not sel:
        return None
    return character_list.get(sel[0])

def add_character():
    new_name = tk.simpledialog.askstring("Add Character", "Enter new character name:")
    if new_name:
        character_list.insert(tk.END, new_name)
        character_folders[new_name] = []
        character_ranks[new_name] = {}
        character_creatures[new_name] = {}
        save_characters()

def remove_character():
    sel = character_list.curselection()
    if not sel:
        messagebox.showerror("Error", "Please select a character to remove.")
        return
    name = character_list.get(sel[0])
    if messagebox.askyesno("Confirm", f"Remove character '{name}'?"):
        character_list.delete(sel[0])
        character_folders.pop(name, None)
        character_ranks.pop(name, None)
        character_creatures.pop(name, None)
        character_ignored.pop(name, None)
        save_characters()

char_buttons_frame = ttk.Frame(char_area)
char_buttons_frame.pack(pady=5)

add_char_btn = ttk.Button(char_buttons_frame, text="Add Character", command=add_character)
add_char_btn.pack(side="left", padx=5)

remove_char_btn = ttk.Button(char_buttons_frame, text="Remove Character", command=remove_character)
remove_char_btn.pack(side="left", padx=5)

# Folder manager
folder_manager_frame = ttk.Frame(frame_characters)

fm_label = ttk.Label(folder_manager_frame, text="Folders for selected character:")
fm_label.pack(pady=5)

fm_folder_list = tk.Listbox(folder_manager_frame, width=60, height=12)
fm_folder_list.pack(pady=5, fill="both", expand=True)

fm_button_frame = ttk.Frame(folder_manager_frame)
fm_button_frame.pack(pady=10)

def update_folder_list_in_manager():
    fm_folder_list.delete(0, tk.END)
    name = get_selected_character()
    if name and name in character_folders:
        for f in character_folders[name]:
            fm_folder_list.insert(tk.END, f)

def add_folder_in_manager():
    folder = filedialog.askdirectory()
    if folder:
        name = get_selected_character()
        if not name:
            messagebox.showerror("Error", "Select a character first.")
            return
        if folder in character_folders.setdefault(name, []):
            messagebox.showinfo("Duplicate Folder", "This folder is already assigned to this character.")
            return
        character_folders[name].append(folder)
        update_folder_list_in_manager()
        save_characters()

def remove_folder_in_manager():
    sel = fm_folder_list.curselection()
    if sel:
        folder = fm_folder_list.get(sel[0])
        name = get_selected_character()
        if name and folder in character_folders.get(name, []):
            character_folders[name].remove(folder)
            update_folder_list_in_manager()
            save_characters()

add_folder_btn = ttk.Button(fm_button_frame, text="Add Folder", command=add_folder_in_manager)
add_folder_btn.pack(side="left", padx=5)

remove_folder_btn = ttk.Button(fm_button_frame, text="Remove Selected", command=remove_folder_in_manager)
remove_folder_btn.pack(side="left", padx=5)

def open_folder_manager():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return
    char_area.pack_forget()
    update_folder_list_in_manager()
    folder_manager_frame.pack(fill="both", expand=True, pady=5)

def close_folder_manager():
    folder_manager_frame.pack_forget()
    char_area.pack(fill="both", expand=True, pady=5)

back_btn = ttk.Button(fm_button_frame, text="Back", command=close_folder_manager)
back_btn.pack(side="left", padx=5)

manage_folders_btn = ttk.Button(char_buttons_frame, text="Folders", command=open_folder_manager)
manage_folders_btn.pack(side="left", padx=5)

# Ranks table
table = ttk.Treeview(frame_ranks, columns=("Trainer", "Ranks"), show="headings")
table.heading("Trainer", text="Trainer")
table.heading("Ranks", text="Ranks")
table.column("Trainer", width=300, stretch=True)
table.column("Ranks", width=80, stretch=False)
table.pack(pady=10, fill="both", expand=True)

# Creatures table
creature_table = ttk.Treeview(frame_creatures, columns=("Creature", "MessageNumber", "KillsTillNext"), show="headings")
creature_table.heading("Creature", text="Creature")
creature_table.heading("MessageNumber", text="Message Number")
creature_table.heading("KillsTillNext", text="Kills Counted")
creature_table.column("Creature", width=420, anchor="w", stretch=True)
creature_table.column("MessageNumber", width=120, anchor="center", stretch=False)
creature_table.column("KillsTillNext", width=160, anchor="center", stretch=False)
creature_table.pack(pady=10, fill="both", expand=True)

creature_context_menu = tk.Menu(root, tearoff=0)
creature_context_menu.add_command(label="Ignore Creature", command=ignore_selected_creature)

btn_ignore_creature = ttk.Button(
    frame_creatures,
    text="Manage Ignored List",
    command=open_ignore_manager
)
btn_ignore_creature.pack(padx=6, pady=4, side="left", anchor="nw")

btn_special_kills = ttk.Button(
    frame_creatures,
    text="View Message Table",
    command=open_kills_to_next_table
)
btn_special_kills.pack(padx=6, pady=4, side="right", anchor="ne")

# Coins table
coins_table = ttk.Treeview(frame_coins, columns=("Event", "Details"), show="headings")
coins_table.heading("Event", text="Event")
coins_table.heading("Details", text="Details")
coins_table.column("Event", width=300)
coins_table.column("Details", width=200)
coins_table.pack(fill="both", expand=True, pady=10)

def show_creature_menu(event):
    item = creature_table.identify_row(event.y)
    if item:
        creature_table.selection_set(item)
        creature_context_menu.post(event.x_root, event.y_root)

creature_table.bind("<Button-3>", show_creature_menu)
creature_table.bind("<Button-2>", show_creature_menu)

# ---------------------------------------------------------
#  PIXEL‑PERFECT MOON CALENDAR (Matches Screenshot Exactly)
# ---------------------------------------------------------

moon_container = ttk.Frame(frame_moon)
moon_container.pack(fill="both", expand=True, padx=20, pady=20)

# -------------------------------
# Current Time — ONE LINE
# -------------------------------
stats_frame = ttk.LabelFrame(moon_container, text="Current Time")
stats_frame.pack(fill="x", pady=(0, 10))

stats_labels = {}
fields = ["Year", "Season", "Zodiac", "Moon Phase", "Time"]

for col, field in enumerate(fields):
    ttk.Label(stats_frame, text=f"{field}:", font=("KIN668", 10, "bold")).grid(row=0, column=col*2, padx=4)
    stats_labels[field] = ttk.Label(stats_frame, text="---", font=("KIN668", 10))
    stats_labels[field].grid(row=0, column=col*2 + 1, padx=4)

# -------------------------------
# Year Selector
# -------------------------------
year_frame = ttk.Frame(moon_container)
year_frame.pack(pady=(0, 10))

year_var = tk.IntVar()

def submit_year():
    build_moon_calendar(year_var.get())

# -------------------------------
# Exact Screenshot Colors
# -------------------------------
season_colors = {
    "Winter": "#C7DDF9",
    "Spring": "#C9F7C9",
    "Summer": "#FFF4C2",
    "Autumn": "#FFD2A6"
}

moon_bg = "#EDEDED"  # moon phase cell background

# -------------------------------
# Calendar Container (VERTICAL)
# -------------------------------
calendar_frame = ttk.Frame(moon_container)
calendar_frame.pack(fill="both", expand=True)

seasons = ["Winter", "Spring", "Summer", "Autumn"]
season_frames = {}

for s in seasons:
    outer = tk.Frame(calendar_frame, bg=season_colors[s], bd=1, relief="solid")
    outer.pack(fill="x", pady=4)
    season_frames[s] = outer

    # Season header
    tk.Label(
        outer,
        text=s.upper(),
        font=("KIN668", 12, "bold"),
        bg=season_colors[s],
        anchor="center"
    ).pack(fill="x", pady=(3, 3))

# -------------------------------
# Preload icons
# -------------------------------
icon_cache = {}
for name, img_file in moon_icons.items():
    path = os.path.join(os.path.dirname(__file__), img_file)
    icon_cache[name] = tk.PhotoImage(file=path)

# -------------------------------
# Moon phase for any IC day
# -------------------------------
def moon_phase_for_day(day_of_year):
    lunar_day = day_of_year % 28
    if lunar_day == 0:
        return lunar_day, "New Moon"
    elif lunar_day == 7:
        return lunar_day, "First Quarter"
    elif lunar_day == 14:
        return lunar_day, "Full Moon"
    elif lunar_day == 21:
        return lunar_day, "Last Quarter"
    else:
        return lunar_day, None  # normal day

# -------------------------------
# Build the 360‑day calendar
# -------------------------------
day_cells = []

def build_moon_calendar(year):
    global day_cells
    day_cells = []

    day = 0
    for season in seasons:
        outer = season_frames[season]

        grid = tk.Frame(outer, bg=season_colors[season])
        grid.pack(padx=4, pady=(0, 6))

        for r in range(2):        # 9 rows
            for c in range(30):   # 10 columns
                day += 1
                lunar_day, phase = moon_phase_for_day(day)

                bg = moon_bg if phase else season_colors[season]

                cell = tk.Frame(
                    grid,
                    bg=bg,
                    width=32,
                    height=32,
                    bd=1,
                    relief="solid"
                )
                cell.grid(row=r, column=c, padx=1, pady=1)
                cell.grid_propagate(False)

                if phase:
                    icon = icon_cache.get(phase)
                    tk.Label(cell, image=icon, bg=bg).pack()
                else:
                    tk.Label(cell, bg=bg).pack()

                tk.Label(cell, text=str(day), font=("KIN668", 8), bg=bg).pack()

                day_cells.append(cell)

# -------------------------------
# Legend (matches screenshot)
# -------------------------------
legend = tk.Frame(moon_container)
legend.pack(pady=5)

for phase in ["New Moon", "First Quarter", "Full Moon", "Last Quarter"]:
    icon = icon_cache.get(phase)
    box = tk.Frame(legend)
    box.pack(side="left", padx=10)

    tk.Label(box, image=icon).pack()
    tk.Label(box, text=phase, font=("KIN668", 9)).pack()

# -------------------------------
# Update loop
# -------------------------------
def update_moon_calendar():
    cl_time = real_to_cl(datetime.now())

    stats_labels["Year"].config(text=str(cl_time.year + 1))
    stats_labels["Season"].config(text=cl_time.season_name)
    stats_labels["Zodiac"].config(text=cl_time.zodiac_name)
    stats_labels["Moon Phase"].config(text=cl_time.moon_phase_name)
    stats_labels["Time"].config(text=f"{cl_time.ic_hour:02}:{cl_time.ic_minute:02}")

    current_day = cl_time.day_of_year - 1

    for i, cell in enumerate(day_cells):
        if i == current_day:
            cell.config(bd=2, relief="solid")
        else:
            cell.config(bd=1, relief="solid")

    frame_moon.after(60000, update_moon_calendar)

# -------------------------------
# Initial build
# -------------------------------
cl_time = real_to_cl(datetime.now())
year_var.set(cl_time.year)
build_moon_calendar(cl_time.year)
update_moon_calendar()

# ----------------------------------------------------------------------
# LOG SEARCH TAB — sentence-level search, file path hidden
# ----------------------------------------------------------------------

# Make the frame itself resizable inside the notebook
frame_logsearch.grid_rowconfigure(2, weight=1)
frame_logsearch.grid_columnconfigure(1, weight=1)
frame_logsearch.grid_columnconfigure(0, weight=0)
frame_logsearch.grid_columnconfigure(2, weight=0)

tk.Label(frame_logsearch, text="Search word:")\
    .grid(row=0, column=0, padx=5, pady=5, sticky="w")

ls_word_var = tk.StringVar()
tk.Entry(frame_logsearch, textvariable=ls_word_var, width=50)\
    .grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# Hidden storage for file paths (parallel to Listbox)
ls_hidden_paths = []


# --- Sentence extractor ------------------------------------------------
def ls_extract_sentences(file_path, word):
    """Return list of (full_line, file_path) for each match."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.rstrip("\r\n")
                if word.lower() in line.lower():
                    results.append((line, file_path))
    except:
        pass

    return results


# --- Background thread search -------------------------------------
def ls_run_scan(name, word):
    results = []

    for folder in character_folders.get(name, []):
        if not os.path.isdir(folder):
            continue

        for root, dirs, files in os.walk(folder):
            for filename in files:
                if not filename.lower().endswith(".txt"):
                    continue

                full_path = os.path.join(root, filename)
                matches = ls_extract_sentences(full_path, word)
                results.extend(matches)

    ls_results_list.after(0, ls_update_results, results, word)


# ---  Show sentences ------------------------------------------
def ls_update_results(results, word):
    ls_results_list.delete(0, tk.END)
    ls_hidden_paths.clear()

    if not results:
        ls_results_list.insert(tk.END, f"No sentences found containing '{word}'.")
        return

    ls_results_list.insert(tk.END, f"Sentences containing '{word}':")
    ls_hidden_paths.append(None)  # placeholder for header

    ls_results_list.insert(tk.END, "--------------------------------")
    ls_hidden_paths.append(None)

    for sentence, file_path in results:
        ls_results_list.insert(tk.END, sentence)
        ls_hidden_paths.append(file_path)  # store file path invisibly


# --- Double-click opens file ---------------------
def ls_open_selected_file(event=None):
    sel = ls_results_list.curselection()
    if not sel:
        return

    index = sel[0]
    file_path = ls_hidden_paths[index]

    if file_path and os.path.isfile(file_path):
        open_file_with_default_app(file_path)


# --- Search button handler --------------------------------------------------
def ls_start_search():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return

    if name not in character_folders or not character_folders[name]:
        messagebox.showerror("Error", "This character has no folders assigned.")
        return

    word = ls_word_var.get().strip()
    if not word:
        messagebox.showerror("Error", "Please enter a word to search for.")
        return

    ls_results_list.delete(0, tk.END)
    ls_results_list.insert(tk.END, "Scanning all folders... Please wait.")
    ls_hidden_paths.clear()

    threading.Thread(target=ls_run_scan, args=(name, word), daemon=True).start()


# --- Search button ----------------------------------------------------------
tk.Button(frame_logsearch, text="Search", command=ls_start_search)\
    .grid(row=0, column=2, padx=5, pady=5, sticky="e")

tk.Label(frame_logsearch, text="Matching Sentences:")\
    .grid(row=1, column=0, padx=5, pady=5, sticky="w")


# --- Listbox expands in BOTH directions ------------------------------------
ls_results_list = tk.Listbox(frame_logsearch, width=90, height=20)
ls_results_list.grid(
    row=2, column=0, columnspan=3,
    padx=5, pady=5,
    sticky="nsew"
)

scrollbar = tk.Scrollbar(frame_logsearch)
scrollbar.grid(row=2, column=3, sticky="ns")
ls_results_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=ls_results_list.yview)

ls_results_list.bind("<Double-Button-1>", ls_open_selected_file)

# ----------------------------------------------------------------------
# FIGHTER CALCULATOR TAB
# ----------------------------------------------------------------------

import math

FighterRaces = [
    [300,100,200,5000,400,3000,300,100,800,600],
    [400,0,300,5300,300,3300,300,100,500,500],
    [200,0,200,5900,500,1500,200,100,700,500],
    [100,0,100,5300,300,3000,600,100,900,700],
    [500,200,400,4400,500,3600,100,100,700,500],
    [300,100,100,5000,500,2400,400,100,800,600],
    [200,0,100,4700,300,3900,200,300,1000,700],
    [0,0,0,0,0,0,0,0,0,0],
]
FighterWeapons = [[0]*10 for _ in range(130)]
FighterWeapons[0]  = [0,0,0,0,0,0,0,0,0,0]
FighterWeapons[1]  = [100,0,0,300,150,0,-200,0,0,0]
FighterWeapons[2]  = [100,-200,-100,600,200,0,0,0,0,0]
FighterWeapons[3]  = [200,-100,-100,900,400,0,-100,0,0,0]
FighterWeapons[4]  = [100,0,0,0,0,0,-400,300,0,0]
FighterWeapons[5]  = [50,0,50,150,100,0,-100,0,0,0]
FighterWeapons[6]  = [-50,0,0,-150,50,0,50,0,0,0]
FighterWeapons[7]  = [100,200,200,0,0,0,0,0,0,0]
FighterWeapons[8]  = [100,100,100,-300,0,0,0,0,0,0]
FighterWeapons[9]  = [100,100,100,300,100,0,-200,0,0,0]
FighterWeapons[10] = [100,200,200,-300,-100,0,-100,0,0,0]
FighterWeapons[11] = [-50,0,50,-300,50,0,100,0,0,0]
FighterWeapons[12] = [100,100,120,0,-50,0,-50,0,0,0]
FighterWeapons[13] = [90,175,225,-300,-90,0,0,0,0,0]
FighterWeapons[20] = [50,0,50,0,0,0,100,0,0,0]
FighterWeapons[21] = [20,20,110,300,50,0,-100,0,0,0]
FighterWeapons[22] = [100,100,150,-240,0,0,40,0,0,0]
FighterWeapons[23] = [150,175,175,-240,-80,0,50,0,0,0]
FighterWeapons[24] = [50,0,50,0,0,0,100,0,0,0]
FighterWeapons[25] = [100,80,80,-180,-60,0,120,0,0,0]
FighterWeapons[30] = [50,50,100,-150,-50,0,0,0,0,0]
FighterWeapons[31] = [90,250,290,-480,-150,0,0,0,0,0]
FighterWeapons[40] = [-100,-50,-150,150,100,0,0,0,0,0]
FighterWeapons[41] = [-50,0,-100,300,100,0,20,0,0,0]
FighterWeapons[42] = [50,0,-60,300,100,0,70,0,0,0]
FighterWeapons[50] = [150,300,350,-600,-200,0,-20,0,0,0]
FighterWeapons[51] = [250,210,210,-300,-100,0,50,0,0,0]
FighterWeapons[60] = [-200,200,200,-300,-300,0,50,0,0,0]
FighterWeapons[80] = [-100,200,300,-300,-100,0,0,0,0,0]
FighterWeapons[81] = [-500,600,600,-1500,-500,0,-500,0,0,0]
FighterWeapons[89] = [50,0,50,0,0,0,100,0,0,0]
for i in range(90, 100):
    FighterWeapons[i] = [100,-50,-50,450,200,0,0,0,0,0]
for i in range(100, 103):
    FighterWeapons[i] = [45,125,145,-240,-80,0,0,0,0,0]
FighterWeapons[103] = [0,0,0,0,50,0,0,0,0,0]
FighterWeapons[110] = [45,125,145,-240,-80,0,0,0,0,0]
FighterWeapons[120] = [180,100,300,300,0,0,0,0,0,0]

FighterLefts = [[0]*10 for _ in range(109)]
FighterLefts[0] = [0,0,0,0,0,0,0,0,0,0]
FighterLefts[1] = [100,10,10,-300,-100,0,100,0,0,0]
FighterLefts[2] = [0,0,0,-300,-100,0,300,0,0,0]
for i in range(101, 109):
    FighterLefts[i] = [0,0,0,0,0,0,0,0,0,0]

FighterShoulders = [[0]*10 for _ in range(109)]
FighterShoulders[0] = [0,0,0,0,0,0,0,0,0,0]
for i in range(101, 109):
    FighterShoulders[i] = [0,0,0,0,0,0,0,0,0,0]

FighterRaceNames = [
    "Human/Undisclosed", "Dwarf", "Fen", "Halfling",
    "Ghorak Zo", "Sylvan", "Thoom", "0-Stat Race",
]
FighterWeaponNames = {
    0:"Roguewood Club", 1:"Dagger", 2:"Dueling Blade", 3:"Shiny Dagger",
    4:"Lyfelidae Claw", 5:"Studded Club", 6:"Shovel", 7:"Boar Tusk",
    8:"Sturdy Limb", 9:"Spike", 10:"Seta Scale", 11:"Quarterstaff",
    12:"Flail", 13:"Battle Hammer", 20:"Short Sword", 21:"Rapier",
    22:"Longsword", 23:"Broadsword", 24:"Machete", 25:"Sword of Souls",
    30:"Hand Axe", 31:"Axe", 40:"Cloth Bracers", 41:"Leather Bracers",
    42:"Metal Bracers", 50:"Greataxe", 51:"Greatsword", 60:"Anchor",
    80:"Mace", 81:"Oak Basher", 89:"Ethereal Sword",
    90:"Gossamer (No Studies)", 93:"Gossamer (Family 10%)",
    94:"Gossamer (Family 20%)", 95:"Gossamer (Family 30%)",
    96:"Gossamer (Family 40%)", 97:"Gossamer (Family 50%)",
    98:"Gossamer (Movement)", 100:"Fell Blade (Normal)",
    101:"Fell Blade (Angled BS)", 102:"Fell Blade (Direct BS)",
    103:"Tell Blade", 110:"Labrys", 120:"Bloodblade",
}
FighterLeftNames = {
    0:"Nothing", 1:"Main Gauche", 2:"Wooden Shield",
    101:"Atkite", 102:"Darkite", 103:"Balthite", 104:"Dethite",
    105:"Atkite (Boosted)", 106:"Darkite (Boosted)",
    107:"Balthite (Boosted)", 108:"Dethite (Boosted)",
}
FighterShoulderNames = {
    0:"Nothing",
    101:"Atkite Pauldron", 102:"Darkite Pauldron",
    103:"Balthite Pauldron", 104:"Dethite Pauldron",
    105:"Atkite Pauldron (Boosted)", 106:"Darkite Pauldron (Boosted)",
    107:"Balthite Pauldron (Boosted)", 108:"Dethite Pauldron (Boosted)",
}

def _f_CMToAccuracy(cm): return math.floor(cm * 25)
def _f_CMToMinDamage(cm): return math.floor(cm * 10.32)
def _f_CMToMaxDamage(cm): return math.floor(cm * 10.32)
def _f_CMToBalance(cm): return math.floor(cm * 51)
def _f_CMToDefense(cm): return math.floor(cm * 19)
def _f_DamageToDarktur(d): return d / 10
def _f_BalthusToBalance(b): return b * 51
def _f_BalanceToBalthus(bal): return bal / 51
def _f_RegiaToRegen(r): return r * 15
def _f_RegenToRegia(r): return r / 15
def _f_HistiaToHealth(h): return h * 111
def _f_HealthToHistia(h): return h / 111
def _f_DethaToDefense(d): return d * 19
def _f_DefenseToDetha(d): return d / 19
def _f_BalanceToDefense(b): return b * 0.3
def _f_CratoToSpirit(c): return c * 373
def _f_SpleishaToSpirit(s): return s * 373
def _f_SplashToSpirit(s): return s * 373
def _f_OldSplashToSpirit(s): return s * 375
def _f_ToomeriaToSpirit(t): return t * 500
def _f_RespinToSpiritRegen(r): return r * 32
def _f_TroilusToRegeneration(t): return t * 6
def _f_RegenerationToTroilus(r): return r / 6
def _f_AkturToAccuracy(a): return a * 25
def _f_AccuracyToAktur(a): return a / 25
def _f_AtkusToAccuracy(a): return a * 16
def _f_AccuracyToAtkus(a): return a / 16
def _f_DarkusToDamage(d): return d * 6
def _f_DamageToDarkus(d): return d / 6
def _f_DarkturToDamage(d): return d * 10

def _f_RoundDown(value):
    return math.floor(value + 0.00000001)

def _f_Round(value):
    v = value * 1000
    s = str(v)
    dot = s.find('.')
    if dot >= 3:
        if s[dot-3:dot] == "999":
            if len(s) <= dot + 6 or s[dot+1:dot+7] != "999999":
                if v < 0:
                    v = math.ceil(v)
                else:
                    v = math.floor(v)
                return v / 1000
    return round(value)

def _f_is_earth_mineral(val):
    return 101 <= val <= 108

def _f_GetLabrysDamage(MinDmg, MaxDmg, TFell, LabrysTargets):
    if LabrysTargets is None or LabrysTargets < 1:
        LabrysTargets = 1
    if LabrysTargets == 1:
        FlatMin, FlatMax, ScaleMin, ScaleMax = -700, -700, 4, 4
    elif LabrysTargets == 2:
        FlatMin, FlatMax, ScaleMin, ScaleMax = -500, -400, 7, 7
    elif LabrysTargets == 3:
        FlatMin, FlatMax, ScaleMin, ScaleMax = 200, 400, 9, 9
    elif LabrysTargets == 4:
        FlatMin, FlatMax, ScaleMin, ScaleMax = 300, 600, 13, 13
    elif LabrysTargets == 5:
        FlatMin, FlatMax, ScaleMin, ScaleMax = 400, 800, 18, 18
    else:
        FlatMin = 100 * (LabrysTargets - 1)
        FlatMax = 200 * (LabrysTargets - 1)
        ScaleMin, ScaleMax = 18, 18
    MinDmg += FlatMin + ScaleMin * TFell
    MaxDmg += FlatMax + ScaleMax * TFell
    MinDmg = math.floor(MinDmg / LabrysTargets)
    MaxDmg = math.floor(MaxDmg / LabrysTargets)
    return [MinDmg, MaxDmg]

def _f_compute_fighter(params):
    g = lambda k, d=0: float(params.get(k, d))
    EAtkus=g("EAtkus"); TAtkus=g("TAtkus")
    EDarkus=g("EDarkus"); TDarkus=g("TDarkus")
    EBalthus=g("EBalthus"); TBalthus=g("TBalthus")
    ERegia=g("ERegia"); TRegia=g("TRegia")
    EHistia=g("EHistia"); THistia=g("THistia")
    EDetha=g("EDetha"); TDetha=g("TDetha")
    ETroilus=g("ETroilus"); TTroilus=g("TTroilus")
    ERodnus=g("ERodnus"); TRodnus=g("TRodnus")
    ESpiritus=g("ESpiritus"); TSpiritus=g("TSpiritus")
    TEvus=g("TEvus"); TSwengus=g("TSwengus"); TFarly=g("TFarly")
    TKnox=g("TKnox"); TAngilsa=g("TAngilsa")
    TBodrus=g("TBodrus"); THardia=g("THardia")
    TForvyola=g("TForvyola"); TBangus=g("TBangus")
    TErthron=g("TErthron"); TErthronNew=g("TErthronNew")
    TAtkia=g("TAtkia"); TDarktur=g("TDarktur")
    TAktur=g("TAktur"); TStedfustus=g("TStedfustus")
    TAnemia=g("TAnemia")
    TFell=g("TFell"); TGoss=g("TGoss"); TChan=g("TChan")
    TAtkite=g("TAtkite"); TDarkite=g("TDarkite")
    TBalthite=g("TBalthite"); TDethite=g("TDethite")
    TToomeria=g("TToomeria")
    TSplash=g("TSplash"); TSplashOld=g("TSplashOld")
    TRespin=g("TRespin"); TChampReg=g("TChampReg")
    TDuvin=g("TDuvin"); THeen=g("THeen")
    TCrato=g("TCrato"); TSpleisha=g("TSpleisha")
    TSpleishaOld=g("TSpleishaOld"); TBB=g("TBB")
    TCloak=g("TCloak"); TGirdle=g("TGirdle")
    TCryptus=g("TCryptus"); TDisabla=g("TDisabla")
    TDantus=g("TDantus"); TAneurus=g("TAneurus")
    TPosuhm=g("TPosuhm"); TTracking=g("TTracking")
    Subclass=int(params.get("Subclass",0))
    Race=int(params.get("Race",0))
    Weapon=int(params.get("Weapon",0))
    Left=int(params.get("Left",0))
    Shoulder=int(params.get("Shoulder",0))
    LabrysTargets=int(params.get("LabrysTargets",1))
    if LabrysTargets<1: LabrysTargets=1
    FPS=float(params.get("FPS",5))
    if FPS<=0: FPS=1
    if TChampReg==11 and Race in (1,2,4): TChampReg=10
    if TChampReg==6 and Race in (0,5): TChampReg=5
    if Subclass!=1: TChan=0; TAtkite=0; TDarkite=0; TBalthite=0; TDethite=0; TToomeria=0; TChampReg=0; TCloak=0; TGirdle=0
    if Subclass!=2: TDuvin=0; TSplash=0; TSplashOld=0; TRespin=0; TTracking=0
    if Subclass!=3: TCryptus=0; TDisabla=0; TDantus=0; TAneurus=0; TPosuhm=0
    ChanMult=1; IsDoubleIte=False
    if _f_is_earth_mineral(Left) and _f_is_earth_mineral(Shoulder):
        ChanMult=0.5; IsDoubleIte=True
        if Left>=105: Left=Left-4
    Chan=TChan+math.floor(TAtkite*5/4)+math.floor(TDarkite*5/4)+math.floor(TBalthite*5/4)+math.floor(TDethite*5/4)
    EFell=TFell+10
    AtkiteStr=Chan; DarkiteStr=Chan; BalthiteStr=Chan; DethiteStr=Chan
    AtkusReq=99999
    AccuracyReq=max(_f_AtkusToAccuracy(AtkusReq),0)
    Accuracy=_f_AtkusToAccuracy(EAtkus+TAtkus)
    Accuracy+=TEvus*4; Accuracy+=TBodrus*4; Accuracy+=THardia*4
    Accuracy-=TKnox*4; Accuracy-=TAngilsa*4
    Accuracy+=TBangus*2; Accuracy+=TErthron*3; Accuracy+=TErthronNew*2
    Accuracy+=_f_AkturToAccuracy(TAktur); Accuracy+=TAtkia*13
    if Left==101 or Left==105: Accuracy+=_f_CMToAccuracy(math.floor(AtkiteStr*ChanMult))
    if Left==105: Accuracy+=_f_CMToAccuracy(max(Chan-20,0))
    if Shoulder==101 or Shoulder==105: Accuracy+=_f_CMToAccuracy(math.floor(AtkiteStr*ChanMult))
    if Shoulder==105: Accuracy+=_f_CMToAccuracy(max(Chan-20,0))
    GossAccuracy=0; GossDamage=0; FellAccuracy=0; TellAccuracy=0
    if 93<=Weapon<=97 and Subclass==2:
        Families=Weapon-92
        GossAccuracy=32*TGoss; GossDamage=12*TGoss
        GossAccuracy=math.floor(GossAccuracy*Families/10)
        GossDamage=math.floor(GossDamage*Families/10)
        GossAccuracy=min(GossAccuracy,max(AccuracyReq-Accuracy,0))
    elif Weapon==98 and Subclass==2:
        GossAccuracy=32*TGoss; GossDamage=12*TGoss
        GossAccuracy=min(GossAccuracy,max(AccuracyReq-Accuracy,0))
    elif Weapon==101:
        FellAccuracy=16*EFell; FellAccuracy=min(FellAccuracy,max(AccuracyReq-Accuracy,0))
    elif Weapon==102:
        FellAccuracy=32*EFell; FellAccuracy=min(FellAccuracy,max(AccuracyReq-Accuracy,0))
    elif Weapon==103 and Subclass==1:
        TellAccuracy=-32*TFell; TellAccuracy=max(TellAccuracy,min(AccuracyReq-Accuracy,0))
    Accuracy+=GossAccuracy+FellAccuracy+TellAccuracy
    ShowVal=Accuracy
    Accuracy+=FighterRaces[Race][0]+FighterWeapons[Weapon][0]+FighterLefts[Left][0]+FighterShoulders[Shoulder][0]
    AccuracyReq+=FighterRaces[Race][0]+FighterWeapons[Weapon][0]+FighterLefts[Left][0]+FighterShoulders[Shoulder][0]
    if Weapon==89:
        ab=0.2*(Accuracy-FighterRaces[0][0])
        if ab!=0: Accuracy+=ab; ShowVal+=ab
    MaxDamage=_f_DarkusToDamage(EDarkus+TDarkus)
    MaxDamage+=TEvus*1+TBodrus*1+TKnox*11-TAngilsa*1+TErthron*1+TErthronNew*1+TAtkia*3
    MaxDamage+=_f_DarkturToDamage(TDarktur)
    MinDamage=MaxDamage
    MaxDamage+=THardia*1+TBangus*3
    MinDamage+=TBangus*2
    if Weapon==101: MaxDamage+=6*EFell; MinDamage+=6*EFell
    if Weapon==102: MaxDamage+=12*EFell; MinDamage+=12*EFell
    if Left==102 or Left==106:
        MaxDamage+=_f_CMToMaxDamage(math.floor(DarkiteStr*ChanMult))
        MinDamage+=_f_CMToMinDamage(math.floor(DarkiteStr*ChanMult))
    if Left==106:
        MaxDamage+=_f_CMToMaxDamage(max(Chan-20,0)); MinDamage+=_f_CMToMinDamage(max(Chan-20,0))
    if Shoulder==102 or Shoulder==106:
        MaxDamage+=_f_CMToMaxDamage(math.floor(DarkiteStr*ChanMult))
        MinDamage+=_f_CMToMinDamage(math.floor(DarkiteStr*ChanMult))
    if Shoulder==106:
        MaxDamage+=_f_CMToMaxDamage(max(Chan-20,0)); MinDamage+=_f_CMToMinDamage(max(Chan-20,0))
    MaxDamage+=GossDamage; MinDamage+=GossDamage
    ShowValMin=MinDamage; ShowValMax=MaxDamage
    ShowValAvg=(MinDamage+MaxDamage*3)/4
    MinDamage+=FighterRaces[Race][1]+FighterWeapons[Weapon][1]+FighterLefts[Left][1]+FighterShoulders[Shoulder][1]
    MaxDamage+=FighterRaces[Race][2]+FighterWeapons[Weapon][2]+FighterLefts[Left][2]+FighterShoulders[Shoulder][2]
    MinDamageNoIte=MinDamage-Shoulder[1] if False else MinDamage-FighterShoulders[Shoulder][1]
    MaxDamageNoIte=MaxDamage-FighterShoulders[Shoulder][2]
    if Weapon==89:
        mb=0.15*(MinDamage-FighterRaces[0][1]); MB=0.15*(MaxDamage-FighterRaces[0][2])
        if mb!=0: MinDamage+=mb; ShowValMin+=mb; ShowValAvg+=mb/4
        if MB!=0: MaxDamage+=MB; ShowValMax+=MB; ShowValAvg+=3*MB/4
    LabrysDamage=None
    if Weapon==110 and Subclass==1:
        LabrysDamage=_f_GetLabrysDamage(MinDamage,MaxDamage,TFell,LabrysTargets)
        ShowValMin=LabrysDamage[0]-(MinDamage-ShowValMin); ShowValMax=LabrysDamage[1]-(MaxDamage-ShowValMax)
        ShowValAvg=(ShowValMin+ShowValMax*3)/4
    if Weapon==110 and Subclass==1: HitMin=LabrysDamage[0]; HitMax=LabrysDamage[1]
    else: HitMin=MinDamage; HitMax=MaxDamage
    HitMax*=3
    if HitMin<0: HitMin=0
    HitMin+=100
    if HitMax<0: HitMax=0
    HitMax+=100
    if HitMax<HitMin: HitMax=HitMin
    UMinDamage=MinDamage if Weapon!=110 or Subclass!=1 else LabrysDamage[0]
    UMaxDamage=MaxDamage if Weapon!=110 or Subclass!=1 else LabrysDamage[1]
    if UMinDamage<0: UMinDamage=0
    if UMaxDamage<0: UMaxDamage=0
    if UMaxDamage<UMinDamage/3: UMaxDamage=UMinDamage/3
    Balance=_f_BalthusToBalance(EBalthus+TBalthus)
    Balance+=TEvus*18+TBodrus*9+THardia*9+TAtkus*15+TDarkus*18+TSwengus*30+TKnox*18-TAngilsa*18+TBangus*21+TErthron*15+TErthronNew*15
    if Left==103 or Left==107: Balance+=_f_CMToBalance(math.floor(BalthiteStr*ChanMult))
    if Left==107: Balance+=_f_CMToBalance(max(Chan-20,0))
    if Shoulder==103 or Shoulder==107: Balance+=_f_CMToBalance(math.floor(BalthiteStr*ChanMult))
    if Shoulder==107: Balance+=_f_CMToBalance(max(Chan-20,0))
    ShowValBal=Balance
    Balance+=FighterRaces[Race][3]+FighterWeapons[Weapon][3]+FighterLefts[Left][3]+FighterShoulders[Shoulder][3]
    if Weapon==89:
        bb=0.1*(Balance-FighterRaces[0][3])
        if bb!=0: Balance+=bb; ShowValBal+=bb
    ShowValBalance=ShowValBal
    Regen=_f_RegiaToRegen(ERegia+TRegia)
    Regen+=TEvus*4+TBodrus*3+THardia*1+TAtkus*1+TDarkus*1+TSwengus*7-TKnox*2+TAngilsa*26+TForvyola*8+TBangus*5+TErthron*3+TErthronNew*2+TAtkia*3+TStedfustus*6+TAnemia*8
    Regen+=FighterRaces[Race][4]+FighterWeapons[Weapon][4]+FighterLefts[Left][4]+FighterShoulders[Shoulder][4]
    RegenNoIte=Regen-FighterShoulders[Shoulder][4]
    if not IsDoubleIte: RegenNoIte-=FighterLefts[Left][4]
    Health=_f_HistiaToHealth(EHistia+THistia)
    Health+=TEvus*24+TBodrus*24+THardia*21+TDetha*3+TRodnus*36+TFarly*48-TKnox*24-TAngilsa*24+TForvyola*54+TBangus*6+TErthron*24+TErthronNew*21+TSpiritus*21+TStedfustus*54+TAnemia*69
    Health+=FighterRaces[Race][5]+FighterWeapons[Weapon][5]+FighterLefts[Left][5]+FighterShoulders[Shoulder][5]
    Defense=_f_DethaToDefense(EDetha+TDetha)
    Defense+=TEvus*1+TBodrus*1+THardia*1+TFarly*2-TKnox*1-TAngilsa*1+TErthron*7+TErthronNew*7
    if Left==104 or Left==108: Defense+=_f_CMToDefense(math.floor(DethiteStr*ChanMult))
    if Left==108: Defense+=_f_CMToDefense(max(Chan-20,0))
    if Shoulder==104 or Shoulder==108: Defense+=_f_CMToDefense(math.floor(DethiteStr*ChanMult))
    if Shoulder==108: Defense+=_f_CMToDefense(max(Chan-20,0))
    ShowValDef=Defense
    Defense+=FighterRaces[Race][6]+FighterWeapons[Weapon][6]+FighterLefts[Left][6]+FighterShoulders[Shoulder][6]
    ShowValDef+=_f_BalanceToDefense(ShowValBalance)
    Regeneration=_f_TroilusToRegeneration(ETroilus+TTroilus)
    Regeneration+=TFarly*4+TBangus*1+TStedfustus*1-TAnemia*1
    Regeneration+=FighterRaces[Race][7]+FighterWeapons[Weapon][7]+FighterLefts[Left][7]
    HealingReceptivity=2*(ERodnus+TRodnus)+TSpiritus+ESpiritus
    Spirit=_f_ToomeriaToSpirit(TToomeria)+_f_SplashToSpirit(TSplash)+_f_OldSplashToSpirit(TSplashOld)+_f_CratoToSpirit(TCrato)+_f_SpleishaToSpirit(TSpleisha)+_f_OldSplashToSpirit(TSpleishaOld)+9*TSpiritus
    Spirit+=FighterRaces[Race][8]+FighterWeapons[Weapon][8]+FighterLefts[Left][8]
    SpiritRegen=_f_RespinToSpiritRegen(TRespin)+TChampReg*20
    if Subclass==1: SpiritRegen+=5
    if Subclass==3: SpiritRegen=25
    SpiritRegen+=FighterRaces[Race][9]+FighterWeapons[Weapon][9]+FighterLefts[Left][9]
    if Subclass==3: SpiritRegen=25
    BaseShieldstoneDrain=1066
    if THeen<0: THeen=0
    if Subclass==3:
        BaseShieldstoneDrain=333
        if THeen<25: SD=BaseShieldstoneDrain-(134*THeen)/24
        else: SD=(196*25)/THeen
    else:
        if THeen<50: SD=BaseShieldstoneDrain-(436*THeen)/49
        else: SD=(628*50)/THeen
    ShieldstoneDrain=round(SD)
    Offense=Accuracy+(3*MaxDamage+MinDamage)/4
    if Offense<200: Offense=200
    BalanceCost=_f_RoundDown((5/3)*Offense)
    GossSpiritCost=0
    if 93<=Weapon<=98: GossSpiritCost=GossDamage/5+(GossAccuracy*7)/80
    SwingsFromFull=Balance/BalanceCost if BalanceCost>0 else 0
    BalancePerTick=Regen/6
    return {
        "Accuracy":Accuracy, "ShowVal":ShowVal,
        "Atkus":_f_AccuracyToAtkus(ShowVal),
        "MinDamage":MinDamage, "MaxDamage":MaxDamage,
        "ShowValMin":ShowValMin, "ShowValMax":ShowValMax, "ShowValAvg":ShowValAvg,
        "UMinDamage":UMinDamage, "UMaxDamage":UMaxDamage,
        "Balance":Balance, "ShowValBalance":ShowValBalance,
        "Balthus":_f_BalanceToBalthus(ShowValBalance),
        "Regen":Regen, "Regia":_f_RegenToRegia(Regen),
        "Health":Health, "Histia":_f_HealthToHistia(Health),
        "Defense":Defense, "ShowValDef":ShowValDef,
        "Detha":_f_DefenseToDetha(ShowValDef),
        "Regeneration":Regeneration, "Troilus":_f_RegenerationToTroilus(Regeneration),
        "HealingReceptivity":HealingReceptivity,
        "Spirit":Spirit, "SpiritRegen":SpiritRegen,
        "ShieldstoneDrain":ShieldstoneDrain,
        "BalanceCost":BalanceCost,
        "SwingsFromFullBalance":SwingsFromFull,
        "BalancePerTick":BalancePerTick,
        "Chan":Chan, "GossSpiritCost":GossSpiritCost,
    }

fighter_vars = {}
f_frame_top = ttk.Frame(frame_fighter)
f_frame_top.pack(fill="both", expand=True, padx=5, pady=5)
f_frame_top.columnconfigure(0, weight=0)
f_frame_top.columnconfigure(1, weight=0)
f_frame_top.columnconfigure(2, weight=1)
f_frame_top.rowconfigure(0, weight=1)

f_frame_left = ttk.LabelFrame(f_frame_top, text="Core Ranks")
f_frame_left.grid(row=0, column=0, sticky="ns", padx=5, pady=2)

f_mid_col = ttk.Frame(f_frame_top)
f_mid_col.grid(row=0, column=1, sticky="ns", padx=5, pady=2)
f_frame_mid = ttk.LabelFrame(f_mid_col, text="Subclass / Weapons")
f_frame_mid.pack(fill="x", padx=0, pady=(0,4))
f_frame_right = ttk.LabelFrame(f_mid_col, text="Subclass Ranks")
f_frame_right.pack(fill="x", padx=0)

f_results_frame = ttk.LabelFrame(f_frame_top, text="Results")
f_results_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=2)

_f_row = 0
def _f_add_et(frame, row, label, keyE, keyT):
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
    vE = tk.StringVar(value="0"); vT = tk.StringVar(value="0")
    fighter_vars[keyE]=vE; fighter_vars[keyT]=vT
    ttk.Label(frame, text="E").grid(row=row, column=1)
    ttk.Entry(frame, width=5, textvariable=vE).grid(row=row, column=2)
    ttk.Label(frame, text="T").grid(row=row, column=3)
    ttk.Entry(frame, width=5, textvariable=vT).grid(row=row, column=4)

for _fl, _fkE, _fkT in [
    ("Atkus","EAtkus","TAtkus"), ("Darkus","EDarkus","TDarkus"),
    ("Balthus","EBalthus","TBalthus"), ("Regia","ERegia","TRegia"),
    ("Histia","EHistia","THistia"), ("Detha","EDetha","TDetha"),
    ("Troilus","ETroilus","TTroilus"), ("Rodnus","ERodnus","TRodnus"),
    ("Spiritus","ESpiritus","TSpiritus"),
]:
    _f_add_et(f_frame_left, _f_row, _fl, _fkE, _fkT)
    _f_row += 1

for _fl, _fk in [
    ("Evus","TEvus"), ("Swengus","TSwengus"), ("Bodrus","TBodrus"),
    ("Hardia","THardia"), ("Farly","TFarly"), ("Knox","TKnox"),
    ("Angilsa","TAngilsa"), ("Aktur","TAktur"), ("Atkia","TAtkia"),
    ("Darktur","TDarktur"), ("Forvyola","TForvyola"),
    ("Bangus","TBangus"), ("Erthron","TErthron"),
    ("ErthronNew","TErthronNew"), ("Stedfustus","TStedfustus"),
    ("Anemia","TAnemia"),
]:
    ttk.Label(f_frame_left, text=_fl).grid(row=_f_row, column=0, sticky="w")
    _fv = tk.StringVar(value="0"); fighter_vars[_fk]=_fv
    ttk.Entry(f_frame_left, width=5, textvariable=_fv).grid(row=_f_row, column=2)
    _f_row += 1

_SUBCLASS_NAMES = ["No Subclass", "Champion", "Ranger", "Bloodmage"]
_SUBCLASS_INT = {"No Subclass":0, "Champion":1, "Ranger":2, "Bloodmage":3}
f_subclass_var = tk.StringVar(value="No Subclass")
ttk.Label(f_frame_mid, text="Subclass").grid(row=0, column=0, sticky="w")
ttk.Combobox(f_frame_mid, textvariable=f_subclass_var, values=_SUBCLASS_NAMES, state="readonly", width=14).grid(row=0, column=1)
f_race_var = tk.StringVar(value=FighterRaceNames[0])
ttk.Label(f_frame_mid, text="Race").grid(row=1, column=0, sticky="w")
ttk.Combobox(f_frame_mid, textvariable=f_race_var, values=FighterRaceNames, state="readonly", width=18).grid(row=1, column=1)
f_weapon_var = tk.StringVar(value=FighterWeaponNames[0])
ttk.Label(f_frame_mid, text="Weapon").grid(row=2, column=0, sticky="w")
ttk.Combobox(f_frame_mid, textvariable=f_weapon_var, values=list(FighterWeaponNames.values()), state="readonly", width=20).grid(row=2, column=1)
f_left_var = tk.StringVar(value=FighterLeftNames[0])
ttk.Label(f_frame_mid, text="Left Hand").grid(row=3, column=0, sticky="w")
ttk.Combobox(f_frame_mid, textvariable=f_left_var, values=list(FighterLeftNames.values()), state="readonly", width=20).grid(row=3, column=1)
f_shoulder_var = tk.StringVar(value=FighterShoulderNames[0])
ttk.Label(f_frame_mid, text="Shoulder").grid(row=4, column=0, sticky="w")
ttk.Combobox(f_frame_mid, textvariable=f_shoulder_var, values=list(FighterShoulderNames.values()), state="readonly", width=20).grid(row=4, column=1)
f_fps_var = tk.StringVar(value="5")
ttk.Label(f_frame_mid, text="FPS").grid(row=5, column=0, sticky="w")
ttk.Entry(f_frame_mid, width=5, textvariable=f_fps_var).grid(row=5, column=1)
f_labrys_var = tk.StringVar(value="1")
ttk.Label(f_frame_mid, text="Labrys Targets").grid(row=6, column=0, sticky="w")
ttk.Entry(f_frame_mid, width=5, textvariable=f_labrys_var).grid(row=6, column=1)

_f_row2 = 0
for _fl, _fk in [
    ("Fell","TFell"), ("Gossamer","TGoss"),
    ("Heen","THeen"), ("Crato","TCrato"),
    ("Spleisha","TSpleisha"), ("SpleishaOld","TSpleishaOld"), ("BB","TBB"),
]:
    ttk.Label(f_frame_right, text=_fl).grid(row=_f_row2, column=0, sticky="w")
    _fv = tk.StringVar(value="0"); fighter_vars[_fk]=_fv
    ttk.Entry(f_frame_right, width=5, textvariable=_fv).grid(row=_f_row2, column=1)
    _f_row2 += 1

f_sub_champ = ttk.LabelFrame(f_frame_right, text="Champion")
f_sub_ranger = ttk.LabelFrame(f_frame_right, text="Ranger")
f_sub_blood = ttk.LabelFrame(f_frame_right, text="Bloodmage")

_sub_champ_widgets = []
for _fl, _fk in [
    ("Channel","TChan"), ("Atkite","TAtkite"), ("Darkite","TDarkite"),
    ("Balthite","TBalthite"), ("Dethite","TDethite"),
    ("Toomeria","TToomeria"), ("ChampReg","TChampReg"),
    ("Cloak","TCloak"), ("Girdle","TGirdle"),
]:
    _sub_champ_widgets.append((_fl, _fk))
_sub_ranger_widgets = []
for _fl, _fk in [
    ("Splash","TSplash"), ("SplashOld","TSplashOld"),
    ("Respin","TRespin"), ("Duvin","TDuvin"), ("Tracking","TTracking"),
]:
    _sub_ranger_widgets.append((_fl, _fk))
_sub_blood_widgets = []
for _fl, _fk in [
    ("Cryptus","TCryptus"), ("Disabla","TDisabla"),
    ("Dantus","TDantus"), ("Aneurus","TAneurus"), ("Posuhm","TPosuhm"),
]:
    _sub_blood_widgets.append((_fl, _fk))

def _f_build_sub_frame(frame, widgets):
    for child in frame.winfo_children():
        child.destroy()
    for i, (label, key) in enumerate(widgets):
        ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w")
        if key not in fighter_vars:
            fighter_vars[key] = tk.StringVar(value="0")
        ttk.Entry(frame, width=5, textvariable=fighter_vars[key]).grid(row=i, column=1)

_f_build_sub_frame(f_sub_champ, _sub_champ_widgets)
_f_build_sub_frame(f_sub_ranger, _sub_ranger_widgets)
_f_build_sub_frame(f_sub_blood, _sub_blood_widgets)

def _f_update_subclassVisibility(*args):
    name = f_subclass_var.get()
    sc = _SUBCLASS_INT.get(name, 0)
    f_sub_champ.grid_forget()
    f_sub_ranger.grid_forget()
    f_sub_blood.grid_forget()
    if sc == 1:
        f_sub_champ.grid(row=_f_row2, column=0, columnspan=2, sticky="w", pady=(5,0))
    elif sc == 2:
        f_sub_ranger.grid(row=_f_row2, column=0, columnspan=2, sticky="w", pady=(5,0))
    elif sc == 3:
        f_sub_blood.grid(row=_f_row2, column=0, columnspan=2, sticky="w", pady=(5,0))

f_subclass_var.trace_add("write", _f_update_subclassVisibility)
_f_update_subclassVisibility()

f_results_text = tk.Text(f_results_frame, width=60, height=30)
f_results_text.pack(fill="both", expand=True, padx=5, pady=5)

def _f_on_calculate():
    params = {}
    for k, v in fighter_vars.items():
        try: params[k] = float(v.get())
        except ValueError: params[k] = 0.0
    params["Subclass"] = _SUBCLASS_INT.get(f_subclass_var.get(), 0)
    params["FPS"] = float(f_fps_var.get() or 5)
    params["LabrysTargets"] = int(f_labrys_var.get() or 1)
    params["Race"] = FighterRaceNames.index(f_race_var.get())
    params["Weapon"] = next(k for k,v in FighterWeaponNames.items() if v==f_weapon_var.get())
    params["Left"] = next(k for k,v in FighterLeftNames.items() if v==f_left_var.get())
    params["Shoulder"] = next(k for k,v in FighterShoulderNames.items() if v==f_shoulder_var.get())
    r = _f_compute_fighter(params)
    f_results_text.delete("1.0", tk.END)
    t = f_results_text.insert
    t(tk.END, f"{r['Accuracy']:.0f} Accuracy ({r['Atkus']:.2f} Atkus)\n")
    t(tk.END, f"{r['ShowValMin']:.0f}-{r['ShowValMax']:.0f} Damage (Avg {r['ShowValAvg']:.1f})\n")
    t(tk.END, f"{_f_DamageToDarkus(r['ShowValAvg']):.2f} Darkus (avg)\n")
    t(tk.END, f"{r['Balance']:.0f} Balance ({r['Balthus']:.2f} Balthus)\n")
    t(tk.END, f"{r['Regen']:.0f} Regen ({r['Regia']:.2f} Regia)\n")
    t(tk.END, f"{r['Health']:.0f} Health ({r['Histia']:.2f} Histia)\n")
    t(tk.END, f"{r['ShowValDef']:.0f} Defense ({r['Detha']:.2f} Detha)\n")
    t(tk.END, f"{r['Regeneration']:.0f} Health Regen ({r['Troilus']:.2f} Troilus)\n")
    t(tk.END, f"{r['HealingReceptivity']:.0f} Healing Receptivity\n")
    t(tk.END, f"{r['Spirit']:.0f} Spirit\n")
    t(tk.END, f"{r['SpiritRegen']:.0f} Spirit Regen\n")
    t(tk.END, f"{r['ShieldstoneDrain']} Shieldstone drain/frame\n")
    t(tk.END, f"\n{r['BalanceCost']:.0f} Balance per swing\n")
    t(tk.END, f"{r['SwingsFromFullBalance']:.2f} Swings from full balance\n")
    t(tk.END, f"{_f_Round(r['BalancePerTick'])} Balance recovered per frame\n")
    t(tk.END, f"{r['Chan']:.0f} Channel Master\n")

ttk.Button(f_mid_col, text="Calculate", command=_f_on_calculate).pack(pady=5)

# ----------------------------------------------------------------------
# HEALER CALCULATOR TAB
# ----------------------------------------------------------------------

H_DEF_HEALSPEED=0; H_DEF_SPIRIT=1; H_DEF_SPIRITREG=2; H_DEF_HEALTH=3
H_DEF_RAISING=4; H_DEF_HEALEFF=5; H_DEF_HEALRANGE=6; H_DEF_REGEN=7
H_DEF_HEALRECEPT=8; H_DEF_BODY=9; H_DEF_GROUPHEAL=10; H_TOTALSTATS=11

h_races = [
    [700,800,600,3000,0,0,0,100,0,0,0],
    [700,500,500,3300,0,0,0,100,0,0,0],
    [700,700,500,1500,0,0,0,100,0,0,0],
    [700,900,700,3000,0,0,0,100,0,0,0],
    [600,700,500,3600,0,0,0,100,0,0,0],
    [700,800,600,2400,0,0,0,100,0,0,0],
    [700,1000,700,3900,0,0,0,300,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0],
]
h_race_names=["Human","Dwarf","Fen","Halfling","Zo","Sylvan","Thoom","0-Stat"]

h_trainers = [[0]*H_TOTALSTATS for _ in range(23)]
h_trainers[0]=[33,0,0,0,0,0,0,0,0,0,0]
h_trainers[1]=[0,0,0,120,0,0,0,0,0,0,0]
h_trainers[2]=[0,29,0,0,0,0,0,0,0,0,0]
h_trainers[3]=[0,0,24,0,0,0,0,0,0,0,0]
h_trainers[4]=[0,0,0,0,100,0,0,0,0,0,0]
h_trainers[5]=[0,0,0,0,0,100,0,0,0,0,0]
h_trainers[6]=[0,0,0,0,0,0,1,0,0,0,0]
h_trainers[7]=[0,0,0,0,0,0,0,6,0,0,0]
h_trainers[8]=[0,0,0,0,0,0,0,0,1,0,0]
h_trainers[9]=[11,8,9,30,6,6,0,0,0,0,0]
h_trainers[10]=[10,7,5,12,0,0,0,0,1,0,0]
h_trainers[11]=[11,9,0,21,0,0,0,0,1,0,0]
h_trainers[12]=[17,0,12,0,0,0,0,0,0,0,0]
h_trainers[13]=[11,0,16,0,0,0,0,0,0,0,0]
h_trainers[14]=[8,0,18,0,0,0,0,0,0,0,0]
h_trainers[15]=[7,0,20,0,0,0,0,0,0,0,0]
h_trainers[16]=[4,0,21,0,0,0,0,0,0,0,0]
h_trainers[17]=[0,0,0,24,0,0,0,0,0,1,0]
h_trainers[18]=[0,0,0,21,0,0,0,0,0,1,0]
h_trainers[19]=[0,0,0,36,0,0,0,0,2,0,0]
h_trainers[20]=[0,0,0,0,0,0,0,0,2,0,0]
h_trainers[21]=[0,0,0,111,0,0,0,0,0,0,0]
h_trainers[22]=[0,0,0,0,0,0,0,0,0,0,1]

h_trainer_names=[
    "Faustus","Higgrus","Sespus","Respia","Horus","Awaria",
    "Proximus","Troilus","Eff. Sprite","Eva","Sprite","Spirtus",
    "Anan","AnDeux","AnTrix","AnQuart","AnSept","Bodrus",
    "Hardia","Rodnus","Eff. Rodnus","Histia","Radium",
]
h_trainer_is_et=[1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,0,0,0,0,0,1]

def h_round_off(val, precise):
    return math.floor(val) if precise else val

def h_self_heal_value(stats, sylph, precise):
    base=h_round_off(stats[H_DEF_HEALSPEED]/100, precise)
    rodding=h_round_off((15*stats[H_DEF_HEALRECEPT])/100, precise)
    eff=h_round_off(stats[H_DEF_HEALEFF]/100, precise)
    eff=h_round_off(eff*31/100, precise)
    freeheal=rodding+eff
    if freeheal>base: freeheal=base
    healamt=(base+freeheal)*10
    return h_round_off(sylph*healamt, precise)

def h_self_heal_cost(stats, precise):
    hv=h_round_off(stats[H_DEF_HEALSPEED]/100, precise)
    return h_round_off(hv*20, precise)

def h_heal_other_rate(stats, other, eff_heal, precise):
    base=stats[H_DEF_HEALSPEED]/100
    rodding=other[H_DEF_HEALRECEPT]/4
    rate=h_round_off(base,precise)+h_round_off(rodding,precise)
    return h_round_off(rate*eff_heal, precise)

def h_heal_other_sp_drain(stats, eff_sp, precise):
    base=stats[H_DEF_HEALSPEED]/100
    base=h_round_off(base,precise)
    return h_round_off(base*eff_sp, precise)

def h_heal_other_hp_drain(stats, other, eff_hp, precise):
    base=stats[H_DEF_HEALSPEED]/100
    rodding=other[H_DEF_HEALRECEPT]/4
    rate=h_round_off(base,precise)+h_round_off(rodding,precise)
    rate=h_round_off(rate/2,precise)
    return h_round_off(rate*eff_hp, precise)

def h_burst_sp_cost(stats, precise):
    sp=stats[H_DEF_SPIRIT]
    if precise:
        chunk=math.floor(stats[H_DEF_HEALSPEED]/100)*4
        if chunk>0: sp=chunk*math.floor(sp/chunk)
    return sp

def h_burst_other_value(stats, other, eff_heal, eff_sp, precise):
    base=stats[H_DEF_HEALSPEED]/100
    rodding=other[H_DEF_HEALRECEPT]/4
    rate=h_round_off(base,precise)+h_round_off(rodding,precise)
    rate=h_round_off(rate*eff_heal,precise)
    sprate=stats[H_DEF_HEALSPEED]/100
    sprate=h_round_off(sprate,precise)
    sprate=h_round_off(sprate*eff_sp,precise)
    spused=h_burst_sp_cost(stats,precise)
    if sprate==0: return 0
    return h_round_off(spused*(rate/sprate)/4,precise)

def h_burst_other_hp_cost(stats, other, eff_heal, eff_hp, eff_sp, precise):
    hpbase=stats[H_DEF_HEALSPEED]/100
    hprodding=other[H_DEF_HEALRECEPT]/4
    hprate=h_round_off(hpbase,precise)+h_round_off(hprodding,precise)
    healrate=h_round_off(hprate*eff_heal,precise)
    hprate=h_round_off(hprate/2,precise)
    hprate=h_round_off(hprate*eff_hp,precise)
    sprate=stats[H_DEF_HEALSPEED]/100
    sprate=h_round_off(sprate,precise)
    sprate=h_round_off(sprate*eff_sp,precise)
    spused=h_burst_sp_cost(stats,precise)
    if sprate==0 or healrate==0: return 0
    hpamt=h_round_off(spused*(healrate/sprate)/4,precise)
    hpamt=hpamt*(hprate/healrate)
    return h_round_off(hpamt,precise)*2

def h_group_rate_individual(stats, other, heal_mult, num_targets, precise):
    if heal_mult<1: heal_mult=1
    base=stats[H_DEF_HEALSPEED]
    base_fract=base%100
    base=h_round_off(base/100,precise)-10
    base_fract=h_round_off(base_fract*3/100,precise)
    radium=stats[H_DEF_GROUPHEAL]*2+base_fract
    radium=h_round_off(radium/3,precise)
    rodding=other[H_DEF_HEALRECEPT]/4
    rodding=h_round_off(rodding,precise)
    rodding=h_round_off(rodding/num_targets,precise)
    rate=base+radium
    rate=h_round_off(rate/num_targets,precise)
    cap=stats[H_DEF_HEALSPEED]/100
    cap=h_round_off(cap,precise)
    cap=h_round_off(cap*(5/12),precise)
    if rate>cap: rate=cap
    rate=rate+rodding
    return h_round_off(rate*heal_mult,precise)

def h_group_sp_drain(stats, other, num_targets, precise):
    base=stats[H_DEF_HEALSPEED]
    base_fract=base%100
    b=h_round_off(base/100,precise)-10
    bf=h_round_off(base_fract*3/100,precise)
    rh=stats[H_DEF_GROUPHEAL]*2+bf
    rh=h_round_off(rh/3,precise)
    rate=b+rh
    rate=h_round_off(rate/num_targets,precise)
    cap=stats[H_DEF_HEALSPEED]/100
    cap=h_round_off(cap,precise)
    cap=h_round_off(cap*(5/12),precise)
    if rate>cap: rate=cap
    total=rate*num_targets
    rateBase=h_round_off(base/100,precise)-10
    rateBase=h_round_off(rateBase/num_targets,precise)
    rateBase=(rateBase*num_targets)+10
    if total<rateBase: total=rateBase
    return total

def h_cad_range(stats, precise):
    r=stats[H_DEF_HEALRANGE]+35
    return h_round_off(0.815*r,precise)-32

def h_group_range(stats, precise):
    cad=h_round_off(0.38*stats[H_DEF_HEALRANGE],precise)
    rad=h_round_off(0.7*stats[H_DEF_GROUPHEAL],precise)
    return 35+cad+rad-32

def h_share_heal_eff(cls, clan, sharing):
    if cls!=2:
        if sharing==0:
            return 0.85 if clan==0 else 0.96
        return 1.0
    return 1.75

def h_share_sp_eff(cls, clan, sharing):
    if cls!=2:
        if sharing==0:
            return 1.5 if clan==0 else 1.125
        return 1.0
    return 1.0

def h_share_hp_eff(cls, clan, sharing):
    return h_share_sp_eff(cls, clan, sharing)

h_trainer_vars={}

h_top=ttk.Frame(frame_healer)
h_top.pack(fill="both", expand=True, padx=5, pady=5)
h_top.columnconfigure(0, weight=0)
h_top.columnconfigure(1, weight=0)
h_top.columnconfigure(2, weight=1)
h_top.rowconfigure(0, weight=1)

h_frame_left=ttk.LabelFrame(h_top, text="Healer Stats")
h_frame_left.grid(row=0, column=0, sticky="ns", padx=5, pady=2)

h_mid_col=ttk.Frame(h_top)
h_mid_col.grid(row=0, column=1, sticky="ns", padx=5, pady=2)
h_frame_target=ttk.LabelFrame(h_mid_col, text="Target Settings")
h_frame_target.pack(fill="x", padx=0, pady=(0,4))
h_frame_combo=ttk.LabelFrame(h_mid_col, text="Healer Ranks")
h_frame_combo.pack(fill="x", padx=0)

h_results_frame=ttk.LabelFrame(h_top, text="Results")
h_results_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=2)

def h_add_et(frame, row, label, keyE, keyT):
    ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
    vE=tk.StringVar(value="0"); vT=tk.StringVar(value="0")
    h_trainer_vars[keyE]=vE; h_trainer_vars[keyT]=vT
    ttk.Label(frame, text="E").grid(row=row, column=1)
    ttk.Entry(frame, width=5, textvariable=vE).grid(row=row, column=2)
    ttk.Label(frame, text="T").grid(row=row, column=3)
    ttk.Entry(frame, width=5, textvariable=vT).grid(row=row, column=4)

_hrow=0
for _hn, _hi in [
    ("Faustus",0),("Higgrus",1),("Sespus",2),("Respia",3),
    ("Horus",4),("Awaria",5),("Proximus",6),("Troilus",7),
]:
    if h_trainer_is_et[_hi]:
        h_add_et(h_frame_left, _hrow, _hn, f"HE{_hi}", f"HT{_hi}")
    else:
        ttk.Label(h_frame_left, text=_hn).grid(row=_hrow, column=0, sticky="w")
        _hv=tk.StringVar(value="0"); h_trainer_vars[f"HT{_hi}"]=_hv
        ttk.Entry(h_frame_left, width=5, textvariable=_hv).grid(row=_hrow, column=2)
    _hrow+=1

h_add_et(h_frame_left, _hrow, "Eff. Sprite", "HE8", "HT8"); _hrow+=1

for _hn, _hi in [
    ("Bodrus",17),("Hardia",18),("Rodnus",19),("Histia",21),
]:
    ttk.Label(h_frame_left, text=_hn).grid(row=_hrow, column=0, sticky="w")
    _hv=tk.StringVar(value="0"); h_trainer_vars[f"HT{_hi}"]=_hv
    ttk.Entry(h_frame_left, width=5, textvariable=_hv).grid(row=_hrow, column=2)
    _hrow+=1

h_add_et(h_frame_left, _hrow, "Radium", "HE22", "HT22"); _hrow+=1

h_target_cls_var=tk.StringVar(value="Healer")
h_target_share_var=tk.StringVar(value="Sharing")
h_target_clan_var=tk.StringVar(value="In Clan")
h_sylph_var=tk.StringVar(value="Nothing")
h_precise_var=tk.BooleanVar(value=False)

ttk.Label(h_frame_target, text="Target Class").grid(row=0, column=0, sticky="w")
ttk.Combobox(h_frame_target, textvariable=h_target_cls_var, values=["Healer","Non-Healer"], state="readonly", width=12).grid(row=0, column=1)
ttk.Label(h_frame_target, text="Sharing").grid(row=1, column=0, sticky="w")
ttk.Combobox(h_frame_target, textvariable=h_target_share_var, values=["Sharing","No Share"], state="readonly", width=12).grid(row=1, column=1)
ttk.Label(h_frame_target, text="Clan").grid(row=2, column=0, sticky="w")
ttk.Combobox(h_frame_target, textvariable=h_target_clan_var, values=["In Clan","Not In Clan"], state="readonly", width=12).grid(row=2, column=1)
ttk.Label(h_frame_target, text="Target Race").grid(row=3, column=0, sticky="w")
h_target_race_var=tk.StringVar(value="Human")
ttk.Combobox(h_frame_target, textvariable=h_target_race_var, values=h_race_names[:7], state="readonly", width=12).grid(row=3, column=1)
ttk.Label(h_frame_target, text="Sylphstone").grid(row=4, column=0, sticky="w")
ttk.Combobox(h_frame_target, textvariable=h_sylph_var, values=["Nothing","75% Efficiency","50% Efficiency"], state="readonly", width=14).grid(row=4, column=1)
ttk.Checkbutton(h_frame_target, text="Precise Mode", variable=h_precise_var).grid(row=5, column=0, columnspan=2, sticky="w")

_hrow2=0
for _hn, _hi in [
    ("Eva",9),("Sprite",10),("Spirtus",11),
    ("Anan",12),("AnDeux",13),("AnTrix",14),("AnQuart",15),("AnSept",16),
]:
    ttk.Label(h_frame_combo, text=_hn).grid(row=_hrow2, column=0, sticky="w")
    _hv=tk.StringVar(value="0"); h_trainer_vars[f"HT{_hi}"]=_hv
    ttk.Entry(h_frame_combo, width=5, textvariable=_hv).grid(row=_hrow2, column=1)
    _hrow2+=1

h_results_text=tk.Text(h_results_frame, width=65, height=30)
h_results_text.pack(fill="both", expand=True, padx=5, pady=5)

def h_get_stat_array():
    s=[0.0]*H_TOTALSTATS
    for i in range(23):
        te_key=f"HE{i}"; tt_key=f"HT{i}"
        e_val=0.0; t_val=0.0
        if te_key in h_trainer_vars:
            try: e_val=float(h_trainer_vars[te_key].get())
            except: pass
        if tt_key in h_trainer_vars:
            try: t_val=float(h_trainer_vars[tt_key].get())
            except: pass
        if h_trainer_is_et[i]:
            total=e_val+t_val
        else:
            total=t_val
        for st in range(H_TOTALSTATS):
            s[st]+=h_trainers[i][st]*total
    return s

def h_eff_ranks(stats):
    er=0.0
    er+=float(h_trainer_vars.get("HT0",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT1",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT2",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT3",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT4",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT5",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT6",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT7",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT22",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT21",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HE8",tk.StringVar(value="0")).get() or 0)*0.48387
    er+=float(h_trainer_vars.get("HT9",tk.StringVar(value="0")).get() or 0)*1.3542
    er+=float(h_trainer_vars.get("HT10",tk.StringVar(value="0")).get() or 0)*1.3366
    er+=float(h_trainer_vars.get("HT11",tk.StringVar(value="0")).get() or 0)*1.3025
    er+=float(h_trainer_vars.get("HT12",tk.StringVar(value="0")).get() or 0)*1.0152
    er+=float(h_trainer_vars.get("HT13",tk.StringVar(value="0")).get() or 0)*1.0
    er+=float(h_trainer_vars.get("HT14",tk.StringVar(value="0")).get() or 0)*0.9924
    er+=float(h_trainer_vars.get("HT15",tk.StringVar(value="0")).get() or 0)*1.0455
    er+=float(h_trainer_vars.get("HT16",tk.StringVar(value="0")).get() or 0)*0.9962
    tb=float(h_trainer_vars.get("HT17",tk.StringVar(value="0")).get() or 0)
    th=float(h_trainer_vars.get("HT18",tk.StringVar(value="0")).get() or 0)
    er+=tb
    bad=max(min(100-tb,th),0)
    er+=bad*0.81748367
    er+=max(th-bad,0)
    er+=float(h_trainer_vars.get("HT19",tk.StringVar(value="0")).get() or 0)
    er+=float(h_trainer_vars.get("HT20",tk.StringVar(value="0")).get() or 0)
    return er

def h_on_calculate():
    precise=h_precise_var.get()
    sylph_map={"Nothing":0.0,"75% Efficiency":0.75,"50% Efficiency":0.5}
    sylph=sylph_map.get(h_sylph_var.get(),0.0)
    cls_map={"Healer":2,"Non-Healer":1}
    tcls=cls_map.get(h_target_cls_var.get(),2)
    share_map={"Sharing":1,"No Share":0}
    sharing=share_map.get(h_target_share_var.get(),1)
    clan_map={"In Clan":1,"Not In Clan":0}
    clan=clan_map.get(h_target_clan_var.get(),1)
    target_race_idx=h_race_names[:7].index(h_target_race_var.get()) if h_target_race_var.get() in h_race_names[:7] else 0

    stats=h_get_stat_array()
    target=[0.0]*H_TOTALSTATS
    target[:7]=list(h_races[target_race_idx][:7])
    target[H_DEF_HEALTH]+=float(h_trainer_vars.get("HT1",tk.StringVar(value="0")).get() or 0)*120
    target[H_DEF_HEALTH]+=float(h_trainer_vars.get("HT17",tk.StringVar(value="0")).get() or 0)*24
    target[H_DEF_HEALTH]+=float(h_trainer_vars.get("HT18",tk.StringVar(value="0")).get() or 0)*21
    target[H_DEF_HEALTH]+=float(h_trainer_vars.get("HT19",tk.StringVar(value="0")).get() or 0)*36
    target[H_DEF_HEALTH]+=float(h_trainer_vars.get("HT21",tk.StringVar(value="0")).get() or 0)*111
    target[H_DEF_HEALRECEPT]+=float(h_trainer_vars.get("HT19",tk.StringVar(value="0")).get() or 0)*2
    target[H_DEF_HEALRECEPT]+=float(h_trainer_vars.get("HE20",tk.StringVar(value="0")).get() or 0)*2
    target[H_DEF_HEALRECEPT]+=float(h_trainer_vars.get("HT10",tk.StringVar(value="0")).get() or 0)*1
    target[H_DEF_HEALRECEPT]+=float(h_trainer_vars.get("HT11",tk.StringVar(value="0")).get() or 0)*1
    target[H_DEF_BODY]+=float(h_trainer_vars.get("HT17",tk.StringVar(value="0")).get() or 0)*1
    target[H_DEF_BODY]+=float(h_trainer_vars.get("HT18",tk.StringVar(value="0")).get() or 0)*1

    eff_heal=h_share_heal_eff(tcls,clan,sharing)
    eff_sp=h_share_sp_eff(tcls,clan,sharing)
    eff_hp=h_share_hp_eff(tcls,clan,sharing)

    hs=stats[H_DEF_HEALSPEED]; sp=stats[H_DEF_SPIRIT]; sr=stats[H_DEF_SPIRITREG]
    hp=stats[H_DEF_HEALTH]; rg=stats[H_DEF_REGEN]
    hr=stats[H_DEF_HEALRANGE]; he=stats[H_DEF_HEALEFF]
    hrec=stats[H_DEF_HEALRECEPT]; raising=stats[H_DEF_RAISING]
    gh=stats[H_DEF_GROUPHEAL]; body=stats[H_DEF_BODY]

    shv=h_self_heal_value(stats,sylph,precise)
    shc=h_self_heal_cost(stats,precise)
    sprf=h_round_off(sr/100,precise)
    hprf=h_round_off(rg/100,precise)

    hor=h_heal_other_rate(stats,target,eff_heal,precise)
    hosd=h_heal_other_sp_drain(stats,eff_sp,precise)
    hohd=h_heal_other_hp_drain(stats,target,eff_hp,precise)

    bsv=h_burst_other_value(stats,target,eff_heal,eff_sp,precise)
    bsc=h_burst_sp_cost(stats,precise)
    bhpc=h_burst_other_hp_cost(stats,target,eff_heal,eff_hp,eff_sp,precise)

    cad=h_cad_range(stats,precise)
    gr=h_group_range(stats,precise)
    ghri=h_group_rate_individual(stats,target,1.0,5,precise)
    ghsd=h_group_sp_drain(stats,target,5,precise)

    sp_sec=sprf*5
    sp_loss_sec=hosd*5 if hor>0 else 0
    sp_net_sec=sp_sec-sp_loss_sec

    t=h_results_text
    t.delete("1.0",tk.END)
    t.insert(tk.END,"--- Healer Stats ---\n")
    t.insert(tk.END, f"Healing Speed: {hs:.0f}\n")
    t.insert(tk.END, f"Spirit: {sp:.0f}\n")
    t.insert(tk.END, f"Spirit Regen: {sr:.0f} ({sprf:.2f}/frame, {sp_sec:.1f}/sec)\n")
    t.insert(tk.END, f"Health: {hp:.0f}\n")
    t.insert(tk.END, f"Health Regen: {rg:.0f} ({hprf:.2f}/frame)\n")
    t.insert(tk.END, f"Heal Efficiency: {he:.0f}\n")
    t.insert(tk.END, f"Heal Receptivity: {hrec:.0f}\n")
    t.insert(tk.END, f"Heal Range: {hr:.0f}\n")
    t.insert(tk.END, f"Reviving: {raising:.0f}\n")
    t.insert(tk.END, f"Group Heal: {gh:.0f}\n")
    t.insert(tk.END, f"Body: {body:.0f}\n")
    t.insert(tk.END, f"Eff. Ranks: {h_eff_ranks(stats):.1f}\n")
    t.insert(tk.END,"\n--- Self-Heal (Moonstone Pulse) ---\n")
    t.insert(tk.END, f"Heal/Pulse: {shv:.0f} HP\n")
    t.insert(tk.END, f"SP Cost/Pulse: {shc:.0f}\n")
    if shc>0: t.insert(tk.END, f"HP per SP: {shv/shc:.2f}\n")
    t.insert(tk.END, f"SP Regen: +{sp_sec:.1f}/sec\n")
    t.insert(tk.END,"\n--- Healing Others (Continuous) ---\n")
    t.insert(tk.END, f"Heal Rate: {hor:.1f}/sec (eff {eff_heal:.2f}x)\n")
    t.insert(tk.END, f"SP Drain: {hosd:.1f}/sec (eff {eff_sp:.2f}x)\n")
    t.insert(tk.END, f"HP Cost: {hohd:.1f}/sec (eff {eff_hp:.2f}x)\n")
    net_sp=sp_sec-hosd*5 if hor>0 else sp_sec
    t.insert(tk.END, f"SP Net: {net_sp:.1f}/sec\n")
    t.insert(tk.END,"\n--- Burst (Full Staff) ---\n")
    t.insert(tk.END, f"Burst Heal: {bsv:.0f} HP\n")
    t.insert(tk.END, f"Burst SP Cost: {bsc:.0f}\n")
    t.insert(tk.END, f"Burst HP Cost: {bhpc:.0f}\n")
    t.insert(tk.END,"\n--- Group Heal (5 targets) ---\n")
    t.insert(tk.END, f"Per-Target Rate: {ghri:.1f}/sec\n")
    t.insert(tk.END, f"Total Rate: {ghri*5:.1f}/sec\n")
    t.insert(tk.END, f"SP Drain Total: {ghsd:.1f}\n")
    t.insert(tk.END,"\n--- Ranges ---\n")
    t.insert(tk.END, f"Caduceus Range: {cad:.0f} px\n")
    t.insert(tk.END, f"Group Heal Range: {gr:.0f} px\n")

ttk.Button(h_mid_col, text="Calculate", command=h_on_calculate).pack(pady=5)

root.mainloop()
