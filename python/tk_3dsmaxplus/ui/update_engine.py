# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'update_engine.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_UpdateEngine(object):
    def setupUi(self, UpdateEngine):
        UpdateEngine.setObjectName("UpdateEngine")
        UpdateEngine.resize(424, 178)
        self.verticalLayout = QtGui.QVBoxLayout(UpdateEngine)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.message = QtGui.QLabel(UpdateEngine)
        self.message.setWordWrap(True)
        self.message.setOpenExternalLinks(True)
        self.message.setObjectName("message")
        self.verticalLayout.addWidget(self.message)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.never_again_checkbox = QtGui.QCheckBox(UpdateEngine)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.never_again_checkbox.sizePolicy().hasHeightForWidth())
        self.never_again_checkbox.setSizePolicy(sizePolicy)
        self.never_again_checkbox.setObjectName("never_again_checkbox")
        self.horizontalLayout.addWidget(self.never_again_checkbox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.ok_button = QtGui.QPushButton(UpdateEngine)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ok_button.sizePolicy().hasHeightForWidth())
        self.ok_button.setSizePolicy(sizePolicy)
        self.ok_button.setDefault(True)
        self.ok_button.setObjectName("ok_button")
        self.horizontalLayout_2.addWidget(self.ok_button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(UpdateEngine)
        QtCore.QMetaObject.connectSlotsByName(UpdateEngine)

    def retranslateUi(self, UpdateEngine):
        UpdateEngine.setWindowTitle(QtGui.QApplication.translate("UpdateEngine", "tk-3dsmaxplus deprecation warning", None, QtGui.QApplication.UnicodeUTF8))
        self.message.setText(QtGui.QApplication.translate("UpdateEngine", "<html><head/><body><p>The tk-3dsmaxplus engine has been deprecated. We recommend that you upgrade your configuration to the new <a href=\"https://github.com/shotgunsoftware/tk-3dsmax\"><span style=\" text-decoration: underline; color:#23a5e1;\">tk-3dsmax</span></a> engine. Versions of 3dsMax 2021 and up will only be supported by the new engine.</p><p>Visit <a href=\"https://developer.shotgridsoftware.com/tk-3dsmax\"><span style=\" text-decoration: underline; color:#23a5e1;\">this page</span></a> if you want to learn more on how to migrate your environment to the new engine.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.never_again_checkbox.setText(QtGui.QApplication.translate("UpdateEngine", "Do not show this again.", None, QtGui.QApplication.UnicodeUTF8))
        self.ok_button.setText(QtGui.QApplication.translate("UpdateEngine", "OK", None, QtGui.QApplication.UnicodeUTF8))

