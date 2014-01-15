'''plantumlwatch package setup script.'''

import os
from setuptools import setup

DESCRIPTION = '''An application to watch a directory for changes to PlantUML source files and 
generate UML diagrams from them.
'''

setup(
    name="plantumlwatch",
    version="0.0.1",
    author="Allen Gooch",
    author_email="allen.gooch@gmail.com",
    description=DESCRIPTION,
    long_description=open(os.path.join(os.path.dirname(__file__), "README.md")).read(),
    license="BSD",
    keywords="uml",
    url="http://github.com/mojochao/plantumlwatch",
    scripts=['plantumlwatch.py'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)