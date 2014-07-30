""" Notes for audiere:
Poor documentation, no easy_install

# Supports WAV, AIFF, OGG, FLAC, MP3, MOD, S3M, IT, XM
# See http://audiere.sourceforge.net/features.php
"""
""" Notes for audiolib:
from scikits.audiolab import Sndfile

    # Try audiolib (Supports WAV, AIFF, SND, RAW, RAF, SVX, SF, VOC, W64, MAT, PVg, X1, HTK, CAF, SD2, FLAC, and OGG)
    # See http://www.mega-nerd.com/libsndfile/#Features for full information
    # Docs at http://www.ar.media.kyoto-u.ac.jp/members/david/softwares/audiolab/sphinx/index.html
    try:
        sndfile = Sndfile(filepath)
        sndfile.read_frames(44100*60*60)
"""
""" Notes for PyMusic:
Could not install ALSA, so PyMusic would not compile
"""

import mad, wave, aifc, sunau, time
import Image, ImageDraw, math
from array import array
import audioop

class AudioReader:
    @staticmethod
    def open(filepath):
        reader = AudioReader.reader(filepath)
        if not reader:
            return None
        return reader(filepath)

    @staticmethod
    def reader(filepath):
        filelow = filepath.lower()
        if filelow.endswith('.mp3'):
            return MP3Reader
        if filelow.endswith('.wav') or filelow.endswith('.aif') or filelow.endswith('.aiff') or filelow.endswith('.au'):
            return PCMReader
        return None

    def __init__(self, filepath):
        self.filepath = filepath
        self.eof = False
        self.leftovers = [] # leftovers from random_read/continue_read

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def sampling_rate(self):
        """Return the samples (frames) per second"""
        return 0

    def duration(self):
        """Return the duration in ms"""
        return 0        

    def current_time(self):
        """Return the current time in ms"""
        return 0

    def seek_time(self, time):
        """Set the read pointer to the specified time (in ms)"""
        pass

    def raw_width(self):
        """Return the width in bytes of raw samples"""
        pass

    def raw_read(self):
        """Return some amount of data as a raw audio string"""
        pass

    def has_unsigned_singles(self):
        """Is the raw data when this has a width of 1 stored in unsigned bytes (but not for higher widths)"""
        return False

    def read(self):
        """Return some number of frames of an channel-interleaved array (len = NxC) of the appropriate sample depth"""
        pass

    def close(self):
        pass

    def random_read(self, start, end, debugs=None):
        """Return the frames between start and end"""
        if self.current_time != start:
            self.seek_time(start)
        lenout = int((end - start) * self.sampling_rate() / 1000.0) * self.channels()
        return self.length_read(lenout, debugs)

    def continue_read(self, end, debugs=None):
        if debugs is not None:
            debugs.append("Continue from " + str(len(self.leftovers)) + " + " + str(self.current_time()) + " to " + str(end))
        if self.leftovers:
            leftovers = self.leftovers
            self.leftovers = []

            lenout = int((end - (self.current_time() - (len(leftovers) / self.channels()) * 1000.0 / self.sampling_rate())) * self.sampling_rate() / 1000.0) * self.channels() - len(leftovers)
            
            after = self.length_read(lenout, debugs)
            result = array(after.typecode)
            result.extend(leftovers)
            result.extend(after)

            return result
        else:
            return self.random_read(self.current_time(), end, debugs)

    def length_read(self, lenout, debugs=None):
        result = self.read()
        if result is None:
            return None
        while len(result) < lenout:
            data = self.read()
            if data is None:
                break
            result.extend(data)

        if len(result) > lenout:
            self.leftovers = result[lenout:]
            result = result[:lenout]
        else:
            self.leftovers = []

        if debugs is not None:
            debugs.append("length_read: Got " + str(lenout) + " at " + str(self.current_time()))

        return result

    def raw_random_read(self, start, end):
        """Return the raw samples between start and end
        XXX: Consider converting to random_read-style length-based limiter"""
        self.seek_time(start)
        result = self.raw_read()
        if result is None:
            return None
        before = self.current_time()
        if before > end:
            fraction = ((end - start) / (before - start)) / (self.raw_width() * self.channels())
            result = result[:(self.raw_width() * self.channels()) * int(fraction * len(result))]
            return result
        
        while before < end:
            data = self.raw_read()
            if data is None:
                break
            after = self.current_time()
            if after > end:
                fraction = ((end - before) / (after - before)) / (self.raw_width() * self.channels())
                data = data[:(self.raw_width() * self.channels()) * int(fraction * len(data))]

            result += data
            before = after

        return result

    def audio_to_image(self, filepath, width, height, divisor=0, dividers=None, start=0, end=None):
        if (end is None):
            end = self.duration()

        if (start > 0):
            self.seek_time(start)
            lastRecorded = self.current_time()
        else:
            self.seek_time(0)
            lastRecorded = start

        time0 = time.clock()
        
        ticksPerPixel = (end - start) / float(width)
        maxEnergy = 0
        pointsAbove = [0, height/2] # Use for left channel
        pointsBelow = [] # Use for right channel
        while lastRecorded < 0:
            pointsAbove.append(len(pointsAbove) / 2)
            pointsAbove.append(height / 2 + 1)
            pointsBelow.append(height / 2)
            pointsBelow.append(len(pointsBelow) / 2)
            lastRecorded += ticksPerPixel

        while time.clock() - time0 < 10 and self.current_time() < end:
            data = self.read()
            if data is None:
                break
            if divisor == 0:
                divisor = pow(256, data.itemsize) / (2*math.sqrt(2))

            startLoop = lastRecorded
            while self.current_time() > lastRecorded + ticksPerPixel and lastRecorded < end:
                pixel = len(pointsAbove) / 2
                segment = data[(self.channels() * int((lastRecorded - startLoop) * self.sampling_rate() / 1000.0)):(self.channels() * int((lastRecorded - startLoop + ticksPerPixel) * self.sampling_rate() / 1000.0))]
                energyLeft = 0
                energyRight = 0
                for ii in range(len(segment) / self.channels()):
                    energyLeft += abs(segment[ii * self.channels()])
                    if self.channels() == 1:
                        energyRight += abs(segment[ii])
                    else:
                        energyRight += abs(segment[ii * self.channels() + 1])

                if len(segment) > 0:
                    energyLeft *= float(self.channels()) / len(segment)
                    energyRight *= float(self.channels()) / len(segment)

                if energyLeft / divisor > .5:
                    divisor = 2 * energyLeft
                if energyRight / divisor > .5:
                    divisor = 2 * energyRight
                maxEnergy = max(maxEnergy, energyLeft, energyRight)

                pointsAbove.append(len(pointsAbove) / 2)
                pointsAbove.append(height / 2 - height * energyLeft / divisor)
                pointsBelow.append(height / 2 + height * energyRight  / divisor)
                pointsBelow.append(len(pointsBelow) / 2)
                lastRecorded += ticksPerPixel
            lastRecorded = (len(pointsAbove) / 2) * ticksPerPixel + start

        if maxEnergy < divisor / 3 and maxEnergy > 0:
            # Try again, with a lower divisor
            reader = AudioReader.open(self.filepath)
            if reader:
                return reader.audio_to_image(filepath, width, height, divisor=2 * maxEnergy, dividers=dividers, start=start, end=end)

        pointsAbove.append(width)
        pointsAbove.append(height / 2)
        image = Image.new("RGB", (width, height), "Black")
        draw = ImageDraw.Draw(image)
        pointsBelow.reverse()
        pointsAbove.extend(pointsBelow)
        draw.polygon(pointsAbove, fill="Blue")

        print lastRecorded

        if dividers:
            for ii in xrange(len(dividers)):
                draw.line([(width * dividers[ii] * 1000.0 / self.duration(), 0),
                           (width * dividers[ii] * 1000.0 / self.duration(), height)], fill="Red")

        del draw

        print(filepath)
        out = open(filepath, "w")
        image.save(out, "PNG")
        return maxEnergy

