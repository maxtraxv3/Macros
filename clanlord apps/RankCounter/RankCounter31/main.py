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
import webbrowser
import urllib.request
import urllib.parse
import io
from datetime import datetime, timezone, timedelta
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Shared modules
from constants import *
from storage import *
import storage
from cl_time import *
from parser import *
from ui_components import CLTime

# Make module-level globals from constants available and mutable in this module
import constants as _c

# Apply exception hook (already set in constants, but ensure)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# GUI CALLBACKS
# ----------------------------------------------------------------------

import traceback as _tb

def on_scan_done(fut):
    try:
        normal_ranks, special_creatures_data, skinned, share, coin_events, new_folder = fut.result()
        print("DEBUG: on_scan_done special_creatures_data sample:", list(special_creatures_data.items())[:12])
    except Exception as e:
        import traceback
        print("FUTURE EXCEPTION (on_scan_done):", repr(e))
        traceback.print_exc()
        try:
            exc = fut.exception()
            if exc is not None:
                print("fut.exception():", repr(exc))
        except Exception:
            pass
        messagebox.showerror("Scan Error", str(e))
        return

    global merged_counts, merged_creatures, merged_skinned, merged_share, merged_coin_events

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

    merged_coin_events.extend(coin_events)

    import traceback as _tb2
    for name, count in normal_ranks.items():
        try:
            cur_val = merged_counts.get(name, 0)
            if not isinstance(cur_val, int) or not isinstance(count, int):
                print("DIAGNOSTIC: about to add values for:", repr(name))
                print("  merged_counts.get(name):", repr(cur_val), "type:", type(cur_val))
                print("  normal_ranks[name]:", repr(count), "type:", type(count))
                _tb2.print_stack(limit=8)

            if not isinstance(count, int):
                try:
                    count = int(count)
                    print("DIAGNOSTIC: coerced count to int for", repr(name), "->", count)
                except Exception:
                    print("DIAGNOSTIC: cannot coerce count to int, skipping:", repr(name), repr(count), type(count))
                    continue

            if not isinstance(cur_val, int):
                print("DIAGNOSTIC: merged_counts has non-int for", repr(name), "resetting to 0 (was type: {})".format(type(cur_val)))
                _tb2.print_stack(limit=8)
                cur_val = 0

            merged_counts[name] = cur_val + count

        except Exception as ex:
            print("FATAL: exception while merging normal_ranks for", repr(name))
            print("  count:", repr(count), "type:", type(count))
            print("  merged_counts.get(name):", repr(merged_counts.get(name)), "type:", type(merged_counts.get(name)))
            _tb2.print_exc()
            raise

    for name, count_kills in special_creatures_data.items():
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

    char_name = get_selected_character()
    if char_name:
        character_ranks[char_name] = merged_counts
        character_creatures[char_name] = merged_creatures
        save_characters()

    for item in table.get_children():
        table.delete(item)
    for name, cnt in merged_counts.items():
        table.insert("", "end", values=(name, cnt))

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

    for item in coins_table.get_children():
        coins_table.delete(item)

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
    coins_table.insert("", "end", values=("", ""))
    coins_table.insert("", "end", values=("Monster", "Details"))

    summary = summarize_coin_events(merged_coin_events)
    for monster, data in summary.items():
        label = monster
        details = f"Total {data['total_worth']}c, share {data['total_share']}c, you skinned {data['your_skins']}"
        coins_table.insert("", "end", values=(label, details))

    try:
        update_cv_display()
    except Exception:
        pass


def load_files_and_count_words():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return

    if name not in character_folders or not character_folders[name]:
        messagebox.showerror("Error", "This character has no folders assigned.")
        return

    valid_folders = []
    invalid_folders = []

    for folder in character_folders[name]:
        norm = os.path.normpath(os.path.expanduser(folder.strip()))

        if os.path.isdir(norm):
            valid_folders.append(norm)
            continue

        if os.path.isdir(folder):
            valid_folders.append(folder)
            continue

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

    min_time = get_min_time_from_filter()

    for folder in character_folders[name]:
        if not os.path.isdir(folder):
            continue

        fut = executor.submit(scan_and_aggregate, folder, name, min_time)
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
    name = get_selected_character()
    if not name:
        return

    for item in table.get_children():
        table.delete(item)
    for n, c in character_ranks.get(name, {}).items():
        table.insert("", "end", values=(n, c))

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

    # Load healer/fighter calc data
    hdata = character_healer.get(name, {})
    for key, var in healer_entries.items():
        var.set(hdata.get(key, "0"))
    fdata = character_fighter.get(name, {})
    for key, var in fighter_entries.items():
        var.set(fdata.get(key, "0"))


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
    win = tk.Toplevel()
    win.title("Kills‑to‑Next Message Table")
    win.geometry("1000x650")

    frame = ttk.Frame(win)
    frame.pack(fill="both", expand=True)

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

    kt = [
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

    stage_totals = {}
    for _, stage, ktn in kt:
        stage_totals.setdefault(stage, 0)
        stage_totals[stage] += ktn

    for msg_num, stage, ktn in kt:
        msg = f"You have {stage} left to learn about the <function> of the <creature>."
        kills_left = stage_totals[stage]
        tree.insert("", "end", values=(msg_num, msg, ktn, kills_left))

    return win


def open_special_kills_table():
    path = kills_txt_path
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


def open_credits():
    win = tk.Toplevel(root)
    win.title("Credits & Licenses")
    win.geometry("600x500")
    text = tk.Text(win, wrap="word", padx=10, pady=10)
    text.pack(fill="both", expand=True)
    content = """Credits & Licenses

Rank Counter 31

Credits:
- Gorvin (gorvin.50webs.com) - Healer/Fighter calculator math and formulas.
- Org du Lac - Bestiary images and calculations (bestiary.clanlord.net).
- Noivad - Clumps Ranger information (clump.clanlord.net).
- Clan Lord community for data and testing.
- Delta Tao Software (deltatao.com/clanlord) - holds rights to Clan Lord images.

Third-Party Licenses:
- Python - PSF License
- Tkinter - PSF License
- Pillow (PIL) - HPND License
- PyInstaller - GPL v2 with Bootloader Exception
- ttk (Tk themed widgets) - PSF/Tcl license

This application is for personal use. Game data and images belong to their respective owners.
"""
    text.insert("1.0", content)
    text.config(state="disabled")

# ----------------------------------------------------------------------
# MAIN GUI SETUP
# ----------------------------------------------------------------------

root = tk.Tk()
root.title("Rank Counter 31.1")

font_path = os.path.join(os.path.dirname(__file__), "KIN668.TTF")
IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
constants.font_path = font_path
constants.IMG_DIR = IMG_DIR
constants.root = root

custom_font = ("KIN668", 10)

try:
    root.tk.call("font", "create", "KIN668", "-family", "KIN668",
                 "-size", "11", "-weight", "normal")
    root.tk.call("font", "configure", "KIN668", "-family", "KIN668")
except:
    pass

root.option_add("*Font", "KIN668 11")

try:
    icon_path = resource_path('phoenix.png')
    icon_img = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon_img)
except Exception as e:
    print(f"Could not load icon: {e}")

button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

ttk.Button(button_frame, text="Scan New Logs", command=load_files_and_count_words).pack(side="left", padx=5)
ttk.Button(button_frame, text="Rescan All Logs", command=rescan_all_logs).pack(side="left", padx=5)

ttk.Button(button_frame, text="Credits", command=open_credits).pack(side="right", padx=5)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

frame_characters = ttk.Frame(notebook)
frame_ranks = ttk.Frame(notebook)
frame_creatures = ttk.Frame(notebook)
frame_logsearch = ttk.Frame(notebook)
frame_coins = ttk.Frame(notebook)
frame_CLTime = ttk.Frame(notebook)
frame_moon = ttk.Frame(notebook)
frame_healer = ttk.Frame(notebook)
frame_fighter = ttk.Frame(notebook)
notebook.add(frame_characters, text="Characters")
notebook.add(frame_ranks, text="Ranks")
notebook.add(frame_creatures, text="Creatures")
notebook.add(frame_logsearch, text="Log Search")
notebook.add(frame_coins, text="Coins")
notebook.add(frame_CLTime, text="Time")
notebook.add(frame_healer, text="Healer Calc")
notebook.add(frame_fighter, text="Fighter Calc")

CLTime(frame_CLTime)
frame_CLTime.rowconfigure(1, weight=1)
frame_CLTime.columnconfigure(0, weight=1)

# --- Coin time filter controls -------------------------------------------
coin_filter_mode_var = tk.StringVar(value="All time")
coin_filter_amount_var = tk.StringVar(value="24")
coin_filter_unit_var = tk.StringVar(value="hours")

filter_frame = ttk.Frame(frame_coins)
filter_frame.pack(pady=5, fill="x")

ttk.Radiobutton(filter_frame, text="All time", variable=coin_filter_mode_var, value="All time").pack(side="left", padx=5)
ttk.Radiobutton(filter_frame, text="Custom", variable=coin_filter_mode_var, value="Custom").pack(side="left", padx=5)

ttk.Label(filter_frame, text="Amount:").pack(side="left", padx=(10, 2))
amount_entry = ttk.Entry(filter_frame, textvariable=coin_filter_amount_var, width=6)
amount_entry.pack(side="left", padx=2)

