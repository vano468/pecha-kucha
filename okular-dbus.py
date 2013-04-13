#!/usr/bin/python

import sys
from PyQt4 import QtGui, QtCore
 
class OkularDbus(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
 
        self.setWindowTitle("Pecha Kucha NG")
        
        layout = QtGui.QVBoxLayout(self)

        titleLabel = QtGui.QLabel("Pecha Kucha NG")
        titleLabel.setAlignment(QtCore.Qt.AlignHCenter)
        tLabelFont = QtGui.QFont(self)
        tLabelFont.setBold(True)
        tLabelFont.setPixelSize(18)
        titleLabel.setFont(tLabelFont)
        layout.addWidget(titleLabel)
 
        quitButton = QtGui.QPushButton("Exit")
        self.connect(quitButton, QtCore.SIGNAL('clicked()'), quit)
        layout.addWidget(quitButton)
 
app = QtGui.QApplication(sys.argv)
window = OkularDbus()
window.show()
sys.exit(app.exec_()) 

