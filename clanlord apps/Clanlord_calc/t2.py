import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math

# === 1. DATA DEFINITIONS ===

race_data = {
    "Human":    {"Accuracy": 3, "Min Damage": 1, "Max Damage": 2, "Balance": 50, "Balance Recovery": 4, "Health": 30, "Defense": 3, "Health Regeneration": 1, "Spirit": 8, "Spirit Recovery": 6},
    "Dwarf":    {"Accuracy": 4, "Min Damage": 0, "Max Damage": 3, "Balance": 53, "Balance Recovery": 3, "Health": 33, "Defense": 3, "Health Regeneration": 1, "Spirit": 5, "Spirit Recovery": 5},
    "Fen":      {"Accuracy": 2, "Min Damage": 0, "Max Damage": 2, "Balance": 59, "Balance Recovery": 5, "Health": 15, "Defense": 2, "Health Regeneration": 1, "Spirit": 7, "Spirit Recovery": 5},
    "Halfling": {"Accuracy": 1, "Min Damage": 0, "Max Damage": 1, "Balance": 53, "Balance Recovery": 3, "Health": 30, "Defense": 6, "Health Regeneration": 1, "Spirit": 9, "Spirit Recovery": 7},
    "Ghorak":   {"Accuracy": 5, "Min Damage": 2, "Max Damage": 4, "Balance": 44, "Balance Recovery": 5, "Health": 36, "Defense": 1, "Health Regeneration": 1, "Spirit": 7, "Spirit Recovery": 5},
    "Sylvan":   {"Accuracy": 3, "Min Damage": 1, "Max Damage": 1, "Balance": 50, "Balance Recovery": 5, "Health": 24, "Defense": 4, "Health Regeneration": 1, "Spirit": 8, "Spirit Recovery": 6},
    "Thoom":    {"Accuracy": 2, "Min Damage": 0, "Max Damage": 1, "Balance": 47, "Balance Recovery": 3, "Health": 39, "Defense": 2, "Health Regeneration": 3, "Spirit": 10, "Spirit Recovery": 7}
}

