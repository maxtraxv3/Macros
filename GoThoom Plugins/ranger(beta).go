package main

import (
    "strings"
)

var PluginName = "Magnic's Ranger Macro"

var (
    FirstMorphName = "Giant Carnivorous Plankton"
    SecondMorphName = "Young Sasquatch"

    speeding   int
    isMorphed  int
    whatShape  int
    swaobackL  string
    keepspeed  int
)

func main() {
    // Setup commands/help
    AddCommand("/ranger", func(args string) {
        lines := []string{
            "F1 = First morph (toggle-able)",
            "F2 = Second morph (toggle-able)",
            "F3 = HeartWood Charm (toggle-able)",
            "F5 = Befriend",
            "F6 = Control Befriend'ed",
            "F7 = Dismiss Friend",
            "/reflect = Uses Belt to reflect what you have learned",
            "F10 = Return and reset macro numbers",
        }
        for _, l := range lines {
            ShowNotification(l)
        }
    })

    // Hotkeys
    AddHotkey("F1", "firstMorph")
    AddCommand("firstMorph", func(args string) { toggleMorph(1, FirstMorphName) })

    AddHotkey("F2", "secondMorph")
    AddCommand("secondMorph", func(args string) { toggleMorph(2, SecondMorphName) })

    AddHotkey("F3", "toggleHeartwood")
    AddCommand("toggleHeartwood", func(args string) { toggleHeartwoodCharm() })

    AddHotkey("F10", "resetAll")
    AddCommand("resetAll", func(args string) { resetState() })

    // Chat/event monitoring — mimic @login rangerloop
    GetChat(func(name, messageType, message string) {
        checkLogEvents(message)
    })
}

func toggleMorph(shape int, name string) {
    // Ensure belt equipped
    if !EqualAnycase(getWaistItem(), "belt of the wild") {
        EquipItem("beltofthewild")
    }

    if isMorphed == 0 || (isMorphed == 1 && whatShape != shape) {
        whatShape = shape
        isMorphed = 1
        SendNow(`/useitem beltofthewild /shape "` + name + `"`)
    } else if isMorphed == 1 && whatShape == shape {
        SendNow("/useitem beltofthewild /return")
        whatShape = 0
        isMorphed = 0
    }
}

func toggleHeartwoodCharm() {
    if speeding == 0 {
        if li := getLeftItem(); !EqualAnycase(li, "Nothing") && !EqualAnycase(li, "Heartwood Charm") {
            swaobackL = li
        }
        if !EqualAnycase(getLeftItem(), "Heartwood Charm") {
            EquipItem("heartwood")
        }
        speeding = 1
        SendNow("/useitem left")
    } else {
        speeding = 0
        if EqualAnycase(getLeftItem(), "Heartwood Charm") {
            SendNow("/useitem heartwood /slow")
            uneq()
        }
    }
}

func checkLogEvents(log string) {
    player := PlayerName()
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
    if !EqualAnycase(swaobackL, "Heartwood Charm") {
        if swaobackL != "" {
            ShowNotification("* swapping left hand back to " + swaobackL)
            EquipItem(swaobackL)
            swaobackL = ""
            keepspeed = 0
        } else {
            UnequipItem("heartwood")
            keepspeed = 0
        }
    }
}

func resetState() {
    SendNow("/useitem beltofthewild /return")
    UnequipItem("heartwood")
    speeding = 0
    isMorphed = 0
    whatShape = 0
    swaobackL = ""
    keepspeed = 0
}

// Helpers to mimic @my.<slot> checks
func getWaistItem() string {
    for _, item := range GetEquippedItems() {
        if strings.Contains(strings.ToLower(item.Name), "belt") {
            return item.Name
        }
    }
    return "Nothing"
}

func getLeftItem() string {
    // You might need an API call if "left hand" is trackable separately
    // Placeholder: scan equipped items
    for _, item := range GetEquippedItems() {
        if strings.Contains(strings.ToLower(item.Name), "heartwood") {
            return item.Name
        }
    }
    return "Nothing"
}