# (C) Copyright 1996-2016 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.

import json
import os
import sys
import tempfile
import threading

import numpy

from . import Magics

LOCK = threading.RLock()

ipython_active = None
try:
    from IPython import get_ipython

    ipython_active = get_ipython()
except Exception:
    pass


class Context(object):
    def __init__(self):
        with LOCK:
            self.tmp = []
            Magics.set_python()
            self.silent = True

    def set(self):
        with LOCK:
            if self.silent:
                os.environ["MAGPLUS_WARNING"] = "off"
                Magics.mute()
            else:
                os.environ["MAGPLUS_INFO"] = "on"


global context

context = Context()


def silent():
    context.silent = False


def unmute():
    context.silent = False


def mute():
    context.silent = True


def keep_compatibility():
    with LOCK:
        Magics.keep_compatibility()


@Magics.log
def warning(int, msg):
    try:
        print(msg.decode().rstrip())
    except Exception:
        print(msg)


@Magics.log
def error(int, msg):
    try:
        print(msg.decode().rstrip())
    except Exception:
        print(msg)


@Magics.log
def info_log(int, msg):
    try:
        print(msg.decode().rstrip())
    except Exception:
        print(msg)


@Magics.log
def debug_log(int, msg):
    try:
        print(msg.decode().rstrip())
    except Exception:
        print(msg)


Magics.warning_log(3, warning)
Magics.error_log(3, error)


def debug():
    Magics.debug_log(3, debug_log)


def info():
    Magics.info_log(3, info_log)


actions = {
    "mobs": "pobs",
    "mcoast": "pcoast",
    "pcoast": "pcoast",
    "mtext": "ptext",
    "ptext": "ptext",
    "psymb": "psymb",
    "msymb": "psymb",
    "pcont": "pcont",
    "mcont": "pcont",
    "pgeo": "pgeo",
    "mgeojson": "pgeojson",
    "mgeo": "pgeo",
    "mlegend": "",
    "plegend": "",
    "mgrib": "pgrib",
    "pgrib": "pgrib",
    "mwind": "pwind",
    "pwind": "pwind",
    "mgraph": "pgraph",
    "pgraph": "pgraph",
    "maxis": "paxis",
    "paxis": "paxis",
    "minput": "pinput",
    "mtable": "ptable",
    "ptable": "ptable",
    "pboxplot": "pboxplot",
    "mboxplot": "pboxplot",
    "pinput": "pinput",
}


