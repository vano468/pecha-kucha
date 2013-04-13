#!/usr/bin/python

import sys
import dbus
import threading
from PyQt4 import QtGui, QtCore
from subprocess import Popen, PIPE
from dbus.exceptions import DBusException
 
class OkularDbus(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.initUI()
        self.okular = None

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
        self.connect(openButton, QtCore.SIGNAL('clicked()'), self.okularOpenFile)
        layout.addWidget(openButton)

        nextSlideButton = QtGui.QPushButton("Next")
        self.connect(nextSlideButton, QtCore.SIGNAL('clicked()'), self.okularNextSlide)
        layout.addWidget(nextSlideButton)

        quitButton = QtGui.QPushButton("Exit")
        self.connect(quitButton, QtCore.SIGNAL('clicked()'), quit)
        layout.addWidget(quitButton)

    def dbusOkularConnect(self):
        try:
            bus = dbus.SessionBus()
            proxy = bus.get_object("org.freedesktop.DBus",  "/")
            dbusIface = dbus.Interface(proxy, "org.freedesktop.DBus")
            okularIface = None
            for iface in dbusIface.ListNames():
                if "okular" in iface:
                    okularIface = iface
            if okularIface != None:
                proxy = bus.get_object(okularIface, "/okular")
                self.okular = dbus.Interface(proxy, "org.kde.okular")
            else:
                print "Okular is not running"
        except DBusException, e:
            raise StandardError("Dbus error: %s" % e)

    def okularOpenFile(self):
        if self.okular != None:
            self.okular.openDocument("/home/vano468/Dropbox/Docs/books/pdf/a.pdf")
            self.okular.slotGotoFirst()

    def okularNextSlide(self):
        if self.okular.pages() == self.okular.currentPage():
            print "Reached end of file"
        else:
            self.okular.slotNextPage()


def main():
    app = QtGui.QApplication(sys.argv)
    okularDbus = OkularDbus()
    okularDbus.show()

    okularDbus.dbusOkularConnect()

    sys.exit(app.exec_()) 

if __name__ == '__main__':
    main()
 


