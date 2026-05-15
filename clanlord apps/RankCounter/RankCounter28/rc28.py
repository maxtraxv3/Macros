import os
import sys
import traceback
import codecs
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import concurrent.futures
import re
import threading
import json
import time
import csv

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
# ----------------------------------------------------------------------
# ---------------------- CORE PARSING / COUNTS ------------------------
# ----------------------------------------------------------------------

def count_special_lines(texts):
    import re

    # Load phrases
    raw = [p.rstrip('.') for p in read_words_from_file(special_file_path)]
    phrases = sorted(raw, key=len, reverse=True)
    phrases_lc = [p.lower() for p in phrases]
    types = ('ways', 'movements', 'essence')

    # Strip timestamps
    ts_strip = re.compile(r'^\[?\d{1,2}:\d{2}:\d{2}\w?\]?\s*[•>:-]*\s*')

    # Kill message regex
    KILL_RX = re.compile(
        r"(?:you|you helped)\s+(?:slaughtered|dispatched|killed|vanquished)\s+the\s+(.+?)\.",
        re.IGNORECASE
    )

    # Stage ordering for filtering (used earlier in the function)
    stage_order = {"movements": 1, "ways": 2, "essence": 3}

    # Count kills per creature
    kill_counts = {}
    for content, _ in texts:
        for line in content.splitlines():
            m = KILL_RX.search(line)
            if m:
                creature = m.group(1).strip().lower()
                kill_counts[creature] = kill_counts.get(creature, 0) + 1

    special = {}
    study_state = {}
    current_stage = {}

    def norm(s: str) -> str:
        s = re.sub(r'[^\w\s\'-]', '', s.strip())
        return s.lower()

    # MAIN LOOP
    for content, _ in texts:
        for raw_line in content.splitlines():
            line = ts_strip.sub('', raw_line.strip())
            low = line.lower()

            if is_excluded(line):
                continue

            # Study begin/abandon
            if "you abandon your study of the" in low:
                m = re.search(r"you abandon your study of the (.+?)\.", low)
                if m:
                    creature = norm(m.group(1))
                    study_state[creature] = False
                    current_stage[creature] = 0
                continue

            if "you begin studying the movements of the" in low:
                m = re.search(r"you begin studying the movements of the (.+?)\.", low)
                if m:
                    c = norm(m.group(1))
                    study_state[c] = True
                    current_stage[c] = stage_order["movements"]
                continue

            if "you begin studying the ways of the" in low:
                m = re.search(r"you begin studying the ways of the (.+?)\.", low)
                if m:
                    c = norm(m.group(1))
                    study_state[c] = True
                    current_stage[c] = stage_order["ways"]
                continue

            if "you begin studying the essence of the" in low:
                m = re.search(r"you begin studying the essence of the (.+?)\.", low)
                if m:
                    c = norm(m.group(1))
                    study_state[c] = True
                    current_stage[c] = stage_order["essence"]
                continue
                
            m = None

            # finished movements: "You learn to fight the <creature> more effectively."
            m = re.search(r'you learn to fight the (.+?) more effectively', low, re.IGNORECASE)
            if m:
                c = norm(m.group(1))
                # remove any existing special entries for earlier stages so they won't show
                if c in special:
                    special.pop(c, None)
                study_state[c] = False
                # promote stage to ways (if you want to treat completion as starting next stage)
                current_stage[c] = stage_order.get("ways", current_stage.get(c, 0))
                continue

            # finished ways: "You learn to befriend the <creature>."
            m = re.search(r'you learn to befriend the (.+?)\.', low, re.IGNORECASE)
            if m:
                c = norm(m.group(1))
                if c in special:
                    special.pop(c, None)
                study_state[c] = False
                # promote stage to essence
                current_stage[c] = stage_order.get("essence", current_stage.get(c, 0))
                continue

            # finished essence: "You learn to assume the form of the <creature>."
            m = re.search(r'you learn to assume the form of the (.+?)\.', low, re.IGNORECASE)
            if m:
                c = norm(m.group(1))
                # final completion: remove any tracked entries and mark finished
                if c in special:
                    special.pop(c, None)
                study_state[c] = False
                # set to highest stage index (optional)
                current_stage[c] = stage_order.get("essence", current_stage.get(c, 0))
                continue

            if "you have " not in low:
                continue

            # Phrase-based fallback
            try:
                idx = low.index("you have ")
                after = line[idx + len("you have "):].strip()
            except ValueError:
                continue

            for pidx, phrase_lc in enumerate(phrases_lc):
                if after.lower().startswith(phrase_lc):
                    orig_phrase = phrases[pidx]
                    rest = after[len(phrase_lc):].lstrip()
                    trainer = rest.split('.', 1)[0].strip()
                    trainer = re.sub(r'\s*\(.*\)\s*$', '', trainer).strip()
                    trainer_clean = norm(trainer)
                    if not trainer_clean:
                        break

                    full_phrase = f"{phrase_lc} {trainer_clean}"
                    if not after.lower().startswith(full_phrase):
                        continue

                    found = next((t for t in types if t in orig_phrase.lower()), None)

                    # Stage filtering (ignore messages from earlier stages)
                    if found:
                        creature_stage = current_stage.get(trainer_clean, 1)
                        message_stage = stage_order[found]
                        if message_stage < creature_stage:
                            continue

                    template = orig_phrase.lower().strip()

                    trainer_bucket = special.setdefault(trainer_clean, {})
                    creature_bucket = trainer_bucket.setdefault(found, {"stage": None, "counts": {}})

                    incoming_stage = _get_stage_index_for_template(template)

                    if creature_bucket["stage"] is None:
                        creature_bucket["stage"] = incoming_stage
                        creature_bucket["counts"][template] = creature_bucket["counts"].get(template, 0) + 1
                    else:
                        current_stage_val = creature_bucket["stage"]
                        if incoming_stage < current_stage_val:
                            # Older stage message — ignore
                            pass
                        elif incoming_stage > current_stage_val:
                            # Newer stage reached — promote and reset counts to only this template
                            creature_bucket["stage"] = incoming_stage
                            creature_bucket["counts"] = {template: 1}
                        else:
                            # Same stage — accumulate
                            creature_bucket["counts"][template] = creature_bucket["counts"].get(template, 0) + 1

                    # msg_num is the count for this template (after stage logic)
                    msg_num = creature_bucket["counts"].get(template, 0)

                    # Get total kills done for this creature
                    kills_done = kill_counts.get(trainer_clean, 0)

                    # Get the TOTAL kills required for this stage (your msg[] table)
                    # summing all kills_to_next values for this template.
                    stage_table = kills_to_next.get(template, {})
                    total_required = sum(stage_table.values()) if stage_table else None

                    # kills to go
                    if total_required is not None:
                        kills_left = max(total_required - kills_done, 0)
                    else:
                        kills_left = None
                        
                    if isinstance(kills_left, int) and kills_left <= 0:
                        continue

                    # Build display label
                    first4 = " ".join(orig_phrase.split()[:4])
                    display_map = {
                        "ways": "ways (befriend)",
                        "essence": "essence (morph)",
                        "movements": "movements",
                    }

                    if found:
                        display_label = f"{first4} {trainer} ({display_map[found]})"
                    else:
                        display_label = f"{first4} {trainer}"

                    if kills_left is not None:
                        display_label += f" — {kills_left} kills left"

                    # Store the final info dict (template -> info)
                    special[trainer_clean][found][template] = {
                        "count": msg_num,
                        "display_label": display_label,
                        "kills_left": kills_left,
                    }

                    break

    # Flatten into a canonical structure keyed by trainer_clean
    flat = {}   # { trainer_clean: [ { "stage_idx": int, "template": str, "count": int, "kills_left": int|None, "display_label": str } ] }

    for trainer_clean, stages in special.items():
        for stage_name, templates in stages.items():
            for template, info in templates.items():
                t_low = str(template).strip().lower()
                if t_low == "stage" or t_low == "counts" or t_low.startswith("stage ") or t_low.startswith("counts "):
                    print("DEBUG: skipping artifact template for", trainer_clean, "template:", repr(template))
                    continue

                # info should be dict with display_label/count/kills_left
                if isinstance(info, dict):
                    lbl = info.get("display_label")
                    cnt = info.get("count", 0)
                    kl  = info.get("kills_left")
                else:
                    try:
                        cnt = int(info)
                    except Exception:
                        cnt = 0
                    lbl = f"{' '.join(template.split()[:4])} {trainer_clean}"
                    kl = None

                stage_idx = _get_stage_index_for_template(str(stage_name or ""))
                entry = {
                    "stage_idx": stage_idx,
                    "template": t_low,
                    "count": int(cnt) if isinstance(cnt, (int, str)) and str(cnt).isdigit() else cnt,
                    "kills_left": kl,
                    "display_label": lbl or f"{' '.join(template.split()[:4])} {trainer_clean}"
                }

                flat.setdefault(trainer_clean, []).append(entry)

    return flat, {}



