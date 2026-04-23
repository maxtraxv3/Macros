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

CHAR_FILE = "characters.json"
character_ranks = {}
character_creatures = {}

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
#-- coins counter ------------------------------------------------------------
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
            "ignored": character_ignored.get(name, [])
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
    # This filters out any empty lines or lines that are just whitespace
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
    for content, _ in texts:  # Unpack the tuple here
        for line in content.splitlines():
            if is_excluded(line):
                continue
            for w in words:
                counts[w] += line.count(w)
    return counts

# -- Special-Line Counter (nested dict: last phrase + count) -----------------
def count_special_lines(texts):
    import re

    # Load phrases
    raw = [p.rstrip('.') for p in read_words_from_file(special_file_path)]
    phrases = sorted(raw, key=len, reverse=True)
    phrases_lc = [p.lower() for p in phrases]
    types = ('ways', 'movements', 'essence')

    # Strip timestamps
    ts_strip = re.compile(r'^\[?\d{1,2}:\d{2}:\d{2}\w?\]?\s*[•>:-]*\s*')

    # Progression regex
    prog_rx = re.compile(
        r'you have .*? about the (ways|movements|essence) of the (.+?)\.\s*$',
        re.IGNORECASE
    )

    # Kill message regex
    KILL_RX = re.compile(
        r"(?:you|you helped)\s+(?:slaughtered|dispatched|killed|vanquished)\s+the\s+(.+?)\.",
        re.IGNORECASE
    )

    # Count kills per creature
    kill_counts = {}
    for content, _ in texts:
        for line in content.splitlines():
            m = KILL_RX.search(line)
            if m:
                creature = m.group(1).strip().lower()
                kill_counts[creature] = kill_counts.get(creature, 0) + 1

    # Embedded kills_to_next table
    kills_to_next = {
        "almost nothing left to learn about the movements of the": {
            1: 4, 2: 2, 3: 2, 4: 2, 5: 2
        },
        "almost nothing left to learn about the ways of the": {
            1: 4, 2: 2, 3: 2, 4: 2, 5: 2
        },
        "almost nothing left to learn about the essence of the": {
            1: 4, 2: 2, 3: 2, 4: 2, 5: 2
        },

        "a few things to learn about the movements of the": {
            1: 3, 2: 3, 3: 3, 4: 3, 5: 3
        },
        "a few things to learn about the ways of the": {
            1: 3, 2: 3, 3: 3, 4: 3, 5: 3
        },
        "a few things to learn about the essence of the": {
            1: 3, 2: 3, 3: 3, 4: 3, 5: 3
        },

        "more than a few things to learn about the ways of the": {
            1: 7, 2: 7, 3: 7, 4: 7, 5: 8
        },
        "more than a few things to learn about the essence of the": {
            1: 7, 2: 7, 3: 7, 4: 7, 5: 8
        },

        "some things to learn about the ways of the": {
            1: 12, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 9
        },
        "some things to learn about the essence of the": {
            1: 12, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 9
        },

        "many things to learn about the ways of the": {
            1: 20, 2: 20, 3: 20, 4: 20, 5: 20, 6: 20, 7: 16
        },
        "many things to learn about the essence of the": {
            1: 20, 2: 20, 3: 20, 4: 20, 5: 20, 6: 20, 7: 16
        },

        "much to learn about the ways of the": {
            1: 30, 2: 30, 3: 30, 4: 30, 5: 30, 6: 30, 7: 20
        },
        "much to learn about the essence of the": {
            1: 30, 2: 30, 3: 30, 4: 30, 5: 30, 6: 30, 7: 20
        },

        "a lot to learn about the ways of the": {
            1: 100, 2: 30, 3: 30, 4: 30, 5: 30
        },
        "a lot to learn about the essence of the": {
            1: 100, 2: 30, 3: 30, 4: 30, 5: 30
        },

        "a vast amount to learn about the ways of the": {
            1: 100, 2: 100, 3: 100, 4: 100, 5: 100, 6: 100
        },
        "a vast amount to learn about the essence of the": {
            1: 100, 2: 100, 3: 100, 4: 100, 5: 100, 6: 100
        }
    }

    special = {}
    exclude = {"ways": set(), "movements": set(), "essence": set()}
    study_state = {}
    pending_apply = {}
    bonus_ranks = {}

    def norm(s: str) -> str:
        s = s.strip()
        s = re.sub(r'[^\w\s\'-]', '', s)
        return s.lower()

    # MAIN LOOP
    for content, _ in texts:
        for raw_line in content.splitlines():
            line = ts_strip.sub('', raw_line.strip())
            if is_excluded(line):
                continue
            low = line.lower()

            # Apply-learning start
            if "would you like to apply some of your learning to" in low:
                m = re.search(r"apply some of your learning to (.+?)’s lessons", line)
                if m:
                    pending_apply[norm(m.group(1))] = True
                continue

            # Apply-learning confirmation
            if "you should now understand much more of" in low:
                m = re.search(r"much more of (.+?)’s teachings", line)
                if m:
                    t = norm(m.group(1))
                    if pending_apply.get(t):
                        bonus_ranks[t] = bonus_ranks.get(t, 0) + 1
                        pending_apply[t] = False
                continue

            # Study begin/abandon
            if "you abandon your study of the" in low:
                m = re.search(r"you abandon your study of the (.+?)\.", low)
                if m:
                    study_state[norm(m.group(1))] = False
                continue

            if "you begin studying the ways of the" in low:
                m = re.search(r"you begin studying the ways of the (.+?)\.", low)
                if m:
                    study_state[norm(m.group(1))] = True
                continue

            if "you begin studying the movements of the" in low:
                m = re.search(r"you begin studying the movements of the (.+?)\.", low)
                if m:
                    study_state[norm(m.group(1))] = True
                continue

            if "you begin studying the essence of the" in low:
                m = re.search(r"you begin studying the essence of the (.+?)\.", low)
                if m:
                    study_state[norm(m.group(1))] = True
                continue

            # Training exclusions
            if "you learn to fight the" in low and "more effectively" in low:
                m = re.search(r"you learn to fight the (.+?) more effectively", low)
                if m:
                    exclude["movements"].add(norm(m.group(1)))
                continue

            if "you learn to befriend the" in low:
                m = re.search(r"you learn to befriend the (.+?)\.", low)
                if m:
                    exclude["ways"].add(norm(m.group(1)))
                continue

            if "you learn to assume the form of the" in low:
                m = re.search(r"you learn to assume the form of the (.+?)\.", low)
                if m:
                    exclude["essence"].add(norm(m.group(1)))
                continue

            if "you have " not in low:
                continue

            # Regex-based progression
            pm = prog_rx.search(low)
            parsed_category = None
            parsed_monster = None
            if pm:
                parsed_category = pm.group(1).lower()
                parsed_monster = norm(pm.group(2))

                if study_state.get(parsed_monster) is False:
                    continue
                if parsed_monster in exclude.get(parsed_category, set()):
                    continue

            # Phrase-based fallback
            try:
                idx = low.index('you have ')
                after = line[idx + len('you have '):].strip()
            except ValueError:
                continue

            for idx, phrase_lc in enumerate(phrases_lc):
                if after.lower().startswith(phrase_lc):
                    orig_phrase = phrases[idx]
                    phrase_key = orig_phrase.lower()

                    rest = after[len(phrase_lc):].lstrip()
                    trainer = rest.split('.', 1)[0].strip()
                    trainer_clean = norm(trainer)

                    if not trainer_clean:
                        break

                    found = next((t for t in types if t in orig_phrase.lower()), None)
                    first4 = ' '.join(orig_phrase.split()[:4])

                    # Count message number
                    if trainer_clean not in special:
                        special[trainer_clean] = {
                            "label": "",
                            "display_label": "",
                            "count": 1,
                            "kills_left": None
                        }
                    else:
                        special[trainer_clean]["count"] += 1

                    phrase_key = orig_phrase.lower()
                    msg_num = special[trainer_clean]["count"]

                    kills_required = kills_to_next.get(phrase_key, {}).get(msg_num)
                    kills_since_last = kill_counts.get(trainer_clean, 0)

                    if kills_required is not None:
                        kills_left = max(kills_required - kills_since_last, 0)
                    else:
                        kills_left = None

                    special[trainer_clean]["kills_left"] = kills_left

                    # Build display label
                    display_map = {
                        "ways": "ways (befriend)",
                        "essence": "essence (morph)",
                        "movements": "movements"
                    }

                    if found:
                        label = f"{first4} {trainer} ({found})"
                        display_label = f"{first4} {trainer} ({display_map.get(found, found)})"
                    else:
                        label = f"{first4} {trainer}"
                        display_label = label

                    if kills_left is not None:
                        display_label = f"{display_label} — {kills_left} kills left"

                    special[trainer_clean]["label"] = label
                    special[trainer_clean]["display_label"] = display_label

                    break

    # Attach bonus ranks
    for trainer, info in special.items():
        bonus = bonus_ranks.get(trainer, 0)
        if bonus:
            info["count_str"] = f"{info['count']} ({bonus})"
        else:
            info["count_str"] = str(info["count"])

    return special, exclude

