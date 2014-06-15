import os
import sys

import MaxPlus


def error(msg):
    print "ERROR: %s" % msg


def bootstrap_tank():
    # use _ssl with fix for slowdown
    if sys.platform == "win32":
        resources = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
        ssl_path = os.path.join(resources, "ssl_fix")
        sys.path.insert(0, ssl_path)
        path = os.environ.get("PATH", "")
        path += ";%s" % ssl_path
        os.environ["PATH"] = path
    else:
        error("Shotgun: Unknown platform - cannot setup ssl")
        return

    try:
        import tank
    except Exception, e:
        error("Shotgun: Could not import sgtk! Disabling for now: %s" % e)
        return

    if not "TANK_ENGINE" in os.environ:
        error("Shotgun: Missing required environment variable TANK_ENGINE.")
        return

    engine_name = os.environ.get("TANK_ENGINE")
    try:
        context = tank.context.deserialize(os.environ.get("TANK_CONTEXT"))
    except Exception, e:
        error("Shotgun: Could not create context! sgtk will be disabled. Details: %s" % e)
        return

    try:
        engine = tank.platform.start_engine(engine_name, context.tank, context)
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

    # startup PySide
    from PySide import QtGui, QtCore
    app = QtGui.QApplication.instance()
    if app is None:
        # create the QApplication
        app = QtGui.QApplication([])
        
        # Manne 15 June 2014: 
        # TODO - Switch over to use new engine._initialize_dark_look_and_feel() method.
        # See https://github.com/shotgunsoftware/tk-core/pull/80 for details.
        
        QtGui.QApplication.setStyle("cleanlooks")
        app.setQuitOnLastWindowClosed(False)

        # tell QT to interpret C strings as utf-8
        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)

        # set the stylesheet
        resources = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
        css_file = os.path.join(resources, "dark.css")
        f = open(css_file)
        css = f.read()
        f.close()
        app.setStyleSheet(css)
        print "Shotgun: PySide initialized"

bootstrap_tank()
