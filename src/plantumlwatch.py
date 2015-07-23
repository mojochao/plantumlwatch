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


DESCRIPTION = """
Watches a directory for changes to PlantUML source files and generates
corresponding UML diagram image files on modification.  COMMAND may be
one of 'watch' or 'configure'.  The 'watch' command begins watching
for source file modifications.  The 'configure' command generates a
configuration file that may be used instead of providing options on
the command line.  If no COMMAND is provided, the default is 'watch'.
"""

CONFIG_FILENAME = '.plantumlwatch'

DEFAULT_CONFIG_FILE = os.path.join(os.getcwd(), CONFIG_FILENAME)
DEFAULT_VERBOSE = False
DEFAULT_JAVA = "java"
DEFAULT_PLANTUML = "plantuml.jar"
DEFAULT_WATCH_DIRECTORY = os.getcwd()
DEFAULT_WATCH_EXTENSION = "pu"
DEFAULT_OUTPUT_DIRECTORY = os.getcwd()
DEFAULT_OUTPUT_FORMAT = "png"

DEFAULT_CONFIG = {
    "verbose": DEFAULT_VERBOSE,
    "java": DEFAULT_JAVA,
    "plantuml": DEFAULT_PLANTUML,
    "watchdir": DEFAULT_WATCH_DIRECTORY,
    "extension": DEFAULT_WATCH_EXTENSION,
    "outputdir": DEFAULT_OUTPUT_DIRECTORY,
    "format": DEFAULT_OUTPUT_FORMAT
}

VALID_COMMANDS = ["watch", "configure"]
VALID_OUTPUT_FORMATS = ["png", "svg"]


def configuration(options):
    """Configuration object builder.

    Returns configuration object built from multiple configuration sources.

    A sample JSON configuration object looks like the following:

        {
            "verbose": false,
            "java": "/usr/local/bin/java",
            "plantuml": "~/lib/plantuml.8024.jar",
            "watchdir": ".",
            "extension": "*.pu",
            "outputdir": "~/myoutputdir",
            "format": "png"
        }

    The configuration object is built by loading these values from one of:
    1. the object deserialized from .plantumlwatch file in current working directory, if exists
    2. the object built from command line options and their defaults

    :param options: options passed on command line
    :type options: dict

    :returns: app configuration
    :rtype: dict

    """
    filename = options['config']
    if not os.path.isfile(filename):
        return options

    try:
        with open(filename) as infile:
            return json.load(infile)
    except ValueError as err:
        raise RuntimeError("configuration file '{}' is not a valid json file: {}".format(filename, err))


def configure(self):
    """Writes out a configuration file in current working directory."""
    if os.path.exists(CONFIG_FILENAME):
        print("configuration file exists: {}")
        return

    with open(CONFIG_FILENAME, "w") as outfile:
        json.dump(outfile, DEFAULT_CONFIG)
    print("wrote configuration file: {}".format(os.path.abspath(CONFIG_FILENAME)))


