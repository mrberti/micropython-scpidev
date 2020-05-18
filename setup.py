import sys
import re
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
# import sdist_upip

def readme():
    with open("README.md") as f:
        return f.read()

with open("scpidev/__init__.py") as f:
    init_text = f.read()

version = re.findall("__version__ = \"([^\"]*)\"", init_text)[0]
author = re.findall("__author__ = \"([^\"]*)\"", init_text)[0]

setup(
    name="micropython-scpidev",
    version=version,
    author=author,
    author_email="simon.bertling@gmx.de",
    description="A python package to turn your device into an SCPI instrument.",
    keywords="scpi measurement instrument",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/mrberti/micropython-scpidev",
    project_urls={
        "Documentation": "https://github.com/mrberti/micropython-scpidev",
        "Source": "https://github.com/mrberti/micropython-scpidev",
    },
    license="MIT",
    packages=["scpidev"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    ],
    # cmdclass={'sdist': sdist_upip.sdist},
    # py_modules=["scpidev"],
    # scripts=["bin/send_tcp.py"],
)
