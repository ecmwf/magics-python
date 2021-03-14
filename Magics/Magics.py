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
import json
import os
import sys

import numpy as np
from numpy.ctypeslib import ndpointer

#
#  This Python interface needs to find the Magics library
#
#  We first search LD_LIBRARY_PATH. If you have strange behaviours,
#  check your $LD_LIBRARY_PATH.
#  This is only required on Linux! Therefore we do not have to check
#  on MacOS the DYLD_LIBRARY_PATH or for *.dylib.
#
lib = None

try:
    import ecmwflibs

    lib = ecmwflibs.find("MagPlus")
except Exception:
    pass

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
        else:
            fullname = os.path.join(
                os.environ.get("MAGPLUS_HOME", ""), "lib64/libMagPlus.so"
            )
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
            raise MagicsError(char_to_string(err))

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

py_open = dll.py_open
py_open.restype = c_char_p


@checked_return_code
def init():
    return py_open()


####################################################################

py_close = dll.py_close
py_close.restype = c_char_p


@checked_return_code
def finalize():
    return py_close()


####################################################################

py_coast = dll.py_coast
py_coast.restype = c_char_p


@checked_return_code
def coast():
    return py_coast()


####################################################################

py_grib = dll.py_grib
py_grib.restype = c_char_p


@checked_return_code
def grib():
    return py_grib()


def oldversion():
    msg = "You are using an old version of magics ( < 4.0.0)"
    return msg.encode()


try:
    version = dll.version
    version.restype = ctypes.c_char_p
    version.argtypes = None
except Exception:
    version = oldversion

try:
    tile = dll.py_tile
except Exception:
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


try:
    py_detect = dll.py_detect
    py_detect.restype = ctypes.c_char_p
    py_detect.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
    py_detect = convert_strings(py_detect)

    detect = py_detect

except Exception:
    detect = dll.detect
    detect.restype = ctypes.c_char_p
    detect.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
    detect = convert_strings(detect)

####################################################################

py_cont = dll.py_cont
py_cont.restype = c_char_p


@checked_return_code
def cont():
    return py_cont()


####################################################################
py_legend = dll.py_legend
py_legend.restype = c_char_p


@checked_return_code
def legend():
    return py_legend()


####################################################################

py_odb = dll.py_odb
py_odb.restype = c_char_p


@checked_return_code
def odb():
    return py_odb()


####################################################################

py_obs = dll.py_obs
py_obs.restype = c_char_p


@checked_return_code
def obs():
    return py_obs()


####################################################################


py_raw = dll.py_raw
py_raw.restype = c_char_p


@checked_return_code
def raw():
    return py_raw()


####################################################################

py_netcdf = dll.py_netcdf
py_netcdf.restype = c_char_p


@checked_return_code
def netcdf():
    return py_netcdf()


####################################################################

py_image = dll.py_image
py_image.restype = c_char_p


@checked_return_code
def image():
    return py_image()


####################################################################

py_plot = dll.py_plot
py_plot.restype = c_char_p


@checked_return_code
def plot():
    return py_plot()


####################################################################
py_text = dll.py_text
py_text.restype = c_char_p


@checked_return_code
def text():
    return py_text()


####################################################################

py_wind = dll.py_wind
py_wind.restype = c_char_p


@checked_return_code
def wind():
    return py_wind()


####################################################################

py_line = dll.py_line
py_line.restype = c_char_p


@checked_return_code
def line():
    return py_line()


####################################################################

py_symb = dll.py_symb
py_symb.restype = c_char_p


@checked_return_code
def symb():
    return py_symb()


####################################################################
py_boxplot = dll.py_boxplot
py_boxplot.restype = c_char_p


@checked_return_code
def boxplot():
    return py_boxplot()


####################################################################

py_taylor = dll.py_taylor
py_taylor.restype = c_char_p


@checked_return_code
def taylor():
    return py_taylor()


####################################################################

py_tephi = dll.py_tephi
py_tephi.restype = c_char_p


@checked_return_code
def tephi():
    return py_tephi()


####################################################################

py_graph = dll.py_graph
py_graph.restype = c_char_p


@checked_return_code
def graph():
    return py_graph()


####################################################################

py_axis = dll.py_axis
py_axis.restype = c_char_p


@checked_return_code
def axis():
    return py_axis()


####################################################################


py_geo = dll.py_geo
py_geo.restype = c_char_p


@checked_return_code
def geo():
    return py_geo()


####################################################################
py_import = dll.py_import
py_import.restype = c_char_p


@checked_return_code
def mimport():
    return py_import()


####################################################################
py_info = dll.py_info
py_info.restype = c_char_p


@checked_return_code
def info():
    return py_info()


####################################################################

py_input = dll.py_input
py_input.restype = c_char_p


@checked_return_code
def minput():
    return py_input()


####################################################################
py_eps = dll.py_eps
py_eps.restype = c_char_p


