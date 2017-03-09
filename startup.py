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
import re
import _winreg

from xml.etree import ElementTree

from sgtk import TankError
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
        return "2015"

    def scan_software(self, versions=None):
        """
        Performs a scan for software installations.

        :param list versions: List of strings representing versions
                              to search for. If set to None, search
                              for all versions. A version string is
                              DCC-specific but could be something
                              like "2017", "6.3v7" or "1.2.3.52".
        :returns: List of :class:`SoftwareVersion` instances
        """
        # First look for executables using the Autodesk Synergy registry.
        sw_versions = self._synergy_software_versions(versions)
        if not sw_versions:
            sw_versions = self._default_path_software_versions(versions)

        if not sw_versions:
            self.logger.info("Unable to determine available SoftwareVersions for engine %s" % self.engine_name)
            return []

        return sw_versions

    def prepare_launch(self, exec_path, args, file_to_open=None):
        """
        Prepares an environment to launch 3dsMax in that will automatically
        load Toolkit and the tk-3dsmaxplus engine when 3dsMax starts.

        :param str exec_path: Path to 3dsMax executable to launch.
        :param str args: Command line arguments as strings.
        :param str file_to_open: (optional) Full path name of a file to open on launch.
        :returns: :class:`LaunchInformation` instance
        """
        required_env = {}

        startup_script_path = os.path.join(self.disk_location, "plugins", "basic", "bootstrap", "(zero-config)", "bootstrap.ms")
        args = "-U MAXScript %s" % startup_script_path

        # TODO: add support for file_to_open
        # TODO: handle Toolkit Classid mode

        return LaunchInformation(exec_path, args, required_env)

    def _synergy_software_versions(self, versions):
        """
        Creates SoftwareVersion instances based on the Synergy configuration
        data from Synergy Config (.syncfg) files found in the local environment.

        :param list versions: (optional) List of strings representing
                              versions to search for. If set to None,
                              search for all versions. A version string
                              is DCC-specific but could be something
                              like "2017", "6.3v7" or "1.2.3.52".
        :returns: List of :class:`SoftwareVersion` instances
        """
        # Get the list of Max*.syncfg files in the local environment
        configs = _synergy_config_files("Max")
        if not configs:
            self.logger.debug("Unable to determine Autodesk Synergy paths for %s platform." % sys.platform)
            return []
        self.logger.debug("Found (%d) Autodesk Synergy 3dsMax config files." % len(configs))

        # Determine the list of SoftwareVersion to return from the list
        # of configurations found and the list of versions requested.
        sw_versions = []
        for config in configs:
            self.logger.debug("Parsing Synergy config '%s' ..." % config)
            try:
                # Parse the Synergy Config file as XML
                doc = ElementTree.parse(config)
            except Exception, e:
                raise TankError(
                    "Caught exception attempting to parse [%s] as XML.\n%s" %
                    (config, e)
                )

            try:
                # Find the <Application> element that contains the data
                # we want.
                app_elem = doc.getroot().find("Application")
                if app_elem is None:
                    self.logger.warning(
                        "No <Application> found in Synergy config file '%s'." %
                        config
                    )
                    continue

                # Convert the element's attribute/value pairs to a dictionary
                synergy_data = dict(app_elem.items())
                self.logger.debug("Synergy data from config : %s" % synergy_data)
            except Exception, e:
                raise TankError(
                    "Caught unknown exception retrieving <Application> data "
                    "from %s:\n%s" % (config, e)
                )

            if versions and synergy_data["NumericVersion"] not in versions:
                # If this version isn't in the list of requested versions, skip it.
                self.logger.debug("Skipping 3dsMax Synergy version %s ..." %
                                  synergy_data["NumericVersion"]
                                  )
                continue

            exec_path = synergy_data.get("StartWrapperPath") or synergy_data["ExecutablePath"]

            if not self.is_version_supported(synergy_data["NumericVersion"]):
                self.logger.info(
                    "Found 3dsMax install in '%s' but only versions %s "
                    "and above are supported" % (exec_path, self.minimum_supported_version)
                )

            if not os.path.exists(exec_path):
                # someone has done a rogue uninstall and the synergy file
                # is there but there is no actual executable
                self.logger.debug("Synergy path '%s' does not exist on disk. Skipping." % exec_path)
                continue

            # Sometimes the Synergy StringVersion is a bit wordy.
            # Truncate non essential strings for the display name.
            synergy_name = None
            if synergy_data["Name"] and synergy_data["NumericVersion"]:
                synergy_name = "%s %s" % (synergy_data["Name"], synergy_data["NumericVersion"])
            elif synergy_data["StringVersion"]:
                synergy_name = str(synergy_data["StringVersion"]).replace("Autodesk", "").strip()

            # Create a SoftwareVersion from input and config data.
            self.logger.debug("Creating SoftwareVersion for '%s'" % exec_path)
            sw_versions.append(SoftwareVersion(
                synergy_data["NumericVersion"],
                synergy_name,
                exec_path,
                os.path.join(self.disk_location, "icon_256.png")
            ))

        return sw_versions

    def _get_installation_paths_from_registry(self):
        """
        Query Windows registry for 3dsMax installations.

        :returns: List of paths where 3dsmax is installed,
        """
        self.logger.debug("Querying windows registry for key HKEY_LOCAL_MACHINE\\SOFTWARE\\Autodesk\\3dsMax")

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
            self.logger.error("error opening key %s" % base_key_name)

        install_paths = []
        # Query the value "Installdir" on all subkeys.
        try:
            for name in sub_key_names:
                key_name = base_key_name + "\\" + name
                key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key_name)
                try:
                    install_paths.append(_winreg.QueryValueEx(key, "Installdir")[0])
                    self.logger.debug("found Installdir value for key %s" % key_name)
                except WindowsError:
                    self.logger.debug("value Installdir not found for key %s, skipping key" % key_name)
                _winreg.CloseKey(key)
        except WindowsError:
            self.logger.error("error opening key %s" % key_name)

        return install_paths

    def _default_path_software_versions(self, versions):
        """
        Creates SoftwareVersion instances based on the default installation path(s).

        :param list versions: (optional) List of strings representing
                              versions to search for. If set to None,
                              search for all versions. A version string
                              is DCC-specific but could be something
                              like "2017", "6.3v7" or "1.2.3.52"
        :returns: List of :class:`SoftwareVersion` instances
        """
        # Determine a list of paths to search for 3dsMax executables based
        # on the windows registry
        search_paths = self._get_installation_paths_from_registry()
        exec_paths = []

        if search_paths:
            for search_path in search_paths:
                # Construct the expected executable name for this path.
                # If it exists, add it to the list of exec_paths to check.
                exec_path = os.path.join(search_path, "3dsmax.exe")

                if os.path.exists(exec_path):
                    self.logger.debug("found version in default installation path %s" % exec_path)
                    exec_paths.append(exec_path)

        sw_versions = []
        if exec_paths:
            for exec_path in exec_paths:
                # Check to see if the version number can be parsed from the path name.
                path_sw_versions = [p.lower() for p in exec_path.split(os.path.sep)
                                    if re.match("3ds max [0-9]+[.0-9]*$", p.lower()) is not None
                                    ]
                if path_sw_versions:
                    # Use this sub dir to determine the default display name
                    # and version for the SoftwareVersion to be created.
                    default_display = path_sw_versions[0]
                    default_version = default_display.replace("3ds max ", "")
                    default_display = "3ds Max %s" % default_version
                    self.logger.debug(
                        "Resolved version '%s' from executable '%s'." %
                        (default_version, exec_path)
                    )

                if versions and default_version not in versions:
                    # If this version isn't in the list of requested versions, skip it.
                    self.logger.debug("Skipping Maya version %s ..." % default_version)
                    continue

                if not self.is_version_supported(default_version):
                    self.logger.info(
                        "Found 3dsMax install in '%s' but only versions %s "
                        "and above are supported" % (exec_path, self.minimum_supported_version)
                    )

                # Create a SoftwareVersion using the information from executable
                # path(s) found in default locations.
                self.logger.debug("Creating SoftwareVersion for executable '%s'." % exec_path)
                sw_versions.append(SoftwareVersion(
                    default_version,
                    default_display,
                    exec_path,
                    os.path.join(self.disk_location, "icon_256.png")
                ))

        return sw_versions


