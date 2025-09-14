import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import csv

# === Trainer data: per-rank stat gains ===
trainer_data = {
    # Core trainers
    "Atkus": {"Accuracy": 16, "Balance": 15, "Balance Recovery": 1},
    "Swengus": {"Balance": 30, "Balance Recovery": 7},
    "Histia": {"Health": 111},
    "Evus": {"Body": 1, "Accuracy": 4, "Health": 24, "Defense": 1, "Balance": 18, "Balance Recovery": 4, "Min Damage": 1, "Max Damage": 1},
    "Detha": {"Defense": 19, "Health": 3},
    "Balthus": {"Balance": 51},
    "Regia": {"Balance Recovery": 15},
    "Darkus": {"Min Damage": 6, "Max Damage": 6, "Balance": 18, "Balance Recovery": 1},
    "Aktur": {"Accuracy": 25},
    "Atkia": {"Accuracy": 13, "Min Damage": 3, "Max Damage": 3, "Balance Recovery": 3},
    "Darktur": {"Min Damage": 10, "Max Damage": 10},
    "Knox": {"Body": -1, "Accuracy": -4, "Health": -24, "Defense": -1, "Balance": 18, "Balance Recovery": -2, "Min Damage": 11, "Max Damage": 11},
    "Angilsa": {"Body": -1, "Accuracy": -4, "Health": -24, "Defense": -1, "Balance": -18, "Balance Recovery": 26, "Min Damage": -1, "Max Damage": -1},
    "Rodnus": {"Healing Receptivity": 2, "Health": 36},
    "Heen Slostid": {"Shieldstone Efficiency": 100},
    "Spleisha'Sul": {"Spirit": 373},

    # Champion weapons
    "Champion Weapon": {},  # shared rank input for Fell Blade, Tell Blade, Labrys

    # Other core trainers
    "Erthron": {"Body": 1, "Accuracy": 2, "Health": 21, "Defense": 7, "Balance": 15, "Balance Recovery": 2, "Min Damage": 1, "Max Damage": 1},
    "Forvyola": {"Health": 54, "Balance Recovery": 8},
    "Channel Master": {"Accuracy": 25, "Min Damage": 10.32, "Max Damage": 10.32, "Balance": 51, "Defense": 19},
    "Vala Loack": {},
    "Corsetta": {},
    "Nomoss": {},
    "Toomeria": {"Spirit": 500},
    "Zehnt": {"Spirit Recovery": 20},

    # Ranger trainers
    "Gossamer": {},  # no direct stats, handled in mechanical output
    "Ranger Masters": {},
    "Splash O'Sul": {"Spirit": 373},
    "Respin Verminbane": {"Spirit Recovery": 32},
    "Tra'Kning": {},
    "Duvin Beastlore": {"Beastlore": 100},
    "Farly Buff": {"Health": 48, "Health Regeneration": 4, "Defense": 2},

    # Bangus / Bloodmage / Utility
    "Bangus Anmash": {"Body": 1, "Accuracy": 2, "Health": 6, "Balance": 21, "Balance Recovery": 5, "Min Damage": 2, "Max Damage": 3, "Health Regeneration": 1},
    "Crato Defeal": {"Spirit": 373},
    "Unrastin": {},
    "Posuhm": {},
    "Aneurus": {},
    "Dantus": {},
    "Disabla": {},
    "Cryptus": {},
    "Anemia": {"Health Regeneration": -1, "Health": 69, "Balance Recovery": 8},
    "Stedfustus": {"Health Regeneration": 1, "Health": 54, "Balance Recovery": 6},
    "Bloodblade": {"Accuracy": 32, "Min Damage": 12, "Max Damage": 12},
    "Marsh Hermit": {},
    "Loovma Gear": {},
    "Dentir Longtooth": {},
    "Skea Brightfur": {},
    "Master Mentus": {"Mind": 1},
    "Troilus": {"Health Regeneration": 6},
    "Master Spirtus": {"Healing Receptivity": 1, "Healing Speed": 11, "Spirit": 9, "Health": 21},
    "Master Bodrus": {"Body": 1, "Accuracy": 4, "Health": 24, "Defense": 1, "Balance": 9, "Balance Recovery": 3, "Min Damage": 1, "Max Damage": 1}
}

