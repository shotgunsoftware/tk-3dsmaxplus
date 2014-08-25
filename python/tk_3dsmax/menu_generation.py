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
import os
import sys
import traceback
import uuid

from PySide import QtGui
from PySide import QtCore

import MaxPlus

class MenuGenerator(object):
    """
    Menu generation functionality for 3dsmax
    """
    def __init__(self, engine):
        self._engine = engine
        self._menu_handle = None
        self._menu_builder = None

    @staticmethod
    def CreateUniqueMenuItem(category, name, fxn):
        """ 
        Creates a new action item from the category, name, function and objct to use as hash for the menu.
        """
        uniqueId = uuid.uuid4()

        item = MaxPlus._CustomActionItem(category, name, fxn)
        
        # MaxPlus normally uses a hash based on menu name, which isn't good for reloading menus. Using a globally unique id instead
        item.GetId = lambda : hash(uniqueId)

        MaxPlus.ActionFactory.CustomActionItems.append(item)
        return MaxPlus.ActionFactory.CreateFromAbstract(item)

    def create_menu(self):
        """
        Create the Shotgun Menu
        """

        # enumerate all items and create menu objects for them
        cmd_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
            cmd_items.append(AppCommand(cmd_name, cmd_details))

        # clear the old menu
        if MaxPlus.MenuManager.MenuExists(u"Shotgun"):
            MaxPlus.MenuManager.UnregisterMenu(u"Shotgun")
        self._menu_builder = MaxPlus.MenuBuilder(u"Shotgun")

        # start with context menu
        ctx_builder = self._create_context_builder()
        for cmd in cmd_items:
            if cmd.get_type() == "context_menu":
                cmd.add_to_builder(ctx_builder)
        self._menu_builder.AddSubMenu(ctx_builder.Create())
        self._menu_builder.AddSeparator()

        # now favourites
        for fav in self._engine.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            # scan through all menu items
            for cmd in cmd_items:
                if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                    # found our match!
                    cmd.add_to_builder(self._menu_builder)
                    # mark as a favourite item
                    cmd.favourite = True
        self._menu_builder.AddSeparator()

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

        # and add it to Max, second to last which should be before Help
        main = MaxPlus.MenuManager.GetMainMenu()
        self._menu_handle = self._menu_builder.Create(main, main.NumItems - 1)

    def _create_context_builder(self):
        """
        Adds a context menu wich displays the current context
        """
        ctx = self._engine.context

        if ctx.entity is None:
            ctx_name = "%s" % ctx.project["name"]

        elif ctx.step is None and ctx.task is None:
            # entity only
            # e.g. Shot ABC_123
            ctx_name = "%s %s" % (ctx.entity["type"], ctx.entity["name"])
        else:
            # we have either step or task
            task_step = None
            if ctx.step:
                task_step = ctx.step.get("name")
            if ctx.task:
                task_step = ctx.task.get("name")

            # e.g. [Lighting, Shot ABC_123]
            ctx_name = "%s, %s %s" % (task_step, ctx.entity["type"], ctx.entity["name"])

        # create the builder object
        if MaxPlus.MenuManager.MenuExists(ctx_name):
            MaxPlus.MenuManager.UnregisterMenu(ctx_name)
        ctx_builder = MaxPlus.MenuBuilder(ctx_name)

        action = MenuGenerator.CreateUniqueMenuItem("Jump to Shotgun", "Jump to Shotgun", self._jump_to_sg)
        ctx_builder.AddItem(action)
        action = MenuGenerator.CreateUniqueMenuItem("Jump to File System", "Jump to File System", self._jump_to_fs)
        ctx_builder.AddItem(action)
        ctx_builder.AddSeparator()

        return ctx_builder

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
        """
        for app_name in sorted(commands_by_app.keys()):
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry fort his app
                # make a sub menu and put all items in the sub menu
                if MaxPlus.MenuManager.MenuExists(app_name):
                    MaxPlus.MenuManager.UnregisterMenu(app_name)
                builder = MaxPlus.MenuBuilder(app_name)

                for cmd in commands_by_app[app_name]:
                    cmd.add_to_builder(builder)

                menu = builder.Create()
                self._menu_builder.AddSubMenu(menu)
            else:
                # this app only has a single entry.
                # display that on the menu
                # todo: Should this be labelled with the name of the app
                # or the name of the menu item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    # skip favourites since they are alreay on the menu
                    cmd_obj.add_to_builder(self._menu_builder)


class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    def __init__(self, name, command_dict):
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
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

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

    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")

    def _caller(self):
        try:
            self.callback()
        except:
            tb = traceback.format_exc()

    def add_to_builder(self, builder):
        action = MenuGenerator.CreateUniqueMenuItem(self.name, self.name, self._caller)
        builder.AddItem(action)