def count_kills(texts):
    """Return dict: { creature_name: total_kills }"""
    kills = {}
    for content, _ in texts:
        for line in content.splitlines():
            m = KILL_RX.search(line)
            if not m:
                continue
            creature = m.group(1).strip().lower()
            kills[creature] = kills.get(creature, 0) + 1
    return kills
   
def filter_finished_studies(special, exclude):
    filtered = {}
    for trainer, data in special.items():
        # Try to extract category from label
        match = re.search(r'\((ways|movements|essence)\)$', data["label"])
        if match:
            category = match.group(1)
            monster = trainer.strip().lower()
            if monster in exclude.get(category, set()):
                continue  # skip if study was finished
        filtered[trainer] = data
    return filtered
    
# -- Coin Scanning ---------------------------------------------------------    
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
    words        = read_words_from_file(words_file_path)
    replacements = read_words_from_file(replacement_file_path)
    
    if len(words) != len(replacements):
        # Improved error message to help you debug
        raise ValueError(f"File Alignment Error: rankmessages.txt ({len(words)} lines) and "
                         f"trainers.txt ({len(replacements)} lines) must match exactly.")

    mapping     = dict(zip(words, replacements))
    texts       = read_text_files(folder_path)
    word_occ    = count_word_occurrences(texts, words)
    special_occ, exclude = count_special_lines(texts)
    filtered_special = filter_finished_studies(special_occ, exclude)
    
    filter_value = time_filter_var.get()
    min_time = get_min_time_from_filter(filter_value)

    skinned, share, coin_events = count_coins(texts, character_name, min_time)

    normal_ranks = {}
    special_creatures = {}

    for w, c in word_occ.items():
        if c:
            t = mapping.get(w, "Unknown")
            normal_ranks[t] = normal_ranks.get(t, 0) + c

    for trainer, info in filtered_special.items():
        print("DEBUG: filtered_special sample:", list(filtered_special.items())[:8])
        print("DEBUG: special_creatures built:", list(special_creatures.items())[:12])
        label = info.get("display_label", info["label"])
        cnt   = info.get("count_str", str(info["count"]))
        kills = info.get("kills_left")
        # normalize kills to a short string for the UI
        if isinstance(kills, tuple):
            kills_str = f"~{kills[0]}–{kills[1]}"
        elif isinstance(kills, int):
            kills_str = str(kills)
        else:
            kills_str = ""
        # store tuple: (count_str, kills_str)
        special_creatures[label] = (cnt, kills_str)
    
    print("DEBUG: special_creatures sample:", list(special_creatures.items())[:12])

    return normal_ranks, special_creatures, skinned, share, coin_events, os.path.basename(folder_path)

