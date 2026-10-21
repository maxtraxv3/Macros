import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone

from cl_time import *


class CLTime:
    def __init__(self, parent):
        self.parent = parent

        self.main = ttk.Frame(parent, padding=10)
        self.main.grid(row=0, column=0, sticky="nsew")

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Header.TLabel", font=("KIN668", 14, "bold"))
        style.configure("Body.TLabel", font=("KIN668", 11))

        self.build_layout()
        self.update_all()

    def header(self, text):
        return ttk.Label(self.main, text=text, style="Header.TLabel")

    def body(self, text):
        return ttk.Label(self.main, text=text, style="Body.TLabel", justify="left")

    def build_layout(self):
        self.lbl_header = self.header("")
        self.lbl_header.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="n")

        self.header("Dawn/Dusk").grid(row=1, column=0, sticky="n")
        self.lbl_dawn = self.body("")
        self.lbl_dawn.grid(row=2, column=0, sticky="n", pady=(0, 20))

        self.header("Lunar cycle").grid(row=1, column=1, sticky="n")
        self.lbl_lunar = self.body("")
        self.lbl_lunar.grid(row=2, column=1, sticky="n", pady=(0, 20))

        self.header("Zodiac cycle").grid(row=3, column=0, sticky="n")
        self.lbl_zodiac = self.body("")
        self.lbl_zodiac.grid(row=4, column=0, sticky="n", pady=(0, 20))

        self.header("Coliseum").grid(row=3, column=1, sticky="n")
        self.lbl_coliseum = self.body("")
        self.lbl_coliseum.grid(row=4, column=1, sticky="n", pady=(0, 20))

        self.header("ooc → ic").grid(row=5, column=0, sticky="n")
        frame1 = ttk.Frame(self.main)
        frame1.grid(row=6, column=0, sticky="n", pady=(0, 5))
        self.entry_ooc = ttk.Entry(frame1, width=30)
        self.entry_ooc.pack(side="left", padx=(0, 5))
        ttk.Button(frame1, text="Convert", command=self.convert_ooc_to_ic).pack(side="left")
        self.lbl_ooc_result = self.body("")
        self.lbl_ooc_result.grid(row=7, column=0, sticky="n", pady=(0, 20))

        self.header("ic → ooc").grid(row=5, column=1, sticky="n")
        frame2 = ttk.Frame(self.main)
        frame2.grid(row=6, column=1, sticky="n", pady=(0, 5))
        self.entry_ic = ttk.Entry(frame2, width=30)
        self.entry_ic.pack(side="left", padx=(0, 5))
        ttk.Button(frame2, text="Convert", command=self.convert_ic_to_ooc).pack(side="left")
        self.lbl_ic_result = self.body("")
        self.lbl_ic_result.grid(row=7, column=1, sticky="n", pady=(0, 20))

        self.main.columnconfigure(0, weight=1)
        self.main.columnconfigure(1, weight=1)

    def update_all(self):
        cl = cl_now()

        self.lbl_header.config(text=fmt_cl_header(cl))

        sunrise, sunset = dawn_dusk_for_day(cl.ic_day)
        sunrise2, sunset2 = dawn_dusk_for_day(cl.ic_day + 1)
        self.lbl_dawn.config(text=(
            "Today:\n"
            f"  Sunrise at: {fmt_real(sunrise)}\n"
            f"  Sunset at:  {fmt_real(sunset)}\n\n"
            "Tomorrow:\n"
            f"  Next sunrise at: {fmt_real(sunrise2)}\n"
            f"  Next sunset at:  {fmt_real(sunset2)}"
        ))

        moon_day, moon_name = moon_phase_for_day(cl.ic_day)
        next_day, start, noon, end = next_full_moon(cl.ic_day)
        lunar = f"{moon_name}, day {moon_day}\n\n"
        if start:
            lunar += (
                "Next Full Moon:\n"
                f"  Starts at: {fmt_real(start)}\n"
                f"  Noon is at: {fmt_real(noon)}\n"
                f"  Ends at:   {fmt_real(end)}"
            )
        self.lbl_lunar.config(text=lunar)

        sign, day_in_sign, days_until_next = zodiac_for_day(cl.ic_day)
        self.lbl_zodiac.config(text=(
            f"Day {day_in_sign} of {sign}\n"
            f"Next sign rises in {days_until_next} days"
        ))

        next_col = cl_to_real(cl.ic_day + 1, 23, 10)
        self.lbl_coliseum.config(text=f"Coliseum opens at {fmt_real(next_col)}")

        self.parent.after(1000, self.update_all)

    def convert_ooc_to_ic(self):
        try:
            dt = datetime.strptime(self.entry_ooc.get(), "%H:%M %m-%d-%Y").replace(tzinfo=timezone.utc)
        except:
            messagebox.showerror("Error", "Format must be: HH:MM M-D-YYYY")
            return

        cl = real_to_cl(dt)
        result = (
            f"{cl.ic_hour:02d}:{cl.ic_minute:02d} "
            f"{cl.season_name}-{cl.season_day + 1}-{cl.year}"
        )
        self.lbl_ooc_result.config(text=result)

    def convert_ic_to_ooc(self):
        try:
            time_part, date_part = self.entry_ic.get().split()
            hour, minute = map(int, time_part.split(":"))
            season, day, year = date_part.split("-")
            season = season.capitalize()
            day = int(day)
            year = int(year)
            season_index = SEASONS.index(season)
        except:
            messagebox.showerror("Error", "Format must be: HH:MM Season-day-year")
            return

        ic_day = year * IC_DAYS_PER_YEAR + season_index * IC_DAYS_PER_SEASON + (day - 1)
        dt = cl_to_real(ic_day, hour, minute)
        self.lbl_ic_result.config(text=fmt_real(dt))
