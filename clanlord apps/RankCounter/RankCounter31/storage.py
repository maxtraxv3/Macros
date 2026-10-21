import os
import codecs
import xml.etree.ElementTree as ET
import json
import time
import sys
import tkinter as tk
from tkinter import messagebox

from constants import *

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
        try:
            messagebox.showerror("Error", f"Failed to open file: {e}")
        except Exception:
            pass

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

def time_filter_seconds(amount, unit):
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return None
    if amount <= 0:
        return None
    if unit == "hours":
        return amount * 3600
    if unit == "days":
        return amount * 86400
    if unit == "months":
        return amount * 30 * 86400
    return None

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

# -- Character Storage --------------------------------------------------------

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

# -- Bestiary (XML) ----------------------------------------------------------

def load_bestiary(path=None):
    if path is None:
        path = BESTIARY_FILE
    if not path or not os.path.exists(path):
        print(f"Bestiary file not found: {path}")
        return
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        data = {}
        for table in root.findall(".//table"):
            cols = {}
            for col in table.findall("column"):
                cols[col.get("name")] = (col.text or "").strip()
            name = cols.get("name")
            if name:
                data[name] = cols
        bestiary_data.clear()
        bestiary_data.update(data)
        print(f"Loaded bestiary: {len(bestiary_data)} creatures")
    except Exception as e:
        print(f"Error loading bestiary: {e}")

def lookup_bestiary(name):
    if not bestiary_data:
        load_bestiary()
    if not name:
        return None
    lname = str(name).strip().lower()
    for k, v in bestiary_data.items():
        if k.strip().lower() == lname:
            return v
    # fallback: contains
    for k, v in bestiary_data.items():
        if lname and lname in k.strip().lower():
            return v
    return None
