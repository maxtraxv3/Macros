import math
import tkinter as tk
from tkinter import ttk

# =========================
# Data tables (from HTML)
# =========================

races = [
    [300,100,200,5000,400,3000,300,100,800,600],   # 0 Human/Undisclosed
    [400,0,300,5300,300,3300,300,100,500,500],     # 1 Dwarf
    [200,0,200,5900,500,1500,200,100,700,500],     # 2 Fen
    [100,0,100,5300,300,3000,600,100,900,700],     # 3 Halfling
    [500,200,400,4400,500,3600,100,100,700,500],   # 4 Ghorak Zo
    [300,100,100,5000,500,2400,400,100,800,600],   # 5 Sylvan
    [200,0,100,4700,300,3900,200,300,1000,700],    # 6 Thoom
    [0,0,0,0,0,0,0,0,0,0],                         # 7 0-Stat Race
]

weapons = [[0]*10 for _ in range(130)]

weapons[0]  = [0,0,0,0,0,0,0,0,0,0]          # 0 - Roguewood Club
weapons[1]  = [100,0,0,300,150,0,-200,0,0,0] # 1 - Dagger
weapons[2]  = [100,-200,-100,600,200,0,0,0,0,0]   # 2 - Dueling Blade
weapons[3]  = [200,-100,-100,900,400,0,-100,0,0,0] # 3 - Shiny Dagger
weapons[4]  = [100,0,0,0,0,0,-400,300,0,0]   # 4 - Lyfelidae Claw
weapons[5]  = [50,0,50,150,100,0,-100,0,0,0] # 5 - Studded Club
weapons[6]  = [-50,0,0,-150,50,0,50,0,0,0]   # 6 - Shovel
weapons[7]  = [100,200,200,0,0,0,0,0,0,0]    # 7 - Boar Tusk
weapons[8]  = [100,100,100,-300,0,0,0,0,0,0] # 8 - Sturdy Limb
weapons[9]  = [100,100,100,300,100,0,-200,0,0,0] # 9 - Spike
weapons[10] = [100,200,200,-300,-100,0,-100,0,0,0] # 10 - Seta Scale
weapons[11] = [-50,0,50,-300,50,0,100,0,0,0] # 11 - Quarterstaff
weapons[12] = [100,100,120,0,-50,0,-50,0,0,0] # 12 - Flail
weapons[13] = [90,175,225,-300,-90,0,0,0,0,0] # 13 - Battle Hammer
weapons[20] = [50,0,50,0,0,0,100,0,0,0]     # 20 - Short Sword
weapons[21] = [20,20,110,300,50,0,-100,0,0,0] # 21 - Rapier
weapons[22] = [100,100,150,-240,0,0,40,0,0,0] # 22 - Longsword
weapons[23] = [150,175,175,-240,-80,0,50,0,0,0] # 23 - Broadsword
weapons[24] = [50,0,50,0,0,0,100,0,0,0]     # 24 - Machete
weapons[25] = [100,80,80,-180,-60,0,120,0,0,0] # 25 - Sword of Souls
weapons[30] = [50,50,100,-150,-50,0,0,0,0,0] # 30 - Hand Axe
weapons[31] = [90,250,290,-480,-150,0,0,0,0,0] # 31 - Axe
weapons[40] = [-100,-50,-150,150,100,0,0,0,0,0] # 40 - Cloth Bracers
weapons[41] = [-50,0,-100,300,100,0,20,0,0,0] # 41 - Leather Bracers
weapons[42] = [50,0,-60,300,100,0,70,0,0,0]  # 42 - Metal Bracers
weapons[50] = [150,300,350,-600,-200,0,-20,0,0,0] # 50 - Greataxe
weapons[51] = [250,210,210,-300,-100,0,50,0,0,0] # 51 - Greatsword
weapons[60] = [-200,200,200,-300,-300,0,50,0,0,0] # 60 - Anchor
weapons[80] = [-100,200,300,-300,-100,0,0,0,0,0] # 80 - Mace
weapons[81] = [-500,600,600,-1500,-500,0,-500,0,0,0] # 81 - Oak Basher
weapons[89] = [50,0,50,0,0,0,100,0,0,0]     # 89 - Ethereal Sword

goss_base = [100,-50,-50,450,200,0,0,0,0,0]
for i in range(90, 100):
    weapons[i] = list(goss_base)

fell_base = [45,125,145,-240,-80,0,0,0,0,0]
for i in range(100, 103):
    weapons[i] = list(fell_base)

weapons[103] = [0,0,0,0,50,0,0,0,0,0]       # 103 - Tell
weapons[110] = [45,125,145,-240,-80,0,0,0,0,0] # 110 - Labrys
weapons[120] = [180,100,300,300,0,0,0,0,0,0] # 120 - Bloodblade

lefts = [[0]*10 for _ in range(109)]
lefts[0] = [0,0,0,0,0,0,0,0,0,0]
lefts[1] = [100,10,10,-300,-100,0,100,0,0,0]
lefts[2] = [0,0,0,-300,-100,0,300,0,0,0]
for i in range(101, 109):
    lefts[i] = [0,0,0,0,0,0,0,0,0,0]

shoulders = [[0]*10 for _ in range(109)]
shoulders[0] = [0,0,0,0,0,0,0,0,0,0]
for i in range(101, 109):
    shoulders[i] = [0,0,0,0,0,0,0,0,0,0]

RACE_NAMES = [
    "Human/Undisclosed",
    "Dwarf",
    "Fen",
    "Halfling",
    "Ghorak Zo",
    "Sylvan",
    "Thoom",
    "0-Stat Race",
]

