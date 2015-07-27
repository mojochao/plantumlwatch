'''plantumlwatch package setup script.'''

import os
from setuptools import setup

DESCRIPTION = '''An application to watch a directory for changes to PlantUML source files and 
generate UML diagrams from them.
'''

setup(
    name="plantumlwatch",
    version="1.0.0",
    author="Allen Gooch",
    author_email="allen.gooch@gmail.com",
    description=DESCRIPTION,
    license="BSD",
    keywords="uml",
    url="http://github.com/mojochao/plantumlwatch",
    py_modules=["plantumlwatch"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    entry_points={
        "console_scripts": [
            "plantumlwatch = plantumlwatch:main"
        ]
    }
)