# -- UI Callbacks & GUI Setup -----------------------------------------------

def parse_creature_count(count_str):
    """Helper to split '5 (1)' into base=5, bonus=1"""
    import re
    # Remove any non-numeric/paren characters just in case
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

def on_scan_done(fut):
    try:
        normal_ranks, special_creatures_data, skinned, share, coin_events, new_folder = fut.result()
        print("DEBUG: on_scan_done special_creatures_data sample:", list(special_creatures_data.items())[:12])
    except Exception as e:
        messagebox.showerror("Scan Error", str(e))
        return

    global merged_counts, merged_creatures, merged_skinned, merged_share, merged_coin_events

    # Merge coin totals
    merged_skinned += skinned
    merged_share += share

    # Merge detailed coin events
    merged_coin_events.extend(coin_events)

    # Merge normal ranks
    for name, count in normal_ranks.items():
        merged_counts[name] = merged_counts.get(name, 0) + count

    # Merge special creatures 
    for name, count_kills in special_creatures_data.items():
        # count_kills may be a tuple (count_str, kills_str) or (legacy) a plain string
        if isinstance(count_kills, tuple):
            count_str, kills_str = count_kills
        else:
            count_str = str(count_kills)
            kills_str = ""

        new_base, new_bonus = parse_creature_count(count_str)

        if name in merged_creatures:
            cur_entry = merged_creatures[name]
            # support legacy stored string or new dict
            if isinstance(cur_entry, dict):
                cur_count_str = cur_entry.get("count", str(cur_entry))
            else:
                cur_count_str = str(cur_entry)
            cur_base, cur_bonus = parse_creature_count(cur_count_str)
            tot_base = new_base
            tot_bonus = cur_bonus + new_bonus
        else:
            tot_base = new_base
            tot_bonus = new_bonus

        merged_creatures[name] = {
            "count": f"{tot_base} ({tot_bonus})" if tot_bonus else str(tot_base),
            "kills": kills_str
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

    # Insert rows into the creatures table (use new column names)
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

    coins_table.insert("", "end", values=("Total Skinned", merged_skinned))
    coins_table.insert("", "end", values=("Total Share", merged_share))
    coins_table.insert("", "end", values=("Total Coins", merged_skinned + merged_share))
    coins_table.insert("", "end", values=("", ""))  # spacer
    coins_table.insert("", "end", values=("Monster", "Details"))

    # Summarize by monster
    summary = summarize_coin_events(merged_coin_events)

    # Add summary rows
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

    global merged_counts, merged_creatures
    merged_counts.clear()
    merged_creatures.clear()

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
    merged_counts.clear()
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
                f.write(f"{n},{c}\n")  # c already includes "(bonus)" if present
        messagebox.showinfo("Success", f"Saved to {path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save:\n{e}")

def ignore_selected_creature():
    """Adds selected creature to ignore list and refreshes table."""
    selected_item = creature_table.selection()
    if not selected_item:
        return
    
    # Get the creature name from the selected row
    creature_name = creature_table.item(selected_item)['values'][0]
    char_name = get_selected_character()
    
    if not char_name:
        return

    # Add to ignored list
    if char_name not in character_ignored:
        character_ignored[char_name] = []
    
    if creature_name not in character_ignored[char_name]:
        character_ignored[char_name].append(creature_name)
        save_characters() # Save to JSON
        
        # Remove from UI immediately
        creature_table.delete(selected_item)
        print(f"Ignored: {creature_name}")

def open_ignore_manager():
    """Opens a popup to see and restore ignored items."""
    char_name = get_selected_character()
    if not char_name:
        messagebox.showerror("Error", "Select a character first.")
        return

    # Create Popup Window
    win = tk.Toplevel(root)
    win.title(f"Ignored Items for {char_name}")
    win.geometry("400x300")

    lbl = tk.Label(win, text="Select items to restore:")
    lbl.pack(pady=5)

    # Listbox
    lb = tk.Listbox(win, selectmode=tk.MULTIPLE)
    lb.pack(fill="both", expand=True, padx=10, pady=5)

    # Fill Listbox
    ignored = character_ignored.get(char_name, [])
    for item in ignored:
        lb.insert(tk.END, item)

    def restore_selected():
        selections = lb.curselection()
        if not selections:
            return
        
        # Get items to remove from ignore list
        to_restore = [lb.get(i) for i in selections]
        
        # Remove them
        for item in to_restore:
            if item in character_ignored[char_name]:
                character_ignored[char_name].remove(item)
        
        save_characters()
        win.destroy()
        on_character_selected() # Refresh main table
    
    

    btn = tk.Button(win, text="Restore Selected", command=restore_selected)
    btn.pack(pady=10)
    
def open_kills_to_next_table():
    """Open a window showing the embedded kills_to_next table."""
    # Use the same kills_to_next dict from count_special_lines
    kills_to_next = {
        "almost nothing left to learn about the movements of the <creature>.": {1:4,2:2,3:2,4:2,5:2},
        "almost nothing left to learn about the ways of the <creature>.": {1:4,2:2,3:2,4:2,5:2},
        "almost nothing left to learn about the essence of the <creature>.": {1:4,2:2,3:2,4:2,5:2},

        "a few things to learn about the movements of the <creature>.": {1:3,2:3,3:3,4:3,5:3},
        "a few things to learn about the ways of the <creature>.": {1:3,2:3,3:3,4:3,5:3},
        "a few things to learn about the essence of the <creature>.": {1:3,2:3,3:3,4:3,5:3},

        "more than a few things to learn about the ways of the <creature>.": {1:7,2:7,3:7,4:7,5:8},
        "more than a few things to learn about the essence of the <creature>.": {1:7,2:7,3:7,4:7,5:8},

        "some things to learn about the ways of the <creature>.": {1:12,2:12,3:12,4:12,5:12,6:12,7:9},
        "some things to learn about the essence of the <creature>.": {1:12,2:12,3:12,4:12,5:12,6:12,7:9},

        "many things to learn about the ways of the <creature>.": {1:20,2:20,3:20,4:20,5:20,6:20,7:16},
        "many things to learn about the essence of the <creature>.": {1:20,2:20,3:20,4:20,5:20,6:20,7:16},

        "much to learn about the ways of the <creature>.": {1:30,2:30,3:30,4:30,5:30,6:30,7:20},
        "much to learn about the essence of the <creature>.": {1:30,2:30,3:30,4:30,5:30,6:30,7:20},

        "a lot to learn about the ways of the <creature>.": {1:100,2:30,3:30,4:30,5:30},
        "a lot to learn about the essence of the <creature>.": {1:100,2:30,3:30,4:30,5:30},

        "a vast amount to learn about the ways of the <creature>.": {1:100,2:100,3:100,4:100,5:100,6:100},
        "a vast amount to learn about the essence of the <creature>.": {1:100,2:100,3:100,4:100,5:100,6:100}
    }

    win = tk.Toplevel(root)
    win.title("Kills Required Table")
    win.geometry("900x500")

    frame = ttk.Frame(win)
    frame.pack(fill="both", expand=True, padx=8, pady=8)

    cols = ("Phrase", "Message #", "Kills to Next")
    tv = ttk.Treeview(frame, columns=cols, show="headings")

    for c in cols:
        tv.heading(c, text=c)

    tv.column("Phrase", width=600, anchor="w")
    tv.column("Message #", width=100, anchor="center")
    tv.column("Kills to Next", width=120, anchor="center")

    tv.pack(fill="both", expand=True, side="left")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    # Populate table
    for phrase, mapping in kills_to_next.items():
        for msg_num, kills_needed in mapping.items():
            tv.insert("", "end", values=(phrase, msg_num, kills_needed))

    
def open_special_kills_table():
    """Open a Toplevel window showing special_kills.txt as a table."""
    path = kills_txt_path  # uses your existing path variable
    if not os.path.exists(path):
        messagebox.showerror("File not found", f"special_kills.txt not found at {path}")
        return

    # parse TSV: expect columns like index, phrase, kills_min, kills_max (or last two numeric)
    rows = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f, delimiter='\t')
            for r in reader:
                if not r:
                    continue
                # normalize to at least 4 columns: index, phrase, kills_min, kills_max
                idx = r[0].strip() if len(r) > 0 else ""
                phrase = r[1].strip() if len(r) > 1 else ""
                # last two columns may be numeric; try to parse them
                kills_min = r[2].strip() if len(r) > 2 else ""
                kills_max = r[3].strip() if len(r) > 3 else ""
                rows.append((idx, phrase, kills_min, kills_max))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read special_kills.txt: {e}")
        return

    # create window
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

    # vertical scrollbar
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    # populate
    for r in rows:
        tv.insert("", "end", values=r)