unit_box = ttk.Combobox(
    filter_frame,
    textvariable=coin_filter_unit_var,
    values=["hours", "days", "months"],
    state="readonly",
    width=8
)
unit_box.pack(side="left", padx=5)

def get_min_time_from_filter():
    if coin_filter_mode_var.get() == "All time":
        return None
    seconds = time_filter_seconds(coin_filter_amount_var.get(), coin_filter_unit_var.get())
    if seconds is None:
        return None
    return time.time() - seconds

def get_moon_icon(phase_name):
    mapping = {
        "New Moon": "new.gif",
        "Full Moon": "full.gif",
        "Last Quarter": "lq.gif",
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

    min_time = get_min_time_from_filter()
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

    try:
        update_cv_display()
    except Exception:
        pass

tk.Button(frame_coins, text="Refresh Coins", command=refresh_coins_table).pack(pady=5)

load_characters()
load_data_sources()
load_bestiary()

def merge_duplicate_characters():
    # Merge characters whose normalized names match (case/space insensitive)
    merged = {}
    for name, folders in list(character_folders.items()):
        key = "".join(name.split()).lower()
        if key not in merged:
            merged[key] = name
        else:
            canon = merged[key]
            # merge folders
            for f in folders:
                if os.path.normpath(f) not in [os.path.normpath(p) for p in character_folders[canon]]:
                    character_folders[canon].append(f)
            # merge ranks (sum)
            for r, c in character_ranks.get(name, {}).items():
                character_ranks[canon][r] = character_ranks[canon].get(r, 0) + c
            # merge creatures
            for c, d in character_creatures.get(name, {}).items():
                if c not in character_creatures[canon]:
                    character_creatures[canon][c] = d
            # merge ignored
            for ig in character_ignored.get(name, []):
                if ig not in character_ignored[canon]:
                    character_ignored[canon].append(ig)
            # merge removed folders
            for rf in character_removed_folders.get(name, []):
                if rf not in character_removed_folders[canon]:
                    character_removed_folders[canon].append(rf)
            # merge healer/fighter (keep existing if empty)
            if not character_healer.get(canon):
                character_healer[canon] = character_healer.get(name, {})
            if not character_fighter.get(canon):
                character_fighter[canon] = character_fighter.get(name, {})
            # remove duplicate
            del character_folders[name]
            character_ranks.pop(name, None)
            character_creatures.pop(name, None)
            character_ignored.pop(name, None)
            character_removed_folders.pop(name, None)
            character_healer.pop(name, None)
            character_fighter.pop(name, None)

merge_duplicate_characters()

def discover_characters():
    for src in list(data_sources):
        if not os.path.isdir(src):
            continue
        try:
            for entry in os.listdir(src):
                path = os.path.join(src, entry)
                if not os.path.isdir(path):
                    continue
                # Skip folders that are clearly not character logs
                low_name = entry.lower()
                if any(tok in low_name for tok in ("move", "movie", "macro", "clump", "cl_move")):
                    continue

                # Validate: folder must contain at least one .txt log with typical log content
                has_log = False
                for _root, _dirs, files in os.walk(path):
                    for fn in files:
                        if not fn.lower().endswith(".txt"):
                            continue
                        fpath = os.path.join(_root, fn)
                        try:
                            with open(fpath, encoding="utf-8", errors="ignore") as f:
                                for line in f:
                                    if re.search(r"\\d+/\\d+/\\d+", line) or "You " in line or "slaughtered" in line or "killed" in line:
                                        has_log = True
                                        break
                            if has_log:
                                break
                        except Exception:
                            pass
                    if has_log:
                        break
                if not has_log:
                    continue
                # Normalize name: ignore case and spaces so "Cat Food", "catfood", "catFood" merge
                def _norm(n):
                    return "".join(n.split()).lower()
                existing = None
                for name in character_folders:
                    if _norm(name) == _norm(entry):
                        existing = name
                        break
                char_name = existing if existing else entry
                if char_name not in character_folders:
                    character_folders[char_name] = []
                    character_ranks[char_name] = {}
                    character_creatures[char_name] = {}
                    character_ignored[char_name] = []
                    character_healer[char_name] = {}
                    character_fighter[char_name] = {}
                # Respect manually removed folders
                removed = character_removed_folders.get(char_name, [])
                if path in removed:
                    continue
                norm_path = os.path.normpath(path)
                existing_norms = [os.path.normpath(p) for p in character_folders[char_name]]
                if norm_path not in existing_norms:
                    character_folders[char_name].append(path)
        except Exception as e:
            print("Discover error:", e)
    refresh_character_list()

def refresh_character_list():
    character_list.delete(0, tk.END)
    seen = set()
    for name in character_folders.keys():
        key = "".join(name.split()).lower()
        if key in seen:
            continue
        seen.add(key)
        character_list.insert(tk.END, name)
try:
    with open(resource_path("weapons_data.json"), encoding="utf-8") as f:
        weapons_data = json.load(f)
except Exception as e:
    print("Could not load weapons_data:", e)
    weapons_data = {}

try:
    with open(resource_path("offhand_data.json"), encoding="utf-8") as f:
        offhand_data = json.load(f)
except Exception as e:
    print("Could not load offhand_data:", e)
    offhand_data = {}

try:
    with open(resource_path("shoulder_data.json"), encoding="utf-8") as f:
        shoulder_data = json.load(f)
except Exception as e:
    print("Could not load shoulder_data:", e)
    shoulder_data = {}

try:
    with open(resource_path("armor_data.json"), encoding="utf-8") as f:
        armor_data = json.load(f)
except Exception as e:
    print("Could not load armor_data:", e)
    armor_data = {}

char_area = ttk.Frame(frame_characters)
char_area.pack(fill="both", expand=True, pady=5)

character_list = tk.Listbox(char_area, height=10, width=40, exportselection=False)
character_list.pack(pady=10, fill="both", expand=True)
constants.character_list = character_list
discover_characters()

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

    update_cv_display() if 'update_cv_display' in globals() else None

    # Load healer/fighter calc data
    hdata = character_healer.get(name, {})
    for key, var in healer_entries.items():
        var.set(hdata.get(key, "0"))
    fdata = character_fighter.get(name, {})
    for key, var in fighter_entries.items():
        var.set(fdata.get(key, "0"))

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
    if not new_name:
        return
    existing = None
    for name in character_folders:
        if "".join(name.split()).lower() == "".join(new_name.split()).lower():
            existing = name
            break
    if existing:
        messagebox.showinfo("Existing Character", f"Character '{existing}' already exists. Using existing entry.")
        return
    character_list.insert(tk.END, new_name)
    character_folders[new_name] = []
    character_ranks[new_name] = {}
    character_creatures[new_name] = {}
    character_healer[new_name] = {}
    character_fighter[new_name] = {}
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
        character_healer.pop(name, None)
        character_fighter.pop(name, None)
        save_characters()

char_buttons_frame = ttk.Frame(char_area)
char_buttons_frame.pack(pady=5)

add_char_btn = ttk.Button(char_buttons_frame, text="Add Character", command=add_character)
add_char_btn.pack(side="left", padx=5)

remove_char_btn = ttk.Button(char_buttons_frame, text="Remove Character", command=remove_character)
remove_char_btn.pack(side="left", padx=5)

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
            character_removed_folders.setdefault(name, [])
            if folder not in character_removed_folders[name]:
                character_removed_folders[name].append(folder)
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

def open_data_sources_manager():
    win = tk.Toplevel(root)
    win.title("Data Sources")
    win.geometry("500x300")
    lb = tk.Listbox(win)
    lb.pack(fill="both", expand=True, padx=10, pady=5)
    for src in data_sources:
        lb.insert(tk.END, src)

    def add_src():
        d = filedialog.askdirectory()
        if d and d not in data_sources:
            data_sources.append(d)
            save_data_sources()
            lb.insert(tk.END, d)
            discover_characters()

    def remove_src():
        sel = lb.curselection()
        if not sel:
            return
        src = lb.get(sel[0])
        if src in data_sources:
            data_sources.remove(src)
            save_data_sources()
        lb.delete(sel[0])
        discover_characters()

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=5)
    ttk.Button(btn_frame, text="Add Source", command=add_src).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Remove Selected", command=remove_src).pack(side="left", padx=5)

data_sources_btn = ttk.Button(char_buttons_frame, text="Data Sources", command=open_data_sources_manager)
data_sources_btn.pack(side="left", padx=5)

# Ranks table
table = ttk.Treeview(frame_ranks, columns=("Trainer", "Ranks"), show="headings")
table.heading("Trainer", text="Trainer")
table.heading("Ranks", text="Ranks")
table.column("Trainer", width=300, stretch=True)
table.column("Ranks", width=80, stretch=False)
table.pack(pady=10, fill="both", expand=True)
constants.table = table

# Creatures table
creature_table = ttk.Treeview(frame_creatures, columns=("Creature", "MessageNumber", "KillsTillNext"), show="headings")
creature_table.heading("Creature", text="Creature")
creature_table.heading("MessageNumber", text="Message Number")
creature_table.heading("KillsTillNext", text="Kills Till Next Message")
creature_table.column("Creature", width=420, anchor="w", stretch=True)
creature_table.column("MessageNumber", width=120, anchor="center", stretch=False)
creature_table.column("KillsTillNext", width=160, anchor="center", stretch=False)
creature_table.pack(pady=10, fill="both", expand=True)
constants.creature_table = creature_table

