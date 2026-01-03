import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

# === Sample trainer data (simplified for demo) ===
trainer_data = {
    "Atkus": {"Accuracy": 16, "Balance": 15, "Balance Recovery": 1},
    "Swengus": {"Balance": 30, "Balance Recovery": 7},
    "Balthus": {"Balance": 51},
    "Regia": {"Balance Recovery": 15},
    "Darkus": {"Min Damage": 6, "Max Damage": 6, "Balance": 18, "Balance Recovery": 1},
}

# === UI Setup ===
root = tk.Tk()
root.title("Trainer Stat Evaluator")

# === Dropdown for result category ===
result_mode_var = tk.StringVar(value="Swings")
result_selector = ttk.Combobox(root, textvariable=result_mode_var, values=[
    "Swings", "Damage", "Health", "Stats", "Personal Notes"
])
result_selector.grid(row=0, column=0, padx=10, pady=5)

# === Entry fields for trainer ranks ===
entries = {}
entry_frame = ttk.Frame(root)
entry_frame.grid(row=1, column=0, padx=10, pady=5)

for i, trainer in enumerate(sorted(trainer_data)):
    ttk.Label(entry_frame, text=trainer).grid(row=i, column=0, sticky="w")
    entry = ttk.Entry(entry_frame, width=10)
    entry.grid(row=i, column=1)
    entry.insert(0, "0")
    entries[trainer] = entry

# === Output box ===
output_box = tk.Text(root, width=70, height=20, wrap="word", font=("Courier", 10))
output_box.grid(row=2, column=0, padx=10, pady=10)

# === Evaluation logic ===
def evaluate():
    total_stats = {}
    for trainer, entry in entries.items():
        try:
            val = int(entry.get())
        except:
            val = 0
        for stat, gain in trainer_data.get(trainer, {}).items():
            total_stats[stat] = total_stats.get(stat, 0) + gain * val

    mode = result_mode_var.get()
    output_lines = [f"=== {mode} Results ==="]

    if mode == "Swings":
        bal = total_stats.get("Balance", 0)
        recov = total_stats.get("Balance Recovery", 0)
        output_lines += [
            f"Balthus consumed per swing: {bal * 0.054:.2f}",
            f"Percent of balance consumed per swing: {bal * 0.054 / 1.0 * 100:.2f}%",
            f"Balthus recovered per second: {recov * 0.17:.3f}",
            f"Seconds from 0 to full balance: {1.0 / (recov * 0.17):.2f}" if recov else "N/A"
        ]
    elif mode == "Damage":
        min_dmg = total_stats.get("Min Damage", 0)
        output_lines += [
            f"Min Histia hit: {0.054 * (min_dmg / 6):.3f}",
            f"Avg Histia hit: {0.108 * (min_dmg / 6):.3f}",
            f"Max Histia hit: {0.162 * (min_dmg / 6):.3f}"
        ]
    elif mode == "Health":
        output_lines += [f"Health: {total_stats.get('Health', 0)}"]
    elif mode == "Stats":
        for stat, val in sorted(total_stats.items()):
            output_lines.append(f"{stat}: {val}")
    elif mode == "Personal Notes":
        output_lines += ["This section is for your own notes."]

    output_box.config(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("end", "\n".join(output_lines))
    output_box.config(state="disabled")

# === Trigger evaluation on dropdown change ===
result_selector.bind("<<ComboboxSelected>>", lambda e: evaluate())

# === Evaluate button ===
ttk.Button(root, text="Evaluate", command=evaluate).grid(row=3, column=0, pady=5)

root.mainloop()
