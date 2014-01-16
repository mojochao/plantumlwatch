''' 
Script to watch a directory for changes to PlantUML source files with a *.pu
extension and generate corresponding UML diagram image files, either in PNG
or SVG format, when modified.

This script works with any Python 2.7 or greater, and additionally requires
the watchdog package available from the Python Package index.

'''
from __future__ import print_function
import argparse
import os
import subprocess
import sys
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


DESCRIPTION = '''
Watches a directory for changes to PlantUML source files with a *.pu
extension and generate corresponding UML diagram image files, either in PNG
or SVG format, when modified.
'''
VALID_OUTPUT_FORMATS = ['png', 'svg']
DEFAULT_OUTPUT_FORMAT = VALID_OUTPUT_FORMATS[0]
DEFAULT_DIRECTORY = os.getcwd()
DEFAULT_JAVA_JVM = 'java'
DEFAULT_PLANTUML_JAR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dist', 'plantuml.jar'))
if not os.path.exists(DEFAULT_PLANTUML_JAR):
    DEFAULT_PLANTUML_JAR = os.path.abspath(os.path.join(os.path.expanduser('~'), 'plantuml.jar'))
PLANTUML_SOURCE_FILE_EXT = '.pu'


class PlantUmlFileModifiedHandler(FileSystemEventHandler):
    '''Handler class for PlantUML source file modifications.
    
    This handler generates UML diagrams on PlantUML source file modifications.
    
    '''
    
    def __init__(self, directory, verbose, output, java, plantuml):
        '''Initialize new PlantUmlFileHandler object.
        
        :param directory: path of directory to watch for PlantUML source file changes
        :type directory: str
        
        :param verbose: enable verbose output when generating diagrams with PlantUML
        :type verbose: bool
        
        :param output: output format, either 'png' or 'svg', to use when generating diagrams with PlantUML
        :type output: str
        
        :param java: path to Java JVM to use when executing PlantUML
        :type java: str
        
        :param plantuml: path PlantUML JAR file to use when executing PlantUML
        :type plantuml: str
        
        '''
        self.directory = directory
        self.verbose = verbose
        self.output = output
        self.java = java
        self.plantuml = plantuml
    
    def plantuml_command(self, filename):
        '''PlantUML command property.
        
        :rtype: string
        
        '''
        return '{java} -jar {plantuml} {verbose} {output} {srcfile}'.format(java=self.java, plantuml=self.plantuml, verbose='-v' if self.verbose else '', output='-t{0}'.format(self.output), srcfile=filename) 
        
    def on_modified(self, event):
        '''File modification event handler.
        
        Generates new diagrams if file modified is a PlantUML source file.
        
        :param event: watchdog file modification event
        :type event: :class:`watchdog.events.FileModifiedEvent`

        '''
        filename = event.src_path
        if filename.endswith(PLANTUML_SOURCE_FILE_EXT):
            print('processing model source: {0}'.format(os.path.join(self.directory, filename)))
            try:
                exit_code = subprocess.call(self.plantuml_command(filename))
                if exit_code == 0:
                    print('generated model diagram: {0}'.format(filename.replace(PLANTUML_SOURCE_FILE_EXT, '.{0}'.format(self.output))))
                else:
                    print('error: exit code {0} processing file {1}'.format(exit_code, filename))
            except OSError as err:
                print('error: {0}'.format(err))


def watch(directory='.', verbose=False, output=DEFAULT_OUTPUT_FORMAT, java=DEFAULT_JAVA_JVM, plantuml=DEFAULT_PLANTUML_JAR):
    '''Watch PlantUML files in current working directory for modifications.
    
    :param directory: path of directory to watch for PlantUML source file changes
    :type directory: str
    
    :param verbose: enable verbose output when generating diagrams with PlantUML
    :type verbose: bool
    
    :param output: output format, either 'png' or 'svg', to use when generating diagrams with PlantUML
    :type output: str
    
    :param java: path to Java JVM to use when executing PlantUML
    :type java: str
    
    :param plantuml: path PlantUML JAR file to use when executing PlantUML
    :type plantuml: str
    
    '''
    directory = os.path.abspath(directory)
    if not os.path.exists(directory):
        print('error: cannot find directory: {0}\nexiting'.format(directory))
        sys.exit(1)
        
    if not os.path.exists(plantuml):
        print('error: cannot find file: {0}\nexiting'.format(plantuml))
        sys.exit(1)
    
    print('watching directory: {0}'.format(directory))
    if verbose:
        print('using plantuml jar: {0}'.format(plantuml))
    
    event_handler = PlantUmlFileModifiedHandler(directory, verbose, output, java, plantuml)
    observer = Observer()
    observer.schedule(event_handler, path=directory)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    '''plantumlwatch module main entrypoint.'''    
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-d', '--directory', default=DEFAULT_DIRECTORY, help='directory to watch', metavar='PATH')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose output')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT_FORMAT, choices=VALID_OUTPUT_FORMATS, help='diagram output format, either "png" or "svg". defaults to "png"', metavar='FORMAT')
    parser.add_argument('-j', '--java', default=DEFAULT_JAVA_JVM, help='java jvm to use. defaults to "java" in your path', metavar='JVM')
    parser.add_argument('-p', '--plantuml', default=DEFAULT_PLANTUML_JAR, help='plantuml jarfile to use. defaults to "plantuml.jar" in your home directory', metavar='JAR')
    args = vars(parser.parse_args())
    watch(**args)
