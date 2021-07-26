#! /usr/bin/python

#
# Qt example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#

import sys
import os.path
from PyQt5.Qt import QDesktopServices, QUrl
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMainWindow, QWidget, QFrame, QSlider, QHBoxLayout, QPushButton, \
    QVBoxLayout, QAction, QFileDialog, QApplication, QLabel
import vlc
import threading
import srt
import time
from urllib.parse import quote

class Player(QMainWindow):
    """A simple Media Player using VLC and Qt
    """
    def __init__(self, master=None):
        QMainWindow.__init__(self, master)
        self.setWindowTitle("Media Player")

        # creating a basic vlc instance
        self.instance = vlc.Instance()
        # creating an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()

        self.createUI()
        self.isPaused = False

        self.subdicS = {}
        self.subdicE = {}

        self.t1 = threading.Thread(target=self.startSub, args=())
        self.clipboard = QApplication.clipboard()

    def createUI(self):
        """Set up the user interface, signals & slots
        """
        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        if sys.platform == "darwin": # for MacOS
            from PyQt5.QtWidgets import QMacCocoaViewContainer	
            self.videoframe = QMacCocoaViewContainer(0)
        else:
            self.videoframe = QFrame()
        self.palette = self.videoframe.palette()
        self.palette.setColor (QPalette.Window,
                               QColor(0,0,0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.positionslider = QSlider(Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.setPosition)

        self.hbuttonbox = QHBoxLayout()
        self.playbutton = QPushButton("Play")
        self.hbuttonbox.addWidget(self.playbutton)
        self.playbutton.clicked.connect(self.PlayPause)

        self.stopbutton = QPushButton("Stop")
        self.hbuttonbox.addWidget(self.stopbutton)
        self.stopbutton.clicked.connect(self.Stop)

        self.subimport = QPushButton("Import Subtitles")
        self.hbuttonbox.addWidget(self.subimport)
        self.subimport.clicked.connect(self.OpenSubs)

        self.hbuttonbox.addStretch(1)
        self.volumeslider = QSlider(Qt.Horizontal, self)
        self.volumeslider.setMaximum(100)
        self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        self.volumeslider.setToolTip("Volume")
        self.hbuttonbox.addWidget(self.volumeslider)
        self.volumeslider.valueChanged.connect(self.setVolume)

        self.subsbox = QHBoxLayout()
        self.subbox = QLabel()
        self.subbox.setFont(QFont("Helvetica [Cronyx]", 20))
        self.subbox.setText(" Polaks are the n*ggas of Europe. - Jean-Jacques Dessalines probably ")
        self.subbox.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.subsbox.addWidget(self.subbox)

        self.subcopy = QPushButton("Copy Subtitle")
        self.hbuttonbox.addWidget(self.subcopy)
        self.subcopy.clicked.connect(self.CopySub)

        self.translate = QPushButton("Translate")
        self.hbuttonbox.addWidget(self.translate)
        self.translate.clicked.connect(self.TranSub)

        self.vboxlayout = QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)
        self.vboxlayout.addWidget(self.positionslider)
        self.vboxlayout.addLayout(self.subsbox)
        self.vboxlayout.addLayout(self.hbuttonbox)

        self.widget.setLayout(self.vboxlayout)

        open = QAction("&Open", self)
        open.triggered.connect(self.OpenFile)
        exit = QAction("&Exit", self)
        exit.triggered.connect(sys.exit)
        menubar = self.menuBar()
        filemenu = menubar.addMenu("&File")
        filemenu.addAction(open)
        filemenu.addSeparator()
        filemenu.addAction(exit)

        #self.subtimer = QTimer(self)
        #self.subtimer.setInterval(1)
        #self.subtimer.timeout.connect(self.updateSubs)

        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.updateUI)

    def PlayPause(self):
        """Toggle play/pause status
        """
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.isPaused = True
            self.t1.join()
        else:
            if self.mediaplayer.play() == -1:
                self.OpenFile()
                return
            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.timer.start()
            self.isPaused = False
            self.t1 = threading.Thread(target=self.startSub, args=())
            self.t1.start()

    def Stop(self):
        """Stop player
        """
        self.mediaplayer.stop()
        self.playbutton.setText("Play")

    def OpenFile(self, filename=None):
        """Open a media file in a MediaPlayer
        """
        if filename is None:
            filename = QFileDialog.getOpenFileName(self, "Open File", os.path.expanduser('~'))[0]
        if not filename:
            return

        # create the media
        if sys.version < '3':
            filename = unicode(filename)
        self.media = self.instance.media_new(filename)
        # put the media in the media player
        self.mediaplayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        # the media player has to be 'connected' to the QFrame
        # (otherwise a video would be displayed in it's own window)
        # this is platform specific!
        # you have to give the id of the QFrame (or similar object) to
        # vlc, different platforms have different functions for this
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaplayer.set_nsobject(int(self.videoframe.winId()))
        self.PlayPause()

    def setVolume(self, Volume):
        """Set the volume
        """
        self.mediaplayer.audio_set_volume(Volume)

    def setPosition(self, position):
        """Set the position
        """
        # setting the position to where the slider was dragged
        self.mediaplayer.set_position(position / 1000.0)
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)

    def updateUI(self):
        """updates the user interface"""
        # setting the slider to the desired position
        self.positionslider.setValue(int(self.mediaplayer.get_position() * 1000))

        if not self.mediaplayer.is_playing():
            # no need to call this function if nothing is played
            self.timer.stop()
            if not self.isPaused:
                # after the video finished, the play button stills shows
                # "Pause", not the desired behavior of a media player
                # this will fix it
                self.Stop()
    def updateSubs(self):
        taym = int(self.mediaplayer.get_time())
        #print(taym)
        tekst = self.subdicS.get(taym,"")
        self.subbox.setText(tekst)
        #print(taym)
        '''
        tekst = self.subdicE.get(taym,"cuck")
        if tekst != "cuck":
            self.subbox.setText(tekst)
            print(taym)
        '''

    def startSub(self):
        while True:
            self.updateSubs()
            #print(time.time())
            time.sleep(0.001)

    def CopySub(self):
        self.clipboard.setText(self.subbox.text())
    def TranSub(self):
        pretrans = quote(self.subbox.text(), safe='')
        posttrans = 'https://translate.google.com/?sl=fr&tl=en&text={}&op=translate'.format(pretrans)
        url = QUrl(posttrans)
        QDesktopServices.openUrl(url)

    def OpenSubs(self):
        """Open a media file in a MediaPlayer
        """
        filename = QFileDialog.getOpenFileName(self, "Open File", os.path.expanduser('~'))[0]

        # create the media
        if sys.version < '3':
            filename = unicode(filename)
        f = open(filename, encoding='utf-8', errors='replace')

        #import srt
        subtitles = srt.parse(f)
        subs = list(subtitles)

        self.subdicS = {}
        self.subdicE = {}

        for cuck in subs:
            for i in range(int(cuck.start.total_seconds()*1000),int(cuck.end.total_seconds()*1000)):
                self.subdicS[i] = cuck.content
            #print(self.subdicS[int(cuck.start.total_seconds())])
            #self.subdicE[int(cuck.end.total_seconds()*1000)] = ""
        #print(self.subdicS)
        #print(subs[166].content)
        #print(subs[166].start.total_seconds())
            
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = Player()
    player.show()
    player.resize(640, 480)
    if sys.argv[1:]:
        player.OpenFile(sys.argv[1])
    sys.exit(app.exec_())
