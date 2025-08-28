//go:build plugin

package main

import (
    "gt"
)

var PluginName = "Rank_Progress_messages"

func init() {
    // Register a handler for all incoming chat/log lines
    gt.RegisterChatHandler(func(msg string) {
        switch {
        case gt.Includes(msg, "is becoming frustrated with your lack of progress"):
            gt.Console("* |══════════| -0%")
        case gt.Includes(msg, "you have a difficult task ahead of you"):
            gt.Console("* |══════════| 0%")
        case gt.Includes(msg, "you have just begun to"):
            gt.Console("* |▰═════════| 0%-13%")
        case gt.Includes(msg, "you are starting to learn, but"):
            gt.Console("* |▰▰▰═══════| 13%-38%")
        case gt.Includes(msg, "you are making progress."):
            gt.Console("* |▰▰▰▰▰═════| 38%-62%")
        case gt.Includes(msg, "you are well on your way to enlightenment"):
            gt.Console("* |▰▰▰▰▰▰════| 62%-75%")
        case gt.Includes(msg, "you are close to mastering"):
            gt.Console("* |▰▰▰▰▰▰▰═══| 75%-88%")
        case gt.Includes(msg, "you are almost ready for a breakthrough"):
            gt.Console("* |▰▰▰▰▰▰▰▰▰═| 88%-100%")
        }
    })
}