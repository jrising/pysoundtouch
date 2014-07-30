/*
 * python interface to soundtouch (the open-source audio processing library)
 */

#ifndef __PY_SOUNDTOUCH_H__
#define __PY_SOUNDTOUCH_H__

#define __cplusplus

#include <Python.h>
#include <SoundTouch.h>

#define BUFFER_SIZE 44100

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

static void py_soundtouch_dealloc(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_set_rate(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_set_tempo(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_set_pitch(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_set_pitch_shift(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_flush(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_clear(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_put_samples(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_get_samples(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_ready_count(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_waiting_count(PyObject* self, PyObject* args);
static PyObject* py_soundtouch_getattr(PyObject* self, char* name);

#endif
