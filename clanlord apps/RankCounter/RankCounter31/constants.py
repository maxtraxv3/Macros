from __future__ import annotations
import os
import sys
import traceback
import codecs
import json
import time
import concurrent.futures
import re
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
character_healer   = {}     # Stores healer calc data
character_fighter  = {}     # Stores fighter calc data
character_removed_folders = {}  # Stores manually removed folders per character
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

# -- UI globals (assigned by main.py) ---------------------------------------

root = None
table = None
creature_table = None
coins_table = None
character_list = None
time_filter_var = None
ls_results_list = None
ls_hidden_paths = []
kills_txt_path = None
BESTIARY_FILE = resource_path('Bestiary_2026_07_06_Dump.xml')
BESTIARY_LEVELS_FILE = resource_path('bestiary_levels.json')
DATA_SOURCES_FILE = "datasources.json"
data_sources = []
bestiary_data = {}
IMG_DIR = None
font_path = None