class Action(object):
    def __init__(self, verb, action, html, args):
        self.verb = verb
        self.action = action

        if verb == "output" and not ("output_formats" in args):
            args["output_formats"] = ["png"]

        self.args = args
        if html == "":
            self.html = verb
        else:
            self.html = "<a href=/wiki/display/MAGP/%s target='_blank'>%s</a>" % (
                html,
                verb,
            )

    def __repr__(self):
        x = ""
        for key in list(self.args.keys()):
            x = x + " %s = '%s'\n" % (key, self.args[key])
        return x

    def inspect(self):
        print(self)

    def quote(self, v):
        return '"' + v + '"'

    def to_yaml(self):
        def tidy(x):
            if isinstance(x, (list, tuple)):
                return [tidy(y) for y in x]

            if isinstance(x, dict):
                d = {}
                for k, v in x.items():
                    d[k] = tidy(v)
                return d

            # Numpy arrays
            if hasattr(x, "tolist"):
                return x.tolist()

            if x in ("on", "true", "yes"):
                return True

            if x in ("off", "false", "no"):
                return False

            return x

        return {self.verb: tidy(self.args)}

    def clean_object(self, obj):
        if sys.version_info[0] < 3:
            if type(obj) in (int, float, str, bool, numpy.float64, numpy.float32):
                return obj
            elif type(obj) == unicode:  # noqa
                return str(obj)
            elif type(obj) in (list, tuple, set, numpy.ndarray) and len(obj):
                if type(obj[0]) != unicode:  # noqa
                    return obj
                obj = list(obj)
                for i, v in enumerate(obj):
                    obj[i] = self.clean_object(v)
            elif type(obj) == dict:
                for i, v in list(obj.items()):
                    obj[i] = self.clean_object(v)
            else:
                print("Invalid object in data, converting to string: ")
                print(type(obj))
                obj = str(obj)
        return obj

    def find_type(self, data):
        for v in data:
            if not isinstance(v, int):
                return "float"
        return "int"
    
    def patch_setli(self, param, value):
        params = Magics.long_parameters()
        if param in params.keys():
            if ( value > 2147483647 ):
                Magics.setli(params[param], value)
                return True
        return False


    def set(self):  # noqa C901
        for key in list(self.args.keys()):
            
            if (self.patch_setli(key, self.args[key])):
                pass

            elif isinstance(self.args[key], dict):
                Magics.setc(key, json.dumps(self.args[key]))
            elif isinstance(self.args[key], bool):
                if self.args[key]:
                    Magics.setc(key, "on")
                else:
                    Magics.setc(key, "off")
            elif isinstance(self.args[key], str):
                if key == "odb_data":
                    Magics.setc("odb_filename", self.args[key])
                else:
                    Magics.setc(key, self.args[key])
            elif isinstance(self.args[key], int):
                Magics.seti(key, self.args[key])
            elif isinstance(self.args[key], float):
                Magics.setr(key, self.args[key])
            elif isinstance(self.args[key], list) and len(self.args[key]):
                if isinstance(self.args[key][0], str):
                    Magics.set1c(key, self.args[key])
                elif isinstance(self.args[key][0], dict):
                    np = []
                    for p in self.args[key]:
                        np.append(json.dumps(p))
                    Magics.set1c(key, np)
                else:
                    type = self.find_type(self.args[key])
                    if type == "int":
                        Magics.set1i(key, numpy.array(self.args[key], dtype="i"))
                    else:
                        Magics.set1r(key, numpy.array(self.args[key]))
            elif isinstance(self.args[key], numpy.ndarray):
                type = self.args[key].dtype
                data = self.args[key].copy()
                size = data.shape
                dim = len(size)
                type = self.find_type(self.args[key])
                if type == "int":
                    if dim == 2:
                        Magics.set2i(key, data.astype(numpy.int64), size[0], size[1])
                    else:
                        Magics.set1i(key, data.astype(numpy.int64), size[0])
                elif type == "float":
                    if dim == 2:
                        Magics.set2r(key, data.astype(numpy.float64), size[1], size[0])
                    else:
                        Magics.set1r(key, data.astype(numpy.float64))
                else:
                    print("can not interpret type %s for %s ???->", (type, key))
            else:
                self.args[key].execute(key)

    def execute(self):

        if self.action != Magics.odb:
            self.args = self.clean_object(self.args)

        self.set()

        if self.action is not None:
            if self.action != Magics.new_page:
                if self.action == Magics.legend:
                    Magics.setc("legend", "on")
                self.action()
                if self.action != Magics.obs and self.action != Magics.minput:
                    for key in list(self.args.keys()):
                        Magics.reset(key)
            else:
                self.action("page")

    def style(self):

        if self.action not in [Magics.grib, Magics.netcdf, Magics.minput]:
            return {}

        self.args = self.clean_object(self.args)

        self.set()
        if self.action == Magics.grib:
            return Magics.metagrib()
        if self.action == Magics.netcdf:
            return Magics.metanetcdf()
        if self.action == Magics.minput:
            return Magics.metainput()


def encode_numpy(np_obj):
    """
    Encode numpy objects to their python equivalents.
    e.g. numpy.int32 -> int

    This is necessary because json is unable to serialize numpy types natively.
    """
    if isinstance(np_obj, numpy.ndarray):
        # Nested array elements are cast from numpy.generic to Python object
        return np_obj.tolist()
    elif isinstance(np_obj, numpy.generic):
        return np_obj.item()
    else:
        raise TypeError(
            "Object of type '{}' is not JSON serializable".format(type(np_obj))
        )


def detect(attributes, dimension):
    return Magics.detect(json.dumps(attributes, default=encode_numpy), dimension)


def detect_lat_lon(xarray_dataset, ds_attributes):
    attrs = {
        ds_attribute: xarray_dataset[ds_attribute].attrs
        for ds_attribute in ds_attributes
    }
    lat_name = detect(attrs, "latitude")
    lon_name = detect(attrs, "longitude")
    return lat_name, lon_name


def mxarray(xarray_dataset, xarray_variable_name, xarray_dimension_settings={}):
    """
    Convert an xarray dataset containing a variable with latitude and longitude data into
    magics.minput.
    """
    # usually we find latitude and longitude in xarray_dataset.coords, but we sometimes see 2d
    # lat/lon data in xarray_dataset.data_vars instead.
    for ds_attributes in [xarray_dataset.coords, xarray_dataset.data_vars]:
        ret = _mxarray(
            xarray_dataset,
            xarray_variable_name,
            ds_attributes,
            xarray_dimension_settings,
        )
        if ret:
            return ret

    raise ValueError("Could not find latitude and longitude in dataset")


