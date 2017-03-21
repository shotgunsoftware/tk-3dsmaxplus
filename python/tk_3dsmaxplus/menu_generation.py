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
Menu handling for 3ds Max
"""
import MaxPlus
import os
import sys
import traceback
import unicodedata

from sgtk.platform.qt import QtCore, QtGui
from .maxscript import MaxScript

MENU_LABEL = "Shotgun"

class MenuGenerator(object):
    """
    Menu generation functionality for 3dsmax
    
    Actual menu creation is done through MaxScript to prevent a crash with modal dialogs.
    The crash happens if a modal dialog is open and a user clicks on a menu with action items 
    that directly call python code
    """
    def __init__(self, engine):
        """
        Initialize Menu Generator.
        :param engine: Engine to get commands from.
        """
        self._engine = engine

        # Maxscript variable name for context menu
        self._ctx_var = 'sgtk_menu_ctx'
        # Mascript variable name for Shotgun main menu
        self._menu_var = 'sgtk_menu_main'
        
        # Need a globally available object for maxscript action callbacks to be able to refer to python objects
        self._engine.maxscript_objects = {}

    def create_menu(self):
        """
        Create the Shotgun Menu
        """

        # Create the main menu
        MaxScript.create_menu(MENU_LABEL, self._menu_var)

        # enumerate all items and create menu objects for them
        cmd_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
            cmd_items.append(AppCommand(cmd_name, cmd_details))

        # start with context menu
        self._create_context_builder()
        for cmd in cmd_items:
            if cmd.get_type() == "context_menu":
                cmd.add_to_menu(self._ctx_var, self._engine)

        # now favourites
        for fav in self._engine.get_setting("menu_favourites", []):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            # scan through all menu items
            for cmd in cmd_items:
                if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                    # found our match!
                    cmd.add_to_menu(self._menu_var, self._engine)
                    # mark as a favourite item
                    cmd.favourite = True

        MaxScript.add_separator(self._menu_var)
        
        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}

        for cmd in cmd_items:
            if cmd.get_type() != "context_menu":
            # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items"
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)

        # now add all apps to main menu
        self._add_app_menu(commands_by_app)

        MaxScript.add_to_main_menu_bar(self._menu_var, MENU_LABEL)

    def destroy_menu(self):
        if MaxPlus.MenuManager.MenuExists(MENU_LABEL):
            MaxPlus.MenuManager.UnregisterMenu(MENU_LABEL)

    def _create_context_builder(self):
        """
        Adds a context menu wich displays the current context
        :returns: Menu builder
        """
        ctx = self._engine.context
        ctx_name = str(ctx)

        MaxScript.create_menu(ctx_name, self._ctx_var)
        MaxScript.add_action_to_menu(self._jump_to_sg, 'Jump to Shotgun', self._ctx_var, self._engine)

        # Add the menu item only when there are some file system locations.
        if ctx.filesystem_locations:
            MaxScript.add_action_to_menu(self._jump_to_fs, 'Jump to File System', self._ctx_var, self._engine)

        MaxScript.add_separator(self._menu_var)
        MaxScript.add_to_menu(self._ctx_var, self._menu_var, "ctx_builder")

    def _jump_to_sg(self):
        """
        Jump from context to Sg
        """
        url = self._engine.context.shotgun_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _jump_to_fs(self):
        """
        Jump from context to Fs
        """
        # launch one window for each location on disk
        paths = self._engine.context.filesystem_locations
        for disk_location in paths:
            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)

    def _add_app_menu(self, commands_by_app):
        """
        Add all apps to the main menu, process them one by one.
        :param commands_by_app: Dictionary of app name and commands related to the app, which
                                will be added to the menu builder
        """
        for app_name in sorted(commands_by_app.keys()):
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry fort his app
                # make a sub menu and put all items in the sub menu
                menu_var = 'sgtk_menu_builder'
                MaxScript.create_menu(app_name, menu_var)
                
                for cmd in commands_by_app[app_name]:
                    cmd.add_to_menu(menu_var, self._engine)

                MaxScript.add_to_menu(menu_var, self._menu_var, "ShotgunMenu")
            else:
                # this app only has a single entry.
                # display that on the menu
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    # skip favourites since they are alreay on the menu
                    cmd_obj.add_to_menu(self._menu_var, self._engine)


class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    def __init__(self, name, command_dict):
        """
        Initialize AppCommand object.
        :param name: Command name
        :param command_dict: Dictionary containing a 'callback' property to use as callback.
        """
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False

    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None

    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        engine = self.get_engine()
        if engine is None:
            return None

        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name

        return None

    def get_documentation_url_str(self):
        """
        Returns the documentation as a str
        """
        if "app" in self.properties:
            app = self.properties["app"]
            doc_url = app.documentation_url
            # deal with nuke's inability to handle unicode. #fail
            if doc_url.__class__ == unicode:
                doc_url = unicodedata.normalize('NFKD', doc_url).encode('ascii', 'ignore')
            return doc_url

        return None

    def get_engine(self):
        """
        Returns the engine from the App Instance
        Returns None if not found
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        return engine

    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default.
        """
        return self.properties.get("type", "default")

    def execute(self):
        """
        Delegate method for this command
        """
        try:
            self.callback()
        except:
            tb = traceback.format_exc()

            engine = self.get_engine()
            if engine is not None:
                engine.log_error("Failed to call command '%s'. '%s'!" % (self.name, tb))

    def add_to_menu(self, menu_var, engine):
        """
        Add command to menu
        :param menu_var: MaxScript menu variable name to add menu item to.
        :param engine: Current engine where the action can be globally linked back to. (Not the App engine)
        """
        MaxScript.add_action_to_menu(self.execute, self.name, menu_var, engine)
