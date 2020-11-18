
Magics is the latest generation of the ECMWF's meteorological plotting software and can be either
accessed directly through its Python or Fortran interfaces or by using Metview.


Features:

- supports plotting of contours, wind fields, observations, satellite images, symbols, text, axis and graphs (including boxplots)
- can plot GRIB 1 and 2 coded data, gaussian grid, regularly spaced grid and fitted data

Limitations:

- development stage: **Alpha**,


Installation
------------

The package is installed from PyPI with::

    $ pip install Magics


System dependencies
~~~~~~~~~~~~~~~~~~~

The python module depends on the ECMWF *Magics* library
that must be installed on the system and accessible as a shared library.
Some Linux distributions ship a binary version that may be installed with the standard package manager.
On Ubuntu 18.04 use the command::

    $ sudo apt-get install libmagplus3v5

As an alternative you may install the official source distribution
by following the instructions at
https://software.ecmwf.int/magics/Installation+Guide

Note that *Magics* support for the Windows operating system is experimental.

You may run a simple selfcheck command to ensure that your system is set up correctly::

    $ python -m Magics selfcheck
    Found: Magics '4.0.0'.
    Your system is ready.


Usage
-----

First, you need a well-formed GRIB file, if you don't have one at hand you can download our
a 2m temperature grib file::

    $ wget http://download.ecmwf.int/test-data/magics/2m_temperature.grib


You may try out the high level API in a python interpreter::



   from Magics import macro as magics

   name = 'magics'
   #Setting of the output file name
   output = magics.output(output_formats = ['png'],
    		output_name_first_page_number = "off",
    		output_name = "magics")

   #Import the  data
   data =  magics.mgrib(grib_input_file_name  = "2m_temperature.grib", )

   #Apply an automatic styling
   contour = magics.mcont( contour_automatic_setting = "ecmwf", )
   coast = magics.mcoast()
   magics.plot(output, data, contour, coast)


Running the test program will create a png named magics.png


You can find notebooks examples :
https://github.com/ecmwf/notebook-examples/tree/master/visualisation

Contributing
------------

The main repository is hosted on GitHub,
testing, bug reports and contributions are highly welcomed and appreciated:

https://github.com/ecmwf/magics-python

Please see the CONTRIBUTING.rst document for the best way to help.

Lead developer:

- `Sylvie Lamy-Thepaut <https://github.com/sylvielamythepaut>`_ - ECMWF

Main contributors:

- `Stephan Siemen <https://github.com/stephansiemen>`_ - ECMWF
- `Alessandro Amici <https://github.com/alexamici>`_ - B-Open
- `Daniel Tipping <https://github.com/dtip>`_ - `Old Reliable <https://oldreliable.tech>`_
- `Ian Vermes <https://github.com/IanVermes>`_ - `Old Reliable <https://oldreliable.tech>`_

License
-------

Copyright 2017-2018 European Centre for Medium-Range Weather Forecasts (ECMWF).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0.
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

.. |Travis Build| image:: https://img.shields.io/travis/ecmwf/magics-python/master.svg?logo=travis
   :target: https://travis-ci.org/ecmwf/magics-python/branches
.. |Appveyor Build| image:: https://img.shields.io/appveyor/ci/ecmwf/magics-python/master.svg?logo=appveyor
   :target: https://ci.appveyor.com/project/ecmwf/magics-python/branch/master
.. |ReadTheDocs Build| image:: https://readthedocs.org/projects/magics-python/badge/?version=latest
    :target: https://magics-python.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
