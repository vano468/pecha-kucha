#!/usr/bin/python

import os
import sys
import dbus
import threading
from xml.dom import minidom
from PyQt4 import QtGui, QtCore
from PyQt4.QtWebKit import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from mako.template import Template
from subprocess import Popen, PIPE
from dbus.exceptions import DBusException

class PechaKuchaManager(QtGui.QDialog):
    def __init__(self, config, okularApp, okularWin):
        QtGui.QDialog.__init__(self)

        self.webView = None
        self.slideTimer = None
        self.config = config
        self.curPresentation = 0
        self.secPerSlide = config["sec-per-slide"]
        self.okularApp = okularApp
        self.okularWin = okularWin

        self.initUI()
        self.initShcuts()
        self.initSignals()
        self.okularLoadNextPresentation()
        self.emit(SIGNAL("setViewContent()"))

    def initUI(self):
        self.setWindowTitle("Pecha Kucha NG")
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.webView = QWebView(self)
        layout.addWidget(self.webView)

    def initShcuts(self):
        self.shcutPgDown = QtGui.QShortcut(self)
        self.shcutPgDown.setKey("PgDown")
        self.connect(self.shcutPgDown, QtCore.SIGNAL("activated()"), self.okularNextPresentation)

        self.shcutEsc = QtGui.QShortcut(self)
        self.shcutEsc.setKey("Esc")
        self.connect(self.shcutEsc, QtCore.SIGNAL("activated()"), self.exit)

        self.shcutUp = QtGui.QShortcut(self)
        self.shcutUp.setKey("Up")
        self.connect(self.shcutUp, QtCore.SIGNAL("activated()"), self.prevPresentation)

        self.shcutUp = QtGui.QShortcut(self)
        self.shcutUp.setKey("Down")
        self.connect(self.shcutUp, QtCore.SIGNAL("activated()"), self.nextPresentation)

        self.shcutSpace = QtGui.QShortcut(self)
        self.shcutSpace.setKey("Space")
        self.connect(self.shcutSpace, QtCore.SIGNAL("activated()"), self.forceStopPresentation)

    def initSignals(self):
        QObject.connect(self, SIGNAL("setViewContent()"), self.setViewContent)

    def exit(self):
        if self.okularWin:
            self.okularWin.close()
        quit()

    def prevPresentation(self):
        if self.curPresentation > 0:
            self.curPresentation -=1
            self.emit(SIGNAL("setViewContent()"))
            self.okularLoadNextPresentation()

    def nextPresentation(self):
        if self.curPresentation < len(self.config["file"]):
            self.curPresentation +=1
            self.emit(SIGNAL("setViewContent()"))
            self.okularLoadNextPresentation()

    def forceStopPresentation(self):
        if self.slideTimer:
            self.slideTimer.cancel()
        self.okularLoadNextPresentation()

    def setViewContent(self):
        presCurrent = Template(filename = self.config["config-path"] + "/templates/pres-current.html")
        presNext = Template(filename = self.config["config-path"] + "/templates/pres-next.html")
        motivation = Template(filename = self.config["config-path"] + "/templates/motivation.html")
        if self.curPresentation < len(self.config["title"]):
            html = presCurrent.render(title = self.config["title"][self.curPresentation], presenter = self.config["presenter"][self.curPresentation])
            for i in xrange(self.curPresentation+1, len(self.config["title"])):
                html += presNext.render(title = self.config["title"][i], presenter = self.config["presenter"][i])
        else:
            html = motivation.render()
        self.webView.setHtml(html)
            
    def okularOpenFile(self, path):
        if self.okularApp:
            self.okularApp.openDocument(path)

    def okularNextPresentation(self):
        if self.curPresentation < len(self.config["file"]):
            self.okularNextSlideTimer()
            self.okularApp.slotGotoFirst()
            self.okularApp.slotTogglePresentation()
            self.setFocus()
        else:
            self.exit()

    def okularLoadNextPresentation(self):
        if self.curPresentation < len(self.config["file"]):
            self.okularOpenFile(self.config["file"][self.curPresentation])

    def okularNextSlide(self):
        if self.okularApp.pages() == self.okularApp.currentPage():
            print "Reached end of file."
            self.okularApp.slotTogglePresentation()
            self.curPresentation += 1
            self.emit(SIGNAL("setViewContent()")) 
            self.okularLoadNextPresentation()
        else:
            self.okularApp.slotNextPage()
            self.okularNextSlideTimer()

    def okularNextSlideTimer(self):
        self.slideTimer = threading.Timer(self.secPerSlide, self.okularNextSlide)
        self.slideTimer.start()

class OkularApplication():
    def __init__(self):
        self.okularApp = None
        self.okularWin = None
        self.alreadyRunning = False

    def launch(self):
        if not self.alreadyRunning:
            process = Popen('/usr/bin/okular', stdout=PIPE)
            self.alreadyRunning = True

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
                print "Okular is not running. Trying to launch and reconnect."
                self.launch()
                self.connectWithTimer()
        except DBusException, e:
            raise StandardError("Dbus error: %s" % e)

    def isSuccessful(self):
        if self.okularApp and self.okularWin:
            return True
        else:
            return False

def configXmlParser(path):
    if os.path.isfile(path):
        config = {"file": [], "title": [], "presenter": [], "organization": [], "sec-per-slide": None, "config-path": None}    
        dom = minidom.parse(path)
        if path[0] == '/':
            configPath = path[:-(len(path) - path.rindex("/"))]
        else: 
            configPath = os.getcwd() + '/' + path
            configPath = configPath[:-(len(configPath) - configPath.rindex("/"))]
        config["config-path"] = configPath

        for node in dom.getElementsByTagName('presentations'):
            config["sec-per-slide"] = float(node.getAttribute("seconds-per-slide"))

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
    okularApp.connect()

    while not okularApp.isSuccessful():
        pass
        
    pkManager = PechaKuchaManager(configXmlParser(arg), okularApp.okularApp, okularApp.okularWin)
    pkManager.showFullScreen()

    sys.exit(app.exec_()) 

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print "Argument 'config file' not presented."
    else:
        main(sys.argv[1])