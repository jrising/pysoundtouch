pysoundtouch
============

Python Wrapper for the SoundTouch Library

Installation
------------

First compile and install SoundTouch using integer samples.

To compile on Linux and MacOS:

(may need to get autoconf, libtool; delete config/m4/*)
./bootstap
./configure --enable-integer-samples CXXFLAGS="-fPIC"
make
sudo make install

Then, run setup.py

sudo python setup.py install

Finally, check that you can import soundtouch

>>> import soundtouch
>>> soundtouch.__version__
'1.4.0'
