"""
This module provides capabilities for watching directories for changes to
PlantUML source files generate image output, when modified.

This module works with Python 2.7 or greater, and additionally requires
the watchdog package available from the Python Package index.

Author: Allen Gooch

"""

from __future__ import print_function
import argparse
import json
import os
import subprocess
import sys
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


CONFIGURATION_FILE_NAME = '.plantumlwatch'

DESCRIPTION = """
Watches a directory for changes to PlantUML source files with a *.pu
extension and generate corresponding UML diagram image files, either in PNG
or SVG format, when modified.
"""

DEFAULT_VERBOSE = False
DEFAULT_JAVA = "java"
DEFAULT_PLANTUML = "plantuml"
DEFAULT_WATCH_DIRECTORY = os.getcwd()
DEFAULT_WATCH_EXTENSION = "pu"
DEFAULT_OUTPUT_DIRECTORY = os.getcwd()
DEFAULT_OUTPUT_FORMAT = "png"

DEFAULT_CONFIGURATION = {
    "verbose": DEFAULT_VERBOSE,
    "java": DEFAULT_JAVA,
    "plantuml": DEFAULT_PLANTUML,
    "watchdir": os.getcwd(),
    "extension": DEFAULT_WATCH_EXTENSION,
    "outputdir": os.getcwd(),
    "format": DEFAULT_OUTPUT_FORMAT
}

VALID_OUTPUT_FORMATS = ["png", "svg"]


class PlantUmlFileModifiedHandler(FileSystemEventHandler):
    """Handler class for PlantUML source file modifications.
    
    This handler generates UML diagrams on PlantUML source file modifications.
    
    """
    
    def __init__(self, watcher):
        """Initialize new PlantUmlFileHandler object.
        
        :param watcher: Watcher associated with this file modification handler
        :type watcher: :class:`plantumlwatch.Watcher`

        """
        self._watcher = watcher

    def plantuml_command(self, filename):
        """PlantUML command builder.

        :param filename: filename of input file to generate image for
        :type filename: str

        :returns: PlantUML command line to generate image for *filename*
        :rtype: string
        
        """
        return "{java} -jar {plantuml} {verbose} {format} {srcfile}".format(
            java=self._watcher.java,
            plantuml=self._watcher.plantuml,
            verbose="-v" if self._watcher.verbose else "",
            format="-t{}".format(self._watcher.format),
            srcfile=filename)
        
    def on_modified(self, event):
        """File modification event handler.
        
        Generates new diagrams if file modified is a PlantUML source file.
        
        :param event: watchdog file modification event
        :type event: :class:`watchdog.events.FileModifiedEvent`

        """
        filename = event.src_path
        extension = "." + self._watcher.extension
        if filename.endswith(extension):
            srcfile = os.path.join(self._watcher.outputdir, filename)
            print("processing model source: {}".format(srcfile))
            try:
                exit_code = subprocess.call(self.plantuml_command(filename))
                if exit_code == 0:
                    genfile = filename.replace(extension, ".{}".format(self._watcher.format))
                    print("generated model diagram: {}".format(genfile))
                else:
                    print("error: exit code {} processing file {}".format(exit_code, filename))
            except OSError as err:
                print("error: {}".format(err))


class Configurator(object):
    """Application configurator.

    This class is responsible for generating Watcher configurations.
    A Watcher configuration is a nested dictionary structure, persisted as
    JSON objects.

    A sample JSON configuration object might look like the following:

    {
        "verbose": false,
        "java": "/usr/local/bin/java",
        "plantuml": "~/lib/plantuml.8024.jar",
        "watchdir": ".",
        "extension": "*.pu",
        "outputdir": "~/myoutputdir",
        "format": "png"
    }

    The configuration object is built by successively loading these values from:
    1. the default object
    2. the object deserialized from user's home .plantumlwatch file, if exists
    3. the object deserialized from .plantumlwatch file in current working directory, if exists
    4. the object built from command line options

    """

    def __init__(self, argopts=None):
        """Initializes a new Configurator object.

        :param argopts: arguments passed on command line
        :type argopts: dict

        """
        # Start by basing our configuration on defaults.
        configuration = dict(DEFAULT_CONFIGURATION)

        # Update our configuration based on the user"s global configuration in home directory
        # and any local configuration in current working directory
        config_filenames = [
            os.path.expanduser("~/{}".format(CONFIGURATION_FILE_NAME)),
            os.path.abspath("./{}".format(CONFIGURATION_FILE_NAME))
        ]
        for filename in config_filenames:
            if os.path.isfile(filename):
                try:
                    with open(filename) as infile:
                        global_configuration = json.load(infile)
                    configuration.update(global_configuration)
                except ValueError as err:
                    raise RuntimeError("configuration file {} is not a valid json file: {}".format(filename, err))

        # Update with any options passed on command line
        if argopts is not None:
            configuration.update(argopts)

        # We're done
        self._configuration = configuration

    @property
    def configuration(self):
        """Configuration accessor.

        :returns: app configuration
        :rtype: dict

        """
        return self._configuration


