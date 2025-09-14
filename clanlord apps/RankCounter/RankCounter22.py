import os
import sys
import traceback
import codecs
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import concurrent.futures
import re

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

base_dir = os.path.dirname(os.path.abspath(__file__))
words_file_path       = os.path.join(base_dir, 'rankmessages.txt')
replacement_file_path = os.path.join(base_dir, 'trainers.txt')
special_file_path     = os.path.join(base_dir, 'specialphrases.txt')

merged_counts      = {}
current_folder_name= None
executor           = concurrent.futures.ThreadPoolExecutor(max_workers=4)

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
    excluded = ["says,", "growls,", "yells,", "ponders,"]
    counts   = {w: 0 for w in words}
    for content in texts:
        for line in content.splitlines():
            low = line.lower()
            if any(exc in low for exc in excluded):
                continue
            for w in words:
                counts[w] += line.count(w)
    return counts

# -- New: Very Forgiving Special-Line Counter -------------------------------

import re

def count_special_lines(texts):
    """
    Reads specialphrases.txt, strips timestamps, extracts lines of the form
    “You have {phrase} {Trainer}”, then builds a label:
      - first 4 words of {phrase}
      - the Trainer name
      - if the phrase contains “ways”, “movements” or “essence”, append that type
    Returns a dict mapping each label to its count.
    """
    # 1) load & normalize your phrases (drop trailing dots)
    raw = [p.rstrip('.') for p in read_words_from_file(special_file_path)]
    # sort by length descending to match longest phrase first
    phrases = sorted(raw, key=len, reverse=True)
    phrases_lc = [p.lower() for p in phrases]
    # types to detect
    types = ('ways', 'movements', 'essence')

    ts_strip = re.compile(r'^\[?\d{1,2}:\d{2}:\d{2}\]?\s*>?\s*')
    special = {}

    for content in texts:
        for raw_line in content.splitlines():
            line = ts_strip.sub('', raw_line.strip())
            low  = line.lower()
            if 'you have ' not in low:
                continue

            # everything after "you have "
            after = line[low.index('you have ') + len('you have '):].strip()

            # match the longest phrase
            for idx, phrase_lc in enumerate(phrases_lc):
                if after.lower().startswith(phrase_lc):
                    orig_phrase = phrases[idx]
                    rest = after[len(phrase_lc):].lstrip()
                    trainer = rest.split('.', 1)[0].strip()
                    if not trainer:
                        break

                    # first 4 words of the phrase
                    first4 = ' '.join(orig_phrase.split()[:4])

                    # detect type
                    found = next((t for t in types if t in orig_phrase.lower()), None)
                    if found:
                        # append the type in parentheses
                        label = f"{first4} {trainer} ({found})"
                    else:
                        label = f"{first4} {trainer}"

                    special[label] = special.get(label, 0) + 1
                    break

    return special

# In your scan_and_aggregate, replace the special-occ merge with:

def scan_and_aggregate(folder_path):
    # … load words/replacements, read_text_files, count_word_occurrences as before …
    word_occ    = count_word_occurrences(texts, words)
    special_occ = count_special_lines(texts)

    agg = {}
    # aggregate normal ranks
    for w, c in word_occ.items():
        if c:
            t = mapping[w]
            agg[t] = agg.get(t, 0) + c

    # aggregate special-line counts by our new label
    for label, cnt in special_occ.items():
        agg[label] = agg.get(label, 0) + cnt

    return agg, os.path.basename(folder_path)

# -- Background Task ---------------------------------------------------------

def scan_and_aggregate(folder_path):
    words        = read_words_from_file(words_file_path)
    replacements = read_words_from_file(replacement_file_path)
    if len(words) != len(replacements):
        raise ValueError("rankmessages.txt and trainers.txt lengths differ")

    mapping     = dict(zip(words, replacements))
    texts       = read_text_files(folder_path)
    word_occ    = count_word_occurrences(texts, words)
    special_occ = count_special_lines(texts)

    agg = {}
    for w, c in word_occ.items():
        if c:
            t = mapping[w]
            agg[t] = agg.get(t, 0) + c

    for phrase, cnt in special_occ.items():
        agg[phrase] = agg.get(phrase, 0) + cnt

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
        merged_counts[name] = merged_counts.get(name, 0) + cnt

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
                f.write(f"{n},{c}\n")
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