weapon_data = {
    "None": {},
    "Roguewood Club": {"Accuracy": 0, "Min Damage": 0, "Max Damage": 0, "Balance": 0, "Balance Recovery": 0, "Defense": 0},
    "Dagger": {"Accuracy": 1.0, "Min Damage": 0, "Max Damage": 0, "Balance": 3.0, "Balance Recovery": 1.5, "Defense": -2.0},
    "Dueling Blade": {"Accuracy": 1.0, "Min Damage": -2.0, "Max Damage": -1.0, "Balance": 6.0, "Balance Recovery": 2.0, "Defense": 0},
    "Shiny Dagger": {"Accuracy": 2.0, "Min Damage": -1.0, "Max Damage": -1.0, "Balance": 9.0, "Balance Recovery": 4.0, "Defense": -1.0},
    "Lyfelidae Claw": {"Accuracy": 1.0, "Min Damage": 0, "Max Damage": 0, "Balance": 0, "Balance Recovery": 0, "Defense": -4.0},
    "Studded Club": {"Accuracy": 0.5, "Min Damage": 0, "Max Damage": 0.5, "Balance": 1.5, "Balance Recovery": 1.0, "Defense": -1.0},
    "Shovel": {"Accuracy": -0.5, "Min Damage": 0, "Max Damage": 0, "Balance": -1.5, "Balance Recovery": 0.5, "Defense": 0.5},
    "Boar Tusk": {"Accuracy": 1.0, "Min Damage": 2.0, "Max Damage": 2.0, "Balance": 0, "Balance Recovery": 0, "Defense": 0},
    "Sturdy Limb": {"Accuracy": 1.0, "Min Damage": 1.0, "Max Damage": 1.0, "Balance": -3.0, "Balance Recovery": 0, "Defense": 0},
    "Spike": {"Accuracy": 1.0, "Min Damage": 1.0, "Max Damage": 1.0, "Balance": 3.0, "Balance Recovery": 1.0, "Defense": -2.0},
    "Seta Scale": {"Accuracy": 1.0, "Min Damage": 2.0, "Max Damage": 2.0, "Balance": -3.0, "Balance Recovery": -1.0, "Defense": -1.0},
    "Quarterstaff": {"Accuracy": -0.5, "Min Damage": 0, "Max Damage": 0.5, "Balance": -3.0, "Balance Recovery": 0.5, "Defense": 1.0},
    "Flail": {"Accuracy": 1.0, "Min Damage": 1.0, "Max Damage": 1.2, "Balance": 0, "Balance Recovery": -0.5, "Defense": -0.5},
    "Battle Hammer": {"Accuracy": 0.9, "Min Damage": 1.75, "Max Damage": 2.25, "Balance": -3.0, "Balance Recovery": -0.9, "Defense": 0},
    "Short Sword": {"Accuracy": 0.5, "Min Damage": 0, "Max Damage": 0.5, "Balance": 0, "Balance Recovery": 0, "Defense": 1.0},
    "Rapier": {"Accuracy": 0.2, "Min Damage": 0.2, "Max Damage": 1.1, "Balance": 3.0, "Balance Recovery": 0.5, "Defense": -1.0},
    "Longsword": {"Accuracy": 1.0, "Min Damage": 1.0, "Max Damage": 1.5, "Balance": -2.4, "Balance Recovery": 0, "Defense": 0.4},
    "Broadsword": {"Accuracy": 1.5, "Min Damage": 1.75, "Max Damage": 1.75, "Balance": -2.4, "Balance Recovery": -0.8, "Defense": 0.5},
    "Machete": {"Accuracy": 0.5, "Min Damage": 0, "Max Damage": 0.5, "Balance": 0, "Balance Recovery": 0, "Defense": 1.0},
    "Sword of Souls": {"Accuracy": 1.0, "Min Damage": 0.8, "Max Damage": 0.8, "Balance": -1.8, "Balance Recovery": -0.6, "Defense": 1.2},
    "Hand Axe": {"Accuracy": 0.5, "Min Damage": 0.5, "Max Damage": 1.0, "Balance": -1.5, "Balance Recovery": -0.5, "Defense": 0},
    "Axe": {"Accuracy": 0.9, "Min Damage": 2.5, "Max Damage": 2.9, "Balance": -4.8, "Balance Recovery": -1.5, "Defense": 0},
    "Cloth Bracers": {"Accuracy": -1.0, "Min Damage": -0.5, "Max Damage": -1.5, "Balance": 1.5, "Balance Recovery": 1.0, "Defense": 0},
    "Leather Bracers": {"Accuracy": -0.5, "Min Damage": 0, "Max Damage": -1.0, "Balance": 3.0, "Balance Recovery": 1.0, "Defense": 0.2},
    "Metal Bracers": {"Accuracy": 0.5, "Min Damage": 0, "Max Damage": -0.6, "Balance": 3.0, "Balance Recovery": 1.0, "Defense": 0.7},
    "Greataxe": {"Accuracy": 1.5, "Min Damage": 3.0, "Max Damage": 3.5, "Balance": -6.0, "Balance Recovery": -2.0, "Defense": -0.2},
    "Greatsword": {"Accuracy": 2.5, "Min Damage": 2.1, "Max Damage": 2.1, "Balance": -3.0, "Balance Recovery": -1.0, "Defense": 0.5},
    "Anchor": {"Accuracy": -2.0, "Min Damage": 2.0, "Max Damage": 2.0, "Balance": -3.0, "Balance Recovery": -3.0, "Defense": 0.5},
    "Mace": {"Accuracy": -1.0, "Min Damage": 2.0, "Max Damage": 3.0, "Balance": -3.0, "Balance Recovery": -1.0, "Defense": 0},
    "Oak Basher": {"Accuracy": -5.0, "Min Damage": 6.0, "Max Damage": 6.0, "Balance": -15.0, "Balance Recovery": -5.0, "Defense": -5.0},
    "Ethereal Sword": {"Accuracy": 0.5, "Min Damage": 0, "Max Damage": 0.5, "Balance": 0, "Balance Recovery": 0, "Defense": 1.0},
    "Gossamer": {"Accuracy": 1.0, "Min Damage": -0.5, "Max Damage": -0.5, "Balance": 4.5, "Balance Recovery": 2.0, "Defense": 0},
    "Fell Blade": {"Accuracy": 0.45, "Min Damage": 1.25, "Max Damage": 1.45, "Balance": -2.4, "Balance Recovery": -0.8, "Defense": 0},
    "Tell": {"Accuracy": 0, "Min Damage": 0, "Max Damage": 0, "Balance": 0, "Balance Recovery": 0.5, "Defense": 0},
    "Labrys": {"Accuracy": 0.45, "Min Damage": 1.25, "Max Damage": 1.45, "Balance": -2.4, "Balance Recovery": -0.8, "Defense": 0},
    "Bloodblade": {"Accuracy": 1.8, "Min Damage": 1.0, "Max Damage": 3.0, "Balance": 3.0, "Balance Recovery": 0, "Defense": 0},
}

