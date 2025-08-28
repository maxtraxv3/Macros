//go:build plugin

package main

import (
    "gt"
    "time"
)

var PluginName = "SaveLog"

var liveLog []string

// Wrap gt.Console to log every line
func logConsole(msg string) {
    gt.Console(msg)              // still prints in game
    liveLog = append(liveLog, msg) // also stores in memory
}

// Example: expose log via /heallog command
func init() {
    gt.RegisterCommand("heallog", func(_ string) {
        logConsole("* ---- Stored Heal Log ---- *")
        for _, line := range liveLog {
            gt.Console(line)
        }
        logConsole("* -------- End -------- *")
    })

    // Demo: log something every 5 seconds
    go func() {
        for {
            logConsole("* Plugin heartbeat OK")
            time.Sleep(5 * time.Second)
        }
    }()
}
