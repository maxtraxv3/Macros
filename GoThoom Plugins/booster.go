//go:build plugin

package main

import (
    "gt"
    "strconv"
    "strings"
    "time"
)

var PluginName = "booster"

var (
    ANum     = 25
    BNum     = 100
    swaoback string
)

func init() {
    // F‑keys
    gt.RegisterCommand("f1", func(_ string) { f1Handler() })
    gt.RegisterCommand("f2", func(_ string) { f2Handler() })
    gt.RegisterCommand("f3", func(_ string) { f3Handler() })
    gt.RegisterCommand("f4", func(_ string) { f4Handler() })
    gt.RegisterCommand("f5", func(_ string) { f5Handler() })
    // /set
    gt.RegisterCommand("set", func(args string) { setHandler(args) })
}

func f1Handler() {
    if !strings.EqualFold(getRightItemName(), "staff of ballou") {
        swaoback = getRightItemName()
        gt.RunCommand(`/equip staffofballou`)
    }
    gt.RunCommand(`/use /QUIET`)
    go switchBack(swaoback, "staffofballou")
}

func f2Handler() {
    if !strings.EqualFold(getRightItemName(), "rod of akea") {
        swaoback = getRightItemName()
        gt.RunCommand(`/equip rodofakea`)
    }
    gt.RunCommand(`/narr Atkus-Boost`)
    gt.RunCommand(`/use r` + strconv.Itoa(ANum) + `% 100% /QUIET`)
    go switchBack(swaoback, "rodofakea")
}

func f3Handler() {
    if !strings.EqualFold(getRightItemName(), "staff of ballou") {
        swaoback = getRightItemName()
        gt.RunCommand(`/equip staffofballou`)
    }
    time.Sleep(1 * time.Second)
    gt.RunCommand(`/narr Balance-Boost in 4 seconds`)
    time.Sleep(4 * time.Second)
    gt.RunCommand(`/use r` + strconv.Itoa(ANum) + `% ` + strconv.Itoa(BNum) + `%/QUIET`)
    gt.Console("* Boosted Range: " + strconv.Itoa(ANum) + "% Power: " + strconv.Itoa(BNum) + "%")
    go switchBack(swaoback, "staffofballou")
}

func f4Handler() {
    switch ANum {
    case 100:
        ANum = 25
    case 75:
        ANum = 100
    case 50:
        ANum = 75
    case 25:
        ANum = 50
    }
    gt.Console("* Range set to " + strconv.Itoa(ANum))
}

func f5Handler() {
    switch BNum {
    case 100:
        BNum = 33
    case 83:
        BNum = 100
    case 66:
        BNum = 83
    case 33:
        BNum = 66
    }
    gt.Console("* Power set to " + strconv.Itoa(BNum))
}

func setHandler(args string) {
    parts := strings.Fields(args)
    if len(parts) < 2 {
        return
    }
    switch strings.ToLower(parts[0]) {
    case "range":
        if val, err := strconv.Atoi(parts[1]); err == nil {
            ANum = val
            gt.Console("* Range set to " + strconv.Itoa(ANum))
        }
    case "power":
        if val, err := strconv.Atoi(parts[1]); err == nil {
            BNum = val
            gt.Console("* Power set to " + strconv.Itoa(BNum))
        }
    }
}

func switchBack(prev, staff string) {
    time.Sleep(2 * time.Second)
    if prev != "" && !strings.EqualFold(prev, "Nothing") {
        gt.Console("* switched: " + prev)
        gt.RunCommand(`/equip ` + prev)
        swaoback = ""
    } else {
        gt.RunCommand(`/unequip ` + staff)
    }
}

func getRightItemName() string {
    for _, it := range gt.EquippedItems() {
        if it.Equipped {
            return it.Name
        }
    }
    return ""
}
