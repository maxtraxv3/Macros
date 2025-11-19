import os
import sys
import traceback
import codecs
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import concurrent.futures
import re

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

    agg = {}
    # normal word counts
    for w, c in word_occ.items():
        if c:
            t = mapping[w]
            agg[t] = agg.get(t, 0) + c

    # special counts with bonus ranks included
    for trainer, info in filtered_special.items():
        label = info["label"]
        cnt   = info.get("count_str", str(info["count"]))  # use count_str if available
        agg[label] = cnt

    return agg, os.path.basename(folder_path)

# -- UI Callbacks & GUI Setup -----------------------------------------------

def on_scan_done(fut):
    try:
        agg_counts, new_folder = fut.result()
    except Exception as e:
        messagebox.showerror("Scan Error", str(e))
        return

    global merged_counts, current_folder_name
    if new_folder != current_folder_name:
        merged_counts.clear()
        current_folder_name = new_folder

    for name, cnt in agg_counts.items():
        merged_counts[name] = cnt  # cnt is already a string like "42 (3)"

    for item in table.get_children():
        table.delete(item)
    for name, cnt in merged_counts.items():
        table.insert("", "end", values=(name, cnt))

def load_files_and_count_words():
    folder = filedialog.askdirectory()
    if not folder:
        return
    fut = executor.submit(scan_and_aggregate, folder)
    fut.add_done_callback(lambda f: root.after(0, on_scan_done, f))

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

# -- Main GUI ---------------------------------------------------------------

root = tk.Tk()
root.title("Textlog Rank Counter")

tk.Button(root, text="Load Text log folder", command=load_files_and_count_words)\
  .pack(pady=10)
tk.Button(root, text="Save Merged Results",   command=save_output)\
  .pack(pady=5)

table = ttk.Treeview(root, columns=("Trainer", "Ranks"), show="headings")
table.heading("Trainer", text="Trainer")
table.heading("Ranks",   text="Ranks")
table.column("Trainer", width=300, stretch=True)
table.column("Ranks",   width= 80, stretch=False)
table.pack(pady=10, fill="both", expand=True)

root.mainloop()