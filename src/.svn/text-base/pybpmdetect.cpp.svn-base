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
#include "pybpmdetect.h"

#if PY_VERSION_HEX < 0x01060000
#define PyObject_DEL(op) PyMem_DEL((op))
#endif

PyTypeObject py_bpmdetect_t = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,
    "BPMDetect",
    sizeof(py_bpmdetect),
    0,
    /* standard methods */
    (destructor) py_bpmdetect_dealloc,
    (printfunc) 0,
    (getattrfunc) py_bpmdetect_getattr,
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

PyObject* py_bpmdetect_new(PyObject* self, PyObject* args) {
  py_bpmdetect* ps = NULL;
  uint sampleRate, channels;
  
  if (!PyArg_ParseTuple(args, "II:Soundtouch", &sampleRate, &channels)) {
    PyErr_SetString(PyExc_RuntimeError, "Requires sampling rate and number of channels (sample size must be 2)");
    return NULL;
  }

  ps = PyObject_NEW(py_bpmdetect, &py_bpmdetect_t);
  ps->bpmdetect = new soundtouch::BPMDetect((int) channels, (int) sampleRate);
  ps->channels = (int) channels;

  return (PyObject*) ps;
}

static void py_bpmdetect_dealloc(PyObject* self, PyObject* args) {
  py_bpmdetect* ps = PY_BPMDETECT(self);

  if (ps->bpmdetect) {
    delete ps->bpmdetect;
    ps->bpmdetect = NULL;
  }

  PyObject_DEL(self);
}

static PyObject* py_bpmdetect_put_samples(PyObject* self, PyObject* args) {
  py_bpmdetect* ps = PY_BPMDETECT(self);
  int buflen;
  char* transfer;

  if (!PyArg_ParseTuple(args, "s#", &transfer, &buflen)) {
    PyErr_SetString(PyExc_TypeError, "invalid argument");
	return NULL;
  }

  for (int ii = 0; ii < buflen; ii++)
    ps->buffer.chars[ii] = transfer[ii];

  ps->bpmdetect->inputSamples(ps->buffer.shorts, (uint) buflen / (2 * ps->channels));

  Py_INCREF(Py_None);
  return Py_None;
}

/* return the beats per minute */
static PyObject* py_bpmdetect_get_bpm(PyObject* self, PyObject* args) {
  py_bpmdetect* ps = PY_BPMDETECT(self);

  float bpm = ps->bpmdetect->getBpm();
  
  return PyFloat_FromDouble(bpm);
}

/* housekeeping */

static PyMethodDef bpmdetect_methods[] = {
    { "put_samples", py_bpmdetect_put_samples, METH_VARARGS, "" },
    { "get_bpm", py_bpmdetect_get_bpm, METH_VARARGS, "" },
    { NULL, 0, 0, NULL }
};

static PyObject* py_bpmdetect_getattr(PyObject* self, char* name) {
  return Py_FindMethod(bpmdetect_methods, self, name);
}
