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

def error(msg):
    """
    Error Repost
    :param msg: Error message string to show
    """
    print "ERROR: %s" % msg

def bootstrap_sgtk():
    """
    Bootstrap. This is called when preparing to launch by multi-launch.
    """
    # use _ssl with fix for slowdown
    if sys.platform == "win32":
        resources = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
        ssl_path = os.path.join(resources, "ssl_fix")
        sys.path.insert(0, ssl_path)
        path_parts = os.environ.get("PYTHONPATH", "").split(";")
        path_parts = [ssl_path] + path_parts
        os.environ["PYTHONPATH"] = ";".join(path_parts)
    else:
        error("Shotgun: Unknown platform - cannot setup ssl")
        return

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
        engine = sgtk.platform.start_engine(engine_name, context.tank, context)
    except Exception, e:
        error("Shotgun: Could not start engine: %s" % e)
        return

    # if a file was specified, load it now
    file_to_open =  os.environ.get("TANK_FILE_TO_OPEN")
    if file_to_open:
        MaxPlus.FileManager.Open(file_to_open)

    # clean up temp env vars
    for var in ["TANK_ENGINE", "TANK_CONTEXT", "TANK_FILE_TO_OPEN"]:
        if var in os.environ:
            del os.environ[var]

bootstrap_sgtk()
