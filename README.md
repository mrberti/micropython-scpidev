# pyscpidev
A python package to turn your device into an SCPI instrument.

## Concept
This package intends to make it easy for developers to turn any device that 
can run python(3) and has some kind of communication interface, e.g. serial or 
Ethernet, into an SCPI instrument. SCPI commands look like 
```
MEASure:VOLTage?
CONFigure[:VOLTage][:DC] [{<range>|AUTO|MIN|MAX|DEF}]
```

### Short Term Plan
Get the basic stuff running...

### Mid Term Plan
Implement some samples for RaspberryPi.

### Long Term Plan
Implement a web application to be able to serve HTTP requests and show some 
nice GUI.

## Installation
I intend to publish this package on PyPi. For now you need to download the 
code and run the following command from the root directory.

```python
python3 -m pip install -e .
```

## Usage
```python
import scpidev
```

## Further Reads
* [Wikipedia](https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments)
* [The SCPI specification](http://www.ivifoundation.org/docs/scpi-99.pdf)
