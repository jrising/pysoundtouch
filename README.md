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

You may need to get autoconf and libtool.

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

Simple Examples
---------------

To use the library directly, audio must already be in an uncompressed, 2-byte-per-sample format.  For all other audio files, see the AudioReader Tool and Shifter Tool sections below.

Detecting the BPM of a .WAV file:

```
import wave
# Open a .WAV file
wf = wave.open(FILEPATH)

# Create the BPMDetect object
bd = soundtouch.BPMDetect(wf.getframerate(), wf.getnchannels())

# Feed samples from the file into BPMDetect
while True:
    buf = wf.readframes(4000)
    if not buf:
        break

    bd.put_samples(buf)

# Clean up
wf.close()
print bd.get_bpm()
```

Shifting the pitch of a .WAV file:

```
import wave
# Open a .WAV file
wf = wave.open(FILEPATH)

# Create the SoundTouch object
st = soundtouch.SoundTouch(wf.getframerate(), wf.getnchannels())
# Specify the shift, as 1 whole step
st.set_pitch_shift(2)

# Feed in samples and add processed samples to resstr
resstr = ""
while True:
    buf = wf.readframes(4000)
    if not buf:
        break

    st.put_samples(buf)
    while st.ready_count() > 0:
        resstr += st.get_samples(4000)

# Flush any additional samples
waiting = st.waiting_count()
ready = st.ready_count()
flushed = ""

# Add silence until another chunk is pushed out
silence = array('h', [0] * 64)
while st.ready_count() == ready:
    st.put_samples(silence)

# Get all of the additional samples
while st.ready_count() > 0:
    flushed += st.get_samples(4000)

st.clear()

if len(flushed) > 2 * wf.getnchannels() * waiting:
    flushed = flushed[0:(2 * wf.getnchannels() * waiting)]

resstr += flushed

# Clean up
wf.close()
del st
```

AudioReader Tool
----------------

AudioReader is an abstraction around the audio handling tools in python, to make it easier to handle audio from many different formats.

Currently MP3, WAV, AIF, and AU files are supported.

All subclasses of AudioReader override the following methods:

* sampling_rate(): Return the samples (frames) per second.
* duration(): Return the duration in ms.
* current_time(): Return the current time in ms.
* seek_time(time): Set the read pointer to the specified time (in ms).
* raw_width(): Return the width in bytes of raw samples.
* raw_read(): Return some amount of data as a raw audio string.
* has_unsigned_singles(): Is the raw data when this has a width of 1 stored in unsigned bytes (but not for higher widths).
* read(): Return some number of frames of an channel-interleaved array (len = NxC) of the appropriate sample depth.
* close(): Perform any necessary cleanup on deallocation.

In addition, the following methods are provided based on these:
* random_read(start, end): Return the frames between start and end
* continue_read(end): Continue reading from the current read head.
* length_read(lenout): Read a given number of samples, by repeated calls to read().
* raw_random_read(start, end): Return the raw samples between start and end
* audio_to_image(filename, width, height): Construct a graph of the samples and save to filepath.

Use the AudioReader.open(filepath) method to get a reader object:

```
from ReadAudio import AudioReader

reader = AudioReader.open("mysong.mp3")
print reader.duration()
```

In addition, AudioReader classes can be used to transparently make changes to audio.  The following classes are provided:
* ConvertReader(source, set_channels=None, set_sampling_rate=None, set_raw_width=None): Convert the samples from one AudioReader into another format, changing the number of channels, sampling rate, and/or raw byte width.
* ScaleReader(source, scale=1.0, bias=0): Scale the audio (volume) in an AudioReader; scale is > 1 to increase volume; bias is inaudible but can be changed to remove clicks.
* AppendReader(one_path, two_path): Concatenate two audio files; the second will be converted to have the same format as the first.

Shifter Tool
------------

The Shifter class provides a set of tools for using SoundTouch with the AudioReader system.

Tools for Shifting Audio
* shift_chunk(chunk, sampling_rate, channels, shift): Shift the pitch of a chunk of audio up or down
* many_shift_chunk(chunk, sampling_rate, channels, shifts): Produce harmonies by shifting a chunk of audio more than once and combining them.
* raw_shift_reader(srcpath, dstpath, shift): Shift an entire file up or down

Example:

```
raw_shift_reader("mysong.mp3", "shifted_mysong.wav", 2)
```

Note that raw_shift_reader always produces a .WAV file.

Tools for detected beats:
* bpm_detect_file(fullpath): Detect the beat from an entire file
* beats_to_ms(bpm, beats): Convert from bpm at a given beat rate to ms between beats.

Other SoundTouch tools
* get_flush(st, channels, fade=0): Get all additional chunks, and optionally fade out the volume on these samples.
* echocancel(outputdata, inputdata): Try to identify an echo and remove it.
* find_division_start(fullpath, bpm, beats_per): Identify the start of the beats, by finding segments that fit together