# === Default ranks ===
defaults = {name: 0 for name in trainer_data}

# === Functions ===
def evaluate():
    try:
        total_ranks = 0
        total_stats = {}

        for trainer, entry in entries.items():
            try:
                val = int(entry.get())
            except (ValueError, TypeError):
                val = 0
            total_ranks += val
            for stat, gain in trainer_data.get(trainer, {}).items():
                total_stats[stat] = total_stats.get(stat, 0) + gain * val

        remaining_ranks = 5000 - total_ranks

        output_lines = [
            f"Total Ranks: {total_ranks}",
            f"Remaining Ranks: {remaining_ranks}",
        ]

        # Raw stats (non-zero only)
        nonzero_stats = [(s, v) for s, v in sorted(total_stats.items()) if v != 0]
        if nonzero_stats:
            output_lines.append("\n=== Total Raw Stats ===")
            for stat, total in nonzero_stats:
                output_lines.append(f"{stat}: {total:.2f}")

        # --- Mechanical outputs ---
        mech_lines = []
        
        # Champion Weapon mechanical outputs (Fell Blade, Tell Blade, Labrys share ranks)
        champ_rank = 0
        if "Champion Weapon" in entries:
            try:
                champ_rank = int(entries["Champion Weapon"].get())
            except (ValueError, TypeError):
                champ_rank = 0

        if champ_rank > 0:
            mech_lines.append(
                f"Fell Blade (Direct Backstab): "
                f"+{32 * champ_rank} Accuracy, "
                f"+{12 * champ_rank} Min Damage, "
                f"+{12 * champ_rank} Max Damage"
            )
            mech_lines.append(
                f"Fell Blade (Angled Backstab): "
                f"+{16 * champ_rank} Accuracy, "
                f"+{6 * champ_rank} Min Damage, "
                f"+{6 * champ_rank} Max Damage"
            )
            mech_lines.append(
                f"Tell Blade: "
                f"{-32 * champ_rank} Accuracy"
            )
            mech_lines.append(
                f"Labrys: (no direct stat change, special effect weapon)"
            )


        # Gossamer (single input -> three modes shown only in output)
        gossamer_rank = 0
        if "Gossamer" in entries:
            try:
                gossamer_rank = int(entries["Gossamer"].get())
            except (ValueError, TypeError):
                gossamer_rank = 0
        if gossamer_rank > 0:
            mech_lines.append(
                f"Gossamer (Studied Bonus): +{32 * gossamer_rank} Accuracy, "
                f"+{12 * gossamer_rank} Min Damage, +{12 * gossamer_rank} Max Damage"
            )
            mech_lines.append(
                f"Gossamer (Family Bonus): +{3.2 * gossamer_rank:.1f} Accuracy, "
                f"+{1.2 * gossamer_rank:.1f} Min Damage, +{1.2 * gossamer_rank:.1f} Max Damage"
            )
            mech_lines.append(
                f"Gossamer (Max Family Bonus): +{16 * gossamer_rank} Accuracy, "
                f"+{6 * gossamer_rank} Min Damage, +{6 * gossamer_rank} Max Damage"
            )

        # Balance Recovery
        regia = total_stats.get("Balance Recovery", 0)
        if regia != 0:
            bal_per_frame_balthus = (5/102) * regia  # Balthus per frame
            mech_lines.append(f"Balance Recovery/frame: {bal_per_frame_balthus:.4f} Balthus")
            mech_lines.append(f"Balance Recovery/4-frame swing: {(bal_per_frame_balthus*4):.4f} Balthus")

        # Damage (Histia range from Min Damage -> infer Darkus-equivalent)
        min_dmg = total_stats.get("Min Damage", 0)
        if min_dmg != 0:
            darkus_equiv = min_dmg / 6.0  # includes Bangus etc. by design
            mech_lines.append(f"Min Histia hit: {0.054 * darkus_equiv:.3f}")
            mech_lines.append(f"Avg Histia hit: {0.108 * darkus_equiv:.3f}")
            mech_lines.append(f"Max Histia hit: {0.162 * darkus_equiv:.3f}")

        # Health Regeneration (Troilus-equivalent already in total_stats)
        troilus_total = total_stats.get("Health Regeneration", 0)
        if troilus_total != 0:
            histia_per_frame = (1/1850) * troilus_total
            mech_lines.append(f"Health Regen/frame: {histia_per_frame:.5f} Histia")
            if troilus_total != 0:
                mech_lines.append(f"Frames to heal 1 Histia: {1850 / troilus_total:.1f}")

        # Spirit Recovery
        spirit_recov = total_stats.get("Spirit Recovery", 0)
        if spirit_recov != 0:
            spirit_per_frame = (1/100) * spirit_recov
            mech_lines.append(f"Spirit Recovery/frame: {spirit_per_frame:.4f} Spirit")
            if spirit_per_frame > 0:
                mech_lines.append(f"Frames to recover 1 Sespus: {29 / spirit_per_frame:.1f}")
                mech_lines.append(f"Frames to recover 1 Splash: {375 / spirit_per_frame:.1f}")

        if mech_lines:
            output_lines.append("\n=== Mechanical Outputs ===")
            output_lines.extend(mech_lines)

        output_box.delete("1.0", "end")
        output_box.insert("end", "\n".join(output_lines))

    except Exception as e:
        # Show any unexpected error instead of hard-crashing
        try:
            messagebox.showerror("Evaluate Error", f"{type(e).__name__}: {e}")
        except Exception:
            print(f"Evaluate Error: {type(e).__name__}: {e}")


