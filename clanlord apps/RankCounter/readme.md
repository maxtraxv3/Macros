### RankCounter
## rank counter is a program to help keep track of things 
## from saved textlogs from the game [Clanlord](https://www.deltatao.com/clanlord/ "Clanlord")

### Screenshots:

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot1.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot1.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175442.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175442.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175453.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175453.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175501.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175501.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175511.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175511.png)

### how to compile your self:
have the files listed in the same folder

    rankmessages.txt
    specialphrases.txt
    trainers.txt
    phoenix.png
    rcXX.py (XX = version number)

and make sure your terminal is in the folder.
## you will need python installed

this make one app on mac or exe on windows.

## Dependency:
you also need to install pyinstaller (about 2mb)
`python -m pip install pyinstaller`

and pillow (about 8mb)
`python -m pip install pillow`

COPY AND PASTE THE WHOLE THE THING
REPLACE XX WITH VERSION NUMVER (IE rc28.py)

mac:
`python -m pyinstaller --noconsole --onefile --icon=phoenix.png \
  --add-data "phoenix.png:." \
  --add-data "rankmessages.txt:." \
  --add-data "trainers.txt:." \
  --add-data "specialphrases.txt:." \
  rcXX.py`

linux:
`python -m pyinstaller --noconsole --onefile --icon=phoenix.png \
  --add-data "phoenix.png:." \
  --add-data "rankmessages.txt:." \
  --add-data "trainers.txt:." \
  --add-data "specialphrases.txt:." \
  rcXX.py`

windows via terminal(win key + x): 
`python -m pyinstaller --noconsole --onefile --icon=phoenix.png --add-data "phoenix.png;." --add-data "rankmessages.txt;." --add-data "trainers.txt;." --add-data "specialphrases.txt;." rcXX.py`
