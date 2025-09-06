//go:build plugin
package main

import (
    "gt"
    "regexp"
    "strings"
    "time"
)

const PluginName       = "Default Macro Port"
const PluginAuthor     = "Magnic"
const PluginCategory   = "Automation"
const PluginAPIVersion = 1

// ===== Configurable morph names =====
var (
    firstMorphName  = `"Giant Carnivorous Plankton"`
    secondMorphName = `"Young Sasquatch"`
)

// ===== State Variables =====
var (
    speeding      bool
    isMorphed     bool
    whatShape     int
    keepspeed     bool
    autoTradeZero bool
    autoMate      bool
    autoBoard     bool
)

// ===== Regex =====
var (
    tradeZeroRegex    = regexp.MustCompile(`(?i)To accept.*\\buy 0\s+(\S+)`)
    boatPromptRegexes []*regexp.Regexp
    rangerRegex       = regexp.MustCompile(`(?i)Ranger progress`)
)

// ===== Init =====
func Init() {
    // Morph / Speed hotkeys
    gt.Key("F1", hotkeyFirstMorph)
    gt.Key("F2", hotkeySecondMorph)
    gt.Key("F3", hotkeyHeartwood)
    gt.Key("F10", hotkeyReset)

    // Befriend / Control / Dismiss
    gt.Key("F5", func() { gt.Run(`/befriend`) })
    gt.Key("F6", func() { gt.Run(`/control`) })
    gt.Key("F7", func() { gt.Run(`/dismiss`) })

    // Pose hotkeys
    gt.Key("Ctrl-1", func() { gt.Run(`/pose wave`) })
    gt.Key("Ctrl-2", func() { gt.Run(`/pose bow`) })
    gt.Key("Ctrl-3", func() { gt.Run(`/pose cheer`) })

    // Example fixed item equip hotkeys
    gt.Key("Alt-1", func() { gt.Run(`/equip heartwood`) })
    gt.Key("Alt-2", func() { gt.Run(`/equip beltofthewild`) })

    // Commands
    gt.RegisterCommand("atz", cmdToggleATZ)
    gt.RegisterCommand("at", cmdToggleAutoMate)
    gt.RegisterCommand("aboard", cmdToggleAutoBoard)
    gt.RegisterCommand("reflect", cmdReflect)

    // Build boat/skiff regexes now that we know player name
    boatPromptRegexes = buildBoatRegexes()

    // Log watcher
    gt.RegisterInputHandler(logWatcher)

    // Background loops
    go autoMateLoop()
}

// ===== Morph / Speed Hotkeys =====
func hotkeyFirstMorph() {
    ensureBelt()
    if !isMorphed {
        whatShape, isMorphed = 1, true
        gt.Run(`/useitem beltofthewild /shape ` + firstMorphName)
    } else if whatShape != 1 {
        whatShape, isMorphed = 1, true
        gt.Run(`/useitem beltofthewild /shape ` + firstMorphName)
    } else {
        gt.Run(`/useitem beltofthewild /return`)
        whatShape, isMorphed = 0, false
    }
}

func hotkeySecondMorph() {
    ensureBelt()
    if !isMorphed {
        gt.Run(`/useitem beltofthewild /shape ` + secondMorphName)
        whatShape, isMorphed = 2, true
    } else if whatShape != 2 {
        gt.Run(`/useitem beltofthewild /shape ` + secondMorphName)
        whatShape, isMorphed = 2, true
    } else {
        gt.Run(`/useitem beltofthewild /return`)
        whatShape, isMorphed = 0, false
    }
}

func hotkeyHeartwood() {
    if !speeding {
        gt.Run(`/equip heartwood`)
        speeding = true
        gt.Run(`/useitem left`)
    } else {
        speeding = false
        gt.Run(`/useitem heartwood /slow`)
        gt.Run(`/unequip heartwood`)
    }
}

func hotkeyReset() {
    gt.Run(`/useitem beltofthewild /return`)
    gt.Run(`/unequip heartwood`)
    speeding = false
    isMorphed = false
    whatShape = 0
    keepspeed = false
}

// ===== Commands =====
func cmdToggleATZ(args string) {
    autoTradeZero = !autoTradeZero
    statusMsg("Auto Trade Zero", autoTradeZero)
}

func cmdToggleAutoMate(args string) {
    autoMate = !autoMate
    statusMsg("Auto Mate", autoMate)
}

func cmdToggleAutoBoard(args string) {
    autoBoard = !autoBoard
    statusMsg("Auto Board", autoBoard)
}

func cmdReflect(args string) {
    ensureBelt()
    gt.Run(`/useitem beltofthewild /reflect`)
}

// ===== Loops =====
func autoMateLoop() {
    for {
        if autoMate {
            gt.Run(`/money`)
        }
        time.Sleep(280 * time.Second)
    }
}

// ===== Log Watcher =====
func logWatcher(line string) string {
    playerName := gt.PlayerName()
    hasFallen := playerName + " has fallen to a"
    l := strings.ToLower(line)

    // Morph/speed reset triggers
    if strings.Contains(l, "you return") ||
        strings.Contains(l, "you are already in") ||
        strings.Contains(l, "cannot possibly use") {
        isMorphed, whatShape = false, 0
    }

    if strings.Contains(l, "using /share to create a spirit link") ||
        strings.Contains(l, strings.ToLower(hasFallen)) {
        if isMorphed {
            keepspeed = true
            isMorphed, whatShape = false, 0
        }
        if !keepspeed && speeding {
            speeding = false
            gt.Run(`/unequip heartwood`)
        }
    }

    if strings.Contains(l, "you slow down") && speeding {
        speeding = false
        gt.Run(`/unequip heartwood`)
    }

    // Auto Trade Zero trigger
    if autoTradeZero {
        if m := tradeZeroRegex.FindStringSubmatch(line); m != nil {
            trader := m[1]
            gt.Run(`/buy 0 ` + trader)
            gt.Print("* Accepted 0c trade from: " + trader)
        }
    }

// Auto Board trigger
if autoBoard {
    for _, rx := range boatPromptRegexes {
        if rx.MatchString(line) {
            gt.Run(`/whisper yes`)
            gt.Print("* Auto Boarded")
            break
        }
    }
}


    // Ranger progress
    if rangerRegex.MatchString(line) {
        gt.Print("* " + line)
    }

    return line
}

// ===== Helpers =====
func ensureBelt() {
    if !gt.IsEquipped("belt of the wild") {
        gt.Run(`/equip beltofthewild`)
    }
}

func statusMsg(feature string, enabled bool) {
    if enabled {
        gt.Print("* " + feature + " ON")
    } else {
        gt.Print("* " + feature + " OFF")
    }
}

func buildBoatRegexes() []*regexp.Regexp {
    name := regexp.QuoteMeta(gt.PlayerName())

    // Pattern 1: Captain Barnac boat rental
    boatPattern := `(?i)Ah,\s*` + name +
        `\.\s*My fine boats cost\s*\d+\s*copper pennies\. Would you like to rent one now\?`

    // Pattern 2: River skiff sale
    skiffPattern := `(?i)Hello,\s*` + name +
        `\. I can sell you a river skiff\. Interested\? It costs\s*\d+\s*coins\.`

    return []*regexp.Regexp{
        regexp.MustCompile(boatPattern),
        regexp.MustCompile(skiffPattern),
    }
}
