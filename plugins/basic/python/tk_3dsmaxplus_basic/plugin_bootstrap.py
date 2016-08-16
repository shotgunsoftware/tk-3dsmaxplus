# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

from sgtk_plugin_basic import manifest

def bootstrap_toolkit(root_path):

    tk_core_path = manifest.get_sgtk_pythonpath(root_path)
    sys.path.append(tk_core_path)

    import sgtk

    sgtk.LogManager().initialize_base_file_handler("tk-3dsmaxplus")

    if manifest.debug_logging:
        sgtk.LogManager().global_debug = True

    sgtk_logger = sgtk.LogManager.get_logger("plugin")

    sgtk_logger.debug("Booting up plugin with manifest %s" % manifest.BUILD_INFO)

    # create boostrap manager
    toolkit_mgr = sgtk.bootstrap.ToolkitManager()
    toolkit_mgr.entry_point = manifest.entry_point
    toolkit_mgr.base_configuration = manifest.base_configuration
    toolkit_mgr.bundle_cache_fallback_paths = [os.path.join(root_path, "bundle_cache")]

    sgtk_logger.info("Starting the 3dsmaxplus engine.")

    toolkit_mgr.bootstrap_engine("tk-3dsmaxplus", entity=None)


def shutdown_toolkit():
    """
    Shutdown the Shotgun toolkit and its Maya engine.
    """
    import sgtk

    # Turn off your engine! Step away from the car!
    engine = sgtk.platform.current_engine()
    if engine:
        engine.destroy()
