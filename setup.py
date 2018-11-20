from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='scpidev',
    version='0.0.0',
    author='Simon Bertling',
    author_email='simon.bertling@gmx.de',
    description='A python package to turn your device into an SCPI end point',
    long_description=readme(),
    long_description_content_type="text/markdown",
    url='https://github.com/mrberti/pyscpidev',
    license='MIT',
    packages=['scpidev'],
    #zip_safe=False,
)