WEAPON_NAMES = {
    0:  "Roguewood Club",
    1:  "Dagger",
    2:  "Dueling Blade",
    3:  "Shiny Dagger",
    4:  "Lyfelidae Claw",
    5:  "Studded Club",
    6:  "Shovel",
    7:  "Boar Tusk",
    8:  "Sturdy Limb",
    9:  "Spike",
    10: "Seta Scale",
    11: "Quarterstaff",
    12: "Flail",
    13: "Battle Hammer",
    20: "Short Sword",
    21: "Rapier",
    22: "Longsword",
    23: "Broadsword",
    24: "Machete",
    25: "Sword of Souls",
    30: "Hand Axe",
    31: "Axe",
    40: "Cloth Bracers",
    41: "Leather Bracers",
    42: "Metal Bracers",
    50: "Greataxe",
    51: "Greatsword",
    60: "Anchor",
    80: "Mace",
    81: "Oak Basher",
    89: "Ethereal Sword",
    90: "Gossamer (No Studies)",
    93: "Gossamer (Family 10%)",
    94: "Gossamer (Family 20%)",
    95: "Gossamer (Family 30%)",
    96: "Gossamer (Family 40%)",
    97: "Gossamer (Family 50%)",
    98: "Gossamer (Movement)",
    100: "Fell Blade (Normal)",
    101: "Fell Blade (Angled BS)",
    102: "Fell Blade (Direct BS)",
    103: "Tell Blade",
    110: "Labrys",
    120: "Bloodblade",
}

LEFT_NAMES = {
    0:  "Nothing",
    1:  "Main Gauche",
    2:  "Wooden Shield",
    101:"Atkite",
    102:"Darkite",
    103:"Balthite",
    104:"Dethite",
    105:"Atkite (Boosted)",
    106:"Darkite (Boosted)",
    107:"Balthite (Boosted)",
    108:"Dethite (Boosted)",
}

SHOULDER_NAMES = {
    0:  "Nothing",
    101:"Atkite Pauldron",
    102:"Darkite Pauldron",
    103:"Balthite Pauldron",
    104:"Dethite Pauldron",
    105:"Atkite Pauldron (Boosted)",
    106:"Darkite Pauldron (Boosted)",
    107:"Balthite Pauldron (Boosted)",
    108:"Dethite Pauldron (Boosted)",
}

# =========================
# JS helper functions
# =========================

def CMToAccuracy(cm):      return math.floor(cm * 25)
def CMToMinDamage(cm):     return math.floor(cm * 10.32)
def CMToMaxDamage(cm):     return math.floor(cm * 10.32)
def CMToAvgDamage(cm):     return math.floor(cm * 10.32)
def CMToBalance(cm):       return math.floor(cm * 51)
def CMToDefense(cm):       return math.floor(cm * 19)

def DamageToDarktur(damage):      return damage / 10
def BalthusToBalance(balthus):    return balthus * 51
def BalanceToBalthus(balance):    return balance / 51
def RegiaToRegen(regia):          return regia * 15
def RegenToRegia(regen):          return regen / 15
def HistiaToHealth(histia):       return histia * 111
def HealthToHistia(health):       return health / 111
def DethaToDefense(detha):        return detha * 19
def DefenseToDetha(defense):      return defense / 19
def BalanceToDefense(balance):    return balance * 0.3
def CratoToSpirit(crato):         return crato * 373
def SpiritToCrato(spirit):        return spirit / 373
def SpleishaToSpirit(spleisha):   return spleisha * 373
def SpiritToSpleisha(spirit):     return spirit / 373
def SplashToSpirit(splash):       return splash * 373
def SpiritToSplash(spirit):       return spirit / 373
def OldSplashToSpirit(splash):    return splash * 375
def SpiritToOldSplash(spirit):    return spirit / 375
def ToomeriaToSpirit(toomeria):   return toomeria * 500
def SpiritToToomeria(spirit):     return spirit / 500
def RespinToSpiritRegen(respin):  return respin * 32
def SpiritRegenToRespin(regen):   return regen / 32

def DamageToMinHistia(damage):
    return (max(damage, 0) + 100) / 111

def DamageToMaxHistia(damage):
    return (max(damage * 3, 0) + 100) / 111

def DamageToAvgHistia(min_d, max_d):
    return (DamageToMinHistia(min_d) + DamageToMaxHistia(max_d)) / 2

def IteCost(stren):
    return 5250

def IteBoostStrength(chan):
    return max(chan - 20, 0)
def TroilusToRegeneration(troilus): return troilus * 6
def RegenerationToTroilus(regen): return regen / 6
def AkturToAccuracy(aktur):       return aktur * 25
def AccuracyToAktur(accuracy):    return accuracy / 25
def AtkusToAccuracy(atkus):       return atkus * 16
def AccuracyToAtkus(accuracy):    return accuracy / 16
def DarkusToDamage(darkus):       return darkus * 6
def DamageToDarkus(damage):       return damage / 6
def DarkturToDamage(darktur):     return darktur * 10

def RoundDown(value):
    return math.floor(value + 0.00000001)

def Round(value):
    v = value * 1000
    s = str(v)
    dot = s.find('.')
    if dot >= 3:
        if s[dot-3:dot] == "999":
            if len(s) <= dot + 6 or s[dot+1:dot+7] != "999999":
                if v < 0:
                    v = math.ceil(v)
                else:
                    v = math.floor(v)
                return v / 1000
    return round(value)

def RoundLong(value):
    v = value * 1000000
    s = str(v)
    dot = s.find('.')
    if dot >= 6:
        if s[dot-6:dot] == "999":
            if len(s) <= dot + 6 or s[dot+1:dot+7] != "999999":
                if v < 0:
                    v = math.ceil(v)
                else:
                    v = math.floor(v)
                return v / 1000000
    return round(value)

def GetLabrysDamage(MinDmg, MaxDmg, TFell, LabrysTargets):
    if LabrysTargets is None or LabrysTargets < 1:
        LabrysTargets = 1
    if LabrysTargets == 1:
        FlatMin, FlatMax, ScaleMin, ScaleMax = -700, -700, 4, 4
    elif LabrysTargets == 2:
        FlatMin, FlatMax, ScaleMin, ScaleMax = -500, -400, 7, 7
    elif LabrysTargets == 3:
        FlatMin, FlatMax, ScaleMin, ScaleMax = 200, 400, 9, 9
    elif LabrysTargets == 4:
        FlatMin, FlatMax, ScaleMin, ScaleMax = 300, 600, 13, 13
    elif LabrysTargets == 5:
        FlatMin, FlatMax, ScaleMin, ScaleMax = 400, 800, 18, 18
    else:
        FlatMin = 100 * (LabrysTargets - 1)
        FlatMax = 200 * (LabrysTargets - 1)
        ScaleMin, ScaleMax = 18, 18
    MinDmg += FlatMin + ScaleMin * TFell
    MaxDmg += FlatMax + ScaleMax * TFell
    MinDmg = math.floor(MinDmg / LabrysTargets)
    MaxDmg = math.floor(MaxDmg / LabrysTargets)
    return [MinDmg, MaxDmg]