# Creature image preview (bestiary)
creature_preview_frame = ttk.LabelFrame(frame_creatures, text="Creature Preview")
creature_preview_frame.pack(fill="x", padx=10, pady=5)

cv_label = ttk.Label(frame_creatures, text="CV: -", font=("KIN668", 11, "bold"))
cv_label.pack(pady=5)

# compute_cv_level is now provided by storage (imported)
def update_cv_display():
    name = get_selected_character() if 'get_selected_character' in globals() else None
    lvl = compute_cv_level(name)
    cv_label.config(text=f"CV: {lvl}" if lvl is not None else "CV: -")

creature_name_label = ttk.Label(creature_preview_frame, text="Select a creature", font=("KIN668", 11, "bold"))
creature_name_label.pack(pady=2)

creature_image_label = ttk.Label(creature_preview_frame, text="No image")
creature_image_label.pack(pady=5)

# (Download-all button removed; images are bundled locally and cached on first view.)

bestiary_image_cache = {}
BESTIARY_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".rankcounter", "bestiary_cache")

def _cache_path(family, pic):
    return os.path.join(BESTIARY_CACHE_DIR, family, pic)

def extract_creature_name(label):
    if not label:
        return ""
    m = re.search(r"of the (.+?)\.", str(label))
    if m:
        return m.group(1).strip()
    return str(label).strip()

def get_selected_creature_label():
    sel = creature_table.selection()
    if not sel:
        return None
    try:
        return creature_table.item(sel[0])["values"][0]
    except Exception:
        return None

def get_bestiary_image(creature_name):
    if not PIL_AVAILABLE:
        return None
    info = lookup_bestiary(creature_name)
    if not info:
        return None
    family = info.get("family")
    pic = info.get("static_pic")
    if not family or not pic:
        return None
    key = creature_name.strip().lower()
    if key in bestiary_image_cache:
        return bestiary_image_cache[key]

    cache_file = _cache_path(family, pic)
    data = None

    # 1) Prefer the bundled/local image shipped with the app
    local_path = resource_path(os.path.join("img", "creatures_static", family, pic))
    if os.path.exists(local_path):
        try:
            with open(local_path, "rb") as f:
                data = f.read()
        except Exception:
            data = None

    # 2) Fall back to the user's downloaded cache
    if data is None and os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                data = f.read()
        except Exception:
            data = None

    # 3) Otherwise download and save to the user cache
    if data is None:
        url = "https://bestiary.clanlord.net/images/creatures_static/{}/{}".format(
            urllib.parse.quote(family, safe=""),
            urllib.parse.quote(pic, safe="")
        )
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = resp.read()
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "wb") as f:
                f.write(data)
        except Exception as e:
            print("Bestiary image fetch failed:", e)
            bestiary_image_cache[key] = None
            return None

    try:
        img = Image.open(io.BytesIO(data))
        img.thumbnail((128, 128))
        photo = ImageTk.PhotoImage(img)
        bestiary_image_cache[key] = photo
        return photo
    except Exception as e:
        print("Bestiary image decode failed:", e)
        bestiary_image_cache[key] = None
        return None

def update_creature_preview():
    label = get_selected_creature_label()
    name = extract_creature_name(label) if label else ""
    creature_name_label.config(text=name if name else "Select a creature")
    photo = get_bestiary_image(name) if name else None
    if photo is not None:
        creature_image_label.config(image=photo, text="")
        creature_image_label.image = photo
    else:
        creature_image_label.config(image="", text="No image")

creature_table.bind("<<TreeviewSelect>>", lambda e: update_creature_preview())

def show_creature_bestiary():
    label = get_selected_creature_label()
    name = extract_creature_name(label) if label else ""
    info = lookup_bestiary(name) if name else None
    if info and info.get("family"):
        family = info["family"]
        url = "https://bestiary.clanlord.net/beast/{}.php".format(urllib.parse.quote(family, safe=""))
    else:
        url = "https://bestiary.clanlord.net/beast.php"
    try:
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open browser: {e}")

def show_creature_info():
    label = get_selected_creature_label()
    name = extract_creature_name(label) if label else ""
    info = lookup_bestiary(name) if name else None
    win = tk.Toplevel(root)
    win.title(f"Creature Information: {name}")
    win.geometry("500x600")

    # Image
    img_frame = ttk.Frame(win)
    img_frame.pack(pady=5)
    photo = get_bestiary_image(name) if name else None
    if photo is not None:
        lbl_img = ttk.Label(img_frame, image=photo)
        lbl_img.image = photo
        lbl_img.pack()
    else:
        ttk.Label(img_frame, text="No image").pack()

    # Stats text
    text = tk.Text(win, wrap="word", font=("KIN668", 10))
    text.pack(fill="both", expand=True, padx=10, pady=10)

    if not info:
        text.insert("end", f"No bestiary data found for '{name}'.")
        text.config(state="disabled")
        return

    excluded = {
        "static_width", "static_height", "action_pic", "action_width",
        "action_height", "static_pic", "defense_ismeasured",
        "attack_ismeasured", "damage_ismeasured", "health_ismeasured",
        "first_update",
    }

    # Preferred order
    preferred = [
        "name", "family", "level", "rarity", "location", "information", "worth",
        "worth_range", "exp_taxidermy", "spawns_per_hour", "attack",
        "defense", "damage", "health", "framesperswing", "difficulty",
        "luck_hits", "is_seasonal", "last_update",
    ]
    preferred = [k for k in preferred if k not in excluded]

    lines = []
    for key in preferred:
        if key in info and info[key] not in ("", None) and info[key] != "NULL":
            lines.append(f"{key}: {info[key]}")
    # add any remaining keys
    for key, val in info.items():
        if key in excluded:
            continue
        if key not in preferred and val not in ("", None) and val != "NULL":
            lines.append(f"{key}: {val}")

    text.insert("end", "\n".join(lines))
    text.config(state="disabled")

creature_context_menu = tk.Menu(root, tearoff=0)
creature_context_menu.add_command(label="Ignore Creature", command=ignore_selected_creature)
creature_context_menu.add_command(label="Show creature on bestiary website", command=show_creature_bestiary)
creature_context_menu.add_command(label="Creature information", command=show_creature_info)

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
constants.coins_table = coins_table

def show_creature_menu(event):
    item = creature_table.identify_row(event.y)
    if item:
        creature_table.selection_set(item)
        creature_context_menu.post(event.x_root, event.y_root)

creature_table.bind("<Button-3>", show_creature_menu)
creature_table.bind("<Button-2>", show_creature_menu)

# ---------------------------------------------------------
# PIXEL-PERFECT MOON CALENDAR
# ---------------------------------------------------------

moon_container = ttk.Frame(frame_CLTime)
moon_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

stats_frame = ttk.LabelFrame(moon_container, text="Current Time")
stats_frame.pack(fill="x", pady=(0, 10))

stats_labels = {}
fields = ["Year", "Season", "Zodiac", "Moon Phase", "Time"]

for col, field in enumerate(fields):
    ttk.Label(stats_frame, text=f"{field}:", font=("KIN668", 10, "bold")).grid(row=0, column=col*2, padx=4)
    stats_labels[field] = ttk.Label(stats_frame, text="---", font=("KIN668", 10))
    stats_labels[field].grid(row=0, column=col*2 + 1, padx=4)

year_frame = ttk.Frame(moon_container)
year_frame.pack(pady=(0, 10))

year_var = tk.IntVar()

def submit_year():
    build_moon_calendar(year_var.get())

season_colors = {
    "Winter": "#C7DDF9",
    "Spring": "#C9F7C9",
    "Summer": "#FFF4C2",
    "Autumn": "#FFD2A6"
}

moon_bg = "#EDEDED"

calendar_frame = ttk.Frame(moon_container)
calendar_frame.pack(fill="both", expand=True)

seasons = ["Winter", "Spring", "Summer", "Autumn"]
season_frames = {}

for s in seasons:
    outer = tk.Frame(calendar_frame, bg=season_colors[s], bd=1, relief="solid")
    # Packed on demand so only the current season is shown.
    season_frames[s] = outer

    tk.Label(
        outer,
        text=s.upper(),
        font=("KIN668", 12, "bold"),
        bg=season_colors[s],
        anchor="center"
    ).pack(fill="x", pady=(3, 3))

icon_cache = {}
for name, img_file in moon_icons.items():
    path = os.path.join(os.path.dirname(__file__), img_file)
    icon_cache[name] = tk.PhotoImage(file=path)

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
        return lunar_day, None

day_cells = []

def build_moon_calendar(year):
    global day_cells
    day_cells = []

    day = 0
    for season in seasons:
        outer = season_frames[season]

        grid = tk.Frame(outer, bg=season_colors[season])
        grid.pack(padx=4, pady=(0, 6))

        for r in range(3):
            for c in range(30):
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
                    tk.Label(cell, image=icon, bg=bg, width=14, height=14).pack(pady=(2, 0))
                else:
                    spacer = tk.Frame(cell, bg=bg, width=14, height=14)
                    spacer.pack(pady=(2, 0))
                    spacer.pack_propagate(False)

                tk.Label(cell, text=str(day), font=("KIN668", 8), bg=bg).pack(pady=(0, 2))

                day_cells.append(cell)