class MP3Reader(AudioReader):
    def __init__(self, filepath):
        AudioReader.__init__(self, filepath)
        self.mf = mad.MadFile(filepath)

    def channels(self):
        return 2

    def sampling_rate(self):
        return self.mf.samplerate()

    def duration(self):
        return self.mf.total_time()

    def current_time(self):
        return self.mf.current_time()        

    def seek_time(self, time):
        """Set the read pointer to the specified time (in ms)"""
        self.mf.seek_time(time)

    def raw_width(self):
        """Return the width in bytes of raw samples"""
        return 2

    def raw_read(self):
        """Return some amount of data as a raw audio string"""
        buf = self.mf.read()
        if buf is None:
            self.eof = True
            return None

        return buf

    def read(self):
        buf = self.raw_read()
        if not buf:
            return None
        
        short_array = array('h')
        short_array.fromstring(buf)
        return short_array

    def close(self):
        del self.mf

class PCMReader(AudioReader):    
    def __init__(self, filepath):
        AudioReader.__init__(self, filepath)
        if filepath.lower().endswith(".aif") or filepath.lower().endswith(".aiff"):
            self.wf = aiff.open(self.filepath)
        elif filepath.lower().endswith('.au'):
            self.wf = sunau.open(self.filepath)
        else:
            self.wf = wave.open(self.filepath)
        self.framesread = 0
        self.frames_per_read = self.wf.getframerate() / 10

    def channels(self):
        return self.wf.getnchannels()

    def sampling_rate(self):
        return self.wf.getframerate()

    def duration(self):
        return round((1000.0 * self.wf.getnframes()) / self.wf.getframerate())

    def current_time(self):
        return round((1000.0 * self.framesread) / self.wf.getframerate())

    def seek_time(self, time):
        """Set the read pointer to the specified time (in ms)"""
        if time == 0:
            self.wf.rewind()
            self.framesread = 0
            return

        # Check the step size
        self.wf.rewind()
        zero = self.wf.tell()
        buf = self.wf.readframes(1)
        one = self.wf.tell()

        # We just have to guess, and hope we're right (no way to check!)
        gotoframe = int(time * self.wf.getframerate() / 1000.0)
        if gotoframe > self.wf.getnframes():
            raise ValueError(str(time) + " is beyond " + str(self.duration()))
        
        gotopos = zero + gotoframe * one
        try:
            self.wf.setpos(gotopos)
        except:
            raise ValueError("Cannot go to " + str(time) + " with " + str(zero) + ":" + str(one))
        self.framesread = gotoframe

    def raw_width(self):
        """Return the width in bytes of raw samples"""
        return self.wf.getsampwidth()

    def raw_read(self):
        """Return some amount of data as a raw audio string"""
        buf = self.wf.readframes(self.frames_per_read)
        if not buf:
            self.eof = True
            return None

        self.framesread += self.frames_per_read

        return buf

    def has_unsigned_singles(self):
        """Is the raw data when this has a width of 1 stored in unsigned bytes (but not for higher widths)"""
        return self.filepath.lower().endswith(".wav")

    def read(self):
        buf = self.raw_read()
        if not buf:
            return None

        if self.wf.getsampwidth() == 1:
            data_array = array('b')
        elif self.wf.getsampwidth() == 2:
            data_array = array('h')
        else:
            data_array = array('i')
        data_array.fromstring(buf)
        return data_array

    def close(self):
        self.wf.close()

