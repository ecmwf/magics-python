"""Binary Driver"""
from collections import namedtuple
import struct
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
from mpl_toolkits.axes_grid1 import make_axes_locatable

LINE_STYLES = ("solid", "dashed", "dotted", "3", "4", "5")

H_ALIGN = ("left", "center", "right")

V_ALIGN = (
    "<????>normal",
    "top",
    "<????>cap",
    "center",
    "baseline",
    "bottom",
)


class BinaryReader:
    '''
    Class which contains functions for reading
    data types stored in C ++ binary format.
    '''
    def __init__(self, path):
        '''
        Init function which reads the binary format file.
        '''
        self.f = open(path, "rb")

    def read_char(self):
        '''
        Function to read Character data type.
        '''
        return self.f.read(1)

    def read_int(self):
        '''
        Function to read Integer data type.
        '''
        return struct.unpack("i", self.f.read(4))[0]

    def read_double(self):
        '''
        Function to read Double data type.
        '''
        return struct.unpack("d", self.f.read(8))[0]

    def read_bool(self):
        '''
        Function to read Boolean data type.
        '''
        return struct.unpack("c", self.f.read(1))[0] == b"\x01"

    def read_string(self, n=None):
        '''
        Function to read String data type.
        '''
        if n is None:
            n = self.read_int()
        return self.f.read(n).decode()

    def read_double_array(self, n):
        '''
        Function to read Array of Double data type.
        '''
        return np.fromfile(self.f, float, n)


class Layout:
    '''
    Class to store the layout of C++ binary format file i.e.
    get attributes for plotting such as ranges of X andd Y coordinates,
    width and height.
    '''
    def __init__(self, x, y, width, height, min_x, min_y, max_x, max_y):
        '''
        Init function.
        '''
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y


