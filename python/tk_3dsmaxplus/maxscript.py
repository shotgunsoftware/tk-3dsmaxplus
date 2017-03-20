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
MaxScript handling for 3ds Max
"""
import hashlib
import MaxPlus

class MaxScript:
    """
    MaxScript/Python Bridge Utilities
    """

    @staticmethod
    def add_to_menu(from_menu_var, to_menu_var, from_menu_name):
        """
        Add given menu to another menu
        :param from_menu_var: MaxScript variable name of menu to add from
        :param to_menu_var: MaxScript variable name of menu to add to
        :param from_menu_name: Name of menu item to give to MaxScript
        """

        MaxPlus.Core.EvalMAXScript('''
            sgtk_menu_sub_item = menuMan.createSubMenuItem "{from_menu_name}" {from_menu_var}
            {to_menu_var}.addItem sgtk_menu_sub_item -1
        '''.format(from_menu_var=from_menu_var, to_menu_var=to_menu_var, from_menu_name=from_menu_name))

    @staticmethod
    def create_menu(menu_name, menu_var):
        """
        Create a menu
        :param menu_name: String name of menu to create
        :param menu_var: MaxScript variable name in which the menu will be created
        """

        MaxPlus.Core.EvalMAXScript('''
            -- clear the old menu
            sgtk_oldMenu = menuMan.findMenu "{menu_name}"
            if sgtk_oldMenu != undefined then menuMan.unregisterMenu sgtk_oldMenu

            -- create the main menu
            {menu_var} = menuMan.createMenu "{menu_name}"
        '''.format(menu_var=menu_var, menu_name=menu_name))

    @staticmethod
    def add_separator(menu_var):
        """
        Add separator to a menu
        :param menu_var: MaxScript variable name of the menu to add separator into
        """

        MaxPlus.Core.EvalMAXScript('''
            sgtk_menu_separator = menuMan.createSeparatorItem()
            {menu_var}.addItem sgtk_menu_separator -1
        '''.format(menu_var=menu_var))

    @staticmethod
    def add_to_main_menu_bar(menu_var, menu_name):
        """
        Add menu to 3ds max's main menu bar
        :param menu_var: MaxScript variable name of menu to add to the main menu bar
        :param menu_name: String name of the menu to add
        """

        MaxPlus.Core.EvalMAXScript('''
            -- Add main menu to Max, second to last which should be before Help
            sgtk_main_menu_bar = menuMan.getMainMenuBar()
            sgtk_sub_menu_index = sgtk_main_menu_bar.numItems() - 1
            sgtk_sub_menu_item = menuMan.createSubMenuItem "{menu_name}" {menu_var}
            sgtk_main_menu_bar.addItem sgtk_sub_menu_item sgtk_sub_menu_index
            menuMan.updateMenuBar()
        '''.format(menu_var=menu_var, menu_name=menu_name))

    @staticmethod
    def add_action_to_menu(callback, action_name, menu_var, engine):
        """
        Add a menu item for this command to the given MaxScript menu variable name.
        :param callback: Callback function to call with this action
        :param action_name: Name of the action, as will appear to the user
        :param menu_var: MaxScript menu variable name to add menu item to.
        :param engine: Current engine where the action can be globally linked back to.
        """
        obj = callback.im_self
        method_name = callback.__name__

        # Note that we're using the action name because we need these
        # macros to reference things consistently across sessions. Sadly,
        # if a second, concurrent, 3ds Max session is launched, Toolkit
        # will build the Shotgun menu in that session and Max will write
        # that updated menu layout to disk for the user, because it thinks
        # that needs to persist across sessions. This causes us problems
        # in the first session, then, because Max looks up what macro to
        # run from the xml stored on disk when the action is triggered.
        # This means that if we have anything referenced from the macro
        # that is not available in the first session, the action will
        # fail.
        hash_name = action_name

        # This won't be visible to the user, so we'll go the ugly route
        # to resolve conflicts and just append underscores until we get
        # a unique key. Ultimately, this is just covering what should be
        # the very rare edge case of having two menu actions with the
        # same name. That would be bad practice, in my opinion, but since
        # it is possible we will handle it.
        while hash_name in engine.maxscript_objects:
            hash_name += "_"

        engine.maxscript_objects[hash_name] = obj
        

        """
        Macro name must not have any strange characters (spaces, dash, etc..)
        These macro script will be saved as files by 3ds max on the user folder.
        Therefore, the name is made unique to the action name so as to not pollute the usermacro folder
        with new macro for the same action every time shotgun is reloaded.
        eg: 'Publish...' action will always re-use the same MacroScript.
        """
        macro_name = 'sg_' + hashlib.md5(action_name).hexdigest()

        # Creating python code separately as it needs to have no indentation in the macroscript
        python_code = (
            "import sgtk\n"
            "engine = sgtk.platform.current_engine()\n"
            "if '{hash_name}' in engine.maxscript_objects:\n"
            "    command_object = engine.maxscript_objects['{hash_name}']\n"
            "    command_object.{command_name}()\n"
            "else:\n"
            "    engine.log_error('Shotgun Error: Failed to find Action command in MAXScript callback for action [{action_name}]!')\n"
        ).format(hash_name=hash_name, command_name=method_name, action_name=action_name)

        MaxPlus.Core.EvalMAXScript('''
            -- Create MacroScript that will callback to our python object
            macroScript {macro_name}
            category: "Shotgun Menu Actions"
            tooltip: "{action_name}"
            (
	            on execute do 
	            (
                    /* 
                        This is a workaround to prevent any menu item from being used while there is a modal window.
                        Calling any python code from maxscript while there is a modal window (even 'a = 1') results in
                        an exception.

                        Note: Keeping the indent is important here
                    */
                    if (sgtk_main_menu_enabled != undefined and sgtk_main_menu_enabled == True) then
		                python.execute "{python_code}"
                    else
                        print "Shotgun Warning: You need to close the current window dialog before using any more commands."
	            )
            )

            -- Add menu item using previous MacroScript action
            sgtk_menu_action = menuMan.createActionItem "{macro_name}" "Shotgun Menu Actions"
            sgtk_menu_action.setUseCustomTitle true
            sgtk_menu_action.setTitle("{action_name}")
            {menu_var}.addItem sgtk_menu_action -1
        '''.format(macro_name=macro_name, menu_var=menu_var, action_name=action_name, python_code=python_code))

    @staticmethod
    def disable_menu():
        """
        Sets a flag so that menu actions will not be called, which would throw exceptions. See add_action_menu's macroscript
        comments for details.

        This is used to disable actions while a modal window is opened.
        """
        MaxPlus.Core.EvalMAXScript("sgtk_main_menu_enabled = False")

    @staticmethod
    def enable_menu():
        """
        Sets a flag so that menu actions can be called.
        """

        MaxPlus.Core.EvalMAXScript("sgtk_main_menu_enabled = True")