def _mxarray(
    xarray_dataset, xarray_variable_name, ds_attributes, xarray_dimension_settings
):
    lat_name, lon_name = detect_lat_lon(xarray_dataset, ds_attributes)

    if lat_name and lon_name:
        lat_dim_names = sorted(xarray_dataset[lat_name].dims)
        lon_dim_names = sorted(xarray_dataset[lon_name].dims)
        n_lat_dims = len(lat_dim_names)
        n_lon_dims = len(lon_dim_names)

        if n_lat_dims != n_lon_dims:
            raise ValueError(
                "Dimension mismatch for latitude and longitude. "
                "lat_dim_names={} lon_dim_names={}".format(lat_dim_names, lon_dim_names)
            )
        elif n_lat_dims == 1:
            return _mxarray_1d(
                xarray_dataset,
                xarray_variable_name,
                lat_name,
                lon_name,
                xarray_dimension_settings,
            )
        elif n_lat_dims == 2:
            return _mxarray_2d(
                xarray_dataset,
                xarray_variable_name,
                lat_name,
                lon_name,
                xarray_dimension_settings,
                lat_dim_names,
            )
        else:
            raise ValueError(
                "Found latitude and longitude with more than 2 dimensions. "
                "lat_dim_names={} lon_dim_names={}".format(lat_dim_names, lon_dim_names)
            )


def _mxarray_1d(
    xarray_dataset, xarray_variable_name, lat_name, lon_name, xarray_dimension_settings
):
    lat = xarray_dataset[lat_name].values.astype(numpy.float64)
    lon = xarray_dataset[lon_name].values.astype(numpy.float64)
    input_field_values = _mxarray_flatten(
        xarray_dataset[xarray_variable_name],
        xarray_dimension_settings,
        [lat_name, lon_name],
    ).values.astype(numpy.float64)

    data = minput(
        input_field=input_field_values,
        input_latitudes_list=lat,
        input_longitudes_list=lon,
        input_metadata=dict(xarray_dataset[xarray_variable_name].attrs),
    )
    return data


def _mxarray_2d(
    xarray_dataset,
    xarray_variable_name,
    lat_name,
    lon_name,
    xarray_dimension_settings,
    dims_to_ignore,
):
    lat = xarray_dataset[lat_name].values.astype(numpy.float64)
    lon = xarray_dataset[lon_name].values.astype(numpy.float64)
    input_field_values = _mxarray_flatten(
        xarray_dataset[xarray_variable_name], xarray_dimension_settings, dims_to_ignore
    ).values.astype(numpy.float64)

    data = minput(
        input_field=input_field_values,
        input_field_organization="nonregular",
        input_field_latitudes=lat,
        input_field_longitudes=lon,
        input_metadata=dict(xarray_dataset[xarray_variable_name].attrs),
    )
    return data


def _mxarray_flatten(xarray_dataset, dims_to_flatten, dims_to_ignore):
    # flatten an nD matrix into a 2d matrix by slicing the matrix based on the values given to
    # dimensions in dims_to_flatten.
    for dim in xarray_dataset.dims:
        if dim in dims_to_ignore:
            continue
        elif dim in dims_to_flatten:
            if dims_to_flatten[dim] not in xarray_dataset[dim]:
                raise ValueError(
                    "Dimension not valid. dimension={} dtype={} options={} dtype={}".format(
                        dim,
                        type(dim),
                        xarray_dataset[dim].values,
                        xarray_dataset[dim].dtype,
                    )
                )
            else:
                xarray_dataset = xarray_dataset.loc[{dim: dims_to_flatten[dim]}]
        elif xarray_dataset[dim].size == 1:
            # automatically squash this dimension
            d = xarray_dataset[dim].values[0]
            print("automatically squashing dimension: {}={}".format(dim, d))
            xarray_dataset = xarray_dataset.loc[{dim: d}]
        else:
            raise ValueError(
                "Missing dimension to flatten. "
                "Please pick a dimension from which to slice data. "
                "dimension={} options={} dtype={}".format(
                    dim, xarray_dataset[dim].values, xarray_dataset[dim].dtype
                )
            )
    return xarray_dataset


def make_action(verb, action, html=""):
    def f(_m=None, **kw):
        args = {}
        if _m is not None:
            args.update(_m)
        args.update(kw)
        return Action(verb, action, html, args)

    return f


