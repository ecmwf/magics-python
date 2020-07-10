# (C) Copyright 2012-2018 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#

import ctypes
import ctypes.util

import sys
import os

import numpy as np
from numpy.ctypeslib import ndpointer
from functools import partial
import json

#
#  This Python interface needs to find the Magics library
#
#  We first search LD_LIBRARY_PATH. If you have strange behaviours,
#  check your $LD_LIBRARY_PATH.
#  This is only required on Linux! Therefore we do not have to check
#  on MacOS the DYLD_LIBRARY_PATH or for *.dylib.
#
lib = None
if sys.platform == "darwin":
    for directory in os.environ.get("DYLD_LIBRARY_PATH", "").split(":"):
        fullname = os.path.join(directory, "libMagPlus.dylib")
        if os.path.exists(fullname):
            lib = fullname
            break

    if lib is None:
        fullname = os.path.join(
            os.environ.get("MAGPLUS_HOME", ""), "lib/libMagPlus.dylib"
        )
        if os.path.exists(fullname):
            lib = fullname

elif sys.platform == "win32":
    if lib is None:
        fullname = os.path.join(
            os.environ.get("MAGPLUS_HOME", ""), "lib/libMagPlus.dll"
        )
        if os.path.exists(fullname):
            lib = fullname

else:
    for directory in os.environ.get("LD_LIBRARY_PATH", "").split(":"):
        fullname = os.path.join(directory, "libMagPlus.so")
        if os.path.exists(fullname):
            lib = fullname
            break

    if lib is None:
        fullname = os.path.join(os.environ.get("MAGPLUS_HOME", ""), "lib/libMagPlus.so")
        if os.path.exists(fullname):
            lib = fullname


#
#  if not overwritten test if instlled version exist and use it
#
# if lib is None:
#    installname = "@CMAKE_INSTALL_PREFIX@/@INSTALL_LIB_DIR@/libMagPlus@CMAKE_SHARED_LIBRARY_SUFFIX@"
#    if os.path.exists(installname):
#        lib = installname

#
# If LD_LIBRARY_PATH does not contain path to Magics and it is not where you installed,
# we search the standard system locations
#
if lib is None:
    lib = ctypes.util.find_library("MagPlus")

# as last resort throw exception
if lib is None:
    raise Exception("Magics library could not be found")

dll = ctypes.CDLL(lib)


class FILE(ctypes.Structure):
    pass


FILE_p = ctypes.POINTER(FILE)

######################## String conversions ##########################


def _string_to_char(x):
    return x.encode()


def _char_to_string(x):
    return x.decode()


def _convert_strings(fn):

    convert = False

    for a in fn.argtypes:
        if a is c_char_p:
            convert = True

    if fn.restype is c_char_p:
        convert = True

    if not convert:
        return fn

    def wrapped(*args):

        new_args = []
        for a, t in zip(args, fn.argtypes):
            if t is c_char_p:
                a = string_to_char(a)
            new_args.append(a)

        r = fn(*new_args)
        if fn.restype is c_char_p:
            r = char_to_string(r)
        return r

    return wrapped


if sys.version_info[0] > 2:
    convert_strings = _convert_strings
    char_to_string = _char_to_string
    string_to_char = _string_to_char
else:
    convert_strings = lambda x: x
    char_to_string = lambda x: x
    string_to_char = lambda x: x


####################################################################
c_int = ctypes.c_int
c_int_p = ctypes.POINTER(c_int)

c_double = ctypes.c_double
c_double_p = ctypes.POINTER(c_double)

c_char = ctypes.c_char
c_char_p = ctypes.c_char_p

c_void_p = ctypes.c_void_p


####################################################################
def checked_error_in_last_paramater(fn):
    def wrapped(*args):
        err = c_int(0)
        err_p = ctypes.cast(ctypes.addressof(err), c_int_p)
        params = [a for a in args]
        params.append(err_p)

        result = fn(*params)
        if err.value:
            raise MagicsError(err)
        return result

    return wrapped


def checked_return_code(fn):
    def wrapped(*args):
        err = fn(*args)
        if err:
            raise MagicsError(err)

    return wrapped


####################################################################


def return_type(fn, ctype):
    def wrapped(*args):
        result = ctype()
        result_p = ctypes.cast(ctypes.addressof(result), ctypes.POINTER(ctype))
        params = [a for a in args]
        params.append(result_p)
        fn(*params)
        return result.value

    return wrapped