left_hand_data = {
    "None": 0,
    "Main Gauche": 1,
    "Wooden Shield": 2,
    "Atkite": 101,
    "Darkite": 102,
    "Balthite": 103,
    "Dethite": 104,
    "Atkite (Boosted)": 105,
    "Darkite (Boosted)": 106,
    "Balthite (Boosted)": 107,
    "Dethite (Boosted)": 108
}

shoulder_data = {
    "None": 0,
    "Atkite": 101,
    "Darkite": 102,
    "Balthite": 103,
    "Dethite": 104,
    "Atkite (Boosted)": 105,
    "Darkite (Boosted)": 106,
    "Balthite (Boosted)": 107,
    "Dethite (Boosted)": 108
}

trainer_data = {
    # Core
    "Atkus": {"Accuracy": 1.0, "Balance": 15.0, "Balance Recovery": 1.0},
    "Darkus": {"Min Damage": 0.6, "Max Damage": 0.6, "Balance": 18.0, "Balance Recovery": 1.0},
    "Balthus": {"Balance": 51.0},
    "Regia": {"Balance Recovery": 15.0},
    "Evus": {"Accuracy": 0.4, "Health": 24.0, "Defense": 1.0, "Balance": 18.0, "Balance Recovery": 4.0, "Min Damage": 0.1, "Max Damage": 0.1},
    "Swengus": {"Balance": 30.0, "Balance Recovery": 7.0},
    "Histia": {"Health": 111.0},
    "Detha": {"Defense": 19.0, "Health": 3.0},
    # Other
    "Master Bodrus": {"Accuracy": 0.4, "Health": 24.0, "Defense": 1.0, "Balance": 9.0, "Balance Recovery": 3.0, "Min Damage": 0.1, "Max Damage": 0.1},
    "Hardia": {"Health": 36.0, "Balance Recovery": 2.0},
    "Troilus": {"Health Regeneration": 6.0},
    "Rodnus": {"Health": 36.0, "Healing Receptivity": 2.0},
    "Master Spirtus": {"Spirit": 9.0, "Health": 21.0, "Healing Speed": 11.0},
    "Aktur": {"Accuracy": 2.5},
    "Atkia": {"Accuracy": 1.3, "Min Damage": 0.3, "Max Damage": 0.3, "Balance Recovery": 3.0},
    "Darktur": {"Min Damage": 1.0, "Max Damage": 1.0},
    "Knox": {"Accuracy": -0.4, "Health": -24.0, "Defense": -1.0, "Balance": 18.0, "Balance Recovery": -2.0, "Min Damage": 1.1, "Max Damage": 1.1},
    "Angilsa": {"Accuracy": -0.4, "Health": -24.0, "Defense": -1.0, "Balance Recovery": 26.0},
    "Heen Slostid": {"Shieldstone Efficiency": 1.0},
    "Channel Master": {"ChanMult": 1.0},
    # Spirit Trainers
    "Spleisha'Sul": {"Spirit": 3.73},
    "Crato Defeal": {"Spirit": 3.73},
    "Toomeria": {"Spirit": 5.0},
    "Respin": {"Spirit Recovery": 0.32},
    "Splash": {"Spirit": 3.73},
    # Subclass specific logic trainers
    "Atkite": {"AtkiteStr": 1.0},
    "Darkite": {"DarkiteStr": 1.0},
    "Balthite": {"BalthiteStr": 1.0},
    "Dethite": {"DethiteStr": 1.0},
    "Fell": {"Min Damage": 1.2, "Max Damage": 1.2},
    "Bloodblade": {"Accuracy": 3.2, "Min Damage": 1.2, "Max Damage": 1.2},
    "Gossamer": {"Accuracy": 0.1},
    "Tracking": {"Utility": 1.0},
    #"Morph": {"Utility": 1.0},
    #"Befriend": {"Utility": 1.0},
    "Cryptus": {"Health": 10.0, "Balance Recovery": 5.0},
    "Disabla": {"Accuracy": 2.0},
    "Dantus": {"Defense": 5.0}
}

