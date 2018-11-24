from setuptools import setup

def readme():
    with open("README.md") as f:
        return f.read()

setup(
    name="scpidev",
    version="0.0.1a1",
    author="Simon Bertling",
    author_email="simon.bertling@gmx.de",
    description="A python package to turn your device into an SCPI instrument.",
    keywords="scpi measurement instrument",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/mrberti/pyscpidev",
    project_urls={
        "Documentation": "https://github.com/mrberti/pyscpidev",
        "Source": "https://github.com/mrberti/pyscpidev",
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
    scripts=["bin/send_tcp.py"],
)
