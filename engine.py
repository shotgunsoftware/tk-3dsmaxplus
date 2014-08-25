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
import thread

import tank

class MaxEngine(tank.platform.Engine):

    def __init__(self, *args, **kwargs):
        # keep track of the main thread id to keep from output on sub-threads
        self._main_thread_id = thread.get_ident()

        # proceed about your business
        tank.platform.Engine.__init__(self, *args, **kwargs)

    def pre_app_init(self):
        """
        constructor
        """
        import MaxPlus
        from tank.platform.qt import QtCore

        self.log_debug("%s: Initializing..." % self)

        # Add image formats since max doesn't add the correct paths by default and jpeg won't be readable
        maxpath = QtCore.QCoreApplication.applicationDirPath()
        pluginsPath = os.path.join(maxpath, "plugins")
        QtCore.QCoreApplication.addLibraryPath(pluginsPath)

        # keep handles to all qt dialogs to help GC
        self.__created_qt_dialogs = []

        # Window focus objects are used to enable proper keyboard handling by the window instead of 3dsMax's accelerators
        class WindowFocus(QtCore.QObject):
            def eventFilter(self, obj, event):
                if event.type() == QtCore.QEvent.WindowActivate:
                    MaxPlus.CUI.DisableAccelerators()
                elif event.type() == QtCore.QEvent.WindowDeactivate:
                    MaxPlus.CUI.EnableAccelerators()

                return False;

        self.windowFocus = WindowFocus()

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
            if thread.get_ident() == self._main_thread_id:
                print "[%-13s] Shotgun Debug: %s" % (str(time.time()), msg)

    def log_info(self, msg):
        if thread.get_ident() == self._main_thread_id:
            print "[%-13s] Shotgun Info: %s" % (str(time.time()), msg)

    def log_warning(self, msg):
        if thread.get_ident() == self._main_thread_id:
            print "[%-13s] Shotgun Warning: %s" % (str(time.time()), msg)

    def log_error(self, msg):
        if thread.get_ident() == self._main_thread_id:
            print "[%-13s] Shotgun Error: %s" % (str(time.time()), msg)

    ##########################################################################################
    # pyside
    def show_dialog(self, title, bundle, widget_class, *args, **kwargs):
        from tank.platform.qt import tankqdialog

        # first construct the widget object
        obj = widget_class(*args, **kwargs)

        # now create a dialog
        dialog = tankqdialog.TankQDialog(title, bundle, obj, None)
        dialog.installEventFilter(self.windowFocus)

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
        dialog.installEventFilter(self.windowFocus)

        # keep a reference to all created dialogs to make GC happy
        self.__created_qt_dialogs.append(dialog)

        # finally launch it, modal state
        status = dialog.exec_()

        # lastly, return the instantiated class
        return (status, obj)
