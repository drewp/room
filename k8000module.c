#include "Python.h"


#define IN_PYTHON_MODULE 1
//#include "/home/drewp/elec/k8000/new/i2c_k8000.c"
#include "i2c_k8000.c"

static PyObject *k8000_ConfigAllIOasInput(PyObject *self, PyObject *args)
{
  ConfigAllIOasInput();
  Py_INCREF(Py_None);
  return Py_None;
}
static PyObject *k8000_ConfigIOchannelAsOutput(PyObject *self, PyObject *args)
{
  int chan;
  if( !PyArg_ParseTuple(args, "i", &chan))
    return NULL;
  ConfigIOchannelAsOutput(chan);
  Py_INCREF(Py_None);
  return Py_None;
}
static PyObject *k8000_ReadIOchannel(PyObject *self, PyObject *args)
{
  int chan,res;
  if( !PyArg_ParseTuple(args, "i", &chan))
    return NULL;
  res = ReadIOchannel(chan);
  return Py_BuildValue("i",res);
}
static PyObject *k8000_OutputDACchannel(PyObject *self, PyObject *args)
{
  int chan,lev;
  if( !PyArg_ParseTuple(args, "ii", &chan, &lev))
    return NULL;

  OutputDACchannel(chan,lev);
  Py_INCREF(Py_None);
  return Py_None;
}
static PyObject *k8000_SetIOchannel(PyObject *self, PyObject *args)
{
  int chan;
  if( !PyArg_ParseTuple(args, "i", &chan))
    return NULL;

  SetIOchannel(chan);
  Py_INCREF(Py_None);
  return Py_None;
}
static PyObject *k8000_ClearIOchannel(PyObject *self, PyObject *args)
{
  int chan;
  if( !PyArg_ParseTuple(args, "i", &chan))
    return NULL;

  ClearIOchannel(chan);
  Py_INCREF(Py_None);
  return Py_None;
}
static PyObject *k8000_UpdateAllDAC(PyObject *self, PyObject *args)
{
  UpdateAllDAC();
  Py_INCREF(Py_None);
  return Py_None;
}
static PyObject *k8000_UpdateIOchip(PyObject *self, PyObject *args)
{
  int chip;
  if( !PyArg_ParseTuple(args, "i", &chip))
    return NULL;

  UpdateIOchip(chip);
  Py_INCREF(Py_None);
  return Py_None;
}
static PyObject *k8000_ReadADchannel(PyObject *self, PyObject *args)
{
  int chan,val;
  if( !PyArg_ParseTuple(args,"i",&chan))
    return NULL;
  val = ReadADchannel(chan);
  return Py_BuildValue("i",val);
}

#if 0
TEMPLATE!
TEMPLATE!
TEMPLATE!
static PyObject *k8000_(PyObject *self, PyObject *args)
{
  ();
  Py_INCREF(Py_None);
  return Py_None;
}
#endif


static PyMethodDef K8000Methods[] = {
  {"ConfigAllIOasInput",k8000_ConfigAllIOasInput,METH_VARARGS},
  {"ConfigIOchannelAsOutput",k8000_ConfigIOchannelAsOutput,METH_VARARGS},
  {"ReadIOchannel",k8000_ReadIOchannel,METH_VARARGS},
  {"OutputDACchannel",k8000_OutputDACchannel,METH_VARARGS},
  {"SetIOchannel",k8000_SetIOchannel,METH_VARARGS},
  {"ClearIOchannel",k8000_ClearIOchannel,METH_VARARGS},
  {"UpdateAllDAC",k8000_UpdateAllDAC,METH_VARARGS},
  {"UpdateIOchip",k8000_UpdateIOchip,METH_VARARGS},
  {"ReadADchannel",k8000_ReadADchannel,METH_VARARGS},
  //  {"",k8000_,METH_VARARGS},
  {NULL,      NULL}        /* Sentinel */
};

void
initk8000()
{
  if (getuid() != 0) {
    fprintf(stderr,"can't start k8000; only root can open the port\n");
    exit(1);
  }
  if(!ioperm(0x378, 3, 1)) {
    perror("opening port");
    exit(1);
  }
  initialize();
  (void) Py_InitModule("k8000", K8000Methods);
}