# ----------------------------------------------------------------------
# ------------------------- NEW GUI SECTION -----------------------------
# ----------------------------------------------------------------------

root = tk.Tk()
root.title("Rank Counter 28")
try:
    icon_path = resource_path('phoenix.png')
    icon_img = tk.PhotoImage(file=icon_path)
    # Set the icon (False means it applies to this window only)
    root.iconphoto(True, icon_img)
except Exception as e:
    print(f"Could not load icon: {e}")

# ---------------- Buttons (Horizontal Layout) ----------------
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

ttk.Button(button_frame, text="Scan New Logs", command=load_files_and_count_words)\
    .pack(side="left", padx=5)

ttk.Button(button_frame, text="Rescan All Logs", command=rescan_all_logs)\
    .pack(side="left", padx=5)
    
# ---------------- Tabbed Notebook ----------------
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

frame_characters = ttk.Frame(notebook)
frame_folders = ttk.Frame(notebook)
frame_ranks = ttk.Frame(notebook)
frame_creatures = ttk.Frame(notebook)
frame_logsearch = ttk.Frame(notebook)
frame_coins = ttk.Frame(notebook)

# --- Time Filter UI inside Coins tab ---
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

    # Update table
    for item in coins_table.get_children():
        coins_table.delete(item)

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

