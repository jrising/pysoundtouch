/* 
 * python interface to soundtouch (the open-source audio processing library)
 * Expose BMP detection and Shifting to python
 */

#ifndef __SOUNDTOUCH_MODULE_H__
#define __SOUNDTOUCH_MODULE_H__

#include <Python.h>

/* module accessible functions */
extern "C" {
  PyObject* py_soundtouch_new(PyObject* self, PyObject* args);
  PyObject* py_bpmdetect_new(PyObject* self, PyObject* args);
}

#endif
