# Copyright (c) 2013 Shotgun Software Inc.
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

import MaxPlus

# the version of max when a working SSL python
# started to be distributed with it.
SSL_INCLUDED_VERSION = 20000

def error(msg):
    """
    Error Repost
    :param msg: Error message string to show
    """
    print "ERROR: %s" % msg


def bootstrap_sgtk_classic():
    """
    Parse environment variables for an engine name and
    serialized Context to use to startup Toolkit and
    the tk-3dsmaxplus engine and environment.
    """

    try:
        import sgtk
    except Exception, e:
        error("Shotgun: Could not import sgtk! Disabling for now: %s" % e)
        return

    if not "TANK_ENGINE" in os.environ:
        error("Shotgun: Missing required environment variable TANK_ENGINE.")
        return

    engine_name = os.environ.get("TANK_ENGINE")
    try:
        context = sgtk.context.deserialize(os.environ.get("TANK_CONTEXT"))
    except Exception, e:
        error("Shotgun: Could not create context! sgtk will be disabled. Details: %s" % e)
        return

    try:
        sgtk.platform.start_engine(engine_name, context.tank, context)
    except Exception, e:
        error("Shotgun: Could not start engine: %s" % e)
        return

def bootstrap_sgtk_with_plugins():
    """
    Parse environment variables for a list of plugins to load that will
    ultimately startup Toolkit and the tk-3dsmaxplus engine and environment.
    """
    import sgtk
    logger = sgtk.LogManager.get_logger(__name__)

    logger.debug("Launching 3dsMax in plugin mode")

    # Load all plugins by calling the 'load()' entry point.
    for plugin_path in os.environ["SGTK_LOAD_MAX_PLUGINS"].split(os.pathsep):
        plugin_python_path = os.path.join(plugin_path, "python")
        for module_name in os.listdir(plugin_python_path):
            sys.path.append(plugin_python_path)
            module = __import__(module_name)
            try:
                module.load(plugin_path)
            except AttributeError:
                logger.error("Missing 'load()' method in plugin %s.  Plugin won't be loaded" % plugin_path)

def bootstrap_sgtk():
    """
    Bootstrap. This is called when preparing to launch by multi-launch.
    """
    if sys.platform == "win32":

        # get the version id from max
        version_id = MaxPlus.Application.Get3DSMAXVersion()
        version_number = (version_id >> 16) & 0xffff

        if version_number < SSL_INCLUDED_VERSION:
            # our version of 3dsmax does not have ssl included.
            # patch this up by adding to the pythonpath
            resources = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
            ssl_path = os.path.join(resources, "ssl_fix")
            sys.path.insert(0, ssl_path)
            path_parts = os.environ.get("PYTHONPATH", "").split(";")
            path_parts = [ssl_path] + path_parts
            os.environ["PYTHONPATH"] = ";".join(path_parts)
    else:
        error("Shotgun: Unknown platform - cannot setup ssl")
        return

    if os.environ.get("SGTK_LOAD_MAX_PLUGINS"):
        bootstrap_sgtk_with_plugins()
    else:
        bootstrap_sgtk_classic()

    # if a file was specified, load it now
    file_to_open = os.environ.get("TANK_FILE_TO_OPEN")
    if file_to_open:
        MaxPlus.FileManager.Open(file_to_open)

    # clean up temp env vars
    for var in ["TANK_ENGINE", "TANK_CONTEXT", "TANK_FILE_TO_OPEN",
                "SGTK_LOAD_MAX_PLUGINS"]:
        if var in os.environ:
            del os.environ[var]

bootstrap_sgtk()