tk.Button(frame_coins, text="Refresh Coins", command=refresh_coins_table).pack(pady=5)

notebook.add(frame_characters, text="Characters")
#notebook.add(frame_folders, text="Folders")
notebook.add(frame_ranks, text="Ranks")
notebook.add(frame_creatures, text="Creatures")
notebook.add(frame_logsearch, text="Log Search")
notebook.add(frame_coins, text="Coins")

# ---------------- Characters Tab ----------------
load_characters()

# Main container for the Characters area
char_area = ttk.Frame(frame_characters)
char_area.pack(fill="both", expand=True, pady=5)

# Create the character_list inside char_area (master set correctly)
character_list = tk.Listbox(char_area, height=10, width=40, exportselection=False)
character_list.pack(pady=10, fill="both", expand=True)

def on_character_selected(event):
    sel = event.widget.curselection()
    if not sel:
        return
    name = event.widget.get(sel[0])
    # clear merged data so UI shows fresh results
    merged_counts.clear()
    merged_creatures.clear()
    # optionally auto-scan assigned folders (comment if you don't want auto-scan)
    # load_files_and_count_words()
    # or just refresh UI from saved character data:
    if name in character_ranks:
        # update ranks table
        for item in table.get_children():
            table.delete(item)
        for n, c in character_ranks[name].items():
            table.insert("", "end", values=(n, c))
    if name in character_creatures:
        for item in creature_table.get_children():
            creature_table.delete(item)
        ignored = character_ignored.get(name, [])
        for n, c in character_creatures[name].items():
            if n not in ignored:
                creature_table.insert("", "end", values=(n, c))