mcoast = make_action("mcoast", Magics.coast, "Coastlines")
pcoast = make_action("pcoast", Magics.coast)
maxis = make_action("maxis", Magics.axis, "Axis")
paxis = make_action("paxis", Magics.axis)
mcont = make_action("mcont", Magics.cont, "Contouring")
pcont = make_action("pcont", Magics.cont)
msymb = make_action("msymb", Magics.symb, "Symbol")
psymb = make_action("psymb", Magics.symb)
pimport = make_action("pimport", Magics.mimport)
mimport = make_action("mimport", Magics.mimport)
mtaylor = make_action("mtaylor", Magics.taylor)
mgeo = make_action("mgeo", Magics.geo)
pgeo = make_action("pgeo", Magics.geo)
pgrib = make_action("pgrib", Magics.grib, "Grib+Input")
mgrib = make_action("mgrib", Magics.grib, "Grib+Input")
pmapgen = make_action("pmapgen", Magics.mapgen)
mmapgen = make_action("mmapgen", Magics.mapgen)
pnetcdf = make_action("pnetcdf", Magics.netcdf)
mnetcdf = make_action("mnetcdf", Magics.netcdf)
odb_geopoints = make_action("odb_geopoints", Magics.odb, "Odbviewer")
odb_geovectors = make_action("odb_geovectors", Magics.odb, "Odbviewer")
odb_xypoints = make_action("odb_xypoints", Magics.odb, "Odbviewer")
odb_xyvectors = make_action("odb_xyvectors", Magics.odb, "Odbviewer")
pmap = make_action("pmap", None, "Subpage")
mmap = make_action("mmap", None, "Subpage")
plegend = make_action("plegend", Magics.legend, "Legend")
mlegend = make_action("mlegend", Magics.legend, "Legend")
ptext = make_action("mtext", Magics.text)
mtext = make_action("mtext", Magics.text)
output = make_action("output", None, "PNG Output")
pwind = make_action("pwind", Magics.wind, "Wind+Plotting")
mwind = make_action("mwind", Magics.wind, "Wind+Plotting")
pline = make_action("pline", Magics.line)
mline = make_action("mline", Magics.line)
pgraph = make_action("pgraph", Magics.graph, "Graph+Plotting")
mgraph = make_action("mgraph", Magics.graph, "Graph+Plotting")
pboxplot = make_action("pboxplot", Magics.boxplot)
mboxplot = make_action("mboxplot", Magics.boxplot)
pobs = make_action("pobs", Magics.obs)
mobs = make_action("mobs", Magics.obs)
page = make_action("page", Magics.new_page)
pinput = make_action("pinput", Magics.minput)
minput = make_action("minput", Magics.minput, "Input+Data")
mtable = make_action("mtable", Magics.mtable, "CSV+Table+Decoder")
mgeojson = make_action("mgeojson", Magics.geojson, "GeoJSon")
mwrepjson = make_action("mwrepjson", Magics.wrepjson, "WrepJSon")
mepsinput = make_action("mepsinput", Magics.epsinput, "EpsInput")
mepscloud = make_action("mepscloud", Magics.epscloud)
mepslight = make_action("mepslight", Magics.epslight)
mepsbar = make_action("mepsbar", Magics.epsbar)
mepswind = make_action("mepswind", Magics.epswind)
mepswave = make_action("mepswave", Magics.epswave)
mepsshading = make_action("mepsshading", Magics.epsshading)
mepsgraph = make_action("mepsgraph", Magics.epsgraph)
mepsplumes = make_action("mepsplumes", Magics.epsplumes)
mtephi = make_action("mtephi", Magics.tephi)
mtile = make_action("mtile", Magics.tile)

mmetgraph = make_action("mmetgraph", Magics.metgraph)
mmetbufr = make_action("mmetbufr", Magics.metbufr)


def examine(*args):
    for n in args:
        try:
            n.inspect()
        except Exception:
            break


def _execute(o):
    if isinstance(o, (list, tuple)):
        for x in o:
            _execute(x)
    else:
        o.execute()


def _plot(*args):

    if os.environ.get("MAGICS_DUMP_YAML"):
        import yaml

        actions = []
        for n in args:
            if isinstance(n, (list, tuple)):
                for v in n:
                    actions.append(v.to_yaml())
            else:
                actions.append(n.to_yaml())
        print(yaml.dump(dict(plot=actions), default_flow_style=False))
        return

    context.set()
    # try :
    Magics.init()
    for n in args:
        _execute(n)

    # Collect the drivers!
    Magics.finalize()
    for f in context.tmp:
        if os.path.exists(f):
            os.remove(f)
    # except:
    # print ("Magics Error")


