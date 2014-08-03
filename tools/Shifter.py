from ReadAudio import AudioReader, ConvertReader
import soundtouch, wave, audioop, math
from array import array

class Shifter:
    @staticmethod
    def shift_chunk(chunk, sampling_rate, channels, shift):
        """Shift the pitch of a chunk of audio up or down
        Width must be 2."""
        st = soundtouch.SoundTouch(sampling_rate, channels)
        st.set_pitch_shift(shift)

        ii = 0
        resstr = ""
        while ii + 4608 < len(chunk):
            st.put_samples(chunk[ii:ii+4608].tostring())
            ii += 4608
            while st.ready_count() > 0:
                resstr += st.get_samples(4608)

        st.put_samples(chunk[ii:])
        while st.ready_count() > 0:
            resstr += st.get_samples(11025)

        resstr += Shifter.get_flush(st, channels, len(chunk) - len(resstr) / 2)

        del st
            
        result = array(chunk.typecode)
        result.fromstring(resstr)

        return result

    @staticmethod
    def many_shift_chunk(chunk, sampling_rate, channels, shifts):
        """Produce harmonies by shifting a chunk of audio more than once and combining them."""
        shifteds = []
        maxlen = 0
        for jj in xrange(len(shifts)):
            if not shifts[jj]:
                shifted = chunk
            else:
                shifted = Shifter.shift_chunk(chunk, sampling_rate, channels, shifts[jj])

            shifteds.append(shifted)
            maxlen = max(maxlen, len(shifted))

        if len(shifteds) > 1:
            newchunk = [0] * maxlen
            for ii in xrange(maxlen):
                count = 0
                for jj in xrange(len(shifteds)):
                    if len(shifteds[jj]) > ii:
                        newchunk[ii] += shifteds[jj][ii]
                        count += 1
                newchunk[ii] /= count

            result = array(chunk.typecode)
            result.fromlist(newchunk)
            return result
        else:
            return shifteds[0]

    @staticmethod
    def raw_shift_reader(srcpath, dstpath, shift):
        """Shift an entire file up or down"""
        reader = AudioReader.open(srcpath)
        reader2 = ConvertReader(reader, set_raw_width=2)

        st = soundtouch.SoundTouch(reader2.sampling_rate(), reader2.channels())
        st.set_pitch_shift(shift)

        writer = wave.open(dstpath, 'w')
        writer.setnchannels(reader2.channels())
        writer.setframerate(reader2.sampling_rate())
        writer.setsampwidth(reader2.raw_width())

        while True:
            data = reader2.raw_read()
            if not data:
                break

            print len(data)
            st.put_samples(data)

            while st.ready_count() > 0:
                writer.writeframes(st.get_samples(11025))

        writer.writeframes(Shifter.get_flush(st, reader2.channels()))
        writer.close()
        reader2.close()

    @staticmethod
    def get_flush(st, channels, fade=0):
        """Like soundtouch's flush, don't require that all data comes through, just any.
        If fade > 0, only allow [fade] samples, and linearly scale volume to 0 over that length"""
        
        waiting = st.waiting_count()
        ready = st.ready_count()
        result = ""

        silence = array('h', [0] * 64)

        while st.ready_count() == ready:
            st.put_samples(silence)

        while st.ready_count() > 0:
            result += st.get_samples(11025)

        st.clear()

        if len(result) > 2 * channels * waiting:
            result = result[0:(2 * channels * waiting)]

        fade = min(fade, len(result) / 2)
        if fade > 0:
            resultstring = ""
            for ii in xrange(fade / channels):
                i0 = ii * 2*channels
                i1 = (ii+1) * 2*channels
                resultstring += audioop.mul(result[i0:i1], 2, 1 - float(ii) / (fade / channels))
            result = resultstring

        return result
    
    @staticmethod
    def bpm_detect_file(fullpath):
        """Detect the beat from an entire file"""
        reader = AudioReader.open(fullpath)
        reader2 = ConvertReader(reader, set_raw_width=2)

        bd = soundtouch.BPMDetect(reader2.sampling_rate(), reader2.channels())

        while True:
            data = reader2.raw_read()
            if not data:
                break

            bd.put_samples(data)

        reader2.close()

        return bd.get_bpm()

    @staticmethod
    def echocancel(outputdata, inputdata):
        """Try to identify an echo and remove it.
        Should contain 2-byte samples"""
        pos = audioop.findmax(outputdata, 800)
        out_test = outputdata[pos*2:]
        in_test = inputdata[pos*2:]
        ipos, factor = audioop.findfit(in_test, out_test)
        factor = audioop.findfactor(in_test[ipos*2:ipos*2+len(out_test)], out_test)
        prefill = '\0'*(pos+ipos)*2
        postfill = '\0'*(len(inputdata) - len(prefill) - len(outputdata))
        outputdata = prefill + audioop.mul(outputdata, 2, -factor) + postfill
        return audioop.add(inputdata, outputdata, 2)

    @staticmethod
    def beats_to_ms(bpm, beats):
        """Convert from bpm at a given beat rate to ms between beats."""
        return 60 * 1000 * beats / bpm

    @staticmethod
    def find_division_start(fullpath, bpm, beats_per):
        """Identify the start of the beats, by finding segments that fit together"""
        reader = AudioReader.open(fullpath)

        # This doesn't find the exact time of the max, but don't need it.
        max_value = 0
        max_time = 0
        while True:
            data = reader.raw_read()
            if data is None:
                break

            data_max = audioop.max(data, reader.raw_width())
            if data_max > max_value:
                max_value = data_max
                max_time = reader.current_time()

        before = max_time - Shifter.beats_to_ms(bpm, beats_per)
        after = max_time + 2 * Shifter.beats_to_ms(bpm, beats_per)
        if before < 0:
            after += -before
            before = 0
        if after > reader.duration():
            before -= after - reader.duration()
            after = reader.duration()
        if before < 0:
            if beats_per < 2:
                raise RuntimeError('This audio file is too short to be divided by beats.')
            else:
                reader.close()
                return Shifting.find_division_start(filepath, bpm, int(beats_per / 2))

        reader.seek_time(0)
        reader2 = ConvertReader(reader, set_raw_width=2, set_channels=1)
        region = reader2.raw_random_read(before, after)

        # both in bytes
        raw_length = 2 * int(len(region) / 6)
        beat_length = int(2 * Shifter.beats_to_ms(bpm, 1) * reader2.sampling_rate() / 1000.0)

        print "Around max: " + str(before) + " - " + str(after) + ": " + str(raw_length)

        min_factor = 0
        min_ii = 0
        # First determine time within a beat
        for ii in xrange(beat_length / 200):
            factor = audioop.findfactor(region[200*ii:200*ii+raw_length], region[200*ii+raw_length:200*ii+2*raw_length])
            if factor < min_factor:
                print "Samp: At " + str(ii) + " " + str(factor)
                min_factor = factor
                min_ii = ii

        # Second, determine which beat to use
        min_factor = 0
        min_jj = 0
        for jj in xrange(beats_per):
            factor = audioop.findfactor(region[jj*beat_length+200*min_ii:jj*beat_length+200*min_ii+raw_length], region[jj*beat_length+200*min_ii+raw_length:jj*beat_length+200*min_ii+2*raw_length])
            print "Beat: At " + str(jj) + " " + str(factor)
            if factor < min_factor:
                min_factor = factor
                min_jj = jj

        print "Best: Beat: " + str(min_jj) + ", Samp: " + str(100*min_ii)
        start_time = before + (min_jj*beat_length*2 + 100*min_ii) * 1000.0 / reader2.sampling_rate()
        reader2.close()

        return math.fmod(start_time, Shifter.beats_to_ms(bpm, beats_per))