def _synergy_config_files(config_match=None):
    """
    Scans the local file system using a list of search paths for
    Autodesk Synergy Config files (.syncfg).

    :param str config_prefix: Substring resolved Synergy config
                              file should start with.
    :returns: List of path names to Synergy Config files found
              in the local environment
    """
    # Check for custom paths defined by the SYNHUB_CONFIG_PATH env var.
    env_paths = os.environ.get("SYNHUB_CONFIG_PATH")
    search_paths = []
    if isinstance(env_paths, basestring):
        # This can be a list of directories and/or files.
        search_paths = env_paths.split(os.pathsep)
    # Check the platfom-specific default installation path
    # if no paths were set in the environment
    else:
        search_paths = ["C:\\ProgramData\\Autodesk\\Synergy"]

    # Find the Synergy config files from the list of paths
    # to search. Filter by files that start with config_prefix
    # if specified.
    synergy_configs = []
    for search_path in search_paths:
        if os.path.isdir(search_path):
            for item in os.listdir(search_path):
                if not item.endswith(".syncfg"):
                    # Skip non Synergy config files
                    continue

                if config_match and config_match not in item:
                    # Skip Synergy config files that do not
                    # contain the requested string
                    continue

                # Found a matching Synergy config file
                synergy_configs.append(os.path.join(search_path, item))

        elif os.path.isfile(search_path):
            # Determine whether this search_path is a Synergy
            # config file and matches the specified config_prefix,
            # if requested.
            file_name = os.path.basename(search_path)
            if file_name.endswith(".syncfg"):
                if config_match:
                    if config_match in file_name:
                        synergy_configs.append(search_path)
                else:
                    synergy_configs.append(search_path)

    return synergy_configs
