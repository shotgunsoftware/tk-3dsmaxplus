import os
import sys

import MaxPlus


def error(msg):
    print "ERROR: %s" % msg


def bootstrap_tank():
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