def save_build():
    build_data = {trainer: entries[trainer].get() for trainer in trainer_data}
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        try:
            with open(file_path, "w") as f:
                json.dump(build_data, f, indent=4)
            messagebox.showinfo("Save Build", "Build saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save build: {e}")

def load_build():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        try:
            with open(file_path, "r") as f:
                build_data = json.load(f)
            for trainer, value in build_data.items():
                if trainer in entries:
                    entries[trainer].delete(0, tk.END)
                    entries[trainer].insert(0, str(value))
            evaluate()
            messagebox.showinfo("Load Build", "Build loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load build: {e}")
            
def load_csv_build():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    trainer_name = row.get("Trainer")
                    ranks_str = row.get("Ranks")
                    if trainer_name in entries:
                        try:
                            ranks_val = int(ranks_str)
                        except (ValueError, TypeError):
                            ranks_val = 0
                        entries[trainer_name].delete(0, tk.END)
                        entries[trainer_name].insert(0, str(ranks_val))
            evaluate()
            messagebox.showinfo("Load CSV Build", "CSV build loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")

# === UI setup ===
root = tk.Tk()
root.title("Clan Lord - All Trainers Rank & Stat Calculator")

# Make root window's grid expandable
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Create canvas and scrollbars
canvas = tk.Canvas(root)
v_scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
h_scrollbar = ttk.Scrollbar(root, orient="horizontal", command=canvas.xview)

scrollable_frame = ttk.Frame(canvas)

# Update scroll region when frame changes
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

# Create window inside canvas
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Configure scrollbars
canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

entries = {}
for i, trainer in enumerate(sorted(trainer_data)):  # sorted for easier finding
    ttk.Label(scrollable_frame, text=trainer).grid(row=i, column=0, sticky="W")
    entry = ttk.Entry(scrollable_frame, width=10)
    entry.grid(row=i, column=1, padx=5, pady=2)
    entry.insert(0, str(defaults[trainer]))
    entries[trainer] = entry

# Layout: canvas + scrollbars
canvas.grid(row=0, column=0, sticky="nsew")
v_scrollbar.grid(row=0, column=1, sticky="ns")
h_scrollbar.grid(row=1, column=0, sticky="ew")

# Buttons
button_frame = ttk.Frame(root)
button_frame.grid(row=2, column=0, pady=10, sticky="ew")

ttk.Button(button_frame, text="Evaluate", command=evaluate).grid(row=0, column=0, padx=5)
ttk.Button(button_frame, text="Save Build", command=save_build).grid(row=0, column=1, padx=5)
ttk.Button(button_frame, text="Load Build", command=load_build).grid(row=0, column=2, padx=5)
ttk.Button(button_frame, text="Load CSV Build", command=load_csv_build).grid(row=0, column=3, padx=5)

# Output box
output_box = tk.Text(root, width=50, height=20, wrap="word")
output_box.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

# Allow output box to expand too
root.grid_rowconfigure(3, weight=1)

root.mainloop()