import os
import re
import time
from datetime import datetime

import constants
from constants import *
from storage import read_words_from_file, read_text_files, get_min_time_from_filter, is_excluded, count_word_occurrences

# -----------------------------
# Core Parsing / Counts
# -----------------------------

def count_special_lines(texts):
    special_occ = {}
    exclude = set()

    ts_re = re.compile(r"^(\d+/\d+/\d+ \d+:\d+:\d+[ap])\s*[•>:-]*\s*(.*)$")
    study_re = re.compile(
        r"You have (almost nothing|a few|more than a few|some things|many things|much to learn|a lot to learn|a vast amount)"
        r" to learn about the (movements|ways|essence) of the (.+?)\.",
        re.IGNORECASE
    )
    kill_re = re.compile(
        r"(?:you|you helped)\s+(?:slaughtered|dispatched|killed|vanquished)\s+the\s+(.+?)\.",
        re.IGNORECASE
    )

    kill_counts = {}
    for content, _ in texts:
        for line in content.splitlines():
            m = kill_re.search(line)
            if m:
                creature = m.group(1).strip().lower()
                kill_counts[creature] = kill_counts.get(creature, 0) + 1

    for content, _ in texts:
        for raw_line in content.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            m = ts_re.match(raw_line)
            if not m:
                continue

            ts_raw, msg = m.groups()

            try:
                timestamp = datetime.strptime(ts_raw, "%m/%d/%y %I:%M:%S%p")
            except Exception:
                timestamp = None

            low = msg.lower()

            if "you abandon your study of the" in low:
                m_ab = re.search(r"you abandon your study of the (.+?)\.", low)
                if m_ab:
                    creature = m_ab.group(1).strip().lower()
                    special_occ.pop(creature, None)
                continue

            m2 = study_re.search(msg)
            if not m2:
                continue

            phrase_group = m2.group(1).lower()
            function     = m2.group(2).lower()
            creature     = m2.group(3).strip().lower()

            trainer_clean = creature

            kt_key = f"{phrase_group} to learn about the {function} of the"

            kills_done = kill_counts.get(trainer_clean, 0)
            stage_table = kills_to_next.get(kt_key, {})

            if stage_table:
                total_required = sum(stage_table.values())
                kills_left = max(total_required - kills_done, 0)
            else:
                kills_left = None

            display_label = f"You have {phrase_group} to learn about the {function} of the {creature}."
            if kills_left is not None:
                display_label += f" — {kills_left} kills left"

            entry = {
                "phrase_group": phrase_group,
                "function": function,
                "timestamp": timestamp,
                "kills_left": kills_left,
                "count": 1,
                "display_label": display_label,
            }

            special_occ.setdefault(trainer_clean, []).append(entry)

    return special_occ, exclude


def count_coins(texts, character_name, min_time=None):
    skinned_total = 0
    share_total = 0
    events = []

    coin_rx = re.compile(
        r"(?:\*\s*)?(You|[A-Za-z][\w']*)\s+recover[s]?\s+the\s+(.+?)\s+(?:fur|blood|mandibles),\s+worth\s+(\d+)c\.\s*Your share is\s+(?:(\d+)c|nothing)",
        re.IGNORECASE
    )

    for content, file_time in texts:
        if min_time and file_time < min_time:
            continue

        for line in content.splitlines():
            if is_excluded(line):
                continue
            m = coin_rx.search(line)
            if not m:
                continue

            groups = m.groups()
            if len(groups) != 4:
                continue
            player, monster, worth, share_str = groups
            did_skin = (player == "You" or player == character_name)

            worth = int(worth)
            share = int(share_str) if share_str else 0

            if did_skin:
                skinned_total += worth
            share_total += share

            events.append({
                "monster": monster.strip(),
                "worth": worth,
                "share": share,
                "skinned": did_skin,
                "file_time": file_time
            })

    return skinned_total, share_total, events


def scan_and_aggregate(folder_path, character_name, min_time=None):
    import re as _re

    words        = read_words_from_file(words_file_path)
    replacements = read_words_from_file(replacement_file_path)

    if len(words) != len(replacements):
        raise ValueError(
            f"File Alignment Error: rankmessages.txt ({len(words)} lines) and "
            f"trainers.txt ({len(replacements)} lines) must match exactly."
        )

    mapping = dict(zip(words, replacements))

    texts = read_text_files(folder_path)
    word_occ = count_word_occurrences(texts, words)

    special_occ, exclude = count_special_lines(texts)

    skinned, share, coin_events = count_coins(texts, character_name, min_time)

    normal_ranks = {}
    for w, c in word_occ.items():
        if c:
            t = mapping.get(w, "Unknown")
            if isinstance(t, str):
                normal_ranks[t] = normal_ranks.get(t, 0) + c

    latest_per_creature = {}

    for trainer_clean, entries in special_occ.items():
        if not entries:
            continue

        for e in entries:
            phrase_group = e["phrase_group"]
            msgnums = phrase_to_msgnums.get(phrase_group)
            if msgnums:
                e["msg_num"] = min(msgnums)
            else:
                e["msg_num"] = None

        entries_sorted = sorted(
            entries,
            key=lambda e: (e["timestamp"] is None, e["timestamp"])
        )
        current_stage = entries_sorted[-1]["function"]

        stage_entries = [e for e in entries if e["function"] == current_stage]

        stage_entries_sorted = sorted(
            stage_entries,
            key=lambda e: (e["timestamp"] is None, e["timestamp"])
        )
        best = stage_entries_sorted[-1]

        latest_per_creature[trainer_clean] = best

    special_creatures = {}

    for trainer_clean, e in latest_per_creature.items():
        lbl = e["display_label"]
        msg_num = e["msg_num"]
        kl  = e["kills_left"]

        if isinstance(kl, int):
            kl_str = str(kl)
        elif kl is None:
            kl_str = ""
        else:
            kl_str = str(kl)

        special_creatures[lbl] = (msg_num, kl_str)

    return normal_ranks, special_creatures, skinned, share, coin_events, os.path.basename(folder_path)


def parse_creature_count(count_str):
    clean = str(count_str).strip()
    match = re.match(r'(\d+)(?:\s*\((\d+)\))?', clean)
    if match:
        base = int(match.group(1))
        bonus = int(match.group(2)) if match.group(2) else 0
        return base, bonus
    return 0, 0


def summarize_coin_events(events):
    summary = {}
    for ev in events:
        monster = ev["monster"]
        if monster not in summary:
            summary[monster] = {
                "total_worth": 0,
                "total_share": 0,
                "your_skins": 0
            }
        summary[monster]["total_worth"] += ev["worth"]
        summary[monster]["total_share"] += ev["share"]
        if ev["skinned"]:
            summary[monster]["your_skins"] += 1
    return summary
