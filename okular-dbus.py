#!/usr/bin/python

import os
import sys
import dbus
import threading
from xml.dom import minidom
from PyQt4 import QtGui, QtCore
from subprocess import Popen, PIPE
from dbus.exceptions import DBusException

class PechaKuchaManager(QtGui.QDialog):
    def __init__(self, config, okularApp, okularWin):
        QtGui.QDialog.__init__(self)

        self.initUI()
        self.initShcuts()

        self.config = config
        self.curPresentation = 0
        self.slideTimer = 0.1
        self.okularApp = okularApp
        self.okularWin = okularWin

    def initUI(self):
        self.setWindowTitle("Pecha Kucha NG")
        layout = QtGui.QVBoxLayout(self)

        titleLabel = QtGui.QLabel("Pecha Kucha NG")
        titleLabel.setAlignment(QtCore.Qt.AlignHCenter)
        tLabelFont = QtGui.QFont(self)
        tLabelFont.setBold(True)
        tLabelFont.setPixelSize(18)
        titleLabel.setFont(tLabelFont)
        layout.addWidget(titleLabel)

        openButton = QtGui.QPushButton("Open")
        self.connect(openButton, QtCore.SIGNAL('clicked()'), self.okularNextPresentation)
        layout.addWidget(openButton)

        nextSlideButton = QtGui.QPushButton("Next")
        self.connect(nextSlideButton, QtCore.SIGNAL('clicked()'), self.okularNextSlide)
        layout.addWidget(nextSlideButton)

        quitButton = QtGui.QPushButton("Exit")
        self.connect(quitButton, QtCore.SIGNAL('clicked()'), self.exit)
        layout.addWidget(quitButton)

    def initShcuts(self):
        self.shcutStart = QtGui.QShortcut(self)
        self.shcutStart.setKey("PgDown")
        self.connect(self.shcutStart, QtCore.SIGNAL("activated()"), self.okularNextPresentation)

    def exit(self):
        if self.okularWin:
            self.okularWin.close()
        quit()

    def okularOpenFile(self, path):
        if self.okularApp:
            self.okularApp.openDocument(path)
            self.okularApp.slotGotoFirst()
            self.okularApp.slotTogglePresentation()
            self.setFocus()

    def okularNextPresentation(self):
        if self.curPresentation < len(self.config["file"]):
            self.okularOpenFile(self.config["file"][self.curPresentation])
            self.okularNextSlideTimer()
        else:
            self.exit()

    def okularNextSlide(self):
        if self.okularApp.pages() == self.okularApp.currentPage():
            print "Reached end of file."
            self.okularApp.slotTogglePresentation()
            self.curPresentation += 1
        else:
            self.okularApp.slotNextPage()
            self.okularNextSlideTimer()

    def okularNextSlideTimer(self):
        slideTimer = threading.Timer(self.slideTimer, self.okularNextSlide)
        slideTimer.start()

class OkularApplication():
    def __init__(self):
        self.okularApp = None
        self.okularWin = None

    def launch(self):
        process = Popen('/usr/bin/okular', stdout=PIPE)

    def connectWithTimer(self):
        sec = 0.1
        connectTimer = threading.Timer(sec, self.connect)
        connectTimer.start()

    def connect(self):
        try:
            bus = dbus.SessionBus()
            proxy = bus.get_object("org.freedesktop.DBus",  "/")
            dbusIface = dbus.Interface(proxy, "org.freedesktop.DBus")
            okularIface = None
            for iface in dbusIface.ListNames():
                if "okular" in iface:
                    okularIface = iface
            if okularIface:
                proxy = bus.get_object(okularIface, "/okular")
                self.okularApp = dbus.Interface(proxy, "org.kde.okular")
                proxy = bus.get_object(okularIface, "/okular/okular__Shell")
                self.okularWin = dbus.Interface(proxy, "org.qtproject.Qt.QWidget")
                self.okularWin.hide()
            else:
                print "Okular is not running. Trying to reconnect."
                self.connectWithTimer()
        except DBusException, e:
            raise StandardError("Dbus error: %s" % e)

    def isSuccessful(self):
        if self.okularApp and self.okularWin:
            return 1
        else:
            return 0

def configXmlParser(path):
    if os.path.isfile(path):
        config = {"file": [], "title": [], "presenter": [], "organization": []}    
        dom = minidom.parse(path)
        configPath = os.getcwd() + '/' + path
        configPath = configPath[:-(len(configPath) - configPath.rindex("/"))]
        for node in dom.getElementsByTagName('id'):
            config["file"].append(configPath + "/" + node.toxml().replace("<id>", "").replace("</id>", "") + ".pdf")
        for node in dom.getElementsByTagName('title'):
            config["title"].append(node.toxml().replace("<title>", "").replace("</title>", ""))
        for node in dom.getElementsByTagName('presenter'):
            config["presenter"].append(node.toxml().replace("<presenter>", "").replace("</presenter>", ""))
        for node in dom.getElementsByTagName('organization'):
            config["organization"].append(node.toxml().replace("<organization>", "").replace("</organization>", ""))
        return config
    else:
        print "File not exist. Exiting."
        self.exit()

def main(arg):
    app = QtGui.QApplication(sys.argv)

    okularApp = OkularApplication()
    okularApp.launch()
    okularApp.connect()

    while not okularApp.isSuccessful():
        pass
        
    pkManager = PechaKuchaManager(configXmlParser(arg), okularApp.okularApp, okularApp.okularWin)
    pkManager.show()
    
    sys.exit(app.exec_()) 

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print "Argument 'config file' not presented."
    else:
        main(sys.argv[1])