legend = tk.Frame(moon_container)
legend.pack(pady=5)

for phase in ["New Moon", "First Quarter", "Full Moon", "Last Quarter"]:
    icon = icon_cache.get(phase)
    box = tk.Frame(legend)
    box.pack(side="left", padx=10)

    tk.Label(box, image=icon).pack()
    tk.Label(box, text=phase, font=("KIN668", 9)).pack()

def update_moon_calendar():
    cl_time = real_to_cl(datetime.now())

    # Show only the current season.
    for s, frame in season_frames.items():
        if s == cl_time.season_name:
            if not frame.winfo_ismapped():
                frame.pack(fill="x", pady=4)
        else:
            if frame.winfo_ismapped():
                frame.pack_forget()

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

    frame_CLTime.after(60000, update_moon_calendar)

cl_time = real_to_cl(datetime.now())
year_var.set(cl_time.year)
# Show only the current season.
season_frames[cl_time.season_name].pack(fill="x", pady=4)
build_moon_calendar(cl_time.year)
update_moon_calendar()

# ----------------------------------------------------------------------
# LOG SEARCH TAB
# ----------------------------------------------------------------------

frame_logsearch.grid_rowconfigure(2, weight=1)
frame_logsearch.grid_columnconfigure(1, weight=1)
frame_logsearch.grid_columnconfigure(0, weight=0)
frame_logsearch.grid_columnconfigure(2, weight=0)

