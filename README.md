# LingoPy
LibVLC-based LingoPie rip-off
Instantly translate foreign subtitles while watching.

~~May or may not use Python (we primarily use C)~~  
Uses Python EXTENSIVELY (for the mean time)

## Phase 1 (prototype phase)

- [x]  find libvlc-based python player on github and clone
- [x]  add text-displaying widget to pyqt5 player
- [x]  process srt files
- [x]  synch srt to video
- [x]  fix crashes when pausing player

### Demo

![image](https://user-images.githubusercontent.com/34742984/127005386-d5644c3a-92dd-4cf6-8024-1639be83abc9.png)


## Phase 2 (prototype phase)

- [ ]  break down subtitle text into EDUs (Elementary Discourse Units) using pretrained text segementation model.
- [ ]  integrate language transformer models (prioritize French)
- [ ]  OR use unofficial google translate API
- [ ]  translate on-click (i.e., when you click on a word in the subtitle, it will show an instant translation of the word or of the whole phrase)

## Phase 3
- [ ] modify VLC source code to render subtitles as in the prototype

# Installation
Download the .zip file from the release page and unzip. Run Main.exe.

## If the current release does not work:
- Have VLC installed on your computer and add libvlc.dll to PATH.
- Have Python 3.6+ installed.
- Clone the repository
- Install required python modules. `pip install -r requirements.txt`
- Run Main.py `python Main.py`
