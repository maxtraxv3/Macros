# RankCounter
## rank counter is a program to help keep track of things 
## from the game [Clanlord](https://www.deltatao.com/clanlord/ "Clanlord")

### Screenshots:

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot1.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot1.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175442.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175442.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175453.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175453.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175501.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175501.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175511.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot%202026-04-22%20175511.png)

## Downloads (releases):
### Windows:
[Rank Counter!](https://github.com/maxtraxv3/Macros/tree/main/clanlord%20apps/RankCounter/Releases/Windows)
### Linux:
[Rank Counter!](https://github.com/maxtraxv3/Macros/tree/main/clanlord%20apps/RankCounter/Releases/Linux)
### Mac:
( none yet, sorry working on it :/ )

# This make one App on Mac or EXE on Windows or an AppImage for Linux

## How to compile your self:
have the files listed in the same folder

    rankmessages.txt
    specialphrases.txt
    trainers.txt
    phoenix.png
    KIN668.ttf (only required for rc29.1+)
    rcXX.py (XX = version number)

And make sure your terminal is in the folder.
## you will need python installed
which you can find here: [Python](https://www.python.org/)

COPY AND PASTE THE WHOLE THE THING
REPLACE XX WITH VERSION NUMBER (IE `rc28.py`)
### Windows:
Via terminal:

    python -m pip install pyinstaller
    python -m pip install tk tcl
    python -m pip install pillow

python 3.10 to 3.12:

    python -m pyinstaller --noconsole --onefile --icon=phoenix.png --add-data "phoenix.png;." --add-data "rankmessages.txt;." --add-data "trainers.txt;." --add-data "specialphrases.txt;." --add-data "KIN668.ttf;." rc29.1.py

python 3.14+:

    pyinstaller --noconsole --onefile --icon=phoenix.png --add-data "phoenix.png;." --add-data "rankmessages.txt;." --add-data "trainers.txt;." --add-data "specialphrases.txt;." --add-data "KIN668.ttf;." rc29.1.py

### Mac:
Via Terminal:
python 3.10 to 3.12:

    python3 -m pip install pyinstaller
    python3 -m pip install tk tcl
    python3 -m pip install pillow
python 3.14+:

    pip3 install pyinstaller
    pip3 install tk tcl
    pip3 install pillow

then:

    python3 -m pyinstaller --noconsole --onefile --icon=phoenix.png \
      --add-data "phoenix.png:." \
      --add-data "rankmessages.txt:." \
      --add-data "trainers.txt:." \
      --add-data "specialphrases.txt:." \
      --add-data "KIN668.ttf:." \
      rc29.1.py


### Linux (Debian):
python 3.10 to 3.12:

    python -m pip install pyinstaller
    python -m pip install tk tcl
    python -m pip install pillow
then:

    python -m pyinstaller --noconsole --onefile --icon=phoenix.png \
      --add-data "phoenix.png:." \
      --add-data "rankmessages.txt:." \
      --add-data "trainers.txt:." \
      --add-data "specialphrases.txt:." \
      --add-data "KIN668.ttf:." \
      rc29.1.py

  
python 3.14+:

    pip install pyinstaller
    pip install tk tcl
    pip install pillow
then:

    pyinstaller --noconsole --onefile --icon=phoenix.png \
      --add-data "phoenix.png:." \
      --add-data "rankmessages.txt:." \
      --add-data "trainers.txt:." \
      --add-data "specialphrases.txt:." \
      --add-data "KIN668.ttf:." \
      rc29.1.py
  then:

    ./appimager.sh


### Linux (ARCH):
python 3.14+:

    sudo pacman -S python-pip
    sudo pacman -S pyinstaller
    sudo pacman -S tk tcl
    sudo pacman -S python-pillow


`paru -S pyinstaller` (enter: 1 then 1 then q then y then y)
-------- OR ------ (OS Dependent)
`yay -S pyinstaller` (enter: 1 then 1 then q then y then y)

    paru -S appimagetool

-------- OR ------ (OS Dependent)

    yay -S appimagetool


    pyinstaller --noconsole --onefile --icon=phoenix.png \
      --add-data "phoenix.png:." \
      --add-data "rankmessages.txt:." \
      --add-data "trainers.txt:." \
      --add-data "specialphrases.txt:." \
      --add-data "KIN668.ttf:." \
      rc29.1.py
then:

    ./appimager.sh

