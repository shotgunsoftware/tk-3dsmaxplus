-- Copyright (c) 2017 Shotgun Software Inc.
--
-- CONFIDENTIAL AND PROPRIETARY
--
-- This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
-- Source Code License included in this distribution package. See LICENSE.
-- By accessing, using, copying or modifying this work you indicate your
-- agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
-- not expressly granted therein are reserved by Shotgun Software Inc.


-- set up a callback that fires when the UI is ready
callbacks.addScript #postSystemStartup "bootstrapToolkit()"


------------------------------------------------------------------------------------------
fn bootstrapToolkit = (
    -- this function will determine the location of the plugin
    -- and then pass control to python which will handle the rest
    -- of the bootstrap.

    -- figure out plugin root path
    bootstrap_folder = getFilenamePath(getSourceFileName())
    plugin_root_folder = pathConfig.appendPath bootstrap_folder ".."
    plugin_root_folder = pathConfig.convertPathToAbsolute plugin_root_folder

    -- figure out where our python bootstrap is
    python_folder = pathConfig.appendPath plugin_root_folder "python"

    -- switch slash direction to prevent escaping issues later on
    plugin_root_folder = substituteString plugin_root_folder "\\" "/"
    python_folder = substituteString python_folder "\\" "/"

    -- put together python bootstrap command
    python_cmd = "import sys; sys.path.append('" + python_folder + "'); import tk_3dsmaxplus_basic; tk_3dsmaxplus_basic.bootstrap_toolkit('" + plugin_root_folder + "');"

    -- execute python and off we go!
    python.Execute python_cmd

)