class WatcherFileChangeHandler(FileSystemEventHandler):
    """Handler class generating diagrams for PlantUML source file modifications."""

    def __init__(self, watcher):
        """Initializes new PlantUmlFileHandler object.

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


class Watcher(object):

    def __init__(self, config):
        """Initializes a new Watcher object.

        Watchers are responsible for configuring themselves, and when run
        watching those files for changes and generating new output.

        The *config* dict looks like the following:

        {
            "verbose": false,
            "java": "/usr/local/bin/java",
            "plantuml": "~/lib/plantuml.8024.jar",
            "watchdir": ".",
            "extension": "*.pu",
            "outputdir": "~/myoutputdir",
            "format": "png"
        }

        :param config: configuration object
        :type config: dict

        """
        self._configuration = config
        if not os.path.isfile(self.java):
            raise RuntimeError("cannot find Java Virtual Machine binary file '{}'".format(self.java))
        if not os.path.isfile(self.plantuml):
            raise RuntimeError("cannot find PlantUML jar file '{}'".format(self.plantuml))
        if not os.path.isdir(self.watchdir):
            raise RuntimeError("cannot find watch directory '{}'".format(self.watchdir))
        if not os.path.isdir(self.outputdir):
            raise RuntimeError("cannot find output directory '{}'".format(self.outputdir))
        if self.format not in VALID_OUTPUT_FORMATS:
            raise RuntimeError("cannot handle output format '{}'".format(self.format))

    @property
    def verbose(self):
        return self._configuration["verbose"] if "verbose" in self._configuration else DEFAULT_VERBOSE

    @property
    def java(self):
        return self._configuration["java"] if "java" in self._configuration else DEFAULT_JAVA

    @property
    def plantuml(self):
        return self._configuration["plantuml"] if "plantuml" in self._configuration else DEFAULT_PLANTUML

    @property
    def watchdir(self):
        return self._configuration["watchdir"] if "watchdir" in self._configuration else DEFAULT_WATCH_DIRECTORY

    @property
    def extension(self):
        return self._configuration["extension"] if "extension" in self._configuration else DEFAULT_WATCH_EXTENSION

    @property
    def outputdir(self):
        return self._configuration["outputdir"] if "outputdir" in self._configuration else DEFAULT_OUTPUT_DIRECTORY

    @property
    def format(self):
        return self._configuration["format"] if "format" in self._configuration else DEFAULT_OUTPUT_FORMAT

    def watch(self):
        """Watch PlantUML files in configuration directories for modifications."""
        # Let the user know what's up.
        print("watching directory {} for files with extension '{}'".format(self.watchdir, self.extension))
        if self.verbose:
            print("using plantuml: {}".format(self.plantuml))

        # Set up the watcher and wait on file modifications.
        event_handler = WatcherFileChangeHandler(self)
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
    parser = argparse.ArgumentParser(usage="%(prog)s [OPTIONS] COMMAND", description=DESCRIPTION)
    parser.add_argument("-c", "--config",
                        default=DEFAULT_CONFIG_FILE,
                        help="configuration file to use. defaults to '{}'.".format(DEFAULT_CONFIG_FILE),
                        metavar="FILE")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="enable verbose output. defaults to '{}'.".format(DEFAULT_VERBOSE))
    parser.add_argument("-j", "--java",
                        default=DEFAULT_JAVA,
                        help="java jvm to use. defaults to '{}'.".format(DEFAULT_JAVA),
                        metavar="FILE")
    parser.add_argument("-p", "--plantuml",
                        default=DEFAULT_PLANTUML,
                        help="plantuml jarfile to use. defaults to '{}'.".format(DEFAULT_PLANTUML),
                        metavar="FILE")
    parser.add_argument("-w", "--watchdir",
                        default=DEFAULT_WATCH_DIRECTORY,
                        help="directory to watch. defaults to current working directory.",
                        metavar="PATH")
    parser.add_argument("-e", "--extension",
                        default=DEFAULT_WATCH_EXTENSION,
                        help="extension of files to watch. defaults to '{}'.".format(DEFAULT_WATCH_EXTENSION),
                        metavar="PATH")
    parser.add_argument("-o", "--outputdir",
                        default=DEFAULT_OUTPUT_DIRECTORY,
                        help="directory to write output to. defaults to current working directory.",
                        metavar="PATH")
    parser.add_argument("-f", "--format",
                        default=DEFAULT_OUTPUT_FORMAT,
                        choices=VALID_OUTPUT_FORMATS,
                        help="output format to emit. valid values include {}. defaults to '{}'.".format(VALID_OUTPUT_FORMATS, DEFAULT_OUTPUT_FORMAT),
                        metavar="FORMAT")
    args, commands = parser.parse_known_args()
    if not commands:
        commands = ["watch"]

    # Configure and run the watcher.
    try:
        if not commands or len(commands) > 1 or commands[0] not in VALID_COMMANDS:
            parser.print_help()
        elif commands[0] == "watch":
            config = configuration(vars(args))
            watcher = Watcher(config)
            watcher.watch()
        elif commands[0] == "configure":
            configure()
    except Exception as err:
        sys.exit("error: {}".format(err))


if __name__ == "__main__":
    main()
