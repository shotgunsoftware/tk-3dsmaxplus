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
import re
import sys
import sgtk

from sgtk.platform import SoftwareLauncher, SoftwareVersion, LaunchInformation


class MaxLauncher(SoftwareLauncher):
    """
    Handles launching 3dsMax executables. Automatically starts up
    a tk-3dsmaxplus engine with the current context in the new session
    of 3dsMax.
    """

    @property
    def minimum_supported_version(self):
        """
        The minimum software version that is supported by the launcher.
        """
        return "2016"

    def scan_software(self):
        """
        Scan the Windows Registry for 3dsMax executables.

        :return: A list of :class:`SoftwareVersion` objects.
        """

        self.logger.debug("Scanning for 3dsMax executables...")

        if sys.platform != "win32":
            # max only exists on windows
            return []

        supported_sw_versions = []
        for sw_version in self._find_software():
            (supported, reason) = self._is_supported(sw_version)
            if supported:
                supported_sw_versions.append(sw_version)
            else:
                self.logger.debug(
                    "SoftwareVersion %s is not supported: %s" %
                    (sw_version, reason)
                )

        return supported_sw_versions

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch 3dsMax in that will automatically
        load Toolkit and the tk-3dsmaxplus engine when 3dsMax starts.

        :param str exec_path: Path to 3dsMax executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """
        # This is a fix for PySide problems in 2017+ versions of Max. Now that
        # Max ships with a full install of PySide, we need to ensure that dlls
        # for the native Max install are sourced. If we don't do this, we end
        # up with dlls loaded from SG Desktop's bin and we have a mismatch that
        # results in complete breakage.
        max_root = os.path.dirname(exec_path)
        sgtk.util.prepend_path_to_env_var("PATH", max_root)

        required_env = {}

        startup_file = os.path.join(self.disk_location, "python", "startup", "bootstrap.py")
        new_args = "-U PythonHost \"%s\"" % startup_file

        if args:
            args = "%s %s" % (args, new_args)
        else:
            args = new_args

        # Check the engine settings to see whether any plugins have been
        # specified to load.
        find_plugins = self.get_setting("launch_builtin_plugins")
        if find_plugins:
            self.logger.debug("Plugins found from 'launch_builtin_plugins': %s" % find_plugins)

            # Keep track of the specific list of Toolkit plugins to load when
            # launching 3dsMax. This list is passed through the environment and
            # used by the startup/bootstrap.py file.
            load_max_plugins = []

            for find_plugin in find_plugins:
                load_plugin = os.path.join(self.disk_location, "plugins", find_plugin)
                if os.path.exists(load_plugin):
                    self.logger.debug("Preparing to launch builtin plugin '%s'" % load_plugin)
                    load_max_plugins.append(load_plugin)
                else:
                    # Report the missing plugin directory
                    self.logger.warning("Resolved plugin path '%s' does not exist!" % load_plugin)

            required_env["SGTK_LOAD_MAX_PLUGINS"] = os.pathsep.join(load_max_plugins)

            # Add context and site info
            std_env = self.get_standard_plugin_environment()
            required_env.update(std_env)

        else:
            # Prepare the launch environment with variables required by the
            # classic bootstrap approach.
            self.logger.debug("Preparing 3dsMax Launch via Toolkit Classic methodology ...")
            required_env["TANK_ENGINE"] = self.engine_name
            required_env["TANK_CONTEXT"] = sgtk.context.serialize(self.context)

        if file_to_open:
            # Add the file name to open to the launch environment
            required_env["SGTK_FILE_TO_OPEN"] = file_to_open

        return LaunchInformation(exec_path, args, required_env)

    def _find_software(self):
        """
        Find executables in the Windows Registry.

        :returns: List of :class:`SoftwareVersion` instances
        """
        # Determine a list of paths to search for 3dsMax executables based
        # on the windows registry
        search_paths = _get_installation_paths_from_registry(self.logger)
        exec_paths = []

        for search_path in search_paths:
            # Construct the expected executable name for this path.
            # If it exists, add it to the list of exec_paths to check.
            exec_path = os.path.join(search_path, "3dsmax.exe")

            if os.path.exists(exec_path):
                self.logger.debug("found version in default installation path %s" % exec_path)
                exec_paths.append(exec_path)

        sw_versions = []
        for exec_path in exec_paths:
            # Check to see if the version number can be parsed from the path name.
            path_sw_versions = [p.lower() for p in exec_path.split(os.path.sep)
                                if re.match("3ds max [0-9]+[.0-9]*$", p.lower()) is not None
                                ]
            if path_sw_versions:
                # Use this sub dir to determine the default display name
                # and version for the SoftwareVersion to be created.
                executable_version = path_sw_versions[0].replace("3ds max ", "")
                self.logger.debug(
                    "Resolved version '%s' from executable '%s'." %
                    (executable_version, exec_path)
                )

            # Create a SoftwareVersion using the information from executable
            # path(s) found in default locations.
            self.logger.debug("Creating SoftwareVersion for executable '%s'." % exec_path)
            sw_versions.append(SoftwareVersion(
                executable_version,
                "3ds Max",
                exec_path,
                os.path.join(self.disk_location, "icon_256.png")
            ))

        return sw_versions


def _get_installation_paths_from_registry(logger):
    """
    Query Windows registry for 3dsMax installations.

    :returns: List of paths where 3dsmax is installed,
    """
    # import it locally so that
    import _winreg
    logger.debug("Querying windows registry for key HKEY_LOCAL_MACHINE\\SOFTWARE\\Autodesk\\3dsMax")

    base_key_name = "SOFTWARE\\Autodesk\\3dsMax"
    sub_key_names = []

    # find all subkeys in key HKEY_LOCAL_MACHINE\SOFTWARE\Autodesk\3dsMax
    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, base_key_name)
        sub_key_count = _winreg.QueryInfoKey(key)[0]
        i = 0
        while i < sub_key_count:
            sub_key_names.append(_winreg.EnumKey(key, i))
            i += 1
        _winreg.CloseKey(key)
    except WindowsError:
        logger.error("error opening key %s" % base_key_name)

    install_paths = []
    # Query the value "Installdir" on all subkeys.
    try:
        for name in sub_key_names:
            key_name = base_key_name + "\\" + name
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key_name)
            try:
                install_paths.append(_winreg.QueryValueEx(key, "Installdir")[0])
                logger.debug("found Installdir value for key %s" % key_name)
            except WindowsError:
                logger.debug("value Installdir not found for key %s, skipping key" % key_name)
            _winreg.CloseKey(key)
    except WindowsError:
        logger.error("error opening key %s" % key_name)

    return install_paths