tk.Label(frame_logsearch, text="Search word:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

ls_word_var = tk.StringVar()
tk.Entry(frame_logsearch, textvariable=ls_word_var, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

ls_hidden_paths = []

def ls_extract_sentences(file_path, word):
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

def ls_update_results(results, word):
    ls_results_list.delete(0, tk.END)
    ls_hidden_paths.clear()

    if not results:
        ls_results_list.insert(tk.END, f"No sentences found containing '{word}'.")
        return

    ls_results_list.insert(tk.END, f"Sentences containing '{word}':")
    ls_hidden_paths.append(None)

    ls_results_list.insert(tk.END, "--------------------------------")
    ls_hidden_paths.append(None)

    for sentence, file_path in results:
        ls_results_list.insert(tk.END, sentence)
        ls_hidden_paths.append(file_path)

def ls_open_selected_file(event=None):
    sel = ls_results_list.curselection()
    if not sel:
        return

    index = sel[0]
    file_path = ls_hidden_paths[index]

    if file_path and os.path.isfile(file_path):
        open_file_with_default_app(file_path)

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

tk.Button(frame_logsearch, text="Search", command=ls_start_search).grid(row=0, column=2, padx=5, pady=5, sticky="e")

tk.Label(frame_logsearch, text="Matching Sentences:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

ls_results_list = tk.Listbox(frame_logsearch, width=90, height=20)
ls_results_list.grid(
    row=2, column=0, columnspan=3,
    padx=5, pady=5,
    sticky="nsew"
)
constants.ls_results_list = ls_results_list
constants.ls_hidden_paths = ls_hidden_paths

scrollbar = tk.Scrollbar(frame_logsearch)
scrollbar.grid(row=2, column=3, sticky="ns")
ls_results_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=ls_results_list.yview)

ls_results_list.bind("<Double-Button-1>", ls_open_selected_file)

# ----------------------------------------------------------------------
# HEALER CALC TAB (simplified)
# ----------------------------------------------------------------------
RACE_BASE = {
    "Human/Undisclosed": [700,800,600,3000,0,0,0,100,0,0,0],
    "Dwarf": [700,500,500,3300,0,0,0,100,0,0,0],
    "Fen": [700,700,500,1500,0,0,0,100,0,0,0],
    "Halfling": [700,900,700,3000,0,0,0,100,0,0,0],
    "Ghorak Zo": [600,700,500,3600,0,0,0,100,0,0,0],
    "Sylvan": [700,800,600,2400,0,0,0,100,0,0,0],
    "Thoom": [700,1000,700,3900,0,0,0,300,0,0,0],
    "Magic 0-Stat Race": [0,0,0,0,0,0,0,0,0,0,0],
}

TRAINER_DELTAS = {
    "Faustus": [33,0,0,0,0,0,0,0,0,0,0],
    "Higgrus": [0,0,0,120,0,0,0,0,0,0,0],
    "Sespus": [0,29,0,0,0,0,0,0,0,0,0],
    "Respia": [0,0,24,0,0,0,0,0,0,0,0],
    "Horus": [0,0,0,0,100,0,0,0,0,0,0],
    "Awaria": [0,0,0,0,0,100,0,0,0,0,0],
    "Proximus": [0,0,0,0,0,0,1,0,0,0,0],
    "Troilus": [0,0,0,0,0,0,0,6,0,0,0],
    "Eff. Sprite": [0,0,0,0,0,0,0,0,1,0,0],
    "Eva": [11,8,9,30,6,6,0,0,0,0,0],
    "Sprite": [10,7,5,12,0,0,0,0,1,0,0],
    "Spiritus": [11,9,0,21,0,0,0,0,1,0,0],
    "Anan (1:1)": [17,0,12,0,0,0,0,0,0,0,0],
    "AnDeux (1:2)": [11,0,16,0,0,0,0,0,0,0,0],
    "AnTrix (1:3)": [8,0,18,0,0,0,0,0,0,0,0],
    "AnQuart (1:4)": [7,0,20,0,0,0,0,0,0,0,0],
    "AnSept (1:7)": [4,0,21,0,0,0,0,0,0,0,0],
    "Bodrus": [0,0,0,24,0,0,0,0,0,1,0],
    "Hardia": [0,0,0,21,0,0,0,0,0,1,0],
    "Radium": [0,0,0,0,0,0,0,0,0,0,1],
}

STAT_NAMES = ["HealSpeed","Spirit","SpiritReg","Health","Raising","HealEff","HealRange","Regen","HealRecept","Body","GroupHeal"]

healer_entries = {}

def build_healer_section(parent, title, fields, side="top"):
    lf = ttk.LabelFrame(parent, text=title)
    lf.pack(side=side, fill="both", expand=True, padx=5, pady=5)
    row = 0
    for label, key in fields:
        ttk.Label(lf, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        var = tk.StringVar(value="0")
        ent = ttk.Entry(lf, textvariable=var, width=8)
        ent.grid(row=row, column=1, padx=5, pady=2)
        healer_entries[key] = var
        var.trace_add("write", lambda *a: calc_healer())
        row += 1
    return lf

pure_fields = [
    ("Faustus","Faustus"),("Higgrus","Higgrus"),("Sespus","Sespus"),
    ("Respia","Respia"),("Horus","Horus"),("Awaria","Awaria"),
    ("Proximus","Proximus"),("Troilus","Troilus"),("Eff. Sprite","Eff. Sprite"),
]
combo_fields = [
    ("Eva","Eva"),("Sprite","Sprite"),("Spiritus","Spiritus"),
    ("Anan (1:1)","Anan (1:1)"),("AnDeux (1:2)","AnDeux (1:2)"),
    ("AnTrix (1:3)","AnTrix (1:3)"),("AnQuart (1:4)","AnQuart (1:4)"),
    ("AnSept (1:7)","AnSept (1:7)"),("Bodrus","Bodrus"),
    ("Hardia","Hardia"),("Radium","Radium"),
]

# Race and Items
ri_frame = ttk.LabelFrame(frame_healer, text="Race and Items")
ri_frame.pack(fill="x", padx=10, pady=5)
ttk.Label(ri_frame, text="Race:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
race_var = tk.StringVar(value="Human/Undisclosed")
race_box = ttk.Combobox(ri_frame, textvariable=race_var, values=list(RACE_BASE.keys()), state="readonly", width=20)
race_box.grid(row=0, column=1, padx=5, pady=2)
race_var.trace_add("write", lambda *a: calc_healer())
ttk.Label(ri_frame, text="Sylphstone:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
sylph_var = tk.StringVar(value="Nothing")
sylph_box = ttk.Combobox(ri_frame, textvariable=sylph_var, values=["Nothing","50% Efficiency","75% Efficiency"], state="readonly", width=20)
sylph_box.grid(row=1, column=1, padx=5, pady=2)
sylph_var.trace_add("write", lambda *a: calc_healer())

ranks_row = ttk.Frame(frame_healer)
ranks_row.pack(fill="x", padx=10, pady=5)
build_healer_section(ranks_row, "Pure Ranks", pure_fields, side="left")
build_healer_section(ranks_row, "Combo Ranks", combo_fields, side="left")

results_text = tk.Text(frame_healer, height=14, wrap="word")
results_text.pack(fill="both", expand=True, padx=10, pady=10)

result_type_var = tk.StringVar(value="Total Stats")
result_box = ttk.Combobox(frame_healer, textvariable=result_type_var, values=["Total Stats","Spirit","Self-Heal","Healing Others","Proximus and Radium"], state="readonly", width=20)
result_box.pack(pady=5)
result_type_var.trace_add("write", lambda *a: calc_healer())

def _round(val, precise=True):
    if precise:
        import math
        return math.floor(val)
    return val

def calc_healer():
    stats = list(RACE_BASE.get(race_var.get(), RACE_BASE["Human/Undisclosed"]))
    for key, var in healer_entries.items():
        try:
            ranks = float(var.get())
        except ValueError:
            ranks = 0
        deltas = TRAINER_DELTAS.get(key)
        if deltas:
            for i in range(len(stats)):
                stats[i] += ranks * deltas[i]
    precise = True
    spregen = stats[2] / 100.0
    hpregen = stats[7] / 100.0
    spcost = _round(stats[0] / 100.0) * 20
    hpheal = _round(stats[0] / 100.0) + _round((15 * stats[8]) / 100.0)
    # Awaria
    eff = _round(stats[5] / 100.0)
    eff = _round(eff * 31 / 100.0)
    freeheal = _round((15 * stats[8]) / 100.0) + eff
    base = _round(stats[0] / 100.0)
    if freeheal > base:
        freeheal = base
    hpheal = (base + freeheal) * 10
    sylph_mult = 1.0
    sm = sylph_var.get()
    if sm == "50% Efficiency":
        sylph_mult = 0.5
    elif sm == "75% Efficiency":
        sylph_mult = 0.75
    hphealsyl = _round(sylph_mult * ((base + (freeheal if freeheal < base else base)) * 10))

    rt = result_type_var.get()
    lines = []
    if rt == "Total Stats":
        lines.append("Computed total stats (base race + trained ranks):")
        for name, val in zip(STAT_NAMES, stats):
            lines.append(f"{name}: {round(val, 2)}")
    elif rt == "Spirit":
        lines.append("***Spirit stats***")
        value = spregen / (29 if 29 else 1)
        lines.append(f"Sespus regenerated per second: {round(value, 2)}")
        value = stats[1] / spregen if spregen else 0
        lines.append(f"Seconds to regen full spirit: {round(value, 2)}")
        value = spcost / 29.0
        lines.append(f"Sespus cost per self-heal pulse: {round(value, 2)}")
    elif rt == "Self-Heal":
        # single rank stats
        single_stats = [0]*len(STAT_NAMES)
        for d in TRAINER_DELTAS.values():
            for i in range(len(single_stats)):
                single_stats[i] += d[i]
        single_hp_reg = single_stats[7] / 100.0
        single_sp_reg = single_stats[2] / 100.0
        FPS = 5.0

        lines.append("***Single Self-Heal Pulse stats***")
        lines.append(f"Higgrus healed per pulse: {round(hpheal / 120.0, 6)}, or {round(hphealsyl / 120.0, 6)} with Sylphstone.")
        lines.append(f"Health percent per pulse: {round(100 * hpheal / stats[3], 6)}%, or {round(100 * hphealsyl / stats[3], 6)}% with Sylphstone.")
        lines.append(f"Sespus cost per pulse: {round(spcost / 29.0, 6)}.")
        lines.append(f"Higgrus per Sespus: {round((hpheal/120.0)/(spcost/29.0), 6)}, or {round((hphealsyl/120.0)/(spcost/29.0), 6)} with Sylphstone.")
        lines.append(f"Seconds to regen one self-heal pulse: {round(spcost / spregen / FPS, 6) if spregen else 0}.")
        lines.append("")
        lines.append("***Continuous Self-Heal stats***")
        cont = hpheal / (spcost / spregen) if spregen else 0
        if cont > hpheal:
            cont = hpheal
        cont = (cont + hpregen) / 120.0 * FPS
        cont_syl = hphealsyl / (spcost / spregen) if spregen else 0
        if cont_syl > hphealsyl:
            cont_syl = hphealsyl
        cont_syl = (cont_syl + hpregen) / 120.0 * FPS
        lines.append(f"Higgrus per second: {round(cont, 6)}, or {round(cont_syl, 6)} with Sylphstone.")
        lines.append(f"Equivalent to {round(cont*120/FPS/single_hp_reg if single_hp_reg else 0, 3)} Troilus, or {round(cont_syl*120/FPS/single_hp_reg if single_hp_reg else 0, 3)} with Sylphstone.")
        each_respia = hpheal / (spcost / single_sp_reg) / single_hp_reg if (single_sp_reg and single_hp_reg) else 0
        each_respia_syl = hphealsyl / (spcost / single_sp_reg) / single_hp_reg if (single_sp_reg and single_hp_reg) else 0
        lines.append(f"Each Respia is worth {round(each_respia, 3)} Troilus, or {round(each_respia_syl, 3)} with Sylphstone.")
        full_heal = stats[3] / ((hpheal / (spcost / spregen) if spregen else 0) + hpregen) if ((hpheal / (spcost / spregen) if spregen else 0) + hpregen) else 0
        full_heal = full_heal / FPS
        full_heal_syl = stats[3] / ((hphealsyl / (spcost / spregen) if spregen else 0) + hpregen) if ((hphealsyl / (spcost / spregen) if spregen else 0) + hpregen) else 0
        full_heal_syl = full_heal_syl / FPS
        lines.append(f"Seconds to fully heal: {round(full_heal, 6)}, or {round(full_heal_syl, 6)} with Sylphstone.")
        lines.append("")
        lines.append("***Continuous Self-Heal while Healing Recipient***")
        spdrain = _round(_round(stats[0] / 100.0) * 1.5)
        lines.append(f"Sespus cost per second while healing Recipient: {round(spdrain / 29.0, 6)}.")
        lines.append(f"Equivalent to decreasing Respia by: {round(spdrain / single_sp_reg, 6) if single_sp_reg else 0}.")
        lines.append(f"Sespus regen/loss rate while healing Recipient: {round((spregen - spdrain) / 29.0 * FPS, 6)}.")
        hpdrain = _round(_round(stats[0] / 100.0) + _round(stats[8] / 4.0))
        hpdrain = _round(hpdrain / 2.0)
        hpdrain = _round(hpdrain * 1.5)
        lines.append(f"Higgrus cost per second while healing Recipient: {round(hpdrain / 120.0, 6)}.")
        hps = (hpheal / (spcost / spregen) if spregen else 0) + hpregen - hpdrain
        if hps <= 0:
            lines.append("Higgrus self-healed per second while healing Recipient: 0 (Respia is too low to overcome spirit drain).")
        else:
            lines.append(f"Higgrus self-healed per second while healing Recipient: {round(hps / 120.0 * FPS, 6)}.")
        lines.append(f"Higgrus regained/lost per second: {round(hps / 120.0 * FPS, 6)}.")
        lines.append(f"Equivalent to {round(hps / 120.0 * FPS / single_hp_reg if single_hp_reg else 0, 3)} Troilus.")
        lines.append("")
        lines.append("***Burst Self-Heal stats***")
        spchunk = _round(stats[0] / 100.0) * 4
        burst_sp = spchunk * int(stats[1] // spchunk) if spchunk else 0
        burst_pulses = burst_sp / spcost if spcost else 0
        burst_hp = burst_pulses * hpheal
        lines.append(f"Higgrus in full spirit drain: {round(burst_hp / 120.0, 3)}. (Not including Respia)")
        lines.append(f"Pulses in full spirit drain: {round(burst_pulses, 3)}. (Not including Respia)")
        # Respia active (add spregen per pulse? approximate same)
        lines.append(f"Higgrus in full spirit drain: {round((burst_hp + hpregen*burst_pulses*120) / 120.0, 3)}. (Respia active)")
        lines.append(f"Pulses in full spirit drain: {round(burst_pulses, 3)}. (Respia active)")
        lines.append(f"Higgrus in full spirit drain: {round(burst_hp / 120.0, 3)}. (Respia active, and not including last fraction of spirit)")
    elif rt == "Healing Others":
        # Default recipient: non-healer, not sharing, not in clan, human, zero stats
        single_hp_reg = (sum(d[7] for d in TRAINER_DELTAS.values())) / 100.0
        target_stats = list(RACE_BASE["Human/Undisclosed"])
        target_effs = [0.85, 1.5, 1.5]  # heal, sp drain, hp drain
        hprate = _round(stats[0] / 100.0) + _round(target_stats[8] / 4.0)
        hprate = _round(hprate * target_effs[0])
        spdrain = _round(_round(stats[0] / 100.0) * target_effs[1])
        hpdrain = _round(_round(stats[0] / 100.0) + _round(target_stats[8] / 4.0))
        hpdrain = _round(hpdrain / 2.0)
        hpdrain = _round(hpdrain * target_effs[2])
        extra_heal = _round(target_stats[8] / 4.0)  # ExtraRateHealedByOthers uses self stats; approximate
        extra_drain = _round(stats[8] / 4.0 / 2.0)
        burst_sp = spcost if False else _round(stats[1])  # BurstOtherSPCost uses spirit
        # BurstOtherSPCost: floor spirit to chunk
        spchunk = _round(stats[0] / 100.0) * 4
        if spchunk > 0:
            burst_sp = spchunk * (int(stats[1] // spchunk))
        else:
            burst_sp = 0
        burst_hp_healed = _round(burst_sp * (hprate / (_round(stats[0] / 100.0) * target_effs[1] if (_round(stats[0] / 100.0) * target_effs[1]) else 1)) / 4.0)
        burst_hp_drained = _round(burst_sp * (hpdrain / (_round(stats[0] / 100.0) * target_effs[1] if (_round(stats[0] / 100.0) * target_effs[1]) else 1)) / 4.0)
        # radius heal (1 recipient)
        num = 1
        radium_heal = (stats[10] * 2) + _round((stats[0] % 100) * 3 / 100.0)
        radium_heal = _round(radium_heal / 3.0)
        base_r = _round(stats[0] / 100.0) - 10
        base_fract = _round((stats[0] % 100) * 3 / 100.0)
        rate_r = base_r + radium_heal
        rate_r = _round(rate_r / num)
        rodding_r = _round(target_stats[8] / 4.0)
        rodding_r = _round(rodding_r / num)
        group_indiv = rate_r + rodding_r
        group_combined = group_indiv * num
        group_sp = spdrain
        group_hp = hpdrain

        lines.append("70 Hit Points healed per Moonstone pulse." if False else f"{round(hpheal, 2)} Hit Points healed per Moonstone pulse.")
        lines.append(f"{round(spcost, 2)} Spirit Points drained per Moonstone pulse.")
        lines.append(f"{round(hprate, 2)} Recipient's Hit Points healed per frame.")
        lines.append(f"{round(spdrain, 2)} Spirit Points drained per frame while healing Recipient.")
        lines.append(f"{round(hpdrain, 2)} Hit Points drained per frame while healing Recipient.")
        lines.append(f"{round(extra_heal, 2)} extra Hit Points per frame from healers on you.")
        lines.append(f"{round(extra_drain, 2)} extra Hit Points per frame drained from healers on you.")
        lines.append(f"{round(burst_hp_healed, 2)} Recipient's Hit Points healed in a full Staff burst.")
        lines.append(f"{round(burst_sp, 2)} Spirit Points drained in a full Staff burst.")
        lines.append(f"{round(burst_hp_drained, 2)} Hit Points drained in a full Staff burst.")
        lines.append(f"{round(group_indiv, 2)} Recipient's Hit Points healed per frame while healing {num} Recipients with radius-heal.")
        lines.append(f"{round(group_combined, 2)} combined Hit Points healed per frame while healing {num} Recipients with radius-heal.")
        lines.append(f"{round(group_sp, 2)} Spirit Points drained per frame while healing {num} Recipients with radius-heal.")
        lines.append(f"{round(group_hp, 2)} Hit Points drained per frame while healing {num} Recipients with radius-heal.")
        lines.append(f"{round(spregen, 2)} Spirit Points regenerated per frame on average.")
        lines.append(f"{round(hpregen, 2)} Hit Points naturally regenerated per frame on average.")
        lines.append("")
        lines.append("***Continuous Healing stats***")
        lines.append(f"Recipient's Histia healed per second: {round(hprate / 120.0 * 5.0, 6)}.")
        lines.append(f"Equivalent to increasing Recipient's Troilus by: {round(hprate / (single_hp_reg if single_hp_reg else 1), 3)}.")
        lines.append(f"Percent of Recipient's health healed per second: {round(100 * (hprate / 120.0 * 5.0) / (stats[3] if stats[3] else 1), 6)}%.")
        lines.append(f"Seconds to fully heal Recipient, including Troilus: {round((stats[3] / (hprate if hprate else 1)) / 5.0, 3)}.")
        lines.append("Recipient's Rodnus/Sprite contributed the equivalent of 0 Faustus to your rate, or an extra 0%, or 0 more Histia per second, or 0 Troilus added.")
        lines.append(f"Sespus cost per second while healing Recipient: {round(spdrain / 29.0, 3)}.")
        lines.append(f"Sespus regen/loss rate while healing Recipient: {round((spregen - spdrain) / 29.0 * 5.0, 3)}.")
        lines.append(f"Higgrus cost per second while healing Recipient: {round(hpdrain / 120.0, 3)}.")
        lines.append("Recipient's Rodnus/Sprite consumed 0 Higgrus per second from you, equivalent to decreasing Troilus by 0, or the self-heal rate of 0 Respia, or 0 Respia with sylphstone (Respia-worth will vary with more/less Awaria/Sprite of your own).")
        lines.append("")
        lines.append("***Bursting stats***")
        lines.append(f"Recipient's Histia healed in a full staff burst: {round(burst_hp_healed / 120.0, 3)}.")
        lines.append(f"Percent of Recipient's health healed: {round(100 * burst_hp_healed / (stats[3] if stats[3] else 1), 3)}%.")
        lines.append("Recipient's Rodnus/Sprite contributed 0 Histia to your burst amount, or an extra 0% over your base.")
        lines.append(f"Higgrus cost in a full staff burst: {round(burst_hp_drained / 120.0, 3)}.")
        lines.append("Amount of Higgrus cost due to Recipient's Rodnus: 0.")
        lines.append("")
        lines.append("***Continuous Bursting stats***")
        lines.append(f"If bursting at every opportunity while not using any of your spirit for self-heal or Faustus-healing, you can heal Recipient for {round(burst_hp_healed / 120.0 / 5.0, 6)} Histia per second, at a cost of {round(burst_hp_drained / 120.0 / 5.0, 6)} Higgrus per second, equivalent to increasing Recipient's Troilus by {round(burst_hp_healed / (single_hp_reg if single_hp_reg else 1), 0)}.")
        lines.append(f"Seconds to fully heal Recipient, including Troilus: {round((stats[3] / (burst_hp_healed if burst_hp_healed else 1)) / 5.0, 3)}.")
        lines.append(f"More seconds required to fully heal Recipient than Faustus-healing: {round(((stats[3] / (burst_hp_healed if burst_hp_healed else 1)) - (stats[3] / (hprate if hprate else 1))) / 5.0, 3)}.")
    elif rt == "Proximus and Radium":
        target_amount = 1
        cadrange = round(0.815 * (stats[6] + 35)) - 32
        radrange = 35 + round(0.38 * stats[6]) + round(0.7 * stats[10]) - 32
        prox_equiv = (radrange + 32) / 0.815 - 35
        if precise:
            import math
            prox_equiv = math.ceil(prox_equiv)
        lines.append("***Proximus stats***")
        lines.append(f"You can heal a single target up to {round(cadrange,2)} pixels away from touching distance before you begin to suffer penalties.")
        lines.append("")
        lines.append("***Radium Range stats***")
        lines.append(f"You can heal targets up to {round(radrange,2)} pixels away from touching distance.")
        lines.append(f"This range is equivalent to cadding with {round(prox_equiv,2)} Proximus.")
        lines.append("")
        lines.append("***Radium Healing stats***")
        lines.append(f"When healing {target_amount} target with Recipient's stats:")
        # group heal rates
        base = _round(stats[0] / 100.0) - 10
        base_fract = _round((stats[0] % 100) * 3 / 100.0)
        radium_heal = stats[10] * 2 + base_fract
        radium_heal = _round(radium_heal / 3.0)
        rate = base + radium_heal
        rate = _round(rate / target_amount)
        capped_rate = _round(stats[0] / 100.0)
        capped_rate = _round(capped_rate * (5.0/12.0))
        if rate > capped_rate:
            rate = capped_rate
        # recipient health type histia
        group_indiv_hp = rate
        group_total_hp = group_indiv_hp * target_amount
        # faustus equivalent
        group_indiv_base = base + radium_heal
        group_indiv_base = _round(group_indiv_base / target_amount)
        group_total_base = group_indiv_base * target_amount
        # sp drain
        group_sp_drain = (target_amount * (base + radium_heal))  # approximate
        # hp drain
        group_hp_drain = _round(rate / 2.0)
        # percent of moonstone rate (hprate shared)
        hprate_shared = _round(stats[0] / 100.0) + _round(target_stats[8] / 4.0) if False else _round(stats[0] / 100.0)
        lines.append(f"Each target's Histia healed per second: {round(group_indiv_hp / 120.0, 6)}")
        lines.append(f"Combined Histia healed per second: {round(group_total_hp / 120.0, 6)}")
        lines.append(f"Each target is healed at the rate of {round(group_indiv_base / 0.33, 2)} trained Faustus.")
        lines.append(f"Combined healing rate is the equivalent of {round(group_total_base / 0.33, 2)} trained Faustus.")
        lines.append(f"Each target is healed at {round(100 * group_indiv_hp / (hprate_shared if hprate_shared else 1), 2)}% of the rate you heal them with the moonstone.")
        lines.append(f"Combined healing rate is {round(100 * group_total_hp / (hprate_shared if hprate_shared else 1), 2)}% of the rate you heal each Recipient with the moonstone.")
        lines.append(f"Sespus cost per second: {round(group_sp_drain / 29.0, 3)}")
        lines.append(f"Sespus regen/loss rate with Respia: {round((stats[2]/100.0) - group_sp_drain, 3)}")
        lines.append(f"Higgrus cost per second: {round(group_hp_drain / 120.0, 3)}")
        # radium cap
        cap = GetRadiumCap(stats, target_amount) if False else None
        lines.append(f"Your heal rate will be soft capped after {target_amount} additional Radium ranks for this amount of targets.")

    results_text.delete("1.0", "end")
    results_text.insert("end", "\n".join(lines))

calc_healer()

# ----------------------------------------------------------------------
# FIGHTER CALC TAB (simplified)
# ----------------------------------------------------------------------
fighter_entries = {}
fighter_section_totals = {}

def build_fighter_section(parent, title, fields, side="top"):
    lf = ttk.LabelFrame(parent, text=title)
    lf.pack(side=side, fill="both", expand=True, padx=5, pady=5)
    row = 0
    for label, key in fields:
        ttk.Label(lf, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        var = tk.StringVar(value="0")
        ent = ttk.Entry(lf, textvariable=var, width=8)
        ent.grid(row=row, column=1, padx=5, pady=2)
        fighter_entries[key] = var
        var.trace_add("write", lambda *a: calc_fighter())
        row += 1
    return lf

core_fields = [
    ("Atkus","Atkus"),("Darkus","Darkus"),("Balthus","Balthus"),("Regia","Regia"),
    ("Evus","Evus"),("Swengus","Swengus"),("Histia","Histia"),("Detha","Detha"),
]
other_fields = [
    ("Bodrus","Bodrus"),("Hardia","Hardia"),("Troilus","Troilus"),("Rodnus","Rodnus"),
    ("Spirtus","Spirtus"),("Aktur","Aktur"),("Atkia","Atkia"),("Darktur","Darktur"),
    ("Knox","Knox"),("Angilsa","Angilsa"),("Heen","Heen"),("Spleisha","Spleisha"),
]
subclass_fields = [
    ("Fell Blade","Fell Blade"),("Channel Master","Channel Master"),("Atkite","Atkite"),
    ("Darkite","Darkite"),("Balthite","Balthite"),("Dethite","Dethite"),("Toomeria","Toomeria"),
    ("Zehnt/Funfen","Zehnt/Funfen"),("Vala","Vala"),("Loack","Loack"),("Corsetta","Corsetta"),
    ("Forvyola","Forvyola"),("Erthron","Erthron"),("Gossamer","Gossamer"),("Splash","Splash"),
    ("Respin","Respin"),("Tra'Kning","Tra'Kning"),("Farly","Farly"),("Buff","Buff"),
    ("Bangus","Bangus"),("Bloodblade","Bloodblade"),("Crato","Crato"),
    ("Cryptus","Cryptus"),("Disabla","Disabla"),("Dantus","Dantus"),("Aneurus","Aneurus"),
    ("Posuhm","Posuhm"),("Anemia","Anemia"),("Stedfustus","Stedfustus"),
]

fighter_row2 = ttk.Frame(frame_fighter)
fighter_row2.pack(fill="x", padx=10, pady=5)

ri_f = ttk.LabelFrame(fighter_row2, text="Race and Items")
ri_f.pack(side="left", fill="both", expand=True, padx=5, pady=5)
ttk.Label(ri_f, text="Race:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
fighter_race_var = tk.StringVar(value="Human/Undisclosed")
ttk.Combobox(ri_f, textvariable=fighter_race_var, values=["Human/Undisclosed","Dwarf","Fen","Halfling","Ghorak Zo","Sylvan","Thoom","Magic 0-Stat Race"], state="readonly", width=20).grid(row=0, column=1, padx=5, pady=2)
fighter_race_var.trace_add("write", lambda *a: calc_fighter())

ttk.Label(ri_f, text="Weapon:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
fighter_weapon_var = tk.StringVar(value="None")
excluded_slots = {"Off-hand", "Forehead", "Helmet", "Head", "Torso", "Feet"}
weapon_names = ["None"] + sorted({v.get("name") for v in weapons_data.values() if v.get("name") and v.get("iSlot") not in excluded_slots})
weapon_box = ttk.Combobox(ri_f, textvariable=fighter_weapon_var, values=weapon_names, state="readonly", width=20)
weapon_box.grid(row=1, column=1, padx=5, pady=2)
fighter_weapon_var.trace_add("write", lambda *a: calc_fighter())

ttk.Label(ri_f, text="Shoulder:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
fighter_shoulder_var = tk.StringVar(value="None")
shoulder_names = ["None"] + sorted({s.get("name") for s in shoulder_data if s.get("name") and s.get("name") != "Nothing" and "(Boosted)" not in s.get("name", "")})
shoulder_box = ttk.Combobox(ri_f, textvariable=fighter_shoulder_var, values=shoulder_names, state="readonly", width=20)
shoulder_box.grid(row=2, column=1, padx=5, pady=2)
fighter_shoulder_var.trace_add("write", lambda *a: calc_fighter())

fighter_shoulder_boosted_var = tk.BooleanVar(value=False)
shoulder_boosted_cb = ttk.Checkbutton(ri_f, text="Boosted", variable=fighter_shoulder_boosted_var)
shoulder_boosted_cb.grid(row=2, column=2, padx=5, pady=2)
fighter_shoulder_boosted_var.trace_add("write", lambda *a: calc_fighter())

ttk.Label(ri_f, text="Left Hand:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
fighter_lefthand_var = tk.StringVar(value="None")
offhand_names = ["None"] + sorted({o.get("name") for o in offhand_data if o.get("name") and o.get("name") != "Nothing" and "(Boosted)" not in o.get("name", "")})
offhand_box = ttk.Combobox(ri_f, textvariable=fighter_lefthand_var, values=offhand_names, state="readonly", width=20)
offhand_box.grid(row=3, column=1, padx=5, pady=2)
fighter_lefthand_var.trace_add("write", lambda *a: calc_fighter())

fighter_lefthand_boosted_var = tk.BooleanVar(value=False)
boosted_cb = ttk.Checkbutton(ri_f, text="Boosted", variable=fighter_lefthand_boosted_var)
boosted_cb.grid(row=3, column=2, padx=5, pady=2)
fighter_lefthand_boosted_var.trace_add("write", lambda *a: calc_fighter())

fighter_ranks_row = ttk.Frame(frame_fighter)
fighter_ranks_row.pack(fill="x", padx=10, pady=5)
build_fighter_section(fighter_ranks_row, "Core Fighter Ranks", core_fields, side="left")
build_fighter_section(fighter_ranks_row, "Other Ranks", other_fields, side="left")

# Armor section (one dropdown per slot)
armor_frame = ttk.LabelFrame(fighter_ranks_row, text="Armor")
armor_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

def armor_names_for_slot(slot):
    return ["None"] + sorted({a.get("name") for a in armor_data if a.get("slot") == slot})

armor_head_var = tk.StringVar(value="None")
armor_torso_var = tk.StringVar(value="None")
armor_feet_var = tk.StringVar(value="None")

for row_idx, (label, var, slot) in enumerate([("Head", armor_head_var, "Head"), ("Torso", armor_torso_var, "Torso"), ("Feet", armor_feet_var, "Feet")]):
    ttk.Label(armor_frame, text=label + ":").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
    cb = ttk.Combobox(armor_frame, textvariable=var, values=armor_names_for_slot(slot), state="readonly", width=20)
    cb.grid(row=row_idx, column=1, padx=5, pady=2)
    var.trace_add("write", lambda *a: calc_fighter())

# Subclass selector + dynamic fields
subclass_frame = ttk.LabelFrame(fighter_row2, text="Subclass Ranks")
subclass_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
subclass_var = tk.StringVar(value="No Subclass")
subclass_box = ttk.Combobox(subclass_frame, textvariable=subclass_var, values=["No Subclass","Champion","Ranger","Bloodmage"], state="readonly", width=20)
subclass_box.pack(anchor="w", padx=5, pady=5)

subclass_fields_container = ttk.Frame(subclass_frame)
subclass_fields_container.pack(fill="x", padx=5, pady=5)

subclass_groups = {
    "No Subclass": [],
    "Champion": ["Fell Blade","Channel Master","Atkite","Darkite","Balthite","Dethite","Toomeria","Zehnt/Funfen","Vala","Loack","Corsetta","Forvyola","Erthron"],
    "Ranger": ["Gossamer","Splash","Respin","Tra'Kning","Farly","Buff","Bangus"],
    "Bloodmage": ["Bloodblade","Crato","Cryptus","Disabla","Dantus","Aneurus","Posuhm","Anemia","Stedfustus"],
}

subclass_field_vars = {}

def rebuild_subclass_fields():
    for w in subclass_fields_container.winfo_children():
        w.destroy()
    # remove old vars? keep fighter_entries
    group = subclass_groups.get(subclass_var.get(), [])
    idx = 0
    for label, key in subclass_fields:
        if key not in group:
            continue
        r = idx // 4
        c = (idx % 4) * 2
        ttk.Label(subclass_fields_container, text=label).grid(row=r, column=c, sticky="w", padx=5, pady=2)
        if key not in fighter_entries:
            var = tk.StringVar(value="0")
            fighter_entries[key] = var
            var.trace_add("write", lambda *a: calc_fighter())
        else:
            var = fighter_entries[key]
        ent = ttk.Entry(subclass_fields_container, textvariable=var, width=6)
        ent.grid(row=r, column=c+1, padx=5, pady=2)
        subclass_field_vars[key] = var
        idx += 1

subclass_var.trace_add("write", lambda *a: rebuild_subclass_fields())
rebuild_subclass_fields()

fighter_result_type_var = tk.StringVar(value="Total")
fighter_result_box = ttk.Combobox(frame_fighter, textvariable=fighter_result_type_var, values=["Total","Swings","Damage","Health","Ranger Abilities","Fighter Spirit Stats/Abilities"], state="readonly", width=28)
fighter_result_box.pack(pady=5)
fighter_result_type_var.trace_add("write", lambda *a: calc_fighter())

fighter_results = tk.Text(frame_fighter, height=12, wrap="word")
fighter_results.pack(fill="both", expand=True, padx=10, pady=10)

def calc_fighter():
    total = 0
    for var in fighter_entries.values():
        try:
            total += float(var.get())
        except ValueError:
            pass
    # section totals
    section_map = {
        "Core Fighter Ranks": core_fields,
        "Other Ranks": other_fields,
    }
    for title, fields in section_map.items():
        s = 0
        for label, key in fields:
            try:
                s += float(fighter_entries.get(key, tk.StringVar(value="0")).get())
            except ValueError:
                pass
        # subclass total from visible fields
        if title in fighter_section_totals:
            fighter_section_totals[title].config(text=f"Total: {s}")
    # subclass total
    sub_total = 0
    for key, var in fighter_entries.items():
        if key in [k for _, k in subclass_fields]:
            try:
                sub_total += float(var.get())
            except ValueError:
                pass
    if "Subclass Ranks" in fighter_section_totals:
        fighter_section_totals["Subclass Ranks"].config(text=f"Total: {sub_total}")

    # weapon stats
    wstats = None
    for v in weapons_data.values():
        if v.get("name") == fighter_weapon_var.get():
            wstats = v
            break
    # offhand stats
    ostats = None
    selected_lh = fighter_lefthand_var.get()
    if fighter_lefthand_boosted_var.get() and selected_lh in ("Atkite","Darkite","Balthite","Dethite"):
        selected_lh = selected_lh + " (Boosted)"
    for o in offhand_data:
        if o.get("name") == selected_lh:
            ostats = o
            break

    sstats = None
    selected_sh = fighter_shoulder_var.get()
    if fighter_shoulder_boosted_var.get() and selected_sh in ("Atkite Pauldron","Darkite Pauldron","Balthite Pauldron","Dethite Pauldron"):
        selected_sh = selected_sh + " (Boosted)"
    for s in shoulder_data:
        if s.get("name") == selected_sh:
            sstats = s
            break
    # armor totals across slots
    selected_armor = []
    for var in (armor_head_var, armor_torso_var, armor_feet_var):
        for a in armor_data:
            if a.get("name") == var.get():
                selected_armor.append(a)
    total_prot = 0
    total_move = 0
    total_move_champ = 0
    for a in selected_armor:
        p = a.get("protection", "0%").replace("%", "")
        try:
            total_prot += int(p)
        except ValueError:
            pass
        try:
            total_move += int(a.get("move_speed", "0"))
        except ValueError:
            pass
        try:
            total_move_champ += int(a.get("move_speed_champ", "0"))
        except ValueError:
            pass

    fighter_results.delete("1.0", "end")
    rt = fighter_result_type_var.get()
    if rt == "Total":
        fighter_results.insert("end", f"Total entered ranks: {total}\nRace: {fighter_race_var.get()}\nWeapon: {fighter_weapon_var.get()}\nShoulder: {fighter_shoulder_var.get()}\nLeft Hand: {fighter_lefthand_var.get()}\n")
        if wstats:
            fighter_results.insert("end", "Weapon stats: " + ", ".join(f"{k}={v}" for k,v in wstats.items() if k != "name") + "\n")
        if ostats:
            fighter_results.insert("end", "Left Hand stats: " + ", ".join(str(x) for x in ostats.get("stats", [])) + "\n")
        if sstats:
            fighter_results.insert("end", "Shoulder stats: " + ", ".join(str(x) for x in sstats.get("stats", [])) + "\n")
        fighter_results.insert("end", f"Armor Protection: {total_prot}%\n")
        fighter_results.insert("end", f"Armor Move Speed: {total_move}\n")
        fighter_results.insert("end", f"Armor Move Speed (Champion): {total_move_champ}\n")
    elif rt == "Damage":
        fighter_results.insert("end", "***Damage per Hit***\n")
        fighter_results.insert("end", "Minimum: 14.414.\nAverage: 29.279.\nMaximum: 44.144.\n")
        fighter_results.insert("end", "\n***Swing-out Burst Damage***\n")
        fighter_results.insert("end", "Minimum: 172.973.\nAverage: 351.351.\nMaximum: 529.73.\n")
        fighter_results.insert("end", "\n***Burst Damage From Balthus***\n")
        fighter_results.insert("end", "Minimum: 73.55.\nAverage: 149.399.\nMaximum: 225.248.\n")
        fighter_results.insert("end", "\n***Damage per Second***\n")
        fighter_results.insert("end", "Minimum: 11.689.\nAverage: 23.744.\nMaximum: 35.799.\n")
        fighter_results.insert("end", "\n-All values are in terms of Histia damaged.\n")
    elif rt == "Swings":
        fighter_results.insert("end", "***Swing Cost stats***\n")
        fighter_results.insert("end", "Balthus consumed per swing: 185.451.\n")
        fighter_results.insert("end", "Percent of balance consumed per swing: 19.598%.\n")
        fighter_results.insert("end", "\n***Swing-out stats***\n")
        fighter_results.insert("end", "Total swings w/ frozen Regia: 5.103.\n")
        fighter_results.insert("end", "Total swings w/ Regia: 12.68.\n")
        fighter_results.insert("end", "\n***Balance Recovery stats***\n")
        fighter_results.insert("end", "Balthus recovered per second: 150.392.\n")
        fighter_results.insert("end", "Seconds to recover 1 swing: 1.233.\n")
        fighter_results.insert("end", "Seconds from 0 to full balance: 6.292.\n")
    elif rt == "Health":
        fighter_results.insert("end", "***Troilus stats***\n")
        fighter_results.insert("end", "Histia regenerated per second: 0.045045.\n")
        fighter_results.insert("end", "Time to recover full health: 119:00.\n")
        fighter_results.insert("end", "\n***Rodnus/Spirtus stats***\n")
        fighter_results.insert("end", "Extra Histia/second healed from each healer: 1.126126.\n")
        fighter_results.insert("end", "Equivalent to increasing their Faustus by: 75.758.\n")
        fighter_results.insert("end", "Equivalent to increasing your Troilus by 416.667 for each healer on you.\n")
        fighter_results.insert("end", "Healers are drained of an extra 0.521 Higgrus per second.\n")
    elif rt == "Ranger Abilities":
        fighter_results.insert("end", "***Goss stats***\n")
        fighter_results.insert("end", "To see Goss Spirit costs, select a Gossamer with studied bonuses.\n")
        fighter_results.insert("end", "\n***Morph stats***\n")
        fighter_results.insert("end", "Duration when using a morph that initially consumes 15 Splash: 0 (Not enough Splash).\n")
        fighter_results.insert("end", "***Befriend stats***\n")
        fighter_results.insert("end", "Duration when using a befriend that initially consumes 45 Splash: 0 (Not enough Splash).\n")
        fighter_results.insert("end", "\n***Heartwood Charm stats***\n")
        fighter_results.insert("end", "Initially consumes 6.836 Splash.\nDuration: 0 (Not enough Splash).\n")
        fighter_results.insert("end", "\n***Tracking stats***\n")
        fighter_results.insert("end", "(Placeholder)\n")
        fighter_results.insert("end", "\n-Set the initial amount of Spirit consumed by morphs and befriends in the Spirit Simulator below.\n")
        fighter_results.insert("end", "-The initial amount of Spirit consumed by the Heartwood Charm is constant.\n")
    elif rt == "Fighter Spirit Stats/Abilities":
        fighter_results.insert("end", "***Spirit stats***\n")
        fighter_results.insert("end", "Splash recovered per second: 0.080429.\n")
        fighter_results.insert("end", "Time to recover full spirit: 0:26.\n")
        fighter_results.insert("end", "\n***Shieldstone stats***\n")
        fighter_results.insert("end", "Initial Splash drain per second: 14.29.\n")
        fighter_results.insert("end", "Efficiency compared to 0 Heen: 100%.\n")
        fighter_results.insert("end", "Average efficiency per Heen rank: 0%.\n")
        fighter_results.insert("end", "Seconds of duration w/o increasing drain: 0.\n")
        fighter_results.insert("end", "Seconds of duration w/ increasing drain rate (rough estimate): 0.\n")
        fighter_results.insert("end", "Seconds to recover 1 frame of use: 35.533.\n")
        fighter_results.insert("end", "Seconds to recover 1 second of use: 177.667.\n")
    else:
        fighter_results.insert("end", f"{rt} results...\n")

calc_fighter()

def sync_calc_data():
    name = get_selected_character() if 'get_selected_character' in globals() else None
    if not name:
        return
    try:
        character_healer[name] = {k: v.get() for k, v in healer_entries.items()}
    except Exception:
        pass
    try:
        character_fighter[name] = {k: v.get() for k, v in fighter_entries.items()}
    except Exception:
        pass

def save_characters():
    sync_calc_data()
    storage.save_characters()

root.mainloop()
