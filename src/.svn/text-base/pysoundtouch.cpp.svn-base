/*
 * python interface to soundtouch (the open-source audio processing library)
 *
 * The structure of this code was based on pymad-0.5.4
 * This is a C++ file.
 */

#include <Python.h>

extern "C" {
  #include "soundtouchmodule.h"
}
#include "pysoundtouch.h"

#if PY_VERSION_HEX < 0x01060000
#define PyObject_DEL(op) PyMem_DEL((op))
#endif

/*#include "WavFile.h"
WavOutFile* inputs = new WavOutFile("/Users/jrising/inputs.wav", 44100, 16, 1);
WavOutFile* outputs = new WavOutFile("/Users/jrising/outputs.wav", 44100, 16, 1);*/

PyTypeObject py_soundtouch_t = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,
    "Soundtouch",
    sizeof(py_soundtouch),
    0,
    /* standard methods */
    (destructor) py_soundtouch_dealloc,
    (printfunc) 0,
    (getattrfunc) py_soundtouch_getattr,
    (setattrfunc) 0,
    (cmpfunc) 0,
    (reprfunc) 0,
    /* type categories */
    0, /* as number */
    0, /* as sequence */
    0, /* as mapping */
    0, /* hash */
    0, /* binary */
    0, /* repr */
    0, /* getattro */
    0, /* setattro */
    0, /* as buffer */
    0, /* tp_flags */
    NULL
};

/* functions */

PyObject* py_soundtouch_new(PyObject* self, PyObject* args) {
  py_soundtouch* ps = NULL;
  uint sampleRate, channels;
  
  if (!PyArg_ParseTuple(args, "II:Soundtouch", &sampleRate, &channels)) {
    PyErr_SetString(PyExc_RuntimeError, "Requires sampling rate and number of channels (sample size must be 2)");
    return NULL;
  }

  ps = PyObject_NEW(py_soundtouch, &py_soundtouch_t);
  ps->soundtouch = new soundtouch::SoundTouch();
  ps->channels = (int) channels;
  ps->soundtouch->setSampleRate(sampleRate);
  ps->soundtouch->setChannels(channels);

  return (PyObject*) ps;
}

static void py_soundtouch_dealloc(PyObject* self, PyObject* args) {
  py_soundtouch* ps = PY_SOUNDTOUCH(self);

  if (ps->soundtouch) {
    delete ps->soundtouch;
    ps->soundtouch = NULL;
  }

  PyObject_DEL(self);
}

static PyObject* py_soundtouch_set_rate(PyObject* self, PyObject* args) {
  float rate;

  if (!PyArg_ParseTuple(args, "f", &rate) || rate < 0) {
    PyErr_SetString(PyExc_TypeError, "invalid argument");
	return NULL;
  }

  PY_SOUNDTOUCH(self)->soundtouch->setRate(rate);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* py_soundtouch_set_tempo(PyObject* self, PyObject* args) {
  float tempo;

  if (!PyArg_ParseTuple(args, "f", &tempo) || tempo < 0) {
    PyErr_SetString(PyExc_TypeError, "invalid argument");
	return NULL;
  }

  PY_SOUNDTOUCH(self)->soundtouch->setTempo(tempo);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* py_soundtouch_set_pitch(PyObject* self, PyObject* args) {
  float pitch;

  if (!PyArg_ParseTuple(args, "f", &pitch) || pitch < 0) {
    PyErr_SetString(PyExc_TypeError, "invalid argument");
	return NULL;
  }

  PY_SOUNDTOUCH(self)->soundtouch->setPitch(pitch);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* py_soundtouch_set_pitch_shift(PyObject* self, PyObject* args) {
  float pitch;

  if (!PyArg_ParseTuple(args, "f", &pitch) || pitch < -12 || pitch > 12) {
    PyErr_SetString(PyExc_TypeError, "invalid argument: pitch must be between -12 and 12");
	return NULL;
  }

  PY_SOUNDTOUCH(self)->soundtouch->setPitchSemiTones(pitch);

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* py_soundtouch_flush(PyObject* self, PyObject* args) {
  PY_SOUNDTOUCH(self)->soundtouch->flush();

  //delete inputs;
  //delete outputs;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* py_soundtouch_clear(PyObject* self, PyObject* args) {
  PY_SOUNDTOUCH(self)->soundtouch->clear();

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* py_soundtouch_put_samples(PyObject* self, PyObject* args) {
  py_soundtouch* ps = PY_SOUNDTOUCH(self);
  int buflen;
  char* transfer;

  if (!PyArg_ParseTuple(args, "s#", &transfer, &buflen)) {
    PyErr_SetString(PyExc_TypeError, "invalid argument");
	return NULL;
  }

  for (int ii = 0; ii < buflen; ii++)
    ps->buffer.chars[ii] = transfer[ii];

  ps->soundtouch->putSamples(ps->buffer.shorts, (uint) buflen / (2 * ps->channels));

  //inputs->write(ps->buffer.shorts, buflen / 2);

  Py_INCREF(Py_None);
  return Py_None;
}

/* return the shifted samples */
static PyObject* py_soundtouch_get_samples(PyObject* self, PyObject* args) {
  py_soundtouch* ps = PY_SOUNDTOUCH(self);
  uint maxSamples;

  if (!PyArg_ParseTuple(args, "|I", &maxSamples)) {
    PyErr_SetString(PyExc_TypeError, "invalid argument");
	return NULL;
  }
  
  uint received = ps->soundtouch->receiveSamples(ps->buffer.shorts, maxSamples);

  //outputs->write(ps->buffer.shorts, received * ps->channels);

  return PyString_FromStringAndSize(ps->buffer.chars, received * 2 * ps->channels);
}

static PyObject* py_soundtouch_ready_count(PyObject* self, PyObject* args) {
  return PyInt_FromLong(PY_SOUNDTOUCH(self)->soundtouch->numSamples());
}

static PyObject* py_soundtouch_waiting_count(PyObject* self, PyObject* args) {
  return PyInt_FromLong(PY_SOUNDTOUCH(self)->soundtouch->numUnprocessedSamples());
}

/* housekeeping */

static PyMethodDef soundtouch_methods[] = {
    { "set_rate", py_soundtouch_set_rate, METH_VARARGS, "" },
    { "set_tempo", py_soundtouch_set_tempo, METH_VARARGS, "" },
    { "set_pitch", py_soundtouch_set_pitch, METH_VARARGS, "" },
    { "set_pitch_shift", py_soundtouch_set_pitch_shift, METH_VARARGS, "" },
    { "flush", py_soundtouch_flush, METH_VARARGS, "" },
    { "clear", py_soundtouch_clear, METH_VARARGS, "" },
    { "put_samples", py_soundtouch_put_samples, METH_VARARGS, "" },
    { "get_samples", py_soundtouch_get_samples, METH_VARARGS, "" },
    { "ready_count", py_soundtouch_ready_count, METH_VARARGS, "" },
    { "waiting_count", py_soundtouch_waiting_count, METH_VARARGS, "" },
    { NULL, 0, 0, NULL }
};

static PyObject* py_soundtouch_getattr(PyObject* self, char* name) {
  // TODO: add soundtouch.getSetting here?  Add a setattr with soundtouch.setSetting?
  return Py_FindMethod(soundtouch_methods, self, name);
}