# === 2. LOGIC FUNCTIONS ===

def compute_totals():
    total_ranks = 0
    total_stats = {}

    # Race
    for stat, val in race_data.get(race_var.get(), {}).items():
        total_stats[stat] = total_stats.get(stat, 0) + val

    # Items (Weapon, Left Hand, Shoulder)
    item_slots = [
        (weapon_data, weapon_var.get()),
        (left_hand_data, left_var.get()),
        (shoulder_data, shoulder_var.get())
    ]
    for data_dict, selection in item_slots:
        for stat, val in data_dict.get(selection, {}).items():
            total_stats[stat] = total_stats.get(stat, 0) + val

    # Trainer Ranks
    for trainer, entry in entries.items():
        try:
            val = int(entry.get())
        except:
            val = 0
        if val == 0: continue
        
        total_ranks += val
        for stat, gain in trainer_data.get(trainer, {}).items():
            total_stats[stat] = total_stats.get(stat, 0) + (gain * val)

    return total_ranks, total_stats
    
def frames_to_minutes(frames, fps):
    seconds = frames / fps
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"

def calculate_mineral_stats(stats_dict):
    """
    stats_dict should contain: 
    AtkiteStr, DarkiteStr, BalthiteStr, DethiteStr, 
    Spirit, SpiritRegen, SpiritRegenES (Regen stat),
    FPS, ChanMult, Chan, Weapon, OffenseNoIte, 
    BalanceNoIte, RegenNoIte
    """
    msg = "***Earth Mineral stats***\n"
    
    # Base costs and identifiers from source
    minerals = [
        {"name": "Atkite", "str": stats_dict['AtkiteStr']},
        {"name": "Darkite", "str": stats_dict['DarkiteStr']},
        {"name": "Balthite", "str": stats_dict['BalthiteStr']},
        {"name": "Dethite", "str": stats_dict['DethiteStr']}
    ]

    for i, mineral in enumerate(minerals):
        # IteCost function calculation (Base logic from source)
        ite_str = mineral['str']
        sp_cost = 500 + (ite_str * 10) # Simplified based on standard ite cost scaling 
        
        msg += f"{mineral['name']}:\n"
        msg += f"Toomeria consumed per boost: {round(sp_cost / 500)}.\n"
        
        # Spirit Regeneration Logic [cite: 610]
        # 68 is the standard IteDuration from the JS source
        regen_per_tick = 68 * (stats_dict['SpiritRegenES'] / 100)
        
        if regen_per_tick >= sp_cost:
            msg += "Total boosts from full spirit: Infinite"
        else:
            ite_boosts = 0
            sp_left = stats_dict['Spirit']
            # Simulation loop as seen in user script
            while sp_left >= sp_cost:
                sp_left -= sp_cost
                sp_left += regen_per_tick
                ite_boosts += 1
                if ite_boosts > 1000: break
            
            if ite_boosts <= 1000:
                if 0 < sp_left < sp_cost:
                    ite_boosts += (sp_left / sp_cost)
                msg += f"Total boosts from full spirit: {round(ite_boosts, 1)}"
            else:
                msg += "Total boosts from full spirit: OVER 1000"
        
        msg += ".\n"
        
        # Recovery timing [cite: 304]
        recovery_val = sp_cost / (stats_dict['SpiritRegen'] / 100)
        if stats_dict['FPS'] == 1:
            msg += f"Frames to recover 1 boost: {round(recovery_val)}"
        else:
            msg += f"Time to recover 1 boost: {frames_to_minutes(recovery_val, stats_dict['FPS'])}"
        msg += ".\n"

        # Atkite/Darkite Offense Calculations (i=0 or i=1)
        if i == 0 or i == 1:
            # Logic for CMToAccuracy/AvgDamage based on source weapon 89 (Ethereal Sword) [cite: 855]
            boost_str = ite_str * stats_dict['ChanMult'] 
            if stats_dict['Weapon'] == 89:
                boost_str *= 1.2 if i == 0 else 1.15
            
            # Swings during duration simulation [cite: 284, 295]
            ite_duration = 68
            bal_left = stats_dict['BalanceNoIte']
            boosted_swings = 0
            swing_wait = 0
            
            # Balance cost calculation from source
            offense_boosted = max(200, stats_dict['OffenseNoIte'] + boost_str)
            bal_cost_boosted = math.floor((5/3) * offense_boosted)
            
            while ite_duration > 0:
                ite_duration -= 1
                if swing_wait > 0:
                    swing_wait -= 1
                elif bal_left >= bal_cost_boosted:
                    boosted_swings += 1
                    bal_left -= bal_cost_boosted
                    swing_wait = 3 # Hardcoded swing delay from script
                
                if ite_duration > 0:
                    bal_left += stats_dict['RegenNoIte'] # Simplified BalancePerTick
                    if bal_left > stats_dict['BalanceNoIte']:
                        bal_left = stats_dict['BalanceNoIte']
            
            msg += f"Total swings during boost duration: {round(boosted_swings, 1)}.\n"

    return msg