# Populate list
for name in character_folders.keys():
    character_list.insert(tk.END, name)
character_list.bind("<<ListboxSelect>>", on_character_selected)

# Helper to get selected character
def get_selected_character():
    sel = character_list.curselection()
    if not sel:
        return None
    return character_list.get(sel[0])

# Define character helper functions BEFORE creating buttons
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

# Character area buttons
char_buttons_frame = ttk.Frame(char_area)
char_buttons_frame.pack(pady=5)

add_char_btn = ttk.Button(char_buttons_frame, text="Add Character", command=add_character)
add_char_btn.pack(side="left", padx=5)

remove_char_btn = ttk.Button(char_buttons_frame, text="Remove Character", command=remove_character)
remove_char_btn.pack(side="left", padx=5)

manage_folders_btn = ttk.Button(char_buttons_frame, text="Folders", command=lambda: open_folder_manager())
manage_folders_btn.pack(side="left", padx=5)

# Folder manager frame (hidden initially)
folder_manager_frame = ttk.Frame(frame_characters)

fm_label = ttk.Label(folder_manager_frame, text="Folders for selected character:")
fm_label.pack(pady=5)

# New Listbox for folder manager (created inside folder_manager_frame)
fm_folder_list = tk.Listbox(folder_manager_frame, width=60, height=12)
fm_folder_list.pack(pady=5, fill="both", expand=True)