def tofortran(file, *args):
    return
    f = open(file + ".f90", "w")
    print(f, "\tprogram magics\n")
    print(f, "\tcall popen\n")
    for n in args:
        n.tofortran(f)
    print(f, "\tcall pclose\n")
    print(f, "\tend")


def tohtml(file, *args):
    return
    f = open(file + ".html", "w")
    print(f, "<html>")
    for n in args:
        n.tohtml(f)
    print(f, "</html>")


def tomv4(file, *args):
    return
    f = open(file + ".mv4", "w")
    for n in args:
        n.tomv4(f)


class odb_filter(object):
    def __init__(self, _m=None, **kw):
        args = {}
        self.verb = "odbfilter"
        if _m is not None:
            args.update(_m)
        self.args = args

    def execute(self, key):
        file = "data%d" % numpy.random.randint(1, 1000)
        odb = "%s.odb" % file
        context.tmp.append(odb)
        cmd = (
            'odbsql -q "'
            + self.args["query"]
            + '" -i '
            + self.args["path"]
            + " -f newodb -o "
            + odb
        )
        print(cmd)
        if os.system(cmd):
            print("Error in filtering ODB data... Aborting")
            os.abort()
        Magics.setc("odb_filename", odb)

    def inspect(self):
        cmd = (
            'odbsql -q "'
            + self.args["query"]
            + '" -i '
            + self.args["path"]
            + " -o data.ascii"
        )
        if os.system(cmd):
            print("Error in filtering ODB data... Aborting")
            os.abort()
        cmd = os.environ["ODB_REPORTER"] + " %s" % "data.ascii"
        if os.system(cmd):
            print("Error in viewing ODB data... Aborting")
            os.abort()


def _jplot(*args):
    from IPython.display import Image

    f, tmp = tempfile.mkstemp(".png")
    os.close(f)

    base, ext = os.path.splitext(tmp)

    img = output(
        output_formats=["png"],
        output_name_first_page_number="off",
        output_name=base,
    )

    all = [img]
    all.extend(args)

    _plot(all)

    image = Image(tmp)
    os.unlink(tmp)
    return image


def plot(*args, **kwargs):
    with LOCK:
        if ipython_active:
            return _jplot(*args, **kwargs)
        else:
            return _plot(*args, **kwargs)


def wmsstyles(data):
    with LOCK:
        context.set()
        try:
            Magics.init()
            styles = data.style()
            Magics.finalize()
            styles = json.loads(styles.decode())
            return styles
        except Exception:
            Magics.finalize()
            return {}


def known_drivers():
    with LOCK:
        return Magics.known_drivers()


def version():
    with LOCK:
        version = Magics.version()
        return version.decode()


def predefined_areas():
    with LOCK:
        home = Magics.home()
        with open("%s/share/magics/styles/projections.json" % (home.decode())) as input:
            projections = json.load(input)
        return list(projections.keys())


def wmscrs():
    os.environ["MAGPLUS_QUIET"] = "on"
    os.environ["MAGPLUS_WARNING"] = "off"
    return {
        "crss": [
            {
                "name": "EPSG:4326",
                "w_lon": -180.0,
                "s_lat": -90.0,
                "e_lon": 180.0,
                "n_lat": 90.0,
            },
            {
                "name": "EPSG:3857",
                "w_lon": -20026376.39,
                "s_lat": -20048966.10,
                "e_lon": 20026376.39,
                "n_lat": 20048966.10,
            },
            {
                "name": "EPSG:32661",
                "w_lon": 1994055.62,
                "s_lat": 5405875.53,
                "e_lon": 2000969.46,
                "n_lat": 2555456.55,
            },
            {
                "name": "EPSG:32762",
                "w_lon": 1999030.54,
                "s_lat": 1444543.45,
                "e_lon": 2005944.38,
                "n_lat": -1405875.53,
            },
            {  # 1896628.62,1507846.05,4662111.45,6829874.45
                # 1896628.62,1507846.05,4662111.45,6829874.45
                "name": "EPSG:3035",
                "w_lon": 1896628.62,
                "s_lat": 1507846.05,
                "e_lon": 4662111.45,
                "n_lat": 6829874.45,
            },
        ],
        "geographic_bounding_box": {
            "w_lon": -180.0,
            "e_lon": 180.0,
            "s_lat": -90.0,
            "n_lat": 90.0,
        },
    }


def get_library_path():
    return Magics.get_library_path()
