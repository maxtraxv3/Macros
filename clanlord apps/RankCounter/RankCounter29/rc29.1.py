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
    "almost nothing left to learn about the movements of the": {1:4,2:2,3:2,4:2,5:2},
    "almost nothing left to learn about the ways of the": {1:4,2:2,3:2,4:2,5:2},
    "almost nothing left to learn about the essence of the": {1:4,2:2,3:2,4:2,5:2},

    "a few things to learn about the movements of the": {1:3,2:3,3:3,4:3,5:3},
    "a few things to learn about the ways of the": {1:3,2:3,3:3,4:3,5:3},
    "a few things to learn about the essence of the": {1:3,2:3,3:3,4:3,5:3},

    "more than a few things to learn about the ways of the": {1:7,2:7,3:7,4:7,5:8},
    "more than a few things to learn about the essence of the": {1:7,2:7,3:7,4:7,5:8},

    "some things to learn about the ways of the": {1:12,2:12,3:12,4:12,5:12,6:12,7:9},
    "some things to learn about the essence of the": {1:12,2:12,3:12,4:12,5:12,6:12,7:9},

    "many things to learn about the ways of the": {1:20,2:20,3:20,4:20,5:20,6:20,7:16},
    "many things to learn about the essence of the": {1:20,2:20,3:20,4:20,5:20,6:20,7:16},

    "much to learn about the ways of the": {1:30,2:30,3:30,4:30,5:30,6:30,7:20},
    "much to learn about the essence of the": {1:30,2:30,3:30,4:30,5:30,6:30,7:20},

    "a lot to learn about the ways of the": {1:100,2:30,3:30,4:30,5:30},
    "a lot to learn about the essence of the": {1:100,2:30,3:30,4:30,5:30},

    "a vast amount to learn about the ways of the": {1:100,2:100,3:100,4:100,5:100,6:100},
    "a vast amount to learn about the essence of the": {1:100,2:100,3:100,4:100,5:100,6:100}
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

phrase_to_msgnums = {}
for msg_num, phrase_group, _kills_required in kills_table:
    phrase_to_msgnums.setdefault(phrase_group, []).append(msg_num)

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
# Clan Lord Time Engine
# -----------------------------
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

CL_EPOCH_UNIX = 912470400  # 1998-11-28 00:00:00 UTC
IC_SPEED_MULTIPLIER = 4

IC_SECONDS_PER_DAY = 86400
IC_DAYS_PER_YEAR = 360
IC_DAYS_PER_SEASON = 90
IC_DAYS_PER_WEEK = 7
IC_MOON_CYCLE_DAYS = 28
IC_ZODIAC_SIGN_DAYS = 30
IC_ZODIAC_SIGNS_COUNT = 12

SEASONS = ["Spring", "Summer", "Fall", "Winter"]
WEEKDAYS = ["Sombdi", "Gradi", "Tridi", "Quartidi", "Quintidi", "Sixdi", "Sevdi"]