class ConvertReader(AudioReader):
    def __init__(self, source, set_channels=None, set_sampling_rate=None, set_raw_width=None):
        AudioReader.__init__(self, source.filepath)
        self.source = source
        self.set_channels = set_channels
        self.set_sampling_rate = set_sampling_rate
        self.set_raw_width = set_raw_width
        self.ratecv_state = None

    def channels(self):
        return self.set_channels or self.source.channels()

    def sampling_rate(self):
        return self.set_sampling_rate or self.source.sampling_rate()

    def duration(self):
        return self.source.duration()

    def current_time(self):
        return self.source.current_time()

    def seek_time(self, time):
        """Set the read pointer to the specified time (in ms)"""
        self.source.seek_time(time)

    def raw_width(self):
        """Return the width in bytes of raw samples"""
        return self.set_raw_width or self.source.raw_width()

    def raw_read(self):
        """Return some amount of data as a raw audio string"""
        buf = self.source.raw_read()
        if buf is None:
            self.eof = True
            return None

        if self.set_channels and self.source.channels() != self.set_channels:
            if self.set_channels == 1:
                buf = audioop.tomono(buf, self.source.raw_width(), .5, .5)
            else:
                buf = audioop.tostereo(buf, self.source.raw_width(), 1, 1)

        if self.set_sampling_rate and self.source.sampling_rate() != self.set_sampling_rate:
            (buf, self.ratecv_state) = audioop.ratecv(buf, self.source.raw_width(), self.channels(), self.source.sampling_rate(), self.set_sampling_rate, self.ratecv_state)

        if self.set_raw_width and self.source.raw_width() != self.set_raw_width:
            if self.source.raw_width() == 1 and self.source.has_unsigned_singles():
                buf = audioop.bias(buf, 1, -128)
            buf = audioop.lin2lin(buf, self.source.raw_width(), self.set_raw_width)
            if self.set_raw_width == 1 and self.source.has_unsigned_singles():
                buf = audioop.bias(buf, 1, 128)

        return buf

    def has_unsigned_singles(self):
        """Is the raw data when this has a width of 1 stored in unsigned bytes (but not for higher widths)"""
        return self.source.has_unsigned_singles()

    def read(self):
        buf = self.raw_read()
        
        if self.raw_width() == 1:
            data_array = array('b')
        elif self.raw_width() == 2:
            data_array = array('h')
        else:
            data_array = array('i')

        data_array.fromstring(buf)
        return data_array

    def close(self):
        self.source.close()

