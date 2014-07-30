from ReadAudio import AudioReader, ConvertReader, ScaleReader
from Shifting import Shifter
import wave, math, audioop
from array import array

class AudioWriter:
    @staticmethod
    def write_parse(srcpath, dstpath, parse, silence=0):
        """Write a file with this order of segments, with silence seconds of silence between parsings"""

        reader = AudioReader.open(srcpath)
        writer = wave.open(dstpath, 'w')
        writer.setnchannels(reader.channels())
        writer.setframerate(reader.sampling_rate())
        first = True
        for segment in parse:
            data = reader.random_read(segment[1] * 1000, segment[2] * 1000)
            if data is None:
                continue
            
            if first:
                writer.setsampwidth(data.itemsize)
                first = False

            writer.writeframes(data.tostring())
            if silence > 0:
                AudioWriter.generate_silence(silence, data.typecode, reader, writer)

        writer.close()
        reader.close()

        return True

    @staticmethod
    def write_split(srcpath, dstpath, division, padding=1000, silence=1000):
        reader = AudioReader.open(srcpath)
        writer = wave.open(dstpath, 'w')
        writer.setnchannels(reader.channels())
        writer.setframerate(reader.sampling_rate())

        if division - padding < 0:
            data = reader.random_read(0, division)
            if data is not None:
                writer.setsampwidth(data.itemsize)

            AudioWriter.generate_silence((padding - division) / 1000, data.typecode, reader, writer)
        else:
            data = reader.random_read(division - padding, division)
            if data is not None:
                writer.setsampwidth(data.itemsize)

        if data is not None:
            writer.writeframes(data.tostring())
            
        AudioWriter.generate_silence(silence / 1000, data.typecode, reader, writer)
        
        data = reader.random_read(division, division + padding)
        if data is not None:
            writer.writeframes(data.tostring())

        writer.close()
        reader.close()

        return True

    @staticmethod
    def overlap_write(overlap_time, fading_time, srcpath, dstpath, parse, times=None, shifts=None, procid=None):
        """Writes a parse using cross-fading and stitching.
        overlap_time, fading_time, times is in seconds
        Shifts, when not none, can be a list of lists of interval shifts to be combined
        Preconditions: input the time of overlap for cross stiching. parsePlayer
        will compile all the events and stitch events together with fading"""

        fade_first = True

        if times is None:
            times = [0];
            for ii in xrange(len(parse)):
                times.append(parse[ii][2] - parse[ii][1] + times[ii])

        # Scale the reader, to deal with maximum overlap amplitude
        reader = ScaleReader(AudioReader.open(srcpath), 1/1.74036269)
        reader.seek_time(0)

        writer = wave.open(dstpath, 'w')
        writer.setnchannels(reader.channels())
        writer.setframerate(reader.sampling_rate())
        first = True
        maxval = None

        debugs = []

        leftovers = [] # data that should be added into the next chunk
        last_writestop = 0 # Where we've written to
        last_readstop = 0 # The previous value of [stop]
        last_overlap = False # Did the last segment end early for an overlap?
        # Each loop looks ahead to add silence or leave leftovers
        for ii in xrange(len(parse)):
            if last_overlap:
                start = (parse[ii][1] - overlap_time) * 1000
                fade_begin = True
            else:
                start = parse[ii][1] * 1000
                fade_begin = False

            if ii < len(parse) - 1 and (parse[ii][0] != parse[ii+1][0] - 1 or (shifts and (shifts[ii] != [0] or shifts[ii+1] != [0]))):
                stop = (parse[ii][2] + overlap_time) * 1000
                fade_end = True
                next_overlap = True
            else:
                stop = parse[ii][2] * 1000
                fade_end = False
                next_overlap = False

            if start < 0:
                presilence = -start
                start = 0
            else:
                presilence = 0

            stop = min(stop, reader.duration())
            if parse[ii][2] == 0: # XXX: To fix CBach.26
                stop = reader.duration()

            if last_readstop == start and len(leftovers) <= 2 * reader.channels() * reader.sampling_rate() / 1000:
                # May have read a little extra-- don't seek
                after = reader.continue_read(stop, debugs)
                chunk = array(after.typecode)
                chunk.extend(leftovers)
                chunk.extend(after)
                leftovers = []
                last_readstop = stop
                debugs.append("Continue read: " + str(len(chunk)))
                print "Continue Read"
            else:
                chunk = reader.random_read(start, stop, debugs)
                last_readstop = stop
                print "Normal Read"

            if chunk is None:
                continue
            if presilence > 0:
                chunk = AudioWriter.fader_logarithmic(chunk, int(fading_time * reader.channels() * reader.sampling_rate()), True, False)
                newchunk = array(chunk.typecode)
                newchunk.extend([0] * int(reader.sampling_rate() * reader.channels() * presilence / 1000.0))
                newchunk.extend(chunk)
                chunk = newchunk
                fade_begin = False

            debugs.append("Got " + str(len(chunk)) + " in [" + str(start) + ", " + str(stop) + "]")

            if len(chunk) == 0:
                raise ValueError("No data between " + str(start) + " and " + str(stop))

            if first:
                writer.setsampwidth(chunk.itemsize)
                maxval = (1 << (chunk.itemsize * 8)) / 2 - 1
                first = False

            debugs.append("Fading: " + str(fade_begin) + ", " + str(fade_end) + " for " + str(int(fading_time * reader.channels() * reader.sampling_rate())))
            chunk = AudioWriter.fader_logarithmic(chunk, int(fading_time * reader.channels() * reader.sampling_rate()), fade_begin, fade_end)

            if shifts and shifts[ii]:
                oldlen = len(chunk)
                chunk = Shifter.many_shift_chunk(chunk, reader.sampling_rate(), reader.channels(), shifts[ii])
                debugs.append("Shift of " + str(shifts[ii]) + " for " + str(len(chunk)))

            for jj in xrange(min(len(leftovers), len(chunk))):
                combined = chunk[jj] + leftovers[jj]
                chunk[jj] = max(-maxval, min(maxval, combined))

            if len(leftovers) > len(chunk):
                chunk.extend(leftovers[len(chunk):])

            if ii == len(parse) - 1:
                # Last segment!  just write everything out
                writer.writeframes(chunk.tostring())
                leftovers = []
                next_writestop = 0
            else:
                print "Writing " + str(ii)
                if next_overlap:
                    leftovers = AudioWriter.write_overlapping_chunk(writer, reader, last_writestop, times[ii + 1] - overlap_time, chunk, leftovers, debugs)
                    next_writestop = times[ii + 1] - overlap_time
                else:
                    leftovers = AudioWriter.write_overlapping_chunk(writer, reader, last_writestop, times[ii + 1], chunk, leftovers, debugs)
                    next_writestop = times[ii + 1]

            last_overlap = next_overlap
            debugs.append("Write over [" + str(last_writestop) + ", " + str(next_writestop) + "]")
            last_writestop = next_writestop
            debugs.append("At " + str(last_writestop) + " write " + str(len(chunk)) + " - "  + str(len(leftovers)) + " => " + str(writer.tell()))

        writer.close()
        reader.close()
        Shifter.close_debug()
        return debugs

    @staticmethod
    def borrow_write(overlap, base_path, base_scale, subs_path, subs_scale, dstpath, parse, parse_length, times=None):
        """Writes a parse using cross-fading and stitching.
        Borrows parse elements >= parse_length from subs
        overlap, times is in seconds"""

        if times is None:
            times = [0];
            for ii in xrange(parse_length):
                times.append(parse[ii][2] - parse[ii][1] + times[ii])

        base_reader = AudioReader.open(base_path)
        subs_reader = ConvertReader(AudioReader.open(subs_path), base_reader.channels(), base_reader.sampling_rate(), base_reader.raw_width())

        writer = wave.open(dstpath, 'w')
        writer.setnchannels(base_reader.channels())
        writer.setframerate(base_reader.sampling_rate())
        first = True
        maxval = None

        leftovers = [] # data that should be added into the next chunk
        # Each loop looks ahead to add silence or leave leftovers
        for ii in xrange(parse_length):
            if parse[ii][1] * 1000.0 < base_reader.duration():
                # From the base file
                start = (parse[ii][1] - overlap / 2) * 1000
                stop = (parse[ii][2] + overlap / 2) * 1000
                print(stop)

                start = max(start, 0)
                stop = min(stop, base_reader.duration())
                print(stop)

                chunk = base_reader.random_read(start, stop)
                if base_scale != 1:
                    for jj in xrange(len(chunk)):
                        chunk[jj] = int(chunk[jj] * base_scale)
            else:
                # From the subs file
                start = (parse[ii][1] - overlap / 2) * 1000 - base_reader.duration()
                stop = (parse[ii][2] + overlap / 2) * 1000 - base_reader.duration()

                start = max(start, 0)
                stop = min(stop, subs_reader.duration())

                chunk = subs_reader.random_read(start, stop)
                if subs_scale != 1:
                    for jj in xrange(len(chunk)):
                        chunk[jj] = int(chunk[jj] * subs_scale)
                
            if chunk is None:
                continue

            if len(chunk) == 0:
                raise ValueError("No data between " + str(start) + " and " + str(stop))

            if first:
                writer.setsampwidth(chunk.itemsize)
                maxval = (1 << (chunk.itemsize * 8)) / 2 - 1
                first = False

            chunk = AudioWriter.fader_logarithmic(chunk, int(overlap * base_reader.channels() * base_reader.sampling_rate()))
            for jj in xrange(min(len(leftovers), len(chunk))):
                combined = chunk[jj] + leftovers[jj]
                chunk[jj] = max(-maxval, min(maxval, combined))

            if len(leftovers) > len(chunk):
                chunk.extend(leftovers[len(chunk):])

            if ii == parse_length - 1:
                # Last segment!  just write everything out
                writer.writeframes(chunk.tostring())
                leftovers = []
            else:
                leftovers = AudioWriter.write_overlapping_chunk(writer, base_reader, times[ii], times[ii + 1] - overlap / 2, chunk, leftovers)

        writer.close()
        base_reader.close()
        subs_reader.close()

    @staticmethod
    def write_overlapping_chunk(writer, reader, start, next_start, chunk, leftovers, debugs=None):
        if next_start > start + float(len(chunk)) / (reader.channels() * reader.sampling_rate()) + .0001:
            # There's some silence between segments
            writer.writeframes(chunk.tostring())
            lasttime = start + float(len(chunk)) / (reader.channels() * reader.sampling_rate())
            AudioWriter.generate_silence(next_start - lasttime, chunk.typecode, reader, writer)
            if debugs:
                debugs.append("Silence of " + str(next_start - lasttime))
            leftovers = []
        else:
            # There's some overlap-- leave leftovers
            towrite = int((next_start - start) * reader.sampling_rate()) * reader.channels()
            leftovers = chunk[towrite:]
            chunk = chunk[:towrite]
            writer.writeframes(chunk.tostring())

        return leftovers

    @staticmethod
    def generate_silence(secs, typecode, reader, writer):
        """Writes a space of 0 secs long to writer, using the parameters of reader"""
        silence = array(typecode)
        silence.extend([0] * int(reader.sampling_rate() * reader.channels() * secs))
        writer.writeframes(silence.tostring())

    @staticmethod
    def fader_logarithmic(data, overlap_count, do_begin=True, do_end=True, special_denom=None):
        """Fades beginnings and end of each event using logarithmic fading"""
        if special_denom is None:
            special_denom = overlap_count
        for ii in xrange(min(overlap_count, len(data))):
            scale = math.log10(1 + 9.0 * ii / special_denom)
            if do_begin:
                data[ii] = scale * data[ii]
            if do_end:
                data[len(data) - ii - 1] = scale * data[len(data) - ii - 1]

        return data    

    @staticmethod
    def fader_linear(data, overlap_count, do_begin=True, do_end=True, special_denom=None):
        """Fades beginnings and end of each event using linear fading"""
        if special_denom is None:
            special_denom = overlap_count
        for ii in xrange(min(overlap_count, len(data))):
            scale = ii / float(special_denom)
            if do_begin:
                data[ii] = scale * data[ii]
            if do_end:
                data[len(data) - ii - 1] = scale * data[len(data) - ii - 1]

        return data

    @staticmethod
    def zero_finder(data):
        """Find closest zero to break point and make that the break point at that zero crossing NOT USED"""
        found = []
        for ii in xrange(len(data)):
            if data[ii] == 0:
                found.append(ii)

        if not found:
            return len(data)
        else:
            return found[-1]

    @staticmethod
    def fader_holder(data,fs,overlap):
        """Fades beginnings and end of each event using different forms of fading,
        can alternate betweeen logistic, exponential and logarithmic"""
        #logistic fading
        #data(1:overlap)=data(1:overlap)./(1+exp(-5*fadeIn));
        #data((end-overlap+1):end)=data((end-overlap+1):len)./(1+exp(-5*fadeOut));

        #exponential fading
        #data(1:overlap)=exp(-3*fadeIn).*data(1:overlap);
        #data((end-overlap+1):end)=exp(-3*fadeOut).*data((end-overlap+1):len);
        pass

    @staticmethod
    def merge(dstpath, srcpath1, srcpath2):
        """Overlay both of these audio files, writing the result to dstpath"""
        reader1 = AudioReader.open(srcpath1)
        reader2 = AudioReader.open(srcpath2)
        if reader1.channels() != reader2.channels() or reader1.sampling_rate() != reader2.sampling_rate():
            raise ValueError("Merging files of different properties not supported.")

        writer = wave.open(dstpath, 'w')
        writer.setnchannels(reader1.channels())
        writer.setframerate(reader1.sampling_rate())
        first = True
        while True:
            data1 = reader1.read()
            data2 = reader2.read()
            if data1 is None or data2 is None or len(data1) != len(data2):
                break
            
            if first:
                if data1.itemsize != data2.itemsize:
                    raise ValueError("Merging files of different properties not supported.")
                writer.setsampwidth(data1.itemsize)
                first = False

            writer.writeframes(audioop.add(audioop.mul(data1.tostring(), data1.itemsize, .5),
                                           audioop.mul(data2.tostring(), data2.itemsize, .5), data1.itemsize))

        if data1 is None:
            datastr1 = ""
        else:
            datastr1 = data1.tostring()
        if data2 is None:
            datastr2 = ""
        else:
            datastr2 = data2.tostring()
            
        common_len = min(len(datastr1), len(datastr2))

        if common_len > 0:
            writer.writeframes(audioop.add(audioop.mul(datastr1[:common_len], data1.itemsize, .5),
                                           audioop.mul(datastr2[:common_len], data2.itemsize, .5), data1.itemsize))
        if len(datastr1) > common_len:
            writer.writeframes(audioop.mul(datastr1[:common_len], data1.itemsize, .5))
        elif len(datastr2) > common_len:
            writer.writeframes(audioop.mul(datastr2[:common_len], data2.itemsize, .5))

        writer.close()

        return True
    