#placeholder i only i am missing 2 and im not sure of the order yet.
ZODIAC_SIGNS = [
    "Arilon", "Balthus", "Camilon", "Darian",
    "Erilon", "Fenthus", "Gamilon", "Harian",
    "Irilon", "Jenthus", "Kamilon", "Larian",
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


def _to_unix(dt_or_unix) -> int:
    if isinstance(dt_or_unix, (int, float)):
        return int(dt_or_unix)
    if isinstance(dt_or_unix, datetime):
        return int(dt_or_unix.astimezone(timezone.utc).timestamp())
    raise TypeError("real_to_cl expects datetime or unix timestamp")


def real_to_cl(dt_or_unix) -> CLTimeStruct:
    unix_time = _to_unix(dt_or_unix)
    ic_seconds = int((unix_time - CL_EPOCH_UNIX) * IC_SPEED_MULTIPLIER)

    ic_second = ic_seconds % 60
    ic_minute = (ic_seconds // 60) % 60
    ic_hour = (ic_seconds // 3600) % 24

    ic_day = ic_seconds // IC_SECONDS_PER_DAY

    year = ic_day // IC_DAYS_PER_YEAR
    day_of_year = ic_day % IC_DAYS_PER_YEAR
    season_index = day_of_year // IC_DAYS_PER_SEASON
    season_day = day_of_year % IC_DAYS_PER_SEASON
    weekday_index = ic_day % IC_DAYS_PER_WEEK

    lunar_day = ic_day % IC_MOON_CYCLE_DAYS
    zodiac_day = ic_day % IC_ZODIAC_SIGN_DAYS
    zodiac_index = (ic_day // IC_ZODIAC_SIGN_DAYS) % IC_ZODIAC_SIGNS_COUNT

    return CLTimeStruct(
        ic_seconds=ic_seconds,
        ic_day=ic_day,
        ic_hour=ic_hour,
        ic_minute=ic_minute,
        ic_second=ic_second,
        year=year,
        day_of_year=day_of_year,
        season_index=season_index,
        season_day=season_day,
        weekday_index=weekday_index,
        lunar_day=lunar_day,
        zodiac_day=zodiac_day,
        zodiac_index=zodiac_index,
    )


def cl_to_real(ic_day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    ic_seconds = ic_day * IC_SECONDS_PER_DAY + hour * 3600 + minute * 60 + second
    real_seconds = ic_seconds // IC_SPEED_MULTIPLIER
    unix_time = CL_EPOCH_UNIX + real_seconds
    return datetime.fromtimestamp(unix_time, tz=timezone.utc)


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
# ----------------------------------------------------------------------
# ---------------------- CORE PARSING / COUNTS ------------------------
# ----------------------------------------------------------------------


def count_special_lines(texts):
    """
    Extracts all study-related lines and returns:
        special_occ: { trainer_clean: [entry, entry, ...] }
        exclude: set()   (kept for compatibility)

    Each entry contains:
        phrase_group, function, timestamp, kills_left, count, display_label
    """
    import re
    from datetime import datetime

    special_occ = {}
    exclude = set()

    # Timestamp format: 5/10/26 8:35:19a • You have many things...
    ts_re = re.compile(r"^(\d+/\d+/\d+ \d+:\d+:\d+[ap])\s*[•>:-]*\s*(.*)$")

    # Study message regex
    study_re = re.compile(
        r"You have (almost nothing|a few|more than a few|some things|many things|much to learn|a lot to learn|a vast amount)"
        r" to learn about the (movements|ways|essence) of the (.+?)\.",
        re.IGNORECASE
    )

    # Kill message regex
    kill_re = re.compile(
        r"(?:you|you helped)\s+(?:slaughtered|dispatched|killed|vanquished)\s+the\s+(.+?)\.",
        re.IGNORECASE
    )

    # Count kills per creature
    kill_counts = {}
    for content, _ in texts:
        for line in content.splitlines():
            m = kill_re.search(line)
            if m:
                creature = m.group(1).strip().lower()
                kill_counts[creature] = kill_counts.get(creature, 0) + 1

    # MAIN LOOP
    for content, _ in texts:
        for raw_line in content.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            # Extract timestamp + message
            m = ts_re.match(raw_line)
            if not m:
                continue

            ts_raw, msg = m.groups()

            # Convert timestamp
            try:
                timestamp = datetime.strptime(ts_raw, "%m/%d/%y %I:%M:%S%p")
            except Exception:
                timestamp = None

            low = msg.lower()

            # ---------------------------------------------------------
            # Abandon study (this is the ONLY old rule we keep)
            # ---------------------------------------------------------
            if "you abandon your study of the" in low:
                m_ab = re.search(r"you abandon your study of the (.+?)\.", low)
                if m_ab:
                    creature = m_ab.group(1).strip().lower()
                    special_occ.pop(creature, None)
                continue

            # ---------------------------------------------------------
            # Study progression message
            # ---------------------------------------------------------
            m2 = study_re.search(msg)
            if not m2:
                continue

            phrase_group = m2.group(1).lower()
            function     = m2.group(2).lower()
            creature     = m2.group(3).strip().lower()

            trainer_clean = creature

            # Build kills_to_next lookup key
            kt_key = f"{phrase_group} to learn about the {function} of the"

            # Determine kills_left
            kills_done = kill_counts.get(trainer_clean, 0)
            stage_table = kills_to_next.get(kt_key, {})

            if stage_table:
                total_required = sum(stage_table.values())
                kills_left = max(total_required - kills_done, 0)
            else:
                kills_left = None

            # Build display label
            display_label = f"You have {phrase_group} to learn about the {function} of the {creature}."
            if kills_left is not None:
                display_label += f" — {kills_left} kills left"

            # Build entry
            entry = {
                "phrase_group": phrase_group,
                "function": function,
                "timestamp": timestamp,
                "kills_left": kills_left,
                "count": 1,
                "display_label": display_label,
            }

            special_occ.setdefault(trainer_clean, []).append(entry)

    return special_occ, exclude

# -- Coin Scanning -----------------------------------------------------------

def count_coins(texts, character_name, min_time=None):
    skinned_total = 0
    share_total = 0
    events = []

    coin_rx = re.compile(
        r"\*\s*(You|.+?) recover[s]? the (.+?) fur, worth (\d+)c\. Your share is (\d+)c",
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
    # SPECIAL CREATURE PROCESSING (MOST RECENT STAGE)
    # --------------------------------------------------------------
    latest_per_creature = {}

    for trainer_clean, entries in special_occ.items():
        if not entries:
            continue

        # Attach msg_num to each entry
        for e in entries:
            phrase_group = e["phrase_group"]
            msgnums = phrase_to_msgnums.get(phrase_group)
            if msgnums:
                e["msg_num"] = min(msgnums)
            else:
                e["msg_num"] = None

        # ----------------------------------------------------------
        # Determine current stage using MOST RECENT message
        # ----------------------------------------------------------
        entries_sorted = sorted(
            entries,
            key=lambda e: (e["timestamp"] is None, e["timestamp"])
        )
        current_stage = entries_sorted[-1]["function"]

        # Filter to only messages of the current stage
        stage_entries = [e for e in entries if e["function"] == current_stage]

        # ----------------------------------------------------------
        # Pick the most recent message WITHIN the current stage
        # ----------------------------------------------------------
        stage_entries_sorted = sorted(
            stage_entries,
            key=lambda e: (e["timestamp"] is None, e["timestamp"])
        )
        best = stage_entries_sorted[-1]

        latest_per_creature[trainer_clean] = best

    # --------------------------------------------------------------
    # Convert to UI format
    # --------------------------------------------------------------
    special_creatures = {}

    for trainer_clean, e in latest_per_creature.items():
        lbl = e["display_label"]
        msg_num = e["msg_num"]
        kl  = e["kills_left"]

        if isinstance(kl, int):
            kl_str = str(kl)
        elif kl is None:
            kl_str = ""
        else:
            kl_str = str(kl)

        special_creatures[lbl] = (msg_num, kl_str)

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

    import traceback as _tb
    print("DIAG: on_scan_done entered")
    print("  merged_skinned type/value:", type(merged_skinned), repr(merged_skinned)[:200])
    print("  merged_share type/value:", type(merged_share), repr(merged_share)[:200])
    print("  returned skinned type/value:", type(skinned), repr(skinned)[:200])
    print("  returned share type/value:", type(share), repr(share)[:200])
    print("  normal_ranks sample:", list(normal_ranks.items())[:8])
    print("  merged_counts sample:", list(merged_counts.items())[:8])

def on_scan_done(fut):
    try:
        normal_ranks, special_creatures_data, skinned, share, coin_events, new_folder = fut.result()
        print("DEBUG: on_scan_done special_creatures_data sample:", list(special_creatures_data.items())[:12])
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

    print("DEBUG: merged_creatures keys:", list(merged_creatures.keys())[:12])

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
    # FULL DATASET FROM YOUR SPREADSHEET (48 messages)
    # ------------------------------------------------------------------
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

    # Stage totals
    stage_totals = {}
    for _, stage, ktn in kills_table:
        stage_totals.setdefault(stage, 0)
        stage_totals[stage] += ktn

    # Insert rows
    for msg_num, stage, ktn in kills_table:
        msg = f"You have {stage} left to learn about the <function> of the <creature>."
        kills_left = stage_totals[stage]
        tree.insert("", "end", values=(msg_num, msg, ktn, kills_left))

    return win

def open_special_kills_table():
    """Open a Toplevel window showing special_kills.txt as a table."""
    path = kills_txt_path  # define kills_txt_path globally
    if not os.path.exists(path):
        messagebox.showerror("File not found", f"special_kills.txt not found at {path}")
        return

    rows = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f, delimiter='\t')
            for r in reader:
                if not r:
                    continue
                idx = r[0].strip() if len(r) > 0 else ""
                phrase = r[1].strip() if len(r) > 1 else ""
                kills_min = r[2].strip() if len(r) > 2 else ""
                kills_max = r[3].strip() if len(r) > 3 else ""
                rows.append((idx, phrase, kills_min, kills_max))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read special_kills.txt: {e}")
        return

    win = tk.Toplevel(root)
    win.title("Special Kills Table")
    win.geometry("900x500")

    frame = ttk.Frame(win)
    frame.pack(fill="both", expand=True, padx=8, pady=8)

    cols = ("Index", "Phrase", "KillsMin", "KillsMax")
    tv = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        tv.heading(c, text=c)
    tv.column("Index", width=60, anchor="center")
    tv.column("Phrase", width=600, anchor="w")
    tv.column("KillsMin", width=100, anchor="center")
    tv.column("KillsMax", width=100, anchor="center")
    tv.pack(fill="both", expand=True, side="left")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    for r in rows:
        tv.insert("", "end", values=r)

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

# Buttons
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

ttk.Button(button_frame, text="Scan New Logs", command=load_files_and_count_words)\
    .pack(side="left", padx=5)
ttk.Button(button_frame, text="Rescan All Logs", command=rescan_all_logs)\
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

notebook.add(frame_characters, text="Characters")
notebook.add(frame_ranks, text="Ranks")
notebook.add(frame_creatures, text="Creatures")
notebook.add(frame_logsearch, text="Log Search")
notebook.add(frame_coins, text="Coins")
notebook.add(frame_CLTime, text="Time")
notebook.add(frame_moon, text="Moon Calendar")

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

character_list = tk.Listbox(char_area, height=10, width=40, exportselection=False)
character_list.pack(pady=10, fill="both", expand=True)

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
creature_table.heading("KillsTillNext", text="Kills Till Next Message")
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

root.mainloop()
