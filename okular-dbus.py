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
    def __init__(self):
        QtGui.QDialog.__init__(self)

        self.initUI()
        self.initShcuts()

        self.curPresentation = 0
        self.slideTimer = 20.0
        self.okular = None
        self.okularWindow = None

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
        if self.okularWindow:
            self.okularWindow.close()
        quit()

    def okularLaunch(self):
        process = Popen('/usr/bin/okular', stdout=PIPE)

    def dbusOkularConnect(self):
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
                self.okular = dbus.Interface(proxy, "org.kde.okular")
                proxy = bus.get_object(okularIface, "/okular/okular__Shell")
                self.okularWindow = dbus.Interface(proxy, "org.qtproject.Qt.QWidget")
                self.okularWindow.hide()
            else:
                print "Okular is not running. Trying to reconnect."
                self.dbusOkularConnectTimer(0.1)
        except DBusException, e:
            raise StandardError("Dbus error: %s" % e)

    def dbusOkularConnectTimer(self, sec):
        connectTimer = threading.Timer(sec, self.dbusOkularConnect)
        connectTimer.start()

    def okularOpenFile(self, path):
        if self.okular:
            self.okular.openDocument(path)
            self.okular.slotGotoFirst()
            self.okular.slotTogglePresentation()
            self.setFocus()

    def okularNextPresentation(self):
        if self.curPresentation < len(self.config["file"]):
            self.okularOpenFile(self.config["file"][self.curPresentation])
            self.okularNextSlideTimer()

    def okularNextSlide(self):
        if self.okular.pages() == self.okular.currentPage():
            print "Reached end of file."
            self.okular.slotTogglePresentation()
            self.curPresentation += 1
        else:
            self.okular.slotNextPage()
            self.okularNextSlideTimer()

    def okularNextSlideTimer(self):
        slideTimer = threading.Timer(self.slideTimer, self.okularNextSlide)
        slideTimer.start()

    def configXmlParser(self, path):
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
            self.config = config
            print self.config
        else:
            print "File not exist. Exiting."
            self.exit()


def main(arg):
    app = QtGui.QApplication(sys.argv)
    pkManager = PechaKuchaManager()
    pkManager.show()
    
    pkManager.configXmlParser(arg)
    pkManager.okularLaunch()
    pkManager.dbusOkularConnectTimer(0.1)

    sys.exit(app.exec_()) 

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print "Argument 'config file', not presented."
    else:
        main(sys.argv[1])