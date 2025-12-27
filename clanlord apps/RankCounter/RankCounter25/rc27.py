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

CHAR_FILE = "characters.json"
character_ranks = {}
character_creatures = {}

def save_characters():
    data = {}
    for name in character_folders:
        data[name] = {
            "folders": character_folders.get(name, []),
            "ranks": character_ranks.get(name, {}),
            "creatures": character_creatures.get(name, {})
        }
    with open(CHAR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_characters():
    if not os.path.exists(CHAR_FILE):
        return
    with open(CHAR_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for name, info in data.items():
        character_folders[name] = info.get("folders", [])
        character_ranks[name] = info.get("ranks", {})
        character_creatures[name] = info.get("creatures", {})

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
character_folders = {}
current_folder_name= None
executor           = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# -- Shared Exclusion Helper -------------------------------------------------

def is_excluded(line: str) -> bool:
    """Return True if the line should be skipped."""
    low = line.lower().strip()
    excluded = ["says,", "growls,", "yells,", "ponders,"]
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


# -- File / Folder Readers ---------------------------------------------------

def read_words_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return [line.strip() for line in smart_read_file(file_path).splitlines() if line.strip()]

def read_text_files(folder_path):
    texts = []
    for fname in os.listdir(folder_path):
        fpath = os.path.join(folder_path, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            texts.append(smart_read_file(fpath))
        except UnicodeDecodeError:
            continue
    return texts

def count_word_occurrences(texts, words):
    counts = {w: 0 for w in words}
    for content in texts:
        for line in content.splitlines():
            if is_excluded(line):
                continue
            for w in words:
                counts[w] += line.count(w)
    return counts

# -- Special-Line Counter (nested dict: last phrase + count) -----------------

def count_special_lines(texts):
    import re

    raw = [p.rstrip('.') for p in read_words_from_file(special_file_path)]
    phrases = sorted(raw, key=len, reverse=True)
    phrases_lc = [p.lower() for p in phrases]
    types = ('ways', 'movements', 'essence')

    ts_strip = re.compile(r'^\[?\d{1,2}:\d{2}:\d{2}\w?\]?\s*[•>:-]*\s*')

    prog_rx = re.compile(
        r'you have .*? about the (ways|movements|essence) of the (.+?)\.\s*$',
        re.IGNORECASE
    )

    special = {}
    exclude = {"ways": set(), "movements": set(), "essence": set()}

    # ✅ Track study state
    study_state = {}

    # ✅ Track apply-learning sequences
    pending_apply = {}
    bonus_ranks = {}

    def norm(s: str) -> str:
        s = s.strip()
        s = re.sub(r'[^\w\s\'-]', '', s)
        return s.lower()

    for content in texts:
        for raw_line in content.splitlines():
            line = ts_strip.sub('', raw_line.strip())
            if is_excluded(line):
                continue
            low = line.lower()

            # --- Apply learning start ---
            if "would you like to apply some of your learning to" in low and "’s lessons" in low:
                m = re.search(r"apply some of your learning to (.+?)’s lessons", line)
                if m:
                    trainer = norm(m.group(1))
                    pending_apply[trainer] = True
                    print(f"Apply-learning started for {trainer}")
                continue

            # --- Apply learning confirmation ---
            if "congratulations" in low and "you should now understand much more of" in low:
                m = re.search(r"much more of (.+?)’s teachings", line)
                if m:
                    trainer = norm(m.group(1))
                    if pending_apply.get(trainer):
                        bonus_ranks[trainer] = bonus_ranks.get(trainer, 0) + 1
                        pending_apply[trainer] = False
                        print(f"Bonus rank added for {trainer}")
                continue

            # --- Abandon / begin study logic (from earlier) ---
            if "you abandon your study of the" in low:
                m = re.search(r"you abandon your study of the (.+?)\.", low)
                if m:
                    monster = norm(m.group(1))
                    study_state[monster] = False
                    print(f"Marked {monster} as abandoned")
                continue

            if "you begin studying the ways of the" in low:
                m = re.search(r"you begin studying the ways of the (.+?)\.", low)
                if m:
                    monster = norm(m.group(1))
                    study_state[monster] = True
                    print(f"Marked {monster} as active (ways)")
                continue

            if "you begin studying the movements of the" in low:
                m = re.search(r"you begin studying the movements of the (.+?)\.", low)
                if m:
                    monster = norm(m.group(1))
                    study_state[monster] = True
                    print(f"Marked {monster} as active (movements)")
                continue

            if "you begin studying the essence of the" in low:
                m = re.search(r"you begin studying the essence of the (.+?)\.", low)
                if m:
                    monster = norm(m.group(1))
                    study_state[monster] = True
                    print(f"Marked {monster} as active (essence)")
                continue

            # --- Training exclusions ---
            if "you learn to fight the" in low and "more effectively" in low:
                m = re.search(r"you learn to fight the (.+?) more effectively", low)
                if m:
                    monster = norm(m.group(1))
                    print(f"Excluding {monster} from movements")
                    exclude["movements"].add(monster)
                continue

            if "you learn to befriend the" in low:
                m = re.search(r"you learn to befriend the (.+?)\.", low)
                if m:
                    monster = norm(m.group(1))
                    print(f"Excluding {monster} from ways")
                    exclude["ways"].add(monster)
                continue

            if "you learn to assume the form of the" in low:
                m = re.search(r"you learn to assume the form of the (.+?)\.", low)
                if m:
                    monster = norm(m.group(1))
                    print(f"Excluding {monster} from essence")
                    exclude["essence"].add(monster)
                continue

            if 'you have ' not in low:
                continue

            # --- Regex-based progression parsing ---
            pm = prog_rx.search(low)
            parsed_category = None
            parsed_monster = None
            if pm:
                parsed_category = pm.group(1).lower()
                parsed_monster = norm(pm.group(2))

                if study_state.get(parsed_monster) is False:
                    print(f"Skipping {parsed_monster} ({parsed_category}) because study abandoned")
                    continue

                if parsed_monster in exclude.get(parsed_category, set()):
                    print(f"Skipping {parsed_monster} from {parsed_category} (regex match)")
                    continue

            # --- Phrase-based fallback ---
            after = line[low.index('you have ') + len('you have '):].strip()

            for idx, phrase_lc in enumerate(phrases_lc):
                if after.lower().startswith(phrase_lc):
                    orig_phrase = phrases[idx]
                    rest = after[len(phrase_lc):].lstrip()
                    trainer = rest.split('.', 1)[0].strip()
                    trainer_clean = norm(trainer)

                    if not trainer_clean:
                        break

                    first4 = ' '.join(orig_phrase.split()[:4])
                    found = next((t for t in types if t in orig_phrase.lower()), None)

                    category_for_check = parsed_category or found
                    monster_for_check = parsed_monster or trainer_clean

                    if study_state.get(monster_for_check) is False:
                        print(f"Skipping {trainer_clean} from {category_for_check} (abandoned)")
                        break

                    if category_for_check and monster_for_check in exclude[category_for_check]:
                        print(f"Skipping {trainer_clean} from {category_for_check} (phrase match)")
                        break

                    if found:
                        label = f"{first4} {trainer} ({found})"
                    else:
                        label = f"{first4} {trainer}"

                    if trainer not in special:
                        special[trainer] = {"label": label, "count": 1}
                    else:
                        special[trainer]["label"] = label
                        special[trainer]["count"] += 1
                    break

    # ✅ Attach bonus ranks to labels
    for trainer, info in special.items():
        bonus = bonus_ranks.get(norm(trainer), 0)
        if bonus:
            info["count_str"] = f"{info['count']} ({bonus})"
        else:
            info["count_str"] = str(info["count"])

    return special, exclude
    
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

# -- Background Task ---------------------------------------------------------

def scan_and_aggregate(folder_path):
    words        = read_words_from_file(words_file_path)
    replacements = read_words_from_file(replacement_file_path)
    if len(words) != len(replacements):
        raise ValueError("rankmessages.txt and trainers.txt lengths differ")

    mapping     = dict(zip(words, replacements))
    texts       = read_text_files(folder_path)
    word_occ    = count_word_occurrences(texts, words)
    special_occ, exclude = count_special_lines(texts)
    filtered_special = filter_finished_studies(special_occ, exclude)

    normal_ranks = {}
    special_creatures = {}

    # normal word counts
    for w, c in word_occ.items():
        if c:
            t = mapping[w]
            normal_ranks[t] = normal_ranks.get(t, 0) + c

    # special counts (ways / movements / essence)
    for trainer, info in filtered_special.items():
        label = info["label"]
        cnt   = info.get("count_str", str(info["count"]))
        special_creatures[label] = cnt

    return normal_ranks, special_creatures, os.path.basename(folder_path)

# -- UI Callbacks & GUI Setup -----------------------------------------------

def on_scan_done(fut):
    try:
        normal_ranks, special_creatures, new_folder = fut.result()
    except Exception as e:
        messagebox.showerror("Scan Error", str(e))
        return

    global merged_counts, current_folder_name
    if new_folder != current_folder_name:
        merged_counts.clear()
        current_folder_name = new_folder

    for item in table.get_children():
        table.delete(item)
        
    for name, cnt in merged_counts.items():
        table.insert("", "end", values=(name, cnt))

    for item in creature_table.get_children():
        creature_table.delete(item)

    # Fill ranks table
    for name, cnt in normal_ranks.items():
        table.insert("", "end", values=(name, cnt))

    # Fill creatures table
    for name, cnt in special_creatures.items():
        creature_table.insert("", "end", values=(name, cnt))
    
    # Save results to character
    name = get_selected_character()
    character_ranks[name] = normal_ranks
    character_creatures[name] = special_creatures
    save_characters()

def load_files_and_count_words():
    name = get_selected_character()
    if not name:
        messagebox.showerror("Error", "Select a character first.")
        return

    if name not in character_folders or not character_folders[name]:
        messagebox.showerror("Error", "This character has no folders assigned.")
        return

    # Clear previous results
    global merged_counts
    merged_counts.clear()

    # Scan each folder assigned to the character
    for folder in character_folders[name]:
        if not os.path.isdir(folder):
            continue

        fut = executor.submit(scan_and_aggregate, folder)
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

# ----------------------------------------------------------------------
# ------------------------- NEW GUI SECTION -----------------------------
# ----------------------------------------------------------------------

root = tk.Tk()
root.title("Textlog Rank Counter")

# ---------------- Buttons (Horizontal Layout) ----------------
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

ttk.Button(button_frame, text="Scan New Logs", command=load_files_and_count_words)\
    .pack(side="left", padx=5)

ttk.Button(button_frame, text="Rescan All Logs", command=rescan_all_logs)\
    .pack(side="left", padx=5)

#ttk.Button(button_frame, text="Save Merged Results", command=save_output)\
 #   .pack(side="left", padx=5)

# ---------------- Tabbed Notebook ----------------
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

frame_characters = ttk.Frame(notebook)
frame_folders = ttk.Frame(notebook)
frame_ranks = ttk.Frame(notebook)
frame_creatures = ttk.Frame(notebook)
frame_logsearch = ttk.Frame(notebook)

notebook.add(frame_characters, text="Characters")
notebook.add(frame_folders, text="Folders")
notebook.add(frame_ranks, text="Ranks")
notebook.add(frame_creatures, text="Creatures")
notebook.add(frame_logsearch, text="Log Search")

# ---------------- Characters Tab ----------------
load_characters()
character_list = tk.Listbox(frame_characters, height=10, width=40, exportselection=False)
character_list.pack(pady=10)

# Load characters from JSON (if any)
for name in character_folders.keys():
    character_list.insert(tk.END, name)

def add_character():
    new_name = tk.simpledialog.askstring("Add Character", "Enter new character name:")
    if new_name:
        character_list.insert(tk.END, new_name)
        character_folders[new_name] = []
        character_ranks[new_name] = {}
        character_creatures[new_name] = {}
        save_characters()

tk.Button(frame_characters, text="Add Character", command=add_character)\
    .pack(pady=5)

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
        save_characters()

        # Clear folder list if no characters left
        if character_list.size() == 0:
            folder_list.delete(0, tk.END)

tk.Button(frame_characters, text="Remove Character", command=remove_character)\
    .pack(pady=5)

# Helper to get selected character
def get_selected_character():
    sel = character_list.curselection()
    if not sel:
        return None
    return character_list.get(sel[0])

# ---------------- Folders Tab ----------------
tk.Label(frame_folders, text="Folders for selected character:").pack(pady=5)

folder_list = tk.Listbox(frame_folders, width=60, height=12)
folder_list.pack(pady=5)

def update_folder_list():
    folder_list.delete(0, tk.END)
    name = get_selected_character()
    if name and name in character_folders:
        for f in character_folders[name]:
            folder_list.insert(tk.END, f)

def on_character_selected(event=None):
    name = get_selected_character()
    if not name:
        return
    update_folder_list()
    
    for item in table.get_children():
        table.delete(item)
        
    if name in character_ranks:
        for r_name, r_cnt in character_ranks[name].items():
            table.insert("", "end", values=(r_name, r_cnt))

    for item in creature_table.get_children():
        creature_table.delete(item)

    if name in character_creatures:
        for c_name, c_cnt in character_creatures[name].items():
            creature_table.insert("", "end", values=(c_name, c_cnt))

character_list.bind("<<ListboxSelect>>", on_character_selected)

def add_folder():
    folder = filedialog.askdirectory()
    if folder:
        name = get_selected_character()
        if not name:
            messagebox.showerror("Error", "Select a character first.")
            return
        character_folders.setdefault(name, []).append(folder)
        update_folder_list()
        save_characters()

def remove_folder():
    sel = folder_list.curselection()
    if sel:
        folder = folder_list.get(sel[0])
        name = get_selected_character()
        if name:
            character_folders[name].remove(folder)
            update_folder_list()
            save_characters()

button_frame_folders = ttk.Frame(frame_folders)
button_frame_folders.pack(pady=10)

tk.Button(button_frame_folders, text="Add Folder", command=add_folder)\
    .pack(side="left", padx=5)

tk.Button(button_frame_folders, text="Remove Selected", command=remove_folder)\
    .pack(side="left", padx=5)

# ---------------- Ranks Table ----------------
table = ttk.Treeview(frame_ranks, columns=("Trainer", "Ranks"), show="headings")
table.heading("Trainer", text="Trainer")
table.heading("Ranks", text="Ranks")
table.column("Trainer", width=300, stretch=True)
table.column("Ranks", width=80, stretch=False)
table.pack(pady=10, fill="both", expand=True)

# ---------------- Creatures Table ----------------
creature_table = ttk.Treeview(frame_creatures, columns=("Creature", "Count"), show="headings")
creature_table.heading("Creature", text="Creature")
creature_table.heading("Count", text="Count")
creature_table.column("Creature", width=300, stretch=True)
creature_table.column("Count", width=80, stretch=False)
creature_table.pack(pady=10, fill="both", expand=True)

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
