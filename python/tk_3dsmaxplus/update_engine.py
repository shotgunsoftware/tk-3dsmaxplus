# Copyright (c) 2019 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Displays a message inviting the user to switch their Max engine to tk-3dsmax.
"""

import contextlib
import os

try:
    from sgtk.platform.qt import QtCore, QtGui
    import sgtk

    settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")

    def _should_skip_dialog():
        settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
        skip_dialog = settings_manager.retrieve("skip_update_engine_dialog", False)
        return skip_dialog

    def _skip_dialog():
        settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
        settings_manager.store("skip_update_engine_dialog", True)

except Exception:
    from PySide2 import QtCore, QtWidgets as QtGui

    def _should_skip_dialog():
        return False

    def _skip_dialog():
        pass


try:
    from PySide2.QtUiTools import QUiLoader
except ImportError:
    from PySide.QtUiTools import QUiLoader

def _show_dialog():
    resource = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "resources",
        "update_engine.ui"
    )
    with contextlib.closing(QtCore.QFile(resource)) as resource_file:
        loader = QUiLoader()
        dialog = loader.load(resource_file)

    checkbox = dialog.findChild(QtGui.QCheckBox, "never_again_checkbox")

    dialog.exec_()

    return checkbox.isChecked()


def show_update_dialog():

    if _should_skip_dialog():
        return

    skip_dialog_on_next_startup = _show_dialog()

    if skip_dialog_on_next_startup:
        _skip_dialog()


if __name__ == "__main__":
    if QtGui.QApplication.instance() is None:
        QtGui.QApplication([])
    show_update_dialog()