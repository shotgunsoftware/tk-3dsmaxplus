# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
"""
A 3ds Max engine for Tank.
"""
import os
import sys
import time

import tank


class MaxEngine(tank.platform.Engine):
    def init_engine(self):
        """
        constructor
        """
        self.log_debug("%s: Initializing..." % self)

        # keep handles to all qt dialogs to help GC
        self.__created_qt_dialogs = []

        # add qt paths and dlls
        self._init_pyside()

    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        # set up menu handler
        tk_3dsmax = self.import_module("tk_3dsmax")
        self._menu_generator = tk_3dsmax.MenuGenerator(self)
        self._menu_generator.create_menu()

    def destroy_engine(self):
        """
        Called when the engine is shutting down
        """
        self.log_debug('%s: Destroying...' % self)

    ##########################################################################################
    # logging
    def log_debug(self, msg):
        if self.get_setting("debug_logging", False):
            print "[%-13s] Shotgun Debug: %s" % (str(time.time()), msg)

    def log_info(self, msg):
        print "[%-13s] Shotgun Info: %s" % (str(time.time()), msg)

    def log_warning(self, msg):
        print "[%-13s] Shotgun Warning: %s" % (str(time.time()), msg)

    def log_error(self, msg):
        print "[%-13s] Shotgun Error: %s" % (str(time.time()), msg)

    ##########################################################################################
    # pyside
    def show_dialog(self, title, bundle, widget_class, *args, **kwargs):
        from tank.platform.qt import tankqdialog

        # first construct the widget object
        obj = widget_class(*args, **kwargs)

        # now create a dialog
        dialog = tankqdialog.TankQDialog(title, bundle, obj, None)

        # keep a reference to all created dialogs to make GC happy
        self.__created_qt_dialogs.append(dialog)

        # finally show it
        dialog.show()

        # lastly, return the instantiated class
        return obj

    def show_modal(self, title, bundle, widget_class, *args, **kwargs):
        from tank.platform.qt import tankqdialog

        # first construct the widget object
        obj = widget_class(*args, **kwargs)

        # now create a dialog
        dialog = tankqdialog.TankQDialog(title, bundle, obj, None)

        # keep a reference to all created dialogs to make GC happy
        self.__created_qt_dialogs.append(dialog)

        # finally launch it, modal state
        status = dialog.exec_()

        # lastly, return the instantiated class
        return (status, obj)

    def _init_pyside(self):
        """Handles the pyside init"""
        # first see if pyside is already present - in that case skip!
        try:
            from PySide import QtGui
        except:
            # fine, we don't expect pyside to be present just yet
            self.log_debug("PySide not detected - Toolkit will add it to the setup now...")
        else:
            # looks like pyside is already working! No need to do anything
            self.log_debug("PySide detected - Toolkit will use the existing version.")
            return

        if sys.platform == "win32":
            pyside_path = os.path.join(self.disk_location, "resources","pyside120_py273_qt471_win64", "python")
            sys.path.append(pyside_path)
            dll_path = os.path.join(self.disk_location, "resources","pyside120_py273_qt471_win64", "lib")
            path = os.environ.get("PATH", "")
            path += ";%s" % dll_path
            os.environ["PATH"] = path
        else:
            self.log_error("Unknown platform - cannot initialize PySide!")

        # now try to import it
        try:
            from PySide import QtGui
        except Exception, e:
            self.log_error("PySide could not be imported! Toolkit Apps using pyside will not "
                           "operate correctly! Error reported: %s" % e)
