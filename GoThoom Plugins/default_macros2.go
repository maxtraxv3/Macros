//go:build plugin

package main

import "gt"

var PluginName = "Default Macros2"

func Init() {
	gt.AddMacros(map[string]string{
		"??":	"/help ",
		"aa":	"/action ",
		"uuaa":	"/action ",
		"ppaa":	"/action ",
		"yyaa":  "/action ",
		"gg":  "/give ",
		"ii":  "/info ",
		"kk":  "/karma ",
		"mm":  "/money ",
		"nn":  "/news ",
		"pp":  "/ponder ",
		"uupp":   "/ponder ",
		"aapp":   "/ponder ",
		"yypp":   "/ponder ",
		"sh":  "/share ",
		"sl":  "/sleep ",
		"t":   "/think ",
		"tt":  "/thinkto ",
		"th":  "/thank ",
		"uu":  "/use ",
		"uuu":  "/use ",
		"uuuu":  "/use ",
		"uuuuu":  "/use ",
		"uuuuuuu":  "/use ",
		"uuuuuuuu":  "/use ",
		"uuuuuuuuu":  "/use ",
		"un":  "/unshare ",
		"unsh": "/unshare ",
		"wh":   "/who ",
		"ww":  "/whisper ",
		"yy":  "/yell ",
		"uuyy":  "/yell ",
		"ppyy":  "/yell ",
		"aayy":  "/yell ",
		"wa": "/action waves \r",
	})
}