def count_kills(texts):
    """Return dict: { creature_name: total_kills }"""
    kills = {}
    KILL_RX = re.compile(
        r"(?:you|you helped)\s+(?:slaughtered|dispatched|killed|vanquished)\s+the\s+(.+?)\.",
        re.IGNORECASE
    )
    for content, _ in texts:
        for line in content.splitlines():
            m = KILL_RX.search(line)
            if not m:
                continue
            creature = m.group(1).strip().lower()
            kills[creature] = kills.get(creature, 0) + 1
    return kills

def filter_finished_studies(special, exclude):
    # After flattening, we cannot detect finished studies reliably.
    # So we simply return the flat dict unchanged.
    return special

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

    words        = read_words_from_file(words_file_path)
    replacements = read_words_from_file(replacement_file_path)

    if len(words) != len(replacements):
        raise ValueError(
            f"File Alignment Error: rankmessages.txt ({len(words)} lines) and "
            f"trainers.txt ({len(replacements)} lines) must match exactly."
        )

    # Wrap mapping so any future assignment is logged with a stack trace
    class LoggingDict(dict):
        def __setitem__(self, key, value):
            import traceback
            print("LOGGING: mapping assignment detected")
            print("  key:", repr(key), "value type:", type(value), "value repr:", repr(value)[:200])
            traceback.print_stack(limit=8)
            super().__setitem__(key, value)

        def update(self, *args, **kwargs):
            for k, v in dict(*args, **kwargs).items():
                self.__setitem__(k, v)

    # Create mapping using the logging wrapper so any later mutation is caught
    mapping = LoggingDict(zip(words, replacements))
    print("DEBUG: mapping created; sample values:", list(mapping.items())[:8])

    texts = read_text_files(folder_path)
    word_occ    = count_word_occurrences(texts, words)
    special_occ, exclude = count_special_lines(texts)
    filtered_special = filter_finished_studies(special_occ, exclude)

    filter_value = time_filter_var.get()
    min_time = get_min_time_from_filter(filter_value)

    skinned, share, coin_events = count_coins(texts, character_name, min_time)

    normal_ranks = {}
    special_creatures = {}

    bad = [(k, type(v), repr(v)) for k, v in mapping.items() if not isinstance(v, str)]
    if bad:
        print("ERROR: mapping contains non-string values right after creation:")
        for k, t, v in bad[:20]:
            print("  key:", repr(k), "value type:", t, "value repr:", v)
        import traceback
        traceback.print_stack()
        raise RuntimeError("mapping contains non-string values after creation")

    # Build normal_ranks with defensive logging to catch dict+int issues
    for w, c in word_occ.items():
        if not c:
            continue

        t = mapping.get(w, "Unknown")

        # print only when something unexpected appears
        if not isinstance(t, str) or not isinstance(c, int):
            print("DEBUG: suspicious mapping entry detected")
            print("  word (w):", repr(w))
            print("  mapped value (t):", repr(t), "type:", type(t))
            print("  count (c):", repr(c), "type:", type(c))
            sample_keys = list(mapping.keys())[:20]
            print("  mapping sample keys:", sample_keys)
            try:
                with open("debug_mapping_dump.json", "a", encoding="utf-8") as df:
                    json.dump({"word": w, "mapped": t, "mapped_type": str(type(t)), "count": c}, df)
                    df.write("\n")
            except Exception:
                pass

        try:
            if not isinstance(t, str):
                continue
            if not isinstance(c, int):
                try:
                    c = int(c)
                except Exception:
                    continue
            normal_ranks[t] = normal_ranks.get(t, 0) + c
        except Exception as ex:
            import traceback as _tb
            print("FATAL: exception while merging normal_ranks")
            print("  word:", repr(w))
            print("  mapped value:", repr(t), "type:", type(t))
            print("  count:", repr(c), "type:", type(c))
            print("  exception:", ex)
            _tb.print_exc()
            raise

    # ------------------------------------------------------------------
    # Normalize special_occ into canonical structure:
    #   canonical_special: { trainer_clean: [ {stage_idx, template, count, kills_left, display_label}, ... ] }
    # Accept both shapes:
    #   - If count_special_lines already returned trainer_clean -> list(entries) use it
    #   - If it returned display_label -> {"count":..., "kills_left":...} convert into trainer_clean groups
    # ------------------------------------------------------------------
    canonical_special = {}

    def _normalize_kills_left(val):
        if isinstance(val, int):
            return val
        if isinstance(val, str):
            try:
                return int(re.sub(r'[^\d-]', '', val))
            except Exception:
                return None
        return None

    # If filtered_special looks like trainer_clean -> list, detect by checking first value type
    if isinstance(filtered_special, dict):
        sample_vals = list(filtered_special.values())[:3]
        # Heuristic: if values are lists of dicts, assume already normalized
        already_normalized = False
        if sample_vals:
            first = sample_vals[0]
            if isinstance(first, list):
                # check element shape
                if first and isinstance(first[0], dict) and "stage_idx" in first[0]:
                    already_normalized = True

        if already_normalized:
            canonical_special = filtered_special.copy()
        else:
            # filtered_special is likely display_label -> {"count":..., "kills_left":...}
            # Convert each display_label into trainer_clean and an entry
            for display_label, info in filtered_special.items():
                lbl = str(display_label)

                # Extract trainer_clean robustly: everything after the first four words up to '(' or ' — ' or end
                m = re.match(r'^(?:\S+\s+){4}(.+?)(?:\s*\(|\s+—\s+|$)', lbl)
                if m:
                    trainer_clean = m.group(1).strip().lower()
                else:
                    clean = lbl.split("(", 1)[0].strip()
                    trainer_clean = " ".join(clean.split()[-3:]).lower()

                # stage index from the label/template text
                stage_idx = _get_stage_index_for_template(lbl)

                # info may be dict with count/kills_left
                if isinstance(info, dict):
                    cnt = info.get("count", 0)
                    kl  = _normalize_kills_left(info.get("kills_left"))
                else:
                    # legacy: info might be tuple (count, kills_str) or int
                    if isinstance(info, (list, tuple)) and len(info) >= 1:
                        try:
                            cnt = int(info[0])
                        except Exception:
                            cnt = 0
                        kl = _normalize_kills_left(info[1]) if len(info) > 1 else None
                    else:
                        try:
                            cnt = int(info)
                        except Exception:
                            cnt = 0
                        kl = None

                entry = {
                    "stage_idx": stage_idx,
                    "template": lbl.lower(),
                    "count": int(cnt) if isinstance(cnt, (int, str)) and str(cnt).isdigit() else cnt,
                    "kills_left": kl,
                    "display_label": lbl
                }
                canonical_special.setdefault(trainer_clean, []).append(entry)
    else:
        # Unexpected shape: leave canonical_special empty
        canonical_special = {}

    # ------------------------------------------------------------------
    # Now for each trainer_clean pick:
    #   - highest stage seen
    #   - within that stage, the entry with highest count
    #   - skip entries that are finished (numeric kills_left <= 0)
    # ------------------------------------------------------------------
    latest_per_creature = {}

    for trainer_clean, entries in canonical_special.items():
        if not entries:
            continue

        # determine highest stage index seen
        max_stage = max(e.get("stage_idx", 0) for e in entries)

        # keep only entries from that stage
        stage_entries = [e for e in entries if e.get("stage_idx", 0) == max_stage]
        if not stage_entries:
            continue

        # normalize kills_left and filter finished entries (treat only numeric <=0 as finished)
        candidates = []
        for e in stage_entries:
            kl = e.get("kills_left")
            if isinstance(kl, str):
                try:
                    kl = int(re.sub(r'[^\d-]', '', kl))
                except Exception:
                    kl = None
            e["kills_left"] = kl

            # keep unknown (None) as not finished; only numeric <=0 is finished
            if isinstance(kl, int) and kl <= 0:
                continue
            candidates.append(e)

        if not candidates:
            # nothing unfinished in this stage; skip creature entirely
            continue

        # pick the candidate with the highest count (coerce to int where possible)
        def _count_key(x):
            v = x.get("count", 0)
            try:
                return int(v)
            except Exception:
                return 0

        best = max(candidates, key=_count_key)

        # store the display label and values for downstream UI
        display_label = best.get("display_label") or trainer_clean
        latest_per_creature[display_label] = {
            "count": best.get("count", 0),
            "kills_left": best.get("kills_left")
        }

    # Build special_creatures in the same shape the rest of the code expects:
    # { display_label: (count, kills_str) }
    for lbl, v in latest_per_creature.items():
        cnt = v.get("count", 0)
        kl  = v.get("kills_left")
        kl_str = str(kl) if isinstance(kl, int) else (str(kl) if kl is not None else "")
        special_creatures[lbl] = (cnt, kl_str)

    # Debug output (optional)
    print("DEBUG: special_creatures sample:", list(special_creatures.items())[:12])

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

    if name not in character_folders or not character_folders[name]:
        messagebox.showerror("Error", "This character has no folders assigned.")
        return

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

# ----------------------------------------------------------------------
# ------------------------- MAIN GUI SETUP -----------------------------
# ----------------------------------------------------------------------

root = tk.Tk()
root.title("Rank Counter 28")
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

notebook.add(frame_characters, text="Characters")
notebook.add(frame_ranks, text="Ranks")
notebook.add(frame_creatures, text="Creatures")
notebook.add(frame_logsearch, text="Log Search")
notebook.add(frame_coins, text="Coins")

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


# --- UPDATED: Background thread search -------------------------------------
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


# --- UPDATED: Show sentences only ------------------------------------------
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


# --- UPDATED: Double-click opens file using hidden list ---------------------
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