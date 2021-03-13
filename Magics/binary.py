#!/usr/bin/env python3
import struct

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

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
    def __init__(self, path):
        self.f = open(path, "rb")

    def readChar(self):
        return self.f.read(1)

    def readInt(self):
        return struct.unpack("i", self.f.read(4))[0]

    def readDouble(self):
        return struct.unpack("d", self.f.read(8))[0]

    def readBool(self):
        return struct.unpack("c", self.f.read(1))[0] == b"\x01"

    def readString(self, n=None):
        if n is None:
            n = self.readInt()
        return self.f.read(n).decode()

    def readDoubleArray(self, n):
        return np.fromfile(self.f, float, n)


class Layout:
    def __init__(self, x, y, width, height, minX, minY, maxX, maxY):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY

        # print('Layout', x, y, width, height, minX, minY, maxX, maxY)


class BinaryDecoder(BinaryReader):
    def __init__(self, path):
        super().__init__(path)
        self.current_colour = "k"
        self.current_linewidth = 1.0
        self.current_linestyle = "-"
        # self.layout = Layout(0.0, 0.0, 100.0, 100.0, 0.0, 0.0, 100.0, 100.0)
        self.stack = []

        #
        self.dimensionX = None  # Will be read from file
        self.dimensionY = None  # Will be read from file
        self.offsetX = 0.0
        self.offsetY = 0.0
        self.coordRatioX = 1.0
        self.coordRatioY = 1.0

    def text(self):
        # print("text")
        size = self.readInt()
        # assert size == 1
        r = self.readDouble()
        g = self.readDouble()
        b = self.readDouble()

        angle = -self.readDouble() * 180 / 3.1416
        blank = self.readBool()
        horizontal = self.readInt()
        vertical = self.readInt()

        n = self.readInt()

        texts = []

        for i in range(n):
            r = self.readDouble()
            g = self.readDouble()
            b = self.readDouble()
            s = self.readDouble()
            m = self.readInt()
            texts.append(self.readString(m))

        for i in range(size):
            x = self.projectX(self.readDouble())
            y = self.projectY(self.readDouble())

            props = dict(
                ha=H_ALIGN[horizontal],
                va=V_ALIGN[vertical],
                rotation=angle,
                color=(r, g, b),
            )

            if blank:
                props["bbox"] = dict(
                    alpha=1,
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
        self.stack.append(
            (
                self.dimensionX,
                self.dimensionY,
                self.offsetX,
                self.offsetY,
                self.coordRatioX,
                self.coordRatioY,
            )
        )

        layout = Layout(
            self.readDouble(),
            self.readDouble(),
            self.readDouble(),
            self.readDouble(),
            self.readDouble(),
            self.readDouble(),
            self.readDouble(),
            self.readDouble(),
        )

        self.offsetX += layout.x * 0.01 * self.dimensionX
        self.offsetY += layout.y * 0.01 * self.dimensionY
        self.dimensionX = layout.width * 0.01 * self.dimensionX
        self.dimensionY = layout.height * 0.01 * self.dimensionY

        sumX = layout.maxX - layout.minX
        sumY = layout.maxY - layout.minY

        if sumX != 0 and sumY != 0:
            self.coordRatioX = self.dimensionX / sumX
            self.coordRatioY = self.dimensionY / sumY

        self.offsetX = self.projectX(-layout.minX)
        self.offsetY = self.projectY(-layout.minY)

    def projectX(self, x):
        return self.coordRatioX * x + self.offsetX

    def projectY(self, y):
        return self.coordRatioY * y + self.offsetY

    def unproject(self):
        (
            self.dimensionX,
            self.dimensionY,
            self.offsetX,
            self.offsetY,
            self.coordRatioX,
            self.coordRatioY,
        ) = self.stack.pop()
        # print("Pop")

    def colour(self):
        r = self.readDouble()
        g = self.readDouble()
        b = self.readDouble()
        a = self.readDouble()
        self.current_colour = (r, g, b, a)
        # print('colour', self.current_colour)

    def line_style(self):
        self.current_linestyle = LINE_STYLES[self.readInt()]
        self.current_linewidth = self.readDouble()

    def line_width(self):
        self.current_linewidth = self.readDouble()

    def new_page(self):
        pass

    def end_page(self):
        pass

    def arrows(self):
        assert False

    def flags(self):
        assert False

    def pixmap(self):
        assert False

    def image(self):
        assert False

    def poly_line(self):
        # print("poly_line")
        n = self.readInt()
        x = self.projectX(self.readDoubleArray(n))
        y = self.projectY(self.readDoubleArray(n))
        self.ax.add_line(
            Line2D(
                x,
                y,
                color=self.current_colour,
                linewidth=self.current_linewidth,
                linestyle=self.current_linestyle,
            )
        )
        self.ax.set_xlim(min(x), max(x))
        self.ax.set_ylim(min(y), max(y))

    def circle(self):

        x = self.projectX(self.readDouble())
        y = self.projectX(self.readDouble())
        r = self.readDouble()
        cs = self.readInt()
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
        # print("simple_polygon")
        n = self.readInt()
        x = self.projectX(self.readDoubleArray(n))
        y = self.projectY(self.readDoubleArray(n))
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
        # print("poly_line_2")
        n = self.readInt()
        x = self.projectX(self.readDoubleArray(n))
        y = self.projectY(self.readDoubleArray(n))
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
        # print("simple_polygon_with_holes")
        n = self.readInt()
        x = self.projectX(self.readDoubleArray(n))
        y = self.projectY(self.readDoubleArray(n))

        # Holes
        for j in range(self.readInt()):
            n = self.readInt()
            # hole_x =
            self.readDoubleArray(n)
            # hole_y =
            self.readDoubleArray(n)

        # Fill colour
        r = self.readDouble()
        g = self.readDouble()
        b = self.readDouble()
        a = self.readDouble()

        self.ax.fill(x, y, color=(r, g, b, a))

    def plot(self, axes):

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
        assert self.readString(6) == "MAGICS"

        # Endianess
        assert self.readInt() == 10

        # Version
        self.readInt()

        # header length
        self.readInt()

        self.dimensionX = self.readDouble()
        self.dimensionY = self.readDouble()

        print(self.dimensionX, self.dimensionY)

        op = self.readChar()
        while op:
            DECODERS[op]()
            op = self.readChar()

        # self.ax.set_xlim(min(x), max(x))
        # self.ax.set_ylim(min(y), max(y))


def plot_mgb(path):
    decoder = BinaryDecoder(path)
    decoder.plot(plt.gca())