class BinaryDecoder(BinaryReader):
    '''
    Class to decode a C++ binary format file and
    convert it into matplotlib axes.
    '''
    def __init__(self, path):
        '''
        Init function.
        '''
        super().__init__(path)
        self.current_colour = "k"
        self.current_linewidth = 1.0
        self.current_linestyle = "-"
        # self.layout = Layout(0.0, 0.0, 100.0, 100.0, 0.0, 0.0, 100.0, 100.0)
        self.stack = []

        #
        self.dimension_x = None  # Will be read from file
        self.dimension_y = None  # Will be read from file
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.coord_ratio_x = 1.0
        self.coord_ratio_y = 1.0
        # variables to set limits of plot
        # based on poly_line()
        self.min_x = np.Inf
        self.max_x = -np.Inf
        self.min_y = np.Inf
        self.max_y = -np.Inf

    def text(self):
        '''
        Function to read text from binary format and
        convert them to matplotlib Text object.
        '''
        # print("text")
        size = self.read_int()
        # assert size == 1
        r = self.read_double()
        g = self.read_double()
        b = self.read_double()

        angle = -self.read_double() * 180 / 3.1416
        blank = self.read_bool()
        horizontal = self.read_int()
        vertical = self.read_int()

        n = self.read_int()

        texts = []

        for i in range(n):
            r = self.read_double()
            g = self.read_double()
            b = self.read_double()
            s = self.read_double()  # noqa
            m = self.read_int()
            texts.append(self.read_string(m))

        for i in range(size):
            x = self.project_x(self.read_double())
            y = self.project_y(self.read_double())

            props = dict(
                ha=H_ALIGN[horizontal],
                va=V_ALIGN[vertical],
                rotation=angle,
                color=(r, g, b),
            )

            if blank:
                props["bbox"] = dict(
                    alpha=0,
                    facecolor="white",
                    #  pad=10,
                    edgecolor="none",
                )

            # print('text', x,y,texts[i])
            self.ax.text(
                x,
                y,
                texts[i],
                #    transform=ax.transAxes,
                #    fontsize=14,
                props,
            )

    def project(self):
        '''
        Function to project the plot properties from
        C++ binary format to matplotlib format.
        '''
        self.stack.append(
            (
                self.dimension_x,
                self.dimension_y,
                self.offset_x,
                self.offset_y,
                self.coord_ratio_x,
                self.coord_ratio_y,
            )
        )

        layout = Layout(
            self.read_double(),
            self.read_double(),
            self.read_double(),
            self.read_double(),
            self.read_double(),
            self.read_double(),
            self.read_double(),
            self.read_double(),
        )

        self.offset_x += layout.x * 0.01 * self.dimension_x
        self.offset_y += layout.y * 0.01 * self.dimension_y
        self.dimension_x = layout.width * 0.01 * self.dimension_x
        self.dimension_y = layout.height * 0.01 * self.dimension_y

        sum_x = layout.max_x - layout.min_x
        sum_y = layout.max_y - layout.min_y

        if sum_x != 0 and sum_y != 0:
            self.coord_ratio_x = self.dimension_x / sum_x
            self.coord_ratio_y = self.dimension_y / sum_y

        self.offset_x = self.project_x(-layout.min_x)
        self.offset_y = self.project_y(-layout.min_y)

    def project_x(self, x):
        '''
        Function to project X coordinate from C++ binary format
        coordinate system to matplotlib coordinate system.
        '''
        return self.coord_ratio_x * x + self.offset_x

    def project_y(self, y):
        '''
        Function to project Y coordinate from C++ binary format
        coordinate system to matplotlib coordinate system.
        '''
        return self.coord_ratio_y * y + self.offset_y

    def unproject(self):
        '''
        Function to project the plot properties from
        matplotlib format back to C++ binary format.
        '''
        (
            self.dimension_x,
            self.dimension_y,
            self.offset_x,
            self.offset_y,
            self.coord_ratio_x,
            self.coord_ratio_y,
        ) = self.stack.pop()

    def colour(self):
        '''
        Function to read colour from binary format and
        convert them to matplotlib colour format i.e.
        R, G, B, A.
        '''
        r = self.read_double()
        g = self.read_double()
        b = self.read_double()
        a = self.read_double()
        self.current_colour = (r, g, b, a)

    def line_style(self):
        '''
        Function to read line properties from binary format and
        convert them to matplotlib compatible format.
        '''
        self.current_linestyle = LINE_STYLES[self.read_int()]
        self.current_linewidth = self.read_double()

    def line_width(self):
        '''
        Function to read and store line width from
        binary format.
        '''
        self.current_linewidth = self.read_double()

    def new_page(self):
        '''
        TODO
        '''
        raise NotImplementedError('new_page() function not implemented!')

    def end_page(self):
        '''
        TODO
        '''
        raise NotImplementedError('end_page() function not implemented!')

    def arrows(self):
        '''
        TODO
        '''
        raise NotImplementedError('arrows() function not implemented!')

    def flags(self):
        '''
        TODO
        '''
        raise NotImplementedError('flags() function not implemented!')

    def pixmap(self):
        '''
        TODO
        '''
        raise NotImplementedError('pixmap() function not implemented!')

    def image(self):
        '''
        TODO
        '''
        raise NotImplementedError('image() function not implemented!')

    def poly_line(self):
        '''
        Function to create 2D Lines.
        '''
        n = self.read_int()
        x = self.project_x(self.read_double_array(n))
        y = self.project_y(self.read_double_array(n))
        self.ax.add_line(
            Line2D(
                x,
                y,
                color=self.current_colour,
                linewidth=self.current_linewidth,
                linestyle=self.current_linestyle,
            )
        )
        if min(x) < self.min_x:
            self.min_x = min(x)
        if max(x) > self.max_x:
            self.max_x = max(x)
        if min(y) < self.min_y:
            self.min_y = min(y)
        if max(y) > self.max_y:
            self.max_y = max(y)

    def circle(self):
        '''
        Function to create a circle.
        '''
        x = self.project_x(self.read_double())
        y = self.project_y(self.read_double())
        r = self.read_double()
        cs = self.read_int()  # noqa
        return
        self.ax.add_patch(
            Circle(
                (
                    x,
                    y,
                ),
                r,
                # color=self.current_colour,
                # linewidth=self.current_linewidth,
                # linestyle=self.current_linestyle,
            )
        )

    def simple_polygon(self):
        '''
        Function to create a simple polygon.
        '''
        n = self.read_int()
        x = self.project_x(self.read_double_array(n))
        y = self.project_y(self.read_double_array(n))
        self.ax.add_line(
            Line2D(
                x,
                y,
                color=self.current_colour,
                linewidth=self.current_linewidth,
                linestyle=self.current_linestyle,
            )
        )

    def poly_line_2(self):
        '''
        Function to create 2D Lines.
        '''
        n = self.read_int()
        x = self.project_x(self.read_double_array(n))
        y = self.project_y(self.read_double_array(n))
        self.ax.add_line(
            Line2D(
                x,
                y,
                color=self.current_colour,
                linewidth=self.current_linewidth,
                linestyle=self.current_linestyle,
            )
        )

    def simple_polygon_with_holes(self):
        '''
        Function to create simple polygon with holes.
        '''
        n = self.read_int()
        x = self.project_x(self.read_double_array(n))
        y = self.project_y(self.read_double_array(n))

        # Holes
        for j in range(self.read_int()):
            n = self.read_int()
            # hole_x =
            self.read_double_array(n)
            # hole_y =
            self.read_double_array(n)

        # Fill colour
        r = self.read_double()
        g = self.read_double()
        b = self.read_double()
        a = self.read_double()

        self.ax.fill(x, y, color=(r, g, b, a))

    def plot(self, axes):
        '''
        Function to plot on the matplotlib axes.
        Args:
        axes() : matplotlib axes to plot the figure on.
        '''

        self.ax = axes

        DECODERS = {
            b"A": self.arrows,
            b"B": self.poly_line_2,
            b"C": self.colour,
            b"E": self.end_page,
            b"F": self.flags,
            b"H": self.poly_line,
            b"I": self.image,
            b"L": self.line_style,
            b"M": self.pixmap,
            b"N": self.new_page,
            b"P": self.project,
            b"R": self.circle,
            b"S": self.simple_polygon,
            b"T": self.text,
            b"U": self.unproject,
            b"W": self.line_width,
            b"X": self.simple_polygon_with_holes,
        }

        # Magic
        assert self.read_string(6) == "MAGICS"

        # Endianess
        assert self.read_int() == 10

        # Version
        self.read_int()

        # header length
        self.read_int()

        self.dimension_x = self.read_double()
        self.dimension_y = self.read_double()

        # print(self.dimension_x, self.dimension_y)

        op = self.read_char()
        while op:
            DECODERS[op]()
            op = self.read_char()

        self.ax.set_xlim(self.min_x, self.max_x)
        self.ax.set_ylim(self.min_y, self.max_y)

