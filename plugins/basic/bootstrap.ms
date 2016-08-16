-- Copyright (c) 2016 Shotgun Software Inc.
--
-- CONFIDENTIAL AND PROPRIETARY
--
-- This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
-- Source Code License included in this distribution package. See LICENSE.
-- By accessing, using, copying or modifying this work you indicate your
-- agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
-- not expressly granted therein are reserved by Shotgun Software Inc.


-- figure out the location of the plugin
plugin_root_folder = getFilenamePath(getSourceFileName())
-- figure out the location of our python payload
python_folder = pathConfig.appendPath plugin_root_folder "python"

-- replace backslashes with slashes for escaping purposes.
plugin_root_folder = substituteString plugin_root_folder "\\" "/"
python_folder = substituteString python_folder "\\" "/"

-- put together python bootstrap command
python_cmd = "import sys; sys.path.append('" + python_folder + "'); import tk_3dsmaxplus_basic; tk_3dsmaxplus_basic.bootstrap_toolkit('" + plugin_root_folder + "');"

-- execute python and off we go!
python.Execute python_cmd