def evaluate_and_render():
    try:
        total_ranks, total_stats = compute_totals()
        mode = result_mode_var.get()
        lines = [f"Total Ranks Spent: {total_ranks}", "-"*30, ""]
        
        if mode == "Earth Minerals":
            # Prepare the dictionary the simulation needs
            sim_dict = {
                'AtkiteStr': total_stats.get('AtkiteStr', 0),
                'DarkiteStr': total_stats.get('DarkiteStr', 0),
                'BalthiteStr': total_stats.get('BalthiteStr', 0),
                'DethiteStr': total_stats.get('DethiteStr', 0),
                'Spirit': total_stats.get('Spirit', 0) * 100, # Convert to base units
                'SpiritRegen': total_stats.get('Spirit Recovery', 0) * 100,
                'SpiritRegenES': total_stats.get('Spirit Recovery', 0) * 100,
                'FPS': 1, # Default to 1 for frames
                'ChanMult': total_stats.get('ChanMult', 0),
                'Weapon': 0, # Placeholder
                'OffenseNoIte': total_stats.get('Accuracy', 0) * 100,
                'BalanceNoIte': total_stats.get('Balance', 0) * 100,
                'RegenNoIte': total_stats.get('Balance Recovery', 0)
            }
            mineral_msg = calculate_mineral_stats(sim_dict)
            lines.append(mineral_msg)
        
        if mode == "Swings":
            bal = total_stats.get("Balance", 0)
            reg = total_stats.get("Balance Recovery", 0)
            bal_per_swing = 0.054 * bal
            bal_sec = 0.170175 * reg
            lines.append(f"Consumed per swing: {bal_per_swing:.3f}")
            lines.append(f"Recovery/sec: {bal_sec:.3f}")
            if bal_sec > 0:
                lines.append(f"Seconds to full: {1.0 / bal_sec:.2f}")

        elif mode == "Damage":
            lines.append(f"Min Damage: {total_stats.get('Min Damage', 0):.2f}")
            lines.append(f"Max Damage: {total_stats.get('Max Damage', 0):.2f}")

        elif mode == "Health":
            lines.append(f"Total HP: {total_stats.get('Health', 0)}")
            lines.append(f"Defense: {total_stats.get('Defense', 0)}")

        output_box.config(state="normal")
        output_box.delete("1.0", "end")
        output_box.insert("end", "\n".join(lines))
        output_box.config(state="disabled")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# === UI CONSTRUCTION ===
root = tk.Tk()
root.title("Clan Lord - Trainer Rank & Stat Analyzer")
root.geometry("1200x850") # Wider to accommodate 4 columns comfortably
root.configure(bg="#a0a0a0")

# Variables
race_var = tk.StringVar(value="Human")
weapon_var = tk.StringVar(value="None")
left_var = tk.StringVar(value="None")
shoulder_var = tk.StringVar(value="None")
result_mode_var = tk.StringVar(value="Swings")
entries = {}

# Define the groups here so the loop can build them automatically
trainer_groups = {
    "Core Fighter": ["Atkus", "Darkus", "Balthus", "Regia", "Evus", "Swengus", "Histia", "Detha"],
    "Secondary": ["Master Bodrus", "Hardia", "Troilus", "Rodnus", "Master Spirtus", "Aktur", "Atkia", "Darktur", "Knox", "Angilsa"],
    "Specialist": ["Heen Slostid", "Spleisha'Sul", "Crato Defeal", "Toomeria", "Respin", "Splash"],
    "Subclasses": [
        "Atkite", "Darkite", "Balthite", "Dethite", "Fell", "Bloodblade", 
        "Gossamer", "Tracking", "Cryptus", "Disabla", "Dantus", 
        "Champion Weapon", "Channel Master"
    ]
}

