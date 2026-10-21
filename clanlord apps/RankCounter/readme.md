# RankCounter
## rank counter is a program to help keep track of things 
## from the game [Clanlord](https://www.deltatao.com/clanlord/ "Clanlord")

### Screenshots:

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104147.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104147.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104202.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104202.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104211.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104211.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104249.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104249.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104414.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104414.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104458.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104458.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104510.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104510.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104520.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104520.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104529.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104529.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104620.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104620.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104719.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104719.png)

[![](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104736.png)](https://github.com/maxtraxv3/Macros/blob/main/clanlord%20apps/RankCounter/screenshots/Screenshot_20261021_104736.png)

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


## Licenses & Credits

- Gorvin (gorvin.50webs.com) - Healer/Fighter calculator math and formulas.
- Org du Lac - Bestiary images and calculations (bestiary.clanlord.net).
- Noivad - Clumps Ranger information (clump.clanlord.net).
- Delta Tao Software (deltatao.com/clanlord) - holds rights to Clan Lord images.

Third-party licenses:
- Python - PSF License
- Tkinter - PSF License
- Pillow (PIL) - HPND License
- PyInstaller - GPL v2 with Bootloader Exception


## Build Information (RankCounter31)

Required files in the same folder:

- Bestiary_2026_07_06_Dump.xml
- KIN668.TTF
- armor_data.json
- cl_time.py
- constants.py
- main.py
- offhand_data.json
- parser.py
- phoenix.png
- rankmessages.txt
- shoulder_data.json
- specialphrases.txt
- storage.py
- trainers.txt
- ui_components.py
- weapons_data.json
- img/ (folder with moon icons and creatures_static images)

Build via GitHub Actions release.yml or compile locally with PyInstaller.