class ScaleReader(AudioReader):
    def __init__(self, source, scale=1.0, bias=0):
        AudioReader.__init__(self, source.filepath)
        self.source = source
        self.scale = scale
        self.bias = bias

    def channels(self):
        return self.source.channels()

    def sampling_rate(self):
        return self.source.sampling_rate()

    def duration(self):
        return self.source.duration()

    def current_time(self):
        return self.source.current_time()

    def seek_time(self, time):
        """Set the read pointer to the specified time (in ms)"""
        self.source.seek_time(time)

    def raw_width(self):
        """Return the width in bytes of raw samples"""
        return self.source.raw_width()

    def raw_read(self):
        """Return some amount of data as a raw audio string"""
        buf = self.source.raw_read()
        if buf is None:
            self.eof = True
            return None

        if self.scale != 1.0:
            buf = audioop.mul(buf, self.source.raw_width(), self.scale)

        if self.bias != 0:
            buf = audioop.bias(buf, self.source.raw_width(), self.bias)

        return buf

    def has_unsigned_singles(self):
        """Is the raw data when this has a width of 1 stored in unsigned bytes (but not for higher widths)"""
        return self.source.has_unsigned_singles()

    def read(self):
        buf = self.raw_read()
        if not buf:
            return None

        if self.raw_width() == 1:
            data_array = array('b')
        elif self.raw_width() == 2:
            data_array = array('h')
        else:
            data_array = array('i')

        data_array.fromstring(buf)
        return data_array

    def close(self):
        self.source.close()

class AppendReader(AudioReader):
    def __init__(self, one_path, two_path):
        AudioReader.__init__(self, one_path)
        self.one_source = AudioReader.open(one_path)
        self.two_source = ConvertReader(AudioReader.open(two_path), one_source.channels(), one_source.sampling_rate(), one_source.raw_width())
        self.current_time = 0

    def channels(self):
        return self.one_source.channels()

    def sampling_rate(self):
        return self.one_source.sampling_rate()

    def duration(self):
        return self.one_source.duration() + self.two_source.duration()

    def current_time(self):
        return self.current_time

    def seek_time(self, time):
        """Set the read pointer to the specified time (in ms)"""
        if time < self.one_source.duration():
            self.one_source.seek_time(time)
        else:
            self.two_source.seek_time(time - self.one_source.duration())
        self.current_time = time

    def raw_width(self):
        """Return the width in bytes of raw samples"""
        return self.one_source.raw_width()

    def raw_read(self):
        """Return some amount of data as a raw audio string"""
        if self.current_time < self.one_source.duration():
            buf = self.one_source.raw_read()
            if buf is None:
                buf = self.two_source.raw_read()
                if buf is None:
                    self.eof = True
                    return None

                self.current_time = self.one_source.duration() + self.two_source.current_time()
                return buf
            else:
                self.current_time = self.one_source.current_time()
                return buf
        else:
            buf = self.two_source.raw_read()
            if buf is None:
                self.eof = True
                return None

            self.current_time = self.one_source.duration() + self.two_source.current_time()
            return buf

    def has_unsigned_singles(self):
        """Is the raw data when this has a width of 1 stored in unsigned bytes (but not for higher widths)"""
        return self.one_source.has_unsigned_singles()

    def read(self):
        buf = self.raw_read()
        
        if self.one_source.raw_width() == 1:
            data_array = array('b')
        elif self.one_source.raw_width() == 2:
            data_array = array('h')
        else:
            data_array = array('i')

        data_array.fromstring(buf)
        return data_array

    def close(self):
        self.one_source.close()
        self.two_source.close()