class ColorBar():
    """
    Class to create a colorbar on an axes.
    """
    def __init__(self, metadata) -> None:
        """
        init function
        Args:
        """
        self.metadata = metadata
        assert isinstance(self.metadata, dict), "Metadata is not a dictionary"
        self.colorbar_entry_type = namedtuple(
            typename= "colorbarEntry",
            field_names=["min", "max"]
        )

    def check_colorbar_available(self):
        """
        function to check if colorbar properties
        are present in the metadata
        """
        plot_colorbar = False
        if 'legend' in self.metadata:
            if 'legend_entries' in self.metadata['legend']:
                if len(self.metadata['legend']['legend_entries'])>0:
                    plot_colorbar = True
        return plot_colorbar

    def rgba_to_np(self, text):
        """
        function to convert RGBA(254,254,223,1) to a numpy array
        Args:
            text (string): RGBA string
        """
        text = text.replace(' ', '').split('(')[-1].split(')')[0]
        r, g, b, a = text.split(',')
        np_array = np.array([int(r), int(g), int(b), int(a)])
        return np_array

    def get_colorbar_entries(self, metadata):
        """
        function to process metadata to get
        colorbar entries
        """
        data = metadata['legend']['legend_entries']
        colorbar_entries = {}
        for entry in data:
            if entry['legend_entry_type'] == 'colorbar':
                key = self.colorbar_entry_type(
                    min = float(entry['legend_entry_min_text']),
                    max = float(entry['legend_entry_max_text'])
                )
                value = entry['legend_entry_colour']
                colorbar_entries[key] = self.rgba_to_np(value)
        return colorbar_entries

    def get_colorbar_image_array(self, metadata):
        """
        function to convert colorbar entries to an image
        """
        colorbar_entries = self.get_colorbar_entries(metadata)
        sorted_entries = dict(sorted(colorbar_entries.items(), key=lambda item: item[0].min))
        image_array = None # nrows x 4
        ticks = []
        for key, value in sorted_entries.items():
            ticks.append(key.min)
            ticks.append(key.max)
            nrows = int((key.max - key.min)*100) # handling upto 2 decimal points
            tmp_arr = np.full((nrows, 4), value)
            if image_array is None:
                image_array = tmp_arr
            else:
                image_array = np.concatenate(
                    (image_array, tmp_arr),
                    axis=0
                )
        ticks = np.sort(np.array(list(set(ticks)))) # remove redundant values
        return image_array, ticks

    def plot(self, axes):
        """
        function to plot the colorbar on an axes
        Args:
            axes (matplotlib.axes._subplots.AxesSubplot):
                Axes object on which the colorbar will be plotted
        """
        if self.check_colorbar_available():
            divider = make_axes_locatable(axes)
            cax = divider.append_axes('right', size='5%', pad='5%')
            cbar_arr, cbar_ticks = self.get_colorbar_image_array(self.metadata)
            # create a copy for later normalization
            cbar_arr_tmp = np.copy(cbar_arr)
            cbar_arr_tmp[:, -1] = cbar_arr_tmp[:, -1]*255
            cmap = matplotlib.colors.ListedColormap(cbar_arr_tmp/255.)
            norm = matplotlib.colors.Normalize()
            cbar = plt.colorbar(
                matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap),
                cax=cax, orientation='vertical'
            )
            # colorbar ticks
            cbar_ticklabels = np.copy(cbar_ticks)
            cbar_arr_range = 1 # since the colormap is normalized
            cbar_ticks_range = np.abs(np.max(cbar_ticks) - np.min(cbar_ticks))
            cbar_ticks = ((cbar_ticks-np.min(cbar_ticks))/cbar_ticks_range)*cbar_arr_range
            cbar.set_ticks(cbar_ticks)
            cbar.set_ticklabels(cbar_ticklabels)
        return axes

def plot_mgb(path, axes=None, **kwargs):
    '''
    API function to to read a mgb file
    and plot it on matplotlib axes.
    Args:
    axes() : matplotlib axes to plot the figure on.
    '''
    decoder = BinaryDecoder(path)

    if axes is None:
        _, axes = plt.subplots(figsize=(20, 20))

    if 'metadata' in kwargs:
        colorbar = ColorBar(kwargs['metadata'])
        axes = colorbar.plot(axes)

    axes.tick_params(
        axis='both',
        which='both',
        left=False, bottom=False,
        labelleft=False, labelbottom=False
    )

    axes.set_aspect("equal")
    decoder.plot(axes)
