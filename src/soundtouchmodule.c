/*
 * python interface to soundtouch (the open-source audio processing library)
 * Expose BMP detection and Shifting to python
 */

#include <SoundTouch.h>
#include "soundtouchmodule.h"

static PyMethodDef soundtouch_methods[] = {
    { "SoundTouch", py_soundtouch_new, METH_VARARGS, "" },
    { "BPMDetect", py_bpmdetect_new, METH_VARARGS, "" },
    { NULL, 0, 0, NULL }
};

PyMODINIT_FUNC
initsoundtouch(void) {
    PyObject *module, *dict;

    module = Py_InitModule("soundtouch", soundtouch_methods);
    dict = PyModule_GetDict(module);

    PyDict_SetItemString(dict, "__version__",
			 PyString_FromString(VERSION));

    if (PyErr_Occurred())
      PyErr_SetString(PyExc_ImportError, "soundtouch: init failed");
}
