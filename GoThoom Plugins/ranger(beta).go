package main

import (
    "strings"
    "gt"
)

var PluginName = "Ranger Macro"

var (
    FirstMorphName  = "Giant Carnivorous Plankton"
    SecondMorphName = "Young Sasquatch"

    speeding  int
    isMorphed int
    whatShape int
    swaobackL string
    keepspeed int
)

func init() {
    // Help text
    gt.RegisterCommand("ranger", func(args string) {
        gt.Console("F1 = First morph (toggle-able)")
        gt.Console("F2 = Second morph (toggle-able)")
        gt.Console("F3 = HeartWood Charm (toggle-able)")
        gt.Console("F10 = Return and reset macro numbers")
    })

    // Hotkey bindings
    gt.AddHotkey("F1", "/_firstMorph")
    gt.RegisterCommand("_firstMorph", func(string) { toggleMorph(1, FirstMorphName) })

    gt.AddHotkey("F2", "/_secondMorph")
    gt.RegisterCommand("_secondMorph", func(string) { toggleMorph(2, SecondMorphName) })

    gt.AddHotkey("F3", "/_toggleHeartwood")
    gt.RegisterCommand("_toggleHeartwood", func(string) { toggleHeartwoodCharm() })

    gt.AddHotkey("F10", "/_resetAll")
    gt.RegisterCommand("_resetAll", func(string) { resetState() })

    // Hook chat log events
    gt.RegisterChatHandler(func(msg string) { checkLogEvents(msg) })
}

func toggleMorph(shape int, name string) {
    if !IgnoreCase(getWaistItem(), "belt of the wild") {
        equipByName("beltofthewild")
    }
    if isMorphed == 0 || (isMorphed == 1 && whatShape != shape) {
        whatShape = shape
        isMorphed = 1
        gt.RunCommand(`/useitem beltofthewild /shape "` + name + `"`)
    } else if isMorphed == 1 && whatShape == shape {
        gt.RunCommand("/useitem beltofthewild /return")
        whatShape = 0
        isMorphed = 0
    }
}

func toggleHeartwoodCharm() {
    if speeding == 0 {
        li := getLeftItem()
        if !IgnoreCase(li, "Nothing") && !IgnoreCase(li, "Heartwood Charm") {
            swaobackL = li
        }
        if !IgnoreCase(li, "Heartwood Charm") {
            equipByName("heartwood")
        }
        speeding = 1
        gt.RunCommand("/useitem left")
    } else {
        speeding = 0
        if IgnoreCase(getLeftItem(), "Heartwood Charm") {
            gt.RunCommand("/useitem heartwood /slow")
            uneq()
        }
    }
}

func resetState() {
    gt.RunCommand("/useitem beltofthewild /return")
    unequipByName("heartwood")
    speeding, isMorphed, whatShape, keepspeed = 0, 0, 0, 0
    swaobackL = ""
}

func checkLogEvents(log string) {
    player := gt.PlayerName()
    hasFallen := player + " has fallen to a"

    switch {
    case strings.Contains(log, "You return"),
        strings.Contains(log, "You are already in"),
        strings.Contains(log, "cannot possibly use"):
        isMorphed, whatShape = 0, 0
        if strings.Contains(log, "cannot possibly use") && speeding == 1 {
            speeding = 0
            uneq()
        }

    case strings.Contains(log, "Using /SHARE to create a spirit link"),
        strings.Contains(log, hasFallen):
        if isMorphed == 1 {
            keepspeed = 1
            isMorphed, whatShape = 0, 0
        }
        if keepspeed == 0 && speeding == 1 {
            speeding = 0
            uneq()
        }

    case strings.Contains(log, "You slow down"):
        if speeding == 1 {
            speeding = 0
            uneq()
        }
    }
}

func uneq() {
    if !IgnoreCase(swaobackL, "Heartwood Charm") {
        if swaobackL != "" {
            gt.ShowNotification("* swapping left hand back to " + swaobackL)
            equipByName(swaobackL)
            swaobackL = ""
            keepspeed = 0
        } else {
            unequipByName("heartwood")
            keepspeed = 0
        }
    }
}

// Inventory helpers
func equipByName(name string) {
    for _, item := range gt.Inventory() {
        if IgnoreCase(item.Name, name) {
            gt.Equip(item.ID)
            return
        }
    }
}

func unequipByName(name string) {
    for _, item := range gt.Inventory() {
        if IgnoreCase(item.Name, name) {
            gt.Unequip(item.ID)
            return
        }
    }
}

func getWaistItem() string {
    for _, item := range gt.EquippedItems() {
        if strings.Contains(strings.ToLower(item.Name), "belt") {
            return item.Name
        }
    }
    return "Nothing"
}

func getLeftItem() string {
    // Assumes "Heartwood" only ever appears in left-hand slot; adapt if needed
    for _, item := range gt.EquippedItems() {
        if strings.Contains(strings.ToLower(item.Name), "heartwood") {
            return item.Name
        }
    }
    return "Nothing"
}

func IgnoreCase(a, b string) bool {
    return strings.EqualFold(a, b)
}
