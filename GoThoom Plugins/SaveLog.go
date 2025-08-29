//go:build plugin

package main

import (
    "fmt"
    "os"
    "path/filepath"
    "time"

    "gt"
)

var PluginName = "SaveLog"


var logFile *os.File

func init() {
    player := gt.PlayerName()
    if player == "" {
        player = "unknown"
    }
    logPath := filepath.Join("logs", fmt.Sprintf("%s.log", player))

    // Ensure logs directory exists
    _ = os.MkdirAll("logs", 0755)

    var err error
    logFile, err = os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        gt.ShowNotification("Failed to open log file")
        return
    }

    gt.ShowNotification(fmt.Sprintf("Logging to %s", logPath))
}

// LogConsole writes to both the in-client console and the log file.
func LogConsole(msg string) {
    timestamp := time.Now().Format("2006-01-02 15:04:05")
    entry := fmt.Sprintf("[%s] %s\n", timestamp, msg)

    // Write to file
    if logFile != nil {
        _, _ = logFile.WriteString(entry)
    }

    // Optionally echo to in-client console
    gt.Console(msg)
}

func main() {
    LogConsole("Plugin initialized")
    LogConsole("Something interesting happened")
}