# Buttons for folder manager
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

back_btn = ttk.Button(fm_button_frame, text="Back", command=lambda: close_folder_manager())
back_btn.pack(side="left", padx=5)

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

# ---------------- Ranks Table ----------------
table = ttk.Treeview(frame_ranks, columns=("Trainer", "Ranks"), show="headings")
table.heading("Trainer", text="Trainer")
table.heading("Ranks", text="Ranks")
table.column("Trainer", width=300, stretch=True)
table.column("Ranks", width=80, stretch=False)
table.pack(pady=10, fill="both", expand=True)

# ---------------- Creatures Table ----------------
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

btn_special_kills = ttk.Button(
    frame_creatures,
    text="View Message Table",
    command=open_kills_to_next_table
)
btn_special_kills.pack(padx=6, pady=4, side="right", anchor="ne")

# ---------------- Coins Table ----------------
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

# Bind Right Click (Button-3 on Windows, Button-2 on Mac sometimes)
creature_table.bind("<Button-3>", show_creature_menu) 
creature_table.bind("<Button-2>", show_creature_menu) # MacOS support

tk.Button(frame_creatures, text="Manage Ignored List", command=open_ignore_manager)\
    .pack(pady=5)

# ---------------- LOG SEARCH TAB (Search ALL character folders) ----------------

tk.Label(frame_logsearch, text="Search word:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

ls_word_var = tk.StringVar()
tk.Entry(frame_logsearch, textvariable=ls_word_var, width=50).grid(row=0, column=1, padx=5, pady=5)

def ls_start_search():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return

    if name not in character_folders or not character_folders[name]:
        messagebox.showerror("Error", "This character has no folders assigned.")
        return

    word = ls_word_var.get()
    if not word:
        messagebox.showerror("Error", "Please enter a word to search for.")
        return

    ls_results_list.delete(0, tk.END)
    ls_results_list.insert(tk.END, "Scanning all folders... Please wait.")

    threading.Thread(target=ls_run_scan, args=(name, word), daemon=True).start()

tk.Button(frame_logsearch, text="Search", command=ls_start_search)\
    .grid(row=0, column=2, padx=5, pady=5)

tk.Label(frame_logsearch, text="Matching Files:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

ls_results_list = tk.Listbox(frame_logsearch, width=90, height=20)
ls_results_list.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

scrollbar = tk.Scrollbar(frame_logsearch)
scrollbar.grid(row=2, column=3, sticky="ns")
ls_results_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=ls_results_list.yview)

def ls_run_scan(name, word):
    found_files = []
    for folder in character_folders[name]:
        if os.path.isdir(folder):
            found_files.extend(scan_directory(folder, word))
    ls_results_list.after(0, ls_update_results, found_files, word)

def ls_update_results(found_files, word):
    ls_results_list.delete(0, tk.END)
    if found_files:
        ls_results_list.insert(tk.END, f"Found '{word}' in:")
        ls_results_list.insert(tk.END, "--------------------------------")
        for f in found_files:
            ls_results_list.insert(tk.END, f)
    else:
        ls_results_list.insert(tk.END, f"No files found containing '{word}'.")

def ls_open_selected_file(event=None):
    sel = ls_results_list.curselection()
    if not sel:
        return
    file_path = ls_results_list.get(sel[0])
    if os.path.isfile(file_path):
        open_file_with_default_app(file_path)

ls_results_list.bind("<Double-Button-1>", ls_open_selected_file)

root.mainloop()