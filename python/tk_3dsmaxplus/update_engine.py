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

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from .ui.update_engine import Ui_UpdateEngine

settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


class UpdateEngineDlg(QtGui.QDialog):
    """
    The Update Engine dialog. It displays a deprecation message with a checkbox to
    choose not to see this message ever again.
    """
    def __init__(self, parent=None):
        super(UpdateEngineDlg, self).__init__(parent)
        self._ui = Ui_UpdateEngine()
        self._ui.setupUi(self)

    def is_never_again_checked(self):
        """
        :returns: ``True`` is the user does not want to see the dialog ever again,
        ``False`` otherwise.
        """
        return self._ui.never_again_checkbox.isChecked()


def _should_skip_dialog():
    """
    :returns: ``True`` if the user dismissed the dialog with "Do not show this again"
        checked in the past, ``False`` otherwise.
    """
    settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
    skip_dialog = settings_manager.retrieve("skip_update_engine_dialog", False)
    return skip_dialog


def _skip_dialog():
    """
    Update user settings so that the dialog is never shown again.
    """
    settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
    settings_manager.store("skip_update_engine_dialog", True)


def _show_dialog():
    """
    Show the dialog warning the user about the deprecation.

    :returns: ``True`` if the user requested the dialog to never be shown
        again, ``False`` otherwise.
    """
    dialog = UpdateEngineDlg()
    dialog.exec_()
    return dialog.is_never_again_checked()


def show_update_dialog():
    """
    Show the update warning dialog.

    If the user checked "Do not show this dialog again." in the past,
    the method will do nothing.
    """

    if _should_skip_dialog():
        return

    skip_dialog_on_next_startup = _show_dialog()

    if skip_dialog_on_next_startup:
        _skip_dialog()