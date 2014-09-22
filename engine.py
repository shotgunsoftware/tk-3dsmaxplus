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
A 3ds Max (2015+) engine for Toolkit that uses MaxPlus.
"""
import os
import sys
import time
import thread
import math

import sgtk
import MaxPlus

class MaxEngine(sgtk.platform.Engine):
    """
    The main Toolkit engine for 3ds Max
    """
    def __init__(self, *args, **kwargs):
        """
        Engine Constructor
        """
        # proceed about your business
        sgtk.platform.Engine.__init__(self, *args, **kwargs)

    ##########################################################################################
    # init
    
    def init_engine(self):
        """
        Init the engine
        """
        self.log_debug("%s: Initializing..." % self)

        if self._get_max_version() > MaxEngine.MAXIMUM_SUPPORTED_VERSION:
            # Untested max version
            msg = ("Shotgun Pipeline Toolkit!\n\n"
                   "The Shotgun Pipeline Toolkit has not yet been fully tested with 3ds Max versions greater then 2015. "
                   "You can continue to use the Toolkit but you may experience bugs or "
                   "instability.  Please report any issues you see to toolkitsupport@shotgunsoftware.com")
            
            # Display warning dialog
            max_year = self._max_version_to_year(self._get_max_version())
            max_next_year = self._max_version_to_year(MaxEngine.MAXIMUM_SUPPORTED_VERSION) + 1
            if max_year >= self.get_setting("compatibility_dialog_min_version", max_next_year):
                MaxPlus.Core.EvalMAXScript('messagebox "Warning - ' + msg + '" title: "Shotgun Warning"')

            # and log the warning
            self.log_warning(msg)

        elif not self._is_at_least_max_2015():
            # Unsupported max version
            msg = ("Shotgun Pipeline Toolkit!\n\n"
                   "The Shotgun Pipeline Toolkit does not work with 3ds max versions prior to 2015.")

            # Display warning dialog
            MaxPlus.Core.EvalMAXScript('messagebox "Warning - ' + msg + '" title: "Shotgun Warning"')
                           
            # and log the warning
            self.log_warning(msg)

    def pre_app_init(self):
        """
        Called before all apps have initialized
        """
        from sgtk.platform.qt import QtCore

        self.log_debug("%s: Initializing..." % self)

        # Add image formats since max doesn't add the correct paths by default and jpeg won't be readable
        maxpath = QtCore.QCoreApplication.applicationDirPath()
        pluginsPath = os.path.join(maxpath, "plugins")
        QtCore.QCoreApplication.addLibraryPath(pluginsPath)

        # Window focus objects are used to enable proper keyboard handling by the window instead of 3dsMax's accelerators
        class WindowFocus(QtCore.QObject):
            def eventFilter(self, obj, event):
                if event.type() == QtCore.QEvent.WindowActivate:
                    MaxPlus.CUI.DisableAccelerators()
                elif event.type() == QtCore.QEvent.WindowDeactivate:
                    MaxPlus.CUI.EnableAccelerators()

                return False;

        self.windowFocus = WindowFocus()

        # set up a qt style sheet
        # note! - try to be smart about this and only run
        # the style setup once per session - it looks like
        # 3dsmax slows down if this is executed every engine restart. 
        qt_app_obj = sgtk.platform.qt.QtCore.QCoreApplication.instance()
        curr_stylesheet = qt_app_obj.styleSheet()

        if "toolkit 3dsmax style extension" not in curr_stylesheet:
            self._initialize_dark_look_and_feel()

            curr_stylesheet += "\n\n /* toolkit 3dsmax style extension */ \n\n"
            curr_stylesheet += "\n\n QDialog#TankDialog > QWidget { background-color: #343434; }\n\n"        
            qt_app_obj.setStyleSheet(curr_stylesheet) 

    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        # set up menu handler
        self.tk_3dsmax = self.import_module("tk_3dsmaxplus")
        self._menu_generator = self.tk_3dsmax.MenuGenerator(self)
        self._menu_generator.create_menu()

    def destroy_engine(self):
        """
        Called when the engine is shutting down
        """
        self.log_debug('%s: Destroying...' % self)

    ##########################################################################################
    # logging
    # Should only call logging function from the main thread, although output to listener is
    # supposed to be thread-safe.
    # Note From the max team: Python scripts run in MAXScript are not thread-safe.  
    #                         Python commands are always executed in the main 3ds Max thread.  
    #                         You should not attempt to spawn separate threads in your scripts 
    #                         (for example, by using the Python threading module).
    def log_debug(self, msg):
        """
        Debug logging.
        :param msg: The message string to log
        """
        if self.get_setting("debug_logging", False):
            print "[%-13s] Shotgun Debug: %s" % (str(time.time()), msg)

    def log_info(self, msg):
        """
        Info logging.
        :param msg: The message string to log
        """
        print "[%-13s] Shotgun Info: %s" % (str(time.time()), msg)

    def log_warning(self, msg):
        """
        Warning logging.
        :param msg: The message string to log
        """
        print "[%-13s] Shotgun Warning: %s" % (str(time.time()), msg)

    def log_error(self, msg):
        """
        Error logging.
        :param msg: The message string to log
        """
        print "[%-13s] Shotgun Error: %s" % (str(time.time()), msg)

    ##########################################################################################
    # Engine
    def _create_dialog(self, title, bundle, widget, parent):
        """
        Parent function override to install event filtering in order to allow proper events to
        reach window dialogs (such as keyboard events).
        """
        dialog = sgtk.platform.Engine._create_dialog(self, title, bundle, widget, parent)
        dialog.installEventFilter(self.windowFocus)

        return dialog

    def show_modal(self, title, bundle, widget_class, *args, **kwargs):
        if not self.has_ui:
            self.log_error("Sorry, this environment does not support UI display! Cannot show "
                           "the requested window '%s'." % title)
            return None
        
        # Disable 'Shotgun' background menu while modals are there.
        self.tk_3dsmax.MaxScript.disable_menu('Shotgun', 'sgtk_main_menu_items')

        # create the dialog:
        dialog, widget = self._create_dialog_with_widget(title, bundle, widget_class, *args, **kwargs)
        
        # finally launch it, modal state
        status = dialog.exec_()

        # Re-enable 'Shotgun' background menu after modal has been closed
        self.tk_3dsmax.MaxScript.enable_menu('Shotgun', 'sgtk_main_menu_items')
        
        # lastly, return the instantiated widget
        return (status, widget)

    ##########################################################################################
    # MaxPlus SDK Patching

    # Version Id for 3dsmax 2015 Taken from Max Sdk (not currently available in maxplus)
    MAX_RELEASE_R17 = 17000

    # Latest supported max version
    MAXIMUM_SUPPORTED_VERSION = 17000

    def _max_version_to_year(self, version):
        """ 
        Get the max year from the max release version. 
        Note that while 17000 is 2015, 17900 would be 2016 alpha
        """
        year = 2000 + (math.ceil(version / 1000.0) - 2)
        return year

    def _get_max_release(self, x): 
        """
        Macro to get 3ds max release from version id 
        (not currently present in MaxPlus, but found in max's c++ sdk)
        :param x: 3ds max Version id
        """
        return (((x)>>16)&0xffff)

    def _get_max_version(self):
        """
        Returns Version integer of max release number.
        """
        # 3dsMax Version returns a number which contains max version, sdk version, etc...
        versionId = MaxPlus.Application.Get3DSMAXVersion()
        
        # Transform it to a version id
        version = self._get_max_release(versionId)

        return version

    def _is_at_least_max_2015(self):
        """
        Returns True if current Max version is equal or above 3ds max 2015
        """
        return self._get_max_version() >= MaxEngine.MAX_RELEASE_R17
