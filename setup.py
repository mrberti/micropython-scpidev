from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='scpidev',
      version='0.0',
      description='A python package to turn your device into an SCPI end point',
      url='https://github.com/mrberti/pyscpidev',
      author='Simon Bertling',
      author_email='simon.bertling@gmx.de',
      license='NOne',
      packages=['scpidev'],
      zip_safe=False)