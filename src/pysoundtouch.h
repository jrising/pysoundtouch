/*
 * python interface to soundtouch (the open-source audio processing library)
 * Pitch, tempo, and rate shifting
 */

#ifndef __PY_SOUNDTOUCH_H__
#define __PY_SOUNDTOUCH_H__

#define __cplusplus

#include <Python.h>
#include <SoundTouch.h>

#define BUFFER_SIZE 44100

// Definition of the soundtouch object
typedef struct {
  PyObject_HEAD
  int channels; // 1 or 2
  soundtouch::SoundTouch* soundtouch;
  union {
    char chars[BUFFER_SIZE];
    short shorts[BUFFER_SIZE/2];
  } buffer;
} py_soundtouch; /* Soundtouch */

#define PY_SOUNDTOUCH(x) ((py_soundtouch *) x)

extern PyTypeObject py_soundtouch_t;

// Deallocate the SoundTouch object
static void py_soundtouch_dealloc(PyObject* self, PyObject* args);

// Adjust attributes of samples that have been entered
static PyObject* py_soundtouch_set_rate(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_set_tempo(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_set_pitch(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_set_pitch_shift(PyObject* self, PyObject* args);

// Move all waiting samples to the output
static PyObject* py_soundtouch_flush(PyObject* self, PyObject* args);

// Clear the buffer of samples
static PyObject* py_soundtouch_clear(PyObject* self, PyObject* args);

// Add new samples to be processed
static PyObject* py_soundtouch_put_samples(PyObject* self, PyObject* args);

// Extract processed samples from the output
static PyObject* py_soundtouch_get_samples(PyObject* self, PyObject* args);

// Return how many samples are available for output
static PyObject* py_soundtouch_ready_count(PyObject* self, PyObject* args);

// Return how many samples will be available given the current data
static PyObject* py_soundtouch_waiting_count(PyObject* self, PyObject* args);

// Get additional attributes from the SoundTouch object
static PyObject* py_soundtouch_getattr(PyObject* self, char* name);

#endif
