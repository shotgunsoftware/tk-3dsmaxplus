# Copyright (c) 2017 Shotgun Software Inc.
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

from . import constants


def bootstrap_toolkit(root_path):
    """
    Entry point for toolkit bootstrap in 3dsmax.
    Called by the bootstrap.ms max script.

    :param str root_path: Path to the root folder of the plugin
    """

    # --- Import Core ---
    #
    # - If we are running the plugin built as a stand-alone unit,
    #   try to retrieve the path to sgtk core and add that to the pythonpath.
    #   When the plugin has been built, there is a sgtk_plugin_basic_3dsmax
    #   module which we can use to retrieve the location of core and add it
    #   to the pythonpath.
    # - If we are running toolkit as part of a larger zero config workflow
    #   and not from a standalone workflow, we are running the plugin code
    #   directly from the engine folder without a bundle cache and with this
    #   configuration, core already exists in the pythonpath.

    try:
        from sgtk_plugin_basic_3dsmax import manifest
        running_as_standalone_plugin = True
    except ImportError:
        running_as_standalone_plugin = False

    if running_as_standalone_plugin:
        # Retrieve the Shotgun toolkit core included with the plug-in and
        # prepend its python package path to the python module search path.
        tkcore_python_path = manifest.get_sgtk_pythonpath(root_path)
        sys.path.insert(0, tkcore_python_path)
        import sgtk

    else:
        # Running as part of the the launch process and as part of zero
        # config. The launch logic that started maya has already
        # added sgtk to the pythonpath.
        import sgtk

    # start logging to log file
    sgtk.LogManager().initialize_base_file_handler("tk-3dsmaxplus")

    # get a logger for the plugin
    sgtk_logger = sgtk.LogManager.get_logger("plugin")
    sgtk_logger.debug("Booting up toolkit plugin.")

    try:
        # When the user is not yet authenticated,
        # pop up the Shotgun login dialog to get the user's credentials,
        # otherwise, get the cached user's credentials.
        user = sgtk.authentication.ShotgunAuthenticator().get_user()

    except sgtk.authentication.AuthenticationCancelled:
        # When the user cancelled the Shotgun login dialog,
        # keep around the displayed login menu.
        sgtk_logger.info("Shotgun login was cancelled by the user.")
        return

    # Create a boostrap manager for the logged in user with the plug-in configuration data.
    toolkit_mgr = sgtk.bootstrap.ToolkitManager(user)
    toolkit_mgr.base_configuration = constants.BASE_CONFIGURATION
    toolkit_mgr.plugin_id = constants.PLUGIN_ID
    toolkit_mgr.bundle_cache_fallback_paths = [os.path.join(root_path, "bundle_cache")]

    # Retrieve the Shotgun entity type and id when they exist in the environment.
    # these are passed down through the app launcher when running in zero config
    entity = toolkit_mgr.get_entity_from_environment()
    sgtk_logger.debug("Will launch the engine with entity: %s" % entity)

    # set up a simple progress reporter
    toolkit_mgr.progress_callback = progress_callback

    # start engine
    sgtk_logger.info("Starting the 3dsmaxplus engine.")
    toolkit_mgr.bootstrap_engine_async("tk-3dsmaxplus", entity)

    sgtk_logger.debug("Bootstrap complete.")

def progress_callback(progress_value, message):
    """
    Called whenever toolkit reports progress.

    :param progress_value: The current progress value as float number.
                           values will be reported in incremental order
                           and always in the range 0.0 to 1.0
    :param message:        Progress message string
    """
    print "Shotgun: %s" % message

def shutdown_toolkit():
    """
    Shutdown the Shotgun toolkit and its Maya engine.
    """
    import sgtk

    # Turn off your engine! Step away from the car!
    engine = sgtk.platform.current_engine()
    if engine:
        engine.destroy()