####################################################################


@checked_return_code
def init():
    return dll.py_open()


####################################################################


@checked_return_code
def finalize():
    return dll.py_close()


####################################################################


@checked_return_code
def coast():
    return dll.py_coast()


####################################################################
@checked_return_code
def grib():
    return dll.py_grib()


def oldversion():
    msg = "You are using an old version of magics ( < 4.0.0)"
    return msg.encode()


try:
    version = dll.version
    version.restype = ctypes.c_char_p
    version.argtypes = None
except:
    version = oldversion

try:
    tile = dll.py_tile
except:
    print("Tile not enabled: You are using an old version of magics ( < 4.1.0)")
    tile = oldversion


home = dll.home
home.restype = ctypes.c_char_p
home.argtypes = None

metanetcdf = dll.py_metanetcdf
metanetcdf.restype = ctypes.c_char_p
metanetcdf.argtypes = None

metagrib = dll.py_metagrib
metagrib.restype = ctypes.c_char_p
metagrib.argtypes = None

metainput = dll.py_metainput
metainput.restype = ctypes.c_char_p
metainput.argtypes = None


detect = dll.detect
detect.restype = ctypes.c_char_p
detect.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
detect = convert_strings(detect)


####################################################################


@checked_return_code
def cont():
    return dll.py_cont()


####################################################################


@checked_return_code
def legend():
    return dll.py_legend()


####################################################################


@checked_return_code
def odb():
    return dll.py_odb()


####################################################################


@checked_return_code
def obs():
    return dll.py_obs()


####################################################################


@checked_return_code
def raw():
    return dll.py_raw()


####################################################################


@checked_return_code
def netcdf():
    return dll.py_netcdf()


####################################################################


@checked_return_code
def image():
    return dll.py_image()


####################################################################


@checked_return_code
def plot():
    return dll.py_plot()


####################################################################


@checked_return_code
def text():
    return dll.py_text()


####################################################################


@checked_return_code
def wind():
    return dll.py_wind()


####################################################################


@checked_return_code
def line():
    return dll.py_line()


####################################################################


@checked_return_code
def symb():
    return dll.py_symb()


####################################################################


@checked_return_code
def boxplot():
    return dll.py_boxplot()


####################################################################


@checked_return_code
def taylor():
    return dll.py_taylor()


####################################################################


@checked_return_code
def tephi():
    return dll.py_tephi()


####################################################################


@checked_return_code
def graph():
    return dll.py_graph()


####################################################################


@checked_return_code
def axis():
    return dll.py_axis()


####################################################################


@checked_return_code
def geo():
    return dll.py_geo()


####################################################################


@checked_return_code
def mimport():
    return dll.py_import()


####################################################################


@checked_return_code
def info():
    return dll.py_info()


####################################################################


@checked_return_code
def minput():
    return dll.py_input()


####################################################################


@checked_return_code
def eps():
    return dll.py_eps()


####################################################################
###
###  Please note: these two functions changed compared to the previous SWIG based Python interface
###
@checked_return_code
def metgraph():
    return dll.py_metgraph()


@checked_return_code
def epsinput():
    return dll.py_epsinput()


####################################################################
###
###  Please note: this function was called mmetbufr to the previous SWIG based Python interface
###
@checked_return_code
def metbufr():
    return dll.py_metbufr()


####################################################################


@checked_return_code
def epsgraph():
    return dll.py_epsgraph()


####################################################################


@checked_return_code
def epscloud():
    return dll.py_epscloud()


####################################################################


@checked_return_code
def epslight():
    return dll.py_epslight()


####################################################################


@checked_return_code
def epsplumes():
    return dll.py_epsplumes()


####################################################################


@checked_return_code
def epswind():
    return dll.py_epswind()


####################################################################


@checked_return_code
def epswave():
    return dll.py_epswave()


####################################################################


@checked_return_code
def epsbar():
    return dll.py_epsbar()


####################################################################


@checked_return_code
def epsshading():
    return dll.py_epsshading()


####################################################################


@checked_return_code
def wrepjson():
    return dll.py_wrepjson()


####################################################################


@checked_return_code
def geojson():
    return dll.py_geojson()


####################################################################


@checked_return_code
def mapgen():
    return dll.py_mapgen()


####################################################################


@checked_return_code
def mtable():
    return dll.py_table()


####################################################################