class Watcher(object):

    def __init__(self, configuration):
        """Initializes a new Watcher object.

        Watchers are responsible for configuring themselves, and when run
        watching those files for changes and generating new output.

        :param configuration: configuration object
        :type configuration: dict

        """

        self._configuration = configuration
        if not os.path.isfile(self.java):
            raise RuntimeError("cannot find Java Virtual Machine binary '{}'".format(self.java))
        if not os.path.isfile(self.plantuml):
            raise RuntimeError("cannot find PlantUML Jar '{}'".format(self.plantuml))
        if not os.path.isdir(self.watchdir):
            raise RuntimeError("cannot find watch directory '{}'".format(self.watchdir))
        if not os.path.isdir(self.outputdir):
            raise RuntimeError("cannot find output directory '{}'".format(self.outputdir))
        if self.format not in VALID_OUTPUT_FORMATS:
            raise RuntimeError("cannot handle output format '{}'".format(self.format))

    @property
    def verbose(self):
        return self._configuration["verbose"]

    @property
    def java(self):
        return self._configuration["java"]

    @property
    def plantuml(self):
        return self._configuration["plantuml"]

    @property
    def watchdir(self):
        return self._configuration["watchdir"]

    @property
    def extension(self):
        return self._configuration["extension"]

    @property
    def outputdir(self):
        return self._configuration["outputdir"]

    @property
    def format(self):
        return self._configuration["format"]

    def run(self):
        """Watch PlantUML files in configuration directories for modifications."""

        # Let the user know what's up.
        print("watching directory {} for files with extension '{}'".format(self.watchdir, self.extension))
        if self.verbose:
            print("using plantuml: {}".format(self.plantuml))

        # Set up the watcher and wait on file modifications.
        event_handler = PlantUmlFileModifiedHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=self.watchdir)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


def main():
    """main entrypoint."""

    # Configure the arguments parser and parse them from the command line arguments.
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="enable verbose output")
    parser.add_argument("-j", "--java",
                        default=DEFAULT_JAVA,
                        help="java jvm to use. defaults to 'java' in your path",
                        metavar="JVM")
    parser.add_argument("-p", "--plantuml",
                        default=DEFAULT_PLANTUML,
                        help="plantuml jarfile to use. defaults to 'plantuml.jar' in your current working directory",
                        metavar="JAR")
    parser.add_argument("-w", "--watchdir",
                        default=DEFAULT_WATCH_DIRECTORY,
                        help="directory to watch",
                        metavar="PATH")
    parser.add_argument("-e", "--extension",
                        default=DEFAULT_WATCH_EXTENSION,
                        help="directory to watch",
                        metavar="PATH")
    parser.add_argument("-o", "--outputdir",
                        default=DEFAULT_OUTPUT_DIRECTORY,
                        help="directory to watch",
                        metavar="PATH")
    parser.add_argument("-f", "--format",
                        default=DEFAULT_OUTPUT_FORMAT,
                        choices=VALID_OUTPUT_FORMATS,
                        help="diagram output format, either 'png' or 'svg'. defaults to 'png'",
                        metavar="FORMAT")
    args = vars(parser.parse_args())

    # Configure and run the watcher.
    try:
        configurator = Configurator(args)
        watcher = Watcher(configurator.configuration)
        watcher.run()
    except Exception as err:
        sys.exit("error: {}".format(err))


if __name__ == "__main__":
    main()
