# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_plot.ui'
#
# Created: Wed May 08 10:02:53 2013
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_win_plot(QtGui.QWidget):
    def setupUi(self, win_plot, lang):
        win_plot.setObjectName(_fromUtf8("win_plot"))
        win_plot.resize(1024, 768)
        self.centralwidget = QtGui.QWidget(win_plot)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.qwtPlot = Qwt5.QwtPlot(self.centralwidget)
        self.qwtPlot.setObjectName(_fromUtf8("qwtPlot"))
        self.verticalLayout.addWidget(self.qwtPlot)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(6, 0, 6, 0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btnA = QtGui.QPushButton(self.centralwidget)
        self.btnA.setObjectName(_fromUtf8("btnA"))
        self.btnA.setAutoRepeat(True)
        self.btnA.setStyleSheet('font: 20px')
        self.horizontalLayout.addWidget(self.btnA)
        self.btnB = QtGui.QPushButton(self.centralwidget)
        self.btnB.setObjectName(_fromUtf8("btnB"))
        self.btnB.setStyleSheet('font: 20px')
        self.horizontalLayout.addWidget(self.btnB)
        self.textbox = QtGui.QTextEdit(self.centralwidget)
        self.textbox.setStyleSheet('font: bold 80px; color: green; text-align: center;')
        #self.btnC = QtGui.QPushButton(self.centralwidget)
        #self.btnC.setObjectName(_fromUtf8("btnC"))
        #self.horizontalLayout.addWidget(self.btnC)
        #self.btnC.setStyleSheet('font: 50px')
        # self.btnD = QtGui.QPushButton(self.centralwidget)
        # self.btnD.setObjectName(_fromUtf8("btnD"))
        # self.horizontalLayout.addWidget(self.btnD)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.textbox)
        win_plot.setCentralWidget(self.centralwidget)

	print lang

	if (lang=="greek"):
            self.prompt_text = QtGui.QApplication.translate("win_plot", "Πώς μπορώ να βοηθήσω;", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_on_fan_text = QtGui.QApplication.translate("win_plot", "Ο ανεμιστήρας Θα ανοίξει.", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_off_fan_text = QtGui.QApplication.translate("win_plot", "Ο ανεμιστήρας θα σβήσει.", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_on_lights_text = QtGui.QApplication.translate("win_plot", "Θα ανάψουν τα φώτα.", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_off_lights_text = QtGui.QApplication.translate("win_plot", "Θα σβήσουν τα φώτα.", None, QtGui.QApplication.UnicodeUTF8)
            self.raise_lights_text = QtGui.QApplication.translate("win_plot", "Θα δυναμώσω τα φώτα.", None, QtGui.QApplication.UnicodeUTF8)
            self.lower_lights_text = QtGui.QApplication.translate("win_plot", "Θα χαμηλώσω τα φώτα.", None, QtGui.QApplication.UnicodeUTF8)
    	    self.switchon_radio_text = QtGui.QApplication.translate("win_plot", "Ανοίγω το ραδιόφωνο.", None, QtGui.QApplication.UnicodeUTF8)
    	    self.switchoff_radio_text = QtGui.QApplication.translate("win_plot", "Κλείνω το ραδιόφωνο.", None, QtGui.QApplication.UnicodeUTF8)
    	    self.xairetismos_text = QtGui.QApplication.translate("win_plot", "Γεια σας παιδιά!.", None, QtGui.QApplication.UnicodeUTF8)
	else:
            self.prompt_text = QtGui.QApplication.translate("win_plot", "How may I help?", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_on_fan_text = QtGui.QApplication.translate("win_plot", "The fan will be switched on", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_off_fan_text = QtGui.QApplication.translate("win_plot", "The fan will be switched off.", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_on_lights_text = QtGui.QApplication.translate("win_plot", "The lights will switch on", None, QtGui.QApplication.UnicodeUTF8)
            self.switched_off_lights_text = QtGui.QApplication.translate("win_plot", "The lights will switch off", None, QtGui.QApplication.UnicodeUTF8)
            self.raise_lights_text = QtGui.QApplication.translate("win_plot", "The lights will be raised", None, QtGui.QApplication.UnicodeUTF8)
            self.lower_lights_text = QtGui.QApplication.translate("win_plot", "The lights will lower", None, QtGui.QApplication.UnicodeUTF8)
    	    self.switchon_radio_text = QtGui.QApplication.translate("win_plot", "The radio is switched on", None, QtGui.QApplication.UnicodeUTF8)
    	    self.switchoff_radio_text = QtGui.QApplication.translate("win_plot", "The radio is sitched off", None, QtGui.QApplication.UnicodeUTF8)
    	    self.xairetismos_text = QtGui.QApplication.translate("win_plot", "Hi", None, QtGui.QApplication.UnicodeUTF8)

        self.retranslateUi(win_plot, lang)
        QtCore.QMetaObject.connectSlotsByName(win_plot)

    def retranslateUi(self, win_plot, lang):
	if (lang=="greek"):
	    win_plot.setWindowTitle(QtGui.QApplication.translate("win_plot", "Σπιτάκι Μου", None, QtGui.QApplication.UnicodeUTF8))
            self.btnA.setText(QtGui.QApplication.translate("win_plot", "ξεκίνα", None, QtGui.QApplication.UnicodeUTF8))
            self.btnB.setText(QtGui.QApplication.translate("win_plot", "σταμάτα", None, QtGui.QApplication.UnicodeUTF8))
	else:
	    win_plot.setWindowTitle(QtGui.QApplication.translate("win_plot", "Home, Sweet Home!", None, QtGui.QApplication.UnicodeUTF8))
            self.btnA.setText(QtGui.QApplication.translate("win_plot", "start", None, QtGui.QApplication.UnicodeUTF8))
            self.btnB.setText(QtGui.QApplication.translate("win_plot", "stop", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import Qwt5

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    win_plot = QtGui.QMainWindow()
    ui = Ui_win_plot()
    ui.setupUi(win_plot)
    win_plot.show()
    sys.exit(app.exec_())