@checked_return_code
def seti(name, value):
    name = string_to_char(name)
    return dll.py_seti(name, value)


def known_drivers():
    try:
        drivers = dll.py_knowndrivers()
        drivers = json.loads(drivers.decode())

        return drivers["drivers"]
    except:
        return "known_drivers is not implemented in this version"


####################################################################
@checked_return_code
def set1i(name, data):
    #    array = np.empty((size,), dtype=np.float64)
    #    array_p = array.ctypes.data_as(c_double_p)
    #    _set1r(name, array_p, size)
    size = len(data)
    name = string_to_char(name)
    array_p = (ctypes.c_int * size)(*data)
    return dll.py_set1i(ctypes.c_char_p(name), array_p, size)
    return None


####################################################################

array_2d_int = ndpointer(dtype=np.int, ndim=2, flags="CONTIGUOUS")
set2i = dll.py_set2i
set2i.restype = None
set2i.argtypes = (c_char_p, array_2d_int, c_int, c_int)
set2i = convert_strings(set2i)

####################################################################

setr = dll.py_setr
setr.restype = None
setr.argtypes = (c_char_p, c_double)
setr = convert_strings(setr)

####################################################################
@checked_return_code
def set1r(name, data):
    size = len(data)
    name = string_to_char(name)
    array_p = (ctypes.c_double * size)(*data)
    return dll.py_set1r(ctypes.c_char_p(name), array_p, size)


####################################################################

array_2d_double = ndpointer(dtype=np.double, ndim=2, flags="CONTIGUOUS")
set2r = dll.py_set2r
set2r.restype = None
set2r.argtypes = (c_char_p, array_2d_double, c_int, c_int)
set2r = convert_strings(set2r)

####################################################################

setc = dll.py_setc
setc.restype = None
setc.argtypes = (c_char_p, c_char_p)
setc = convert_strings(setc)

####################################################################
@checked_return_code
def set1c(name, data):
    new_data = []
    for s in data:
        new_data.append(string_to_char(s))
    name = string_to_char(name)
    data_p = (c_char_p * (len(new_data)))(*new_data)
    return dll.py_set1c(ctypes.c_char_p(name), data_p, len(new_data))


####################################################################

new_page = dll.py_new
new_page.restype = None
new_page.argtypes = (c_char_p,)
new_page = convert_strings(new_page)

####################################################################

reset = dll.py_reset
reset.restype = None
reset.argtypes = (c_char_p,)
reset = convert_strings(reset)

####################################################################


class MagicsError(Exception):
    def __init__(self, err):
        super(MagicsError, self).__init__(
            "Magics Error - No Plot Produced!!! (%s)" % err
        )


####################################################################


def no_log(a, b):
    print(
        "Log listeners not handled in this version, consider using a version > 4.0.0 "
    )


def not_implemented():
    print("Not Implemented, consider upgrading a version > 4.4.0 ")


try:
    set_python = dll.py_set_python
    set_python.restype = None
    set_python.argtypes = None

    keep_compatibility = dll.py_keep_compatibility
    keep_compatibility.restype = None
    keep_compatibility.argtypes = None

    mute = dll.py_mute
    mute.restype = None
    mute.argtypes = None

    unmute = dll.py_unmute
    unmute.restype = None
    unmute.argtypes = None

    knowndrivers = dll.py_knowndrivers
    knowndrivers.restype = ctypes.c_char_p
    knowndrivers.argtypes = None

except:
    set_python = not_implemented
    keep_compatibility = not_implemented
    mute = not_implemented
    unmute = not_implemented
    knowndrivers = not_implemented


log = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, c_char_p)

try:
    warning_log = dll.mag_add_warning_listener
    warning_log.restype = None
    warning_log.argtypes = (ctypes.c_void_p, log)

    error_log = dll.mag_add_error_listener
    error_log.restype = None
    error_log.argtypes = (ctypes.c_void_p, log)

    info_log = dll.mag_add_info_listener
    info_log.restype = None
    info_log.argtypes = (ctypes.c_void_p, log)

    debug_log = dll.mag_add_debug_listener
    debug_log.restype = None
    debug_log.argtypes = (ctypes.c_void_p, log)
except:
    error_log = no_log
    warning_log = no_log
    debug_log = no_log
    info_log = no_log


@log
def magics_log(data, msg):
    print("SUPER-->", msg.decode())
    return 0


# if __name__ == "__main__":
#    print "..."