@checked_return_code
def eps():
    return py_eps()


####################################################################
###
###  Please note: these two functions changed compared to the previous SWIG based Python interface
###

py_metgraph = dll.py_metgraph
py_metgraph.restype = c_char_p


@checked_return_code
def metgraph():
    return py_metgraph()


py_epsinput = dll.py_epsinput
py_epsinput.restype = c_char_p


@checked_return_code
def epsinput():
    return py_epsinput()


####################################################################
###
###  Please note: this function was called mmetbufr to the previous SWIG based Python interface
###

py_metbufr = dll.py_metbufr
py_metbufr.restype = c_char_p


@checked_return_code
def metbufr():
    return py_metbufr()


####################################################################

py_epsgraph = dll.py_epsgraph
py_epsgraph.restype = c_char_p


@checked_return_code
def epsgraph():
    return py_epsgraph()


####################################################################

py_epscloud = dll.py_epscloud
py_epscloud.restype = c_char_p


@checked_return_code
def epscloud():
    return py_epscloud()


####################################################################
py_epslight = dll.py_epslight
py_epslight.restype = c_char_p


@checked_return_code
def epslight():
    return py_epslight()


####################################################################

py_epsplumes = dll.py_epsplumes
py_epsplumes.restype = c_char_p


@checked_return_code
def epsplumes():
    return py_epsplumes()


####################################################################
py_epswind = dll.py_epswind
py_epswind.restype = c_char_p


@checked_return_code
def epswind():
    return py_epswind()


####################################################################
py_epswave = dll.py_epswave
py_epswave.restype = c_char_p


@checked_return_code
def epswave():
    return py_epswave()


####################################################################

py_epsbar = dll.py_epsbar
py_epsbar.restype = c_char_p


@checked_return_code
def epsbar():
    return py_epsbar()


####################################################################

py_epsshading = dll.py_epsshading
py_epsshading.restype = c_char_p


@checked_return_code
def epsshading():
    return py_epsshading()


####################################################################

py_wrepjson = dll.py_wrepjson
py_wrepjson.restype = c_char_p


@checked_return_code
def wrepjson():
    return py_wrepjson()


####################################################################


py_geojson = dll.py_geojson
py_geojson.restype = c_char_p


@checked_return_code
def geojson():
    return py_geojson()


####################################################################

py_mapgen = dll.py_mapgen
py_mapgen.restype = c_char_p


@checked_return_code
def mapgen():
    return py_mapgen()


####################################################################


py_table = dll.py_table
py_table.restype = c_char_p


@checked_return_code
def mtable():
    return py_table()


####################################################################

py_seti = dll.py_seti
py_seti.restype = c_char_p
# py_seti.argtypes = (c_char,)


@checked_return_code
def seti(name, value):
    name = string_to_char(name)
    return py_seti(name, value)


def known_drivers():
    try:
        drivers = dll.py_knowndrivers()
        drivers = json.loads(drivers.decode())

        return drivers["drivers"]
    except Exception:
        return "known_drivers is not implemented in this version"


####################################################################
py_set1i = dll.py_set1i
py_set1i.restype = c_char_p
# py_set1i.argtypes = (c_char_p, c_int_p, c_int)


@checked_return_code
def set1i(name, data):
    #    array = np.empty((size,), dtype=np.float64)
    #    array_p = array.ctypes.data_as(c_double_p)
    #    _set1r(name, array_p, size)
    size = len(data)
    name = string_to_char(name)
    array_p = (ctypes.c_int * size)(*data)
    return py_set1i(ctypes.c_char_p(name), array_p, size)


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
py_set1r = dll.py_set1r
py_set1r.restype = c_char_p
# py_set1r.argtypes = (c_char_p, c_double_p, c_int)


@checked_return_code
def set1r(name, data):
    size = len(data)
    name = string_to_char(name)
    array_p = (ctypes.c_double * size)(*data)
    return py_set1r(ctypes.c_char_p(name), array_p, size)


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

py_set1c = dll.py_set1c
py_set1c.restype = c_char_p
# py_set1c.argtypes = (c_char_p, c_char_p, c_int)


@checked_return_code
def set1c(name, data):
    new_data = []
    for s in data:
        new_data.append(string_to_char(s))
    name = string_to_char(name)
    data_p = (c_char_p * (len(new_data)))(*new_data)
    return py_set1c(ctypes.c_char_p(name), data_p, len(new_data))


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
        super(MagicsError, self).__init__(str(err))


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

except Exception:
    set_python = not_implemented
    keep_compatibility = not_implemented
    mute = not_implemented
    unmute = not_implemented
    knowndrivers = not_implemented

try:
    strict_mode = dll.py_strict_mode
    strict_mode.restype = None
    strict_mode.argtypes = None
except Exception:
    strict_mode = not_implemented


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
except Exception:
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
