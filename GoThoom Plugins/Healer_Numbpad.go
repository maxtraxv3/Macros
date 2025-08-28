//go:build plugin

package main

import (
    "gt"
    "strconv"
    "strings"
    "time"
)

var PluginName = "Healer_Numbpad"

var (
    numHn        [10]string // name slots 0–9
    nextSlot     = 0        // pointer for auto-assign
    rightH       string
)

// ===== INIT =====
func init() {
    // Detect healer on login
    setHealerItemFromEquip()

    // /hi – manual rescan healer item
    gt.RegisterCommand("hi", func(_ string) { setHealerItemFromEquip() })

    // /num <slot> <name> – manual set
    gt.RegisterCommand("num", func(args string) { numCommand(args) })

    // /wn – list stored names
    gt.RegisterCommand("wn", func(_ string) { listNumpadNames() })

    // Ctrl+Numpad hotkeys → heal
    for i := 0; i <= 9; i++ {
        slot := i
        gt.AddHotkey("ctrl+num"+strconv.Itoa(slot), "/healSlot "+strconv.Itoa(slot))
    }
    gt.RegisterCommand("healSlot", func(args string) {
        if val, err := strconv.Atoi(strings.TrimSpace(args)); err == nil {
            healSlot(val)
        }
    })

    // Alt+Shift+Right‑Click → capture & assign to nextSlot
    go func() {
        for {
            if gt.KeyPressed("Alt") && gt.KeyPressed("Shift") && gt.MouseJustPressed("Right") {
                click := gt.LastClick()
                if click.OnMobile {
                    saveToNextSlot(click.Mobile.Name)
                }
            }
            time.Sleep(50 * time.Millisecond)
        }
    }()
}

// ===== Healer detection =====
func setHealerItemFromEquip() {
    healerNames := []string{
        "caduceus", "mercurial staff", "asklepian", "asklepian staff",
    }
    items := gt.EquippedItems()
    for _, it := range items {
        lname := strings.ToLower(it.Name)
        for _, heal := range healerNames {
            if lname == heal {
                rightH = it.Name
                gt.Console("* Healer Item set to " + rightH)
                return
            }
        }
    }
    rightH = ""
    gt.Console("* No healer item equipped")
}

func getRightItemName() string {
    for _, it := range gt.EquippedItems() {
        if it.Equipped {
            return it.Name
        }
    }
    return ""
}

// ===== Save & assign =====
func saveToNextSlot(name string) {
    numHn[nextSlot] = name
    gt.Console(name + " assigned to Numpad " + strconv.Itoa(nextSlot))
    nextSlot++
    if nextSlot > 9 {
        nextSlot = 0
    }
}

// ===== /num handler =====
func numCommand(args string) {
    parts := strings.Fields(args)
    if len(parts) >= 2 {
        if val, err := strconv.Atoi(parts[0]); err == nil && val >= 0 && val <= 9 {
            numHn[val] = parts[1]
            gt.Console(parts[1] + " assigned to Numpad " + strconv.Itoa(val))
        }
    }
}

// ===== Heal from slot =====
func healSlot(slot int) {
    if slot < 0 || slot > 9 {
        return
    }
    target := numHn[slot]
    if target == "" {
        gt.Console("* No name stored in Numpad " + strconv.Itoa(slot))
        return
    }
    if !strings.EqualFold(getRightItemName(), rightH) && rightH != "" {
        gt.RunCommand(`/equip ` + rightH)
    }
    gt.Console("* healing " + target)
    gt.RunCommand(`/use ` + target)
}

// ===== List stored names =====
func listNumpadNames() {
    gt.Console("* Numpad assignments:")
    for i := 0; i <= 9; i++ {
        if numHn[i] != "" {
            gt.Console(strconv.Itoa(i) + ": " + numHn[i])
        }
    }
    gt.Console("* ---- end ---- *")
}