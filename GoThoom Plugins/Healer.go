//go:build plugin

package main

import (
    "gt"
    "strings"
    "time"
)

var PluginName = "Healer"

var (
    rightH string
    rad    bool
)

func init() {
    // Detect healer on login
    setHealerItemFromEquip()

    // /hi – manual rescan
    gt.RegisterCommand("hi", func(_ string) { setHealerItemFromEquip() })

    // F‑key and whisper commands
    gt.RegisterCommand("f1", func(_ string) { f1Handler() })
    gt.RegisterCommand("f3", func(_ string) { f3Handler() })
    gt.RegisterCommand("f4", func(_ string) { gt.RunCommand(`/whisper Attack`) })
    gt.RegisterCommand("f5", func(_ string) { gt.RunCommand(`/whisper Stay`) })
    gt.RegisterCommand("f6", func(_ string) { gt.RunCommand(`/whisper Obey`) })
    gt.RegisterCommand("f9", func(_ string) { gt.RunCommand(`/whisper Go home`) })
    gt.RegisterCommand("f10", func(_ string) { f10Handler() })

    // Continuous check for right‑click healing
    go func() {
        for {
            if gt.MouseJustPressed("Right") {
                handleRightClickHeal()
            }
            time.Sleep(50 * time.Millisecond) // gentle poll
        }
    }()
}

// ===== Healer scan =====
func setHealerItemFromEquip() {
    healerNames := []string{
        "caduceus",
        "mercurial staff",
        "asklepian",
        "asklepian staff",
    }
    items := gt.EquippedItems()
    for _, it := range items {
        name := strings.ToLower(it.Name)
        for _, healName := range healerNames {
            if name == healName {
                rightH = it.Name
                rad = strings.Contains(name, "asklepian")
                gt.Console("* Healer Item set to " + rightH)
                return
            }
        }
    }
    rightH = ""
    rad = false
    gt.Console("* No healer item equipped")
}

// ===== Handlers =====
func handleRightClickHeal() {
    clickTarget := getClickedPlayerName()

    if strings.Contains(strings.ToLower(getRightItemName()), "chain") {
        gt.Console("* Disabled chain equipped!")
        return
    }

    if clickTarget != "" {
        if !strings.EqualFold(getRightItemName(), rightH) && rightH != "" {
            gt.RunCommand(`/equip ` + rightH)
        }
        gt.RunCommand(`/use ` + clickTarget)
        gt.Console("* Healing " + clickTarget)
    } else {
        if !strings.EqualFold(getRightItemName(), rightH) && rightH != "" {
            gt.RunCommand(`/equip ` + rightH)
        }
        gt.RunCommand(`/use /off`)
    }

    if strings.EqualFold(clickTarget, gt.PlayerName()) {
        gt.RunCommand(`/equip moonstone`)
    }
}

func f1Handler() {
    if strings.Contains(strings.ToLower(getRightItemName()), "chain") {
        gt.Console("* Disabled chain equipped!")
        return
    }
    if rad {
        if !strings.EqualFold(getRightItemName(), rightH) && rightH != "" {
            gt.RunCommand(`/equip ` + rightH)
        }
        gt.RunCommand(`/use`)
        gt.Console("* Radium Mode")
    } else {
        gt.Console("* Your healer item isn't capable of that")
    }
}

func f3Handler() {
    if strings.Contains(strings.ToLower(getRightItemName()), "chain") {
        gt.Console("* Disabled chain equipped!")
        return
    }
    if !strings.EqualFold(getRightItemName(), rightH) && rightH != "" {
        gt.RunCommand(`/equip ` + rightH)
    }
    gt.RunCommand(`/use /pet`)
}

func f10Handler() {
    if !strings.EqualFold(getNeckItemName(), "purgatory pendant") {
        gt.RunCommand(`/equip purgatorypendant`)
    }
    gt.RunCommand(`/useitem purgatorypendant`)
}

// ===== Helpers =====
func getRightItemName() string {
    for _, it := range gt.EquippedItems() {
        if it.Equipped {
            return it.Name
        }
    }
    return ""
}

func getNeckItemName() string {
    for _, it := range gt.EquippedItems() {
        if it.Equipped && strings.Contains(strings.ToLower(it.Name), "purgatory") {
            return it.Name
        }
    }
    return ""
}

func getClickedPlayerName() string {
    click := gt.LastClick()
    if click.OnMobile {
        return click.Mobile.Name
    }
    return ""
}