def is_earth_mineral(val):
    return 101 <= val <= 108

# =========================
# Calculator class
# =========================

class FighterCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clan Lord Fighter Calculator")
        self.build_ui()

    def build_ui(self):
        self.frame_train = ttk.LabelFrame(self, text="Core Fighter Ranks")
        self.frame_train.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        self.vars = {}

        def add_et_row(row, label, keyE, keyT):
            ttk.Label(self.frame_train, text=label).grid(row=row, column=0, sticky="w")
            vE = tk.StringVar(value="0")
            vT = tk.StringVar(value="0")
            self.vars[keyE] = vE
            self.vars[keyT] = vT
            ttk.Label(self.frame_train, text="E").grid(row=row, column=1)
            ttk.Entry(self.frame_train, width=6, textvariable=vE).grid(row=row, column=2)
            ttk.Label(self.frame_train, text="T").grid(row=row, column=3)
            ttk.Entry(self.frame_train, width=6, textvariable=vT).grid(row=row, column=4)

        add_et_row(0, "Atkus",    "EAtkus",    "TAtkus")
        add_et_row(1, "Darkus",   "EDarkus",   "TDarkus")
        add_et_row(2, "Balthus",  "EBalthus",  "TBalthus")
        add_et_row(3, "Regia",    "ERegia",    "TRegia")
        add_et_row(4, "Histia",   "EHistia",   "THistia")
        add_et_row(5, "Detha",    "EDetha",    "TDetha")
        add_et_row(6, "Troilus",  "ETroilus",  "TTroilus")
        add_et_row(7, "Rodnus",   "ERodnus",   "TRodnus")
        add_et_row(8, "Spiritus", "ESpiritus", "TSpiritus")

        row = 9
        other_trainers = [
            ("Evus", "TEvus"), ("Swengus", "TSwengus"), ("Bodrus", "TBodrus"),
            ("Hardia", "THardia"), ("Farly", "TFarly"), ("Knox", "TKnox"),
            ("Angilsa", "TAngilsa"), ("Aktur", "TAktur"), ("Atkia", "TAtkia"),
            ("Darktur", "TDarktur"), ("Forvyola", "TForvyola"),
            ("Bangus", "TBangus"), ("Erthron", "TErthron"),
            ("ErthronNew", "TErthronNew"), ("Stedfustus", "TStedfustus"),
            ("Anemia", "TAnemia"),
        ]
        for label, key in other_trainers:
            ttk.Label(self.frame_train, text=label).grid(row=row, column=0, sticky="w")
            v = tk.StringVar(value="0")
            self.vars[key] = v
            ttk.Entry(self.frame_train, width=6, textvariable=v).grid(row=row, column=2)
            row += 1

        self.frame_sub = ttk.LabelFrame(self, text="Subclass / Weapons / Items")
        self.frame_sub.grid(row=0, column=1, sticky="nw", padx=5, pady=5)
        sub_row = 0

        ttk.Label(self.frame_sub, text="Subclass").grid(row=sub_row, column=0, sticky="w")
        self.subclass_var = tk.IntVar(value=0)
        subclass_combo = ttk.Combobox(
            self.frame_sub, textvariable=self.subclass_var,
            values=[0,1,2,3], state="readonly", width=12
        )
        sub_combo_names = {0:"No Subclass", 1:"Champion", 2:"Ranger", 3:"Bloodmage"}
        subclass_combo.grid(row=sub_row, column=1)
        sub_row += 1

        ttk.Label(self.frame_sub, text="Race").grid(row=sub_row, column=0, sticky="w")
        self.race_var = tk.StringVar(value=RACE_NAMES[0])
        ttk.Combobox(
            self.frame_sub, textvariable=self.race_var,
            values=RACE_NAMES, state="readonly", width=20
        ).grid(row=sub_row, column=1)
        sub_row += 1

        ttk.Label(self.frame_sub, text="Weapon").grid(row=sub_row, column=0, sticky="w")
        self.weapon_var = tk.StringVar(value=WEAPON_NAMES[0])
        ttk.Combobox(
            self.frame_sub, textvariable=self.weapon_var,
            values=list(WEAPON_NAMES.values()), state="readonly", width=22
        ).grid(row=sub_row, column=1)
        sub_row += 1

        ttk.Label(self.frame_sub, text="Left Hand").grid(row=sub_row, column=0, sticky="w")
        self.left_var = tk.StringVar(value=LEFT_NAMES[0])
        ttk.Combobox(
            self.frame_sub, textvariable=self.left_var,
            values=list(LEFT_NAMES.values()), state="readonly", width=22
        ).grid(row=sub_row, column=1)
        sub_row += 1

        ttk.Label(self.frame_sub, text="Shoulder").grid(row=sub_row, column=0, sticky="w")
        self.shoulder_var = tk.StringVar(value=SHOULDER_NAMES[0])
        ttk.Combobox(
            self.frame_sub, textvariable=self.shoulder_var,
            values=list(SHOULDER_NAMES.values()), state="readonly", width=22
        ).grid(row=sub_row, column=1)
        sub_row += 1

        ttk.Label(self.frame_sub, text="FPS").grid(row=sub_row, column=0, sticky="w")
        self.fps_var = tk.StringVar(value="5")
        ttk.Entry(self.frame_sub, width=6, textvariable=self.fps_var).grid(row=sub_row, column=1)
        sub_row += 1

        ttk.Label(self.frame_sub, text="Labrys Targets").grid(row=sub_row, column=0, sticky="w")
        self.labrys_targets_var = tk.StringVar(value="1")
        ttk.Entry(self.frame_sub, width=6, textvariable=self.labrys_targets_var).grid(row=sub_row, column=1)
        sub_row += 1

        self.frame_chan = ttk.LabelFrame(self, text="Subclass Ranks")
        self.frame_chan.grid(row=0, column=2, sticky="nw", padx=5, pady=5)
        chan_row = 0

        chan_trainers = [
            ("Fell", "TFell"), ("Gossamer", "TGoss"),
            ("Channel", "TChan"), ("Atkite", "TAtkite"),
            ("Darkite", "TDarkite"), ("Balthite", "TBalthite"),
            ("Dethite", "TDethite"), ("Toomeria", "TToomeria"),
            ("ChampReg", "TChampReg"),
            ("Splash", "TSplash"), ("SplashOld", "TSplashOld"),
            ("Respin", "TRespin"), ("Duvin", "TDuvin"),
            ("Heen", "THeen"),
            ("Crato", "TCrato"), ("Spleisha", "TSpleisha"),
            ("SpleishaOld", "TSpleishaOld"), ("Tracking", "TTracking"),
            ("BB", "TBB"), ("Cloak", "TCloak"), ("Girdle", "TGirdle"),
            ("Cryptus", "TCryptus"), ("Disabla", "TDisabla"),
            ("Dantus", "TDantus"), ("Aneurus", "TAneurus"),
            ("Posuhm", "TPosuhm"),
        ]
        for label, key in chan_trainers:
            ttk.Label(self.frame_chan, text=label).grid(row=chan_row, column=0, sticky="w")
            v = tk.StringVar(value="0")
            self.vars[key] = v
            ttk.Entry(self.frame_chan, width=6, textvariable=v).grid(row=chan_row, column=1)
            chan_row += 1

        self.frame_results = ttk.LabelFrame(self, text="Results")
        self.frame_results.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.results_text = tk.Text(self.frame_results, width=90, height=30)
        self.results_text.grid(row=0, column=0, sticky="nsew")

        self.btn_calc = ttk.Button(self, text="Calculate", command=self.on_calculate)
        self.btn_calc.grid(row=2, column=0, columnspan=3, pady=5)

    def on_calculate(self):
        params = {}
        for k, v in self.vars.items():
            try:
                params[k] = float(v.get())
            except ValueError:
                params[k] = 0.0

        params["Subclass"] = int(self.subclass_var.get())
        params["FPS"] = float(self.fps_var.get() or 5)
        params["LabrysTargets"] = int(self.labrys_targets_var.get() or 1)

        race_idx = RACE_NAMES.index(self.race_var.get())
        params["Race"] = race_idx

        weapon_idx = next(k for k, v in WEAPON_NAMES.items() if v == self.weapon_var.get())
        left_idx = next(k for k, v in LEFT_NAMES.items() if v == self.left_var.get())
        shoulder_idx = next(k for k, v in SHOULDER_NAMES.items() if v == self.shoulder_var.get())

        params["Weapon"] = weapon_idx
        params["Left"] = left_idx
        params["Shoulder"] = shoulder_idx

        res = self.compute(params)
        self.show_results(res)

    def compute(self, params):
        g = lambda k, d=0: float(params.get(k, d))

        EAtkus = g("EAtkus"); TAtkus = g("TAtkus")
        EDarkus = g("EDarkus"); TDarkus = g("TDarkus")
        EBalthus = g("EBalthus"); TBalthus = g("TBalthus")
        ERegia = g("ERegia"); TRegia = g("TRegia")
        EHistia = g("EHistia"); THistia = g("THistia")
        EDetha = g("EDetha"); TDetha = g("TDetha")
        ETroilus = g("ETroilus"); TTroilus = g("TTroilus")
        ERodnus = g("ERodnus"); TRodnus = g("TRodnus")
        ESpiritus = g("ESpiritus"); TSpiritus = g("TSpiritus")

        TEvus = g("TEvus"); TSwengus = g("TSwengus"); TFarly = g("TFarly")
        TKnox = g("TKnox"); TAngilsa = g("TAngilsa")
        TBodrus = g("TBodrus"); THardia = g("THardia")
        TForvyola = g("TForvyola"); TBangus = g("TBangus")
        TErthron = g("TErthron"); TErthronNew = g("TErthronNew")
        TAtkia = g("TAtkia"); TDarktur = g("TDarktur")
        TAktur = g("TAktur"); TStedfustus = g("TStedfustus")
        TAnemia = g("TAnemia")

        TFell = g("TFell"); TGoss = g("TGoss"); TChan = g("TChan")
        TAtkite = g("TAtkite"); TDarkite = g("TDarkite")
        TBalthite = g("TBalthite"); TDethite = g("TDethite")
        TToomeria = g("TToomeria")
        TSplash = g("TSplash"); TSplashOld = g("TSplashOld")
        TRespin = g("TRespin"); TChampReg = g("TChampReg")
        TDuvin = g("TDuvin"); THeen = g("THeen")
        TCrato = g("TCrato"); TSpleisha = g("TSpleisha")
        TSpleishaOld = g("TSpleishaOld"); TBB = g("TBB")
        TCloak = g("TCloak"); TGirdle = g("TGirdle")
        TCryptus = g("TCryptus"); TDisabla = g("TDisabla")
        TDantus = g("TDantus"); TAneurus = g("TAneurus")
        TPosuhm = g("TPosuhm"); TTracking = g("TTracking")

        Subclass = int(params.get("Subclass", 0))
        Race = int(params.get("Race", 0))
        Weapon = int(params.get("Weapon", 0))
        Left = int(params.get("Left", 0))
        Shoulder = int(params.get("Shoulder", 0))
        LabrysTargets = int(params.get("LabrysTargets", 1))
        if LabrysTargets < 1:
            LabrysTargets = 1

        FPS = float(params.get("FPS", 5))
        if FPS <= 0:
            FPS = 1

        if TChampReg == 11 and Race in (1, 2, 4):
            TChampReg = 10
        if TChampReg == 6 and Race in (0, 5):
            TChampReg = 5

        if Subclass != 1:
            TChan = 0; TAtkite = 0; TDarkite = 0
            TBalthite = 0; TDethite = 0
            TToomeria = 0; TChampReg = 0
            TCloak = 0; TGirdle = 0
        if Subclass != 2:
            TDuvin = 0; TSplash = 0; TSplashOld = 0
            TRespin = 0; TTracking = 0
        if Subclass != 3:
            TCryptus = 0; TDisabla = 0; TDantus = 0
            TAneurus = 0; TPosuhm = 0

        ChanMult = 1
        IsDoubleIte = False
        if is_earth_mineral(Left) and is_earth_mineral(Shoulder):
            ChanMult = 0.5
            IsDoubleIte = True
            if Left >= 105:
                Left = Left - 4

        Chan = TChan + math.floor(TAtkite * 5 / 4) + math.floor(TDarkite * 5 / 4) \
                     + math.floor(TBalthite * 5 / 4) + math.floor(TDethite * 5 / 4)

        EFell = TFell + 10
        AtkiteStr = Chan
        DarkiteStr = Chan
        BalthiteStr = Chan
        DethiteStr = Chan

        AtkusReq = 99999
        AccuracyReq = max(AtkusToAccuracy(AtkusReq), 0)

        SEvus = 0
        SSwengus = 0

        Accuracy = AtkusToAccuracy(EAtkus + TAtkus)
        Accuracy += TEvus * 4
        Accuracy += TBodrus * 4
        Accuracy += THardia * 4
        Accuracy -= TKnox * 4
        Accuracy -= TAngilsa * 4
        Accuracy += TBangus * 2
        Accuracy += TErthron * 3
        Accuracy += TErthronNew * 2
        Accuracy += AkturToAccuracy(TAktur)
        Accuracy += TAtkia * 13

        SEvus = Accuracy / 4
        SBodrus = Accuracy / 4
        SHardia = Accuracy / 4
        SErthron = Accuracy / 3
        SErthronNew = Accuracy / 2
        SBangus = Accuracy / 2
        SAtkia = Accuracy / 13

        if Left == 101 or Left == 105:
            Accuracy += CMToAccuracy(math.floor(AtkiteStr * ChanMult))
        if Left == 105:
            Accuracy += CMToAccuracy(IteBoostStrength(Chan))
        if Shoulder == 101 or Shoulder == 105:
            Accuracy += CMToAccuracy(math.floor(AtkiteStr * ChanMult))
        if Shoulder == 105:
            Accuracy += CMToAccuracy(IteBoostStrength(Chan))

        GossAccuracy = 0
        GossDamage = 0
        FellAccuracy = 0
        TellAccuracy = 0

        if 93 <= Weapon <= 97 and Subclass == 2:
            Families = Weapon - 92
            GossAccuracy = 32 * TGoss
            GossDamage = 12 * TGoss
            GossAccuracy = math.floor(GossAccuracy * Families / 10)
            GossDamage = math.floor(GossDamage * Families / 10)
            GossAccuracy = min(GossAccuracy, max(AccuracyReq - Accuracy, 0))
        elif Weapon == 98 and Subclass == 2:
            GossAccuracy = 32 * TGoss
            GossDamage = 12 * TGoss
            GossAccuracy = min(GossAccuracy, max(AccuracyReq - Accuracy, 0))
        elif Weapon == 101:
            FellAccuracy = 16 * EFell
            FellAccuracy = min(FellAccuracy, max(AccuracyReq - Accuracy, 0))
        elif Weapon == 102:
            FellAccuracy = 32 * EFell
            FellAccuracy = min(FellAccuracy, max(AccuracyReq - Accuracy, 0))
        elif Weapon == 103 and Subclass == 1:
            TellAccuracy = -32 * TFell
            TellAccuracy = max(TellAccuracy, min(AccuracyReq - Accuracy, 0))

        Accuracy += GossAccuracy
        Accuracy += FellAccuracy
        Accuracy += TellAccuracy

        ShowVal = Accuracy
        Accuracy += races[Race][0]
        Accuracy += weapons[Weapon][0]
        Accuracy += lefts[Left][0]
        Accuracy += shoulders[Shoulder][0]
        AccuracyReq += races[Race][0]
        AccuracyReq += weapons[Weapon][0]
        AccuracyReq += lefts[Left][0]
        AccuracyReq += shoulders[Shoulder][0]

        AccuracyBuff = 0
        if Weapon == 89:
            AccuracyBuff = 0.2 * (Accuracy - races[0][0])
        if AccuracyBuff != 0:
            Accuracy += AccuracyBuff
            ShowVal += AccuracyBuff

        AccuracyNoIte = Accuracy - shoulders[Shoulder][0] - TellAccuracy
        if (Left == 101 or Left == 105) and not IsDoubleIte:
            AccuracyNoIte -= lefts[Left][0]
            AccuracyNoIte -= CMToAccuracy(math.floor(AtkiteStr * ChanMult))
        if Left == 105 and not IsDoubleIte:
            AccuracyNoIte -= CMToAccuracy(IteBoostStrength(Chan))
        if Shoulder == 101 or Shoulder == 105:
            AccuracyNoIte -= CMToAccuracy(math.floor(AtkiteStr * ChanMult))
        if Shoulder == 105:
            AccuracyNoIte -= CMToAccuracy(IteBoostStrength(Chan))

        MaxDamage = DarkusToDamage(EDarkus + TDarkus)
        MaxDamage += TEvus * 1
        MaxDamage += TBodrus * 1
        MaxDamage += TKnox * 11
        MaxDamage -= TAngilsa * 1
        MaxDamage += TErthron * 1
        MaxDamage += TErthronNew * 1
        MaxDamage += TAtkia * 3
        MaxDamage += DarkturToDamage(TDarktur)
        MinDamage = MaxDamage
        MaxDamage += THardia * 1
        MaxDamage += TBangus * 3
        MinDamage += TBangus * 2

        SKnox = MaxDamage / 11
        if MinDamage / 11 < SKnox:
            SKnox = MinDamage / 11
        if MaxDamage < SEvus:
            SEvus = MaxDamage
        if MinDamage < SEvus:
            SEvus = MinDamage
        if MaxDamage < SBodrus:
            SBodrus = MaxDamage
        if MinDamage < SBodrus:
            SBodrus = MinDamage
        if MaxDamage < SHardia:
            SHardia = MaxDamage
        if MaxDamage / 3 < SBangus:
            SBangus = MaxDamage / 3
        if MinDamage / 2 < SBangus:
            SBangus = MinDamage / 2
        if MaxDamage < SErthron:
            SErthron = MaxDamage
        if MinDamage < SErthron:
            SErthron = MinDamage
        if MaxDamage < SErthronNew:
            SErthronNew = MaxDamage
        if MinDamage < SErthronNew:
            SErthronNew = MinDamage
        if MaxDamage / 3 < SAtkia:
            SAtkia = MaxDamage / 3
        if MinDamage / 3 < SAtkia:
            SAtkia = MinDamage / 3

        if Weapon == 101:
            MaxDamage += 6 * EFell
            MinDamage += 6 * EFell
        if Weapon == 102:
            MaxDamage += 12 * EFell
            MinDamage += 12 * EFell

        if Left == 102 or Left == 106:
            MaxDamage += CMToMaxDamage(math.floor(DarkiteStr * ChanMult))
            MinDamage += CMToMinDamage(math.floor(DarkiteStr * ChanMult))
        if Left == 106:
            MaxDamage += CMToMaxDamage(IteBoostStrength(Chan))
            MinDamage += CMToMinDamage(IteBoostStrength(Chan))
        if Shoulder == 102 or Shoulder == 106:
            MaxDamage += CMToMaxDamage(math.floor(DarkiteStr * ChanMult))
            MinDamage += CMToMinDamage(math.floor(DarkiteStr * ChanMult))
        if Shoulder == 106:
            MaxDamage += CMToMaxDamage(IteBoostStrength(Chan))
            MinDamage += CMToMinDamage(IteBoostStrength(Chan))

        MaxDamage += GossDamage
        MinDamage += GossDamage

        if MinDamage <= MaxDamage:
            ShowValDmg = MinDamage
        else:
            ShowValDmg = MaxDamage
        ShowValMin = MinDamage
        ShowValMax = MaxDamage
        ShowValAvg = (MinDamage + MaxDamage * 3) / 4

        MinDamage += races[Race][1]
        MaxDamage += races[Race][2]
        MinDamage += weapons[Weapon][1]
        MaxDamage += weapons[Weapon][2]
        MinDamage += lefts[Left][1]
        MaxDamage += lefts[Left][2]
        MinDamage += shoulders[Shoulder][1]
        MaxDamage += shoulders[Shoulder][2]

        MinDamageNoIte = MinDamage - shoulders[Shoulder][1]
        MaxDamageNoIte = MaxDamage - shoulders[Shoulder][2]
        if (Left == 102 or Left == 106) and not IsDoubleIte:
            MinDamageNoIte -= lefts[Left][1]
            MaxDamageNoIte -= lefts[Left][2]
            MinDamageNoIte -= CMToMinDamage(math.floor(DarkiteStr * ChanMult))
            MaxDamageNoIte -= CMToMaxDamage(math.floor(DarkiteStr * ChanMult))
        if Left == 106 and not IsDoubleIte:
            MinDamageNoIte -= CMToMinDamage(IteBoostStrength(Chan))
            MaxDamageNoIte -= CMToMaxDamage(IteBoostStrength(Chan))
        if Shoulder == 102 or Shoulder == 106:
            MinDamageNoIte -= CMToMinDamage(math.floor(DarkiteStr * ChanMult))
            MaxDamageNoIte -= CMToMaxDamage(math.floor(DarkiteStr * ChanMult))
        if Shoulder == 106:
            MinDamageNoIte -= CMToMinDamage(IteBoostStrength(Chan))
            MaxDamageNoIte -= CMToMaxDamage(IteBoostStrength(Chan))

        MinDamageBuff = 0
        MaxDamageBuff = 0
        if Weapon == 89:
            MinDamageBuff = 0.15 * (MinDamage - races[0][1])
            MaxDamageBuff = 0.15 * (MaxDamage - races[0][2])
        if MinDamageBuff != 0:
            MinDamage += MinDamageBuff
            ShowValMin += MinDamageBuff
            ShowValAvg += MinDamageBuff / 4
        if MaxDamageBuff != 0:
            MaxDamage += MaxDamageBuff
            ShowValMax += MaxDamageBuff
            ShowValAvg += 3 * MaxDamageBuff / 4

        MinDamageBuff = 0
        MaxDamageBuff = 0
        if Weapon == 89:
            MinDamageBuff = 0.15 * (MinDamageNoIte - races[0][1])
            MaxDamageBuff = 0.15 * (MaxDamageNoIte - races[0][2])
        if MinDamageBuff != 0:
            MinDamageNoIte += MinDamageBuff
        if MaxDamageBuff != 0:
            MaxDamageNoIte += MaxDamageBuff

        LabrysDamage = None
        if Weapon == 110 and Subclass == 1:
            LabrysDamage = GetLabrysDamage(MinDamage, MaxDamage, TFell, LabrysTargets)
            ShowValMin = LabrysDamage[0] - (MinDamage - ShowValMin)
            ShowValMax = LabrysDamage[1] - (MaxDamage - ShowValMax)
            ShowValAvg = (ShowValMin + ShowValMax * 3) / 4
            ShowValDmg = ShowValAvg

        if Weapon == 110 and Subclass == 1:
            HitMin = LabrysDamage[0]
            HitMax = LabrysDamage[1]
        else:
            HitMin = MinDamage
            HitMax = MaxDamage
        HitMax = HitMax * 3
        if HitMin < 0:
            HitMin = 0
        HitMin = HitMin + 100
        if HitMax < 0:
            HitMax = 0
        HitMax = HitMax + 100
        if HitMax < HitMin:
            HitMax = HitMin

        UMinDamage = MinDamage if Weapon != 110 or Subclass != 1 else LabrysDamage[0]
        UMaxDamage = MaxDamage if Weapon != 110 or Subclass != 1 else LabrysDamage[1]
        if UMinDamage < 0:
            UMinDamage = 0
        if UMaxDamage < 0:
            UMaxDamage = 0
        if UMaxDamage < UMinDamage / 3:
            UMaxDamage = UMinDamage / 3

        Balance = BalthusToBalance(EBalthus + TBalthus)
        Balance += TEvus * 18
        Balance += TBodrus * 9
        Balance += THardia * 9
        Balance += TAtkus * 15
        Balance += TDarkus * 18
        Balance += TSwengus * 30
        Balance += TKnox * 18
        Balance -= TAngilsa * 18
        Balance += TBangus * 21
        Balance += TErthron * 15
        Balance += TErthronNew * 15

        if Balance / 18 < SEvus:
            SEvus = Balance / 18
        if Balance / 15 < SErthron:
            SErthron = Balance / 15
        if Balance / 15 < SErthronNew:
            SErthronNew = Balance / 15
        if Balance / 9 < SBodrus:
            SBodrus = Balance / 9
        if Balance / 9 < SHardia:
            SHardia = Balance / 9
        if Balance / 21 < SBangus:
            SBangus = Balance / 21
        SSwengus = Balance / 30

        if Left == 103 or Left == 107:
            Balance += CMToBalance(math.floor(BalthiteStr * ChanMult))
        if Left == 107:
            Balance += CMToBalance(IteBoostStrength(Chan))
        if Shoulder == 103 or Shoulder == 107:
            Balance += CMToBalance(math.floor(BalthiteStr * ChanMult))
        if Shoulder == 107:
            Balance += CMToBalance(IteBoostStrength(Chan))

        ShowValBal = Balance
        Balance += races[Race][3]
        Balance += weapons[Weapon][3]
        Balance += lefts[Left][3]
        Balance += shoulders[Shoulder][3]

        BalanceBuff = 0
        if Weapon == 89:
            BalanceBuff = 0.1 * (Balance - races[0][3])
        if BalanceBuff != 0:
            Balance += BalanceBuff
            ShowValBal += BalanceBuff

        ShowValBalance = ShowValBal

        BalanceNoIte = Balance - shoulders[Shoulder][3]
        if (Left == 103 or Left == 107) and not IsDoubleIte:
            BalanceNoIte -= lefts[Left][3]
            BalanceNoIte -= CMToBalance(math.floor(BalthiteStr * ChanMult))
        if Left == 107 and not IsDoubleIte:
            BalanceNoIte -= CMToBalance(IteBoostStrength(Chan))
        if Shoulder == 103 or Shoulder == 107:
            BalanceNoIte -= CMToBalance(math.floor(BalthiteStr * ChanMult))
        if Shoulder == 107:
            BalanceNoIte -= CMToBalance(IteBoostStrength(Chan))

        Regen = RegiaToRegen(ERegia + TRegia)
        Regen += TEvus * 4
        Regen += TBodrus * 3
        Regen += THardia * 1
        Regen += TAtkus * 1
        Regen += TDarkus * 1
        Regen += TSwengus * 7
        Regen -= TKnox * 2
        Regen += TAngilsa * 26
        Regen += TForvyola * 8
        Regen += TBangus * 5
        Regen += TErthron * 3
        Regen += TErthronNew * 2
        Regen += TAtkia * 3
        Regen += TStedfustus * 6
        Regen += TAnemia * 8

        SAngilsa = Regen / 26
        SForvyola = Regen / 8
        SStedfustus = Regen / 6
        SAnemia = Regen / 8
        if Regen / 4 < SEvus:
            SEvus = Regen / 4
        if Regen / 3 < SErthron:
            SErthron = Regen / 3
        if Regen / 2 < SErthronNew:
            SErthronNew = Regen / 2
        if Regen / 3 < SBodrus:
            SBodrus = Regen / 3
        if Regen / 1 < SHardia:
            SHardia = Regen / 1
        if Regen / 7 < SSwengus:
            SSwengus = Regen / 7
        if Regen / 5 < SBangus:
            SBangus = Regen / 5
        if Regen / 3 < SAtkia:
            SAtkia = Regen / 3

        Regen += races[Race][4]
        Regen += weapons[Weapon][4]
        Regen += lefts[Left][4]
        Regen += shoulders[Shoulder][4]

        RegenNoIte = Regen - shoulders[Shoulder][4]
        if not IsDoubleIte:
            RegenNoIte -= lefts[Left][4]

        Health = HistiaToHealth(EHistia + THistia)
        Health += TEvus * 24
        Health += TBodrus * 24
        Health += THardia * 21
        Health += TDetha * 3
        Health += TRodnus * 36
        Health += TFarly * 48
        Health -= TKnox * 24
        Health -= TAngilsa * 24
        Health += TForvyola * 54
        Health += TBangus * 6
        Health += TErthron * 24
        Health += TErthronNew * 21
        Health += TSpiritus * 21
        Health += TStedfustus * 54
        Health += TAnemia * 69

        SFarly = Health / 48
        if Health / 24 < SEvus:
            SEvus = Health / 24
        if Health / 24 < SErthron:
            SErthron = Health / 24
        if Health / 21 < SErthronNew:
            SErthronNew = Health / 21
        if Health / 24 < SBodrus:
            SBodrus = Health / 24
        if Health / 21 < SHardia:
            SHardia = Health / 21
        if Health / 54 < SForvyola:
            SForvyola = Health / 54
        if Health / 6 < SBangus:
            SBangus = Health / 6
        if Health / 54 < SStedfustus:
            SStedfustus = Health / 54
        if Health / 69 < SAnemia:
            SAnemia = Health / 69

        Health += races[Race][5]
        Health += weapons[Weapon][5]
        Health += lefts[Left][5]
        Health += shoulders[Shoulder][5]

        Defense = DethaToDefense(EDetha + TDetha)
        Defense += TEvus * 1
        Defense += TBodrus * 1
        Defense += THardia * 1
        Defense += TFarly * 2
        Defense -= TKnox * 1
        Defense -= TAngilsa * 1
        Defense += TErthron * 7
        Defense += TErthronNew * 7

        if Defense < SEvus:
            SEvus = Defense
        if Defense / 7 < SErthron:
            SErthron = Defense / 7
        if Defense / 7 < SErthronNew:
            SErthronNew = Defense / 7
        if Defense < SBodrus:
            SBodrus = Defense
        if Defense < SHardia:
            SHardia = Defense
        if Defense / 2 < SFarly:
            SFarly = Defense / 2

        if Left == 104 or Left == 108:
            Defense += CMToDefense(math.floor(DethiteStr * ChanMult))
        if Left == 108:
            Defense += CMToDefense(IteBoostStrength(Chan))
        if Shoulder == 104 or Shoulder == 108:
            Defense += CMToDefense(math.floor(DethiteStr * ChanMult))
        if Shoulder == 108:
            Defense += CMToDefense(IteBoostStrength(Chan))

        ShowValDef = Defense
        Defense += races[Race][6]
        Defense += weapons[Weapon][6]
        Defense += lefts[Left][6]
        Defense += shoulders[Shoulder][6]
        ShowValDef += BalanceToDefense(ShowValBalance)

        Regeneration = TroilusToRegeneration(ETroilus + TTroilus)
        Regeneration += TFarly * 4
        Regeneration += TBangus * 1
        Regeneration += TStedfustus * 1
        Regeneration -= TAnemia * 1

        if Regeneration / 4 < SFarly:
            SFarly = Regeneration / 4
        if Regeneration < SBangus:
            SBangus = Regeneration
        if Regeneration < SStedfustus:
            SStedfustus = Regeneration

        Regeneration += races[Race][7]
        Regeneration += weapons[Weapon][7]
        Regeneration += lefts[Left][7]

        HealingReceptivity = 2 * (ERodnus + TRodnus)
        HealingReceptivity += TSpiritus
        HealingReceptivity += ESpiritus

        Spirit = ToomeriaToSpirit(TToomeria)
        Spirit += SplashToSpirit(TSplash)
        Spirit += OldSplashToSpirit(TSplashOld)
        Spirit += CratoToSpirit(TCrato)
        Spirit += SpleishaToSpirit(TSpleisha)
        Spirit += OldSplashToSpirit(TSpleishaOld)
        Spirit += 9 * TSpiritus

        Spirit += races[Race][8]
        Spirit += weapons[Weapon][8]
        Spirit += lefts[Left][8]

        SpiritRegen = RespinToSpiritRegen(TRespin)
        SpiritRegen += TChampReg * 20
        if Subclass == 1:
            SpiritRegen += 5
        if Subclass == 3:
            SpiritRegen = 25

        SpiritRegen += races[Race][9]
        SpiritRegen += weapons[Weapon][9]
        SpiritRegen += lefts[Left][9]
        if Subclass == 3:
            SpiritRegen = 25

        BaseShieldstoneDrain = 1066
        if THeen < 0:
            THeen = 0
        if Subclass == 3:
            BaseShieldstoneDrain = 333
            if THeen < 25:
                ShieldstoneDrain = BaseShieldstoneDrain - (134 * THeen) / 24
            else:
                ShieldstoneDrain = (196 * 25) / THeen
        else:
            if THeen < 50:
                ShieldstoneDrain = BaseShieldstoneDrain - (436 * THeen) / 49
            else:
                ShieldstoneDrain = (628 * 50) / THeen
        ShieldstoneDrain = round(ShieldstoneDrain)

        Offense = Accuracy + (3 * MaxDamage + MinDamage) / 4
        OffenseUncapped = Offense
        if Offense < 200:
            Offense = 200

        BalanceCost = RoundDown((5 / 3) * Offense)
        BalanceCostUncapped = RoundDown((5 / 3) * OffenseUncapped)

        GossSpiritCost = 0
        if 93 <= Weapon <= 98:
            GossSpiritCost = GossDamage / 5 + (GossAccuracy * 7) / 80

        SwingsFromFull = Balance / BalanceCost if BalanceCost > 0 else 0
        BalancePerTick = Regen / 6

        return {
            "Accuracy": Accuracy,
            "Atkus": AccuracyToAtkus(ShowVal),
            "ShowVal": ShowVal,

            "MinDamage": MinDamage,
            "MaxDamage": MaxDamage,
            "ShowValMin": ShowValMin,
            "ShowValMax": ShowValMax,
            "ShowValAvg": ShowValAvg,
            "UMinDamage": UMinDamage,
            "UMaxDamage": UMaxDamage,

            "Balance": Balance,
            "ShowValBalance": ShowValBalance,
            "Balthus": BalanceToBalthus(ShowValBalance),

            "Regen": Regen,
            "Regia": RegenToRegia(Regen),

            "Health": Health,
            "Histia": HealthToHistia(Health),

            "Defense": Defense,
            "ShowValDef": ShowValDef,
            "Detha": DefenseToDetha(ShowValDef),

            "Regeneration": Regeneration,
            "Troilus": RegenerationToTroilus(Regeneration),

            "HealingReceptivity": HealingReceptivity,

            "Spirit": Spirit,
            "SpiritRegen": SpiritRegen,

            "ShieldstoneDrain": ShieldstoneDrain,
            "BalanceCost": BalanceCost,
            "BalanceCostUncapped": BalanceCostUncapped,
            "SwingsFromFullBalance": SwingsFromFull,
            "BalancePerTick": BalancePerTick,
            "Chan": Chan,
            "GossSpiritCost": GossSpiritCost,
        }

    def show_results(self, r):
        self.results_text.delete("1.0", tk.END)
        t = self.results_text.insert

        t(tk.END, f"{r['Accuracy']:.0f} Accuracy ({r['Atkus']:.2f} Atkus)\n")
        t(tk.END, f"{r['ShowValMin']:.0f}-{r['ShowValMax']:.0f} Damage (Avg {r['ShowValAvg']:.1f})\n")
        t(tk.END, f"{DamageToDarkus(r['ShowValAvg']):.2f} Darkus (avg)\n")
        t(tk.END, f"{r['Balance']:.0f} Balance ({r['Balthus']:.2f} Balthus)\n")
        t(tk.END, f"{r['Regen']:.0f} Regen ({r['Regia']:.2f} Regia)\n")
        t(tk.END, f"{r['Health']:.0f} Health ({r['Histia']:.2f} Histia)\n")
        t(tk.END, f"{r['ShowValDef']:.0f} Defense ({r['Detha']:.2f} Detha)\n")
        t(tk.END, f"{r['Regeneration']:.0f} Health Regen ({r['Troilus']:.2f} Troilus)\n")
        t(tk.END, f"{r['HealingReceptivity']:.0f} Healing Receptivity\n")
        t(tk.END, f"{r['Spirit']:.0f} Spirit\n")
        t(tk.END, f"{r['SpiritRegen']:.0f} Spirit Regen\n")
        t(tk.END, f"{r['ShieldstoneDrain']} Shieldstone drain/frame\n")
        t(tk.END, f"\n{r['BalanceCost']:.0f} Balance per swing")
        if r['BalanceCostUncapped'] < r['BalanceCost']:
            t(tk.END, f" ({r['BalanceCostUncapped']:.0f} uncapped)")
        t(tk.END, "\n")
        t(tk.END, f"{r['SwingsFromFullBalance']:.2f} Swings from full balance\n")
        t(tk.END, f"{Round(r['BalancePerTick'])} Balance recovered per frame\n")
        t(tk.END, f"{r['Chan']:.0f} Channel Master\n")
        t(tk.END, f"{r['UMinDamage']+100:.0f}-{r['UMaxDamage']*3+100:.0f} Random damage range\n")

if __name__ == "__main__":
    app = FighterCalculator()
    app.mainloop()
