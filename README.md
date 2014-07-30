pysoundtouch
============

Python Wrapper for the SoundTouch Library

SoundTouch is a library for changing the pitch and tempo of audio
files and detecting beat rates.  See the website at
http://www.surina.net/soundtouch/

This module exposes the pitch shifting and beat detection algorithms
in SoundTouch to Python.

Installation
------------

First compile and install SoundTouch using integer samples.

To compile on Linux and MacOS:

You may need to get autoconf and libtool and delete config/m4/*.

```
./bootstap
./configure --enable-integer-samples CXXFLAGS="-fPIC"
make
sudo make install
```

Then, run setup.py

```
sudo python setup.py install
```

Finally, check that you can import soundtouch

```
>>> import soundtouch
>>> soundtouch.__version__
'1.4.0'
```