# Styling
style = ttk.Style()
style.theme_use('clam')
style.configure("TLabelframe", background="#a0a0a0", relief="ridge", borderwidth=2)
style.configure("TLabelframe.Label", background="#a0a0a0", font=('Helvetica', 10, 'bold'))
style.configure("TLabel", background="#a0a0a0")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both", padx=5, pady=5)

tab_trainers = ttk.Frame(notebook)
tab_results = ttk.Frame(notebook)
notebook.add(tab_trainers, text="Trainer Ranks")
notebook.add(tab_results, text="Results")

# --- Trainer Ranks Tab (Scrollable) ---
canvas = tk.Canvas(tab_trainers, bg="#a0a0a0", highlightthickness=0)
v_scroll = ttk.Scrollbar(tab_trainers, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#a0a0a0")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def configure_canvas(event):
    if canvas.winfo_width() > scrollable_frame.winfo_reqwidth():
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())
canvas.bind("<Configure>", configure_canvas)

canvas.configure(yscrollcommand=v_scroll.set)

# MouseWheel Support
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
canvas.bind_all("<MouseWheel>", _on_mousewheel)

v_scroll.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Main Container for all UI elements
main_container = tk.Frame(scrollable_frame, bg="#a0a0a0")
main_container.pack(padx=10, pady=10, fill="both", expand=True)

# Top Section: Character Configuration
top_f = ttk.LabelFrame(main_container, text="Character Configuration")
top_f.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

item_slots = [
    ("Race:", race_var, list(race_data.keys())),
    ("Weapon:", weapon_var, list(weapon_data.keys())),
    ("Left Hand:", left_var, list(left_hand_data.keys())),
    ("Shoulder:", shoulder_var, list(shoulder_data.keys()))
]

for i, (txt, var, vals) in enumerate(item_slots):
    ttk.Label(top_f, text=txt).grid(row=0, column=i*2, padx=5, pady=10, sticky="w")
    ttk.Combobox(top_f, textvariable=var, values=vals, state="readonly", width=18).grid(row=0, column=i*2+1, padx=5, pady=10)

# Trainer Groups: Created dynamically in columns
for col_idx, (group_name, names) in enumerate(trainer_groups.items()):
    group_frame = ttk.LabelFrame(main_container, text=group_name)
    group_frame.grid(row=1, column=col_idx, padx=10, pady=10, sticky="nsew")
    
    ttk.Label(group_frame, text="Ranks", font=('Helvetica', 8, 'italic')).grid(row=0, column=1, sticky="e", padx=5)

    for row_idx, name in enumerate(names):
        ttk.Label(group_frame, text=name).grid(row=row_idx+1, column=0, sticky="w", padx=5, pady=2)
        
        entries[name] = ttk.Entry(group_frame, width=8)
        entries[name].insert(0, "0")
        entries[name].grid(row=row_idx+1, column=1, padx=5, pady=2)
        
        # Highlight logic
        def validate_entry(event, entry_name=name):
            entry = entries[entry_name]
            try:
                if int(entry.get()) > 0:
                    entry.config(foreground="blue", font=('Helvetica', 9, 'bold'))
                else:
                    entry.config(foreground="black", font=('Helvetica', 9))
            except: pass
        entries[name].bind("<FocusOut>", validate_entry)

# Weights to keep columns even
for i in range(4):
    main_container.columnconfigure(i, weight=1)

# --- Results Tab ---
res_top = ttk.Frame(tab_results)
res_top.pack(fill="x", padx=10, pady=10)
ttk.Label(res_top, text="Mode:").pack(side="left")

m_box = ttk.Combobox(res_top, textvariable=result_mode_var, 
                     values=["Swings", "Damage", "Health", "Earth Minerals"], 
                     state="readonly")
m_box.pack(side="left", padx=5)

ttk.Button(res_top, text="Evaluate", command=evaluate_and_render).pack(side="left")

output_box = tk.Text(tab_results, bg="white", font=("Courier New", 10), state="disabled")
output_box.pack(expand=True, fill="both", padx=10, pady=10)

root.mainloop()