"""
MicroPython max7219 cascading 8x8 LED matrix driver

Licensed under MIT, found in LICENSE.txt
    Copyright (c) 2017 Mike Causer
    Copyright (c) 2022 Leo Spratt
    Copyright (c) 2024 Jonathan Walker
"""
from micropython import const
from framebuf import FrameBuffer, MONO_HLSB
from machine import Pin, SPI
from proto_pi.rendering import Glyph
from proto_pi.fonts import String

# Command constants
_NOOP = const(0)
_DIGIT_0 = const(1)
_DECODE_MODE = const(9)
_INTENSITY = const(10)
_SCAN_LIMIT = const(11)
_SHUTDOWN = const(12)
_DISPLAY_TEST = const(15)

# Lookup table for CRC8
# noinspection SpellCheckingInspection
_table = (b'\x00\x07\x0e\t\x1c\x1b\x12\x158?61$#*-pw~ylkbeHOFATSZ]\xe0\xe7\xee\xe9\xfc\xfb\xf2\xf5\xd8\xdf\xd6\xd1'
          b'\xc4\xc3\xca\xcd\x90\x97\x9e\x99\x8c\x8b\x82\x85\xa8\xaf\xa6\xa1\xb4\xb3\xba\xbd\xc7\xc0\xc9\xce\xdb'
          b'\xdc\xd5\xd2\xff\xf8\xf1\xf6\xe3\xe4\xed\xea\xb7\xb0\xb9\xbe\xab\xac\xa5\xa2\x8f\x88\x81\x86\x93\x94'
          b'\x9d\x9a\' ).;<52\x1f\x18\x11\x16\x03\x04\r\nWPY^KLEBohafst}z\x89\x8e\x87\x80\x95\x92\x9b\x9c\xb1\xb6'
          b'\xbf\xb8\xad\xaa\xa3\xa4\xf9\xfe\xf7\xf0\xe5\xe2\xeb\xec\xc1\xc6\xcf\xc8\xdd\xda\xd3\xd4ing`ur{|QV_XM'
          b'JCD\x19\x1e\x17\x10\x05\x02\x0b\x0c!&/(=:34NI@GRU\\[vqx\x7fjmdc>907"%,+\x06\x01\x08\x0f\x1a\x1d\x14\x13'
          b'\xae\xa9\xa0\xa7\xb2\xb5\xbc\xbb\x96\x91\x98\x9f\x8a\x8d\x84\x83\xde\xd9\xd0\xd7\xc2\xc5\xcc\xcb\xe6'
          b'\xe1\xe8\xef\xfa\xfd\xf4\xf3')


def _crc82(*args):
    _sum = 0
    table = _table
    for arg in args:
        for byte in arg:
            _sum = table[_sum ^ byte]
    return _sum


class Matrix(FrameBuffer):
    """
    Driver for cascading MAX7219 8x8 LED matrices.
    """

    def __init__(self, spi: SPI, cs: Pin, cols: int, rows: int,
                 pixels_per_side: int = 8, pixel_format: int = MONO_HLSB,
                 reverse_ids: bool = False, skip_devices: list[int] | None = None) -> None:
        """
        Create a new Matrix
        :param spi: SPI object from machine
        :param cs: CS Pin
        :param cols: The number of devices horizontally
        :param rows: The number of devices vertically
        :param pixels_per_side: The number of pixels in a device, default: `8`
        :param pixel_format: See :class:`FrameBuffer<framebuf.FrameBuffer>`
        :param reverse_ids: Reverse the device IDs, default: `False`
        :param skip_devices: List of device IDs to ignore, default: `[]`
        """
        if skip_devices is None:
            skip_devices = []
        self._cols: int = cols
        self._rows: int = rows
        self._reverse_ids: bool = reverse_ids
        self._skip_devices: list[int] = skip_devices
        self._pixels_per_side: int = pixels_per_side
        self._spi: SPI = spi
        self._cs: Pin = cs
        self._cs.init(self._cs.OUT, True)
        self._buffer: bytearray = bytearray(self.device_count * pixels_per_side)
        self._checksum: int = 0
        super().__init__(self._buffer, cols * pixels_per_side, rows * pixels_per_side, pixel_format)
        self._write_init()

    @property
    def current_checksum(self) -> int:
        """
        Calculates the checksum of the buffer
        :return: checksum
        """
        return _crc82(self._buffer)

    @property
    def changed(self) -> bool:
        """
        Checks if the buffer has changed
        :return: True if the buffer has changed
        """
        return self.current_checksum != self._checksum

    @property
    def device_count(self) -> int:
        return self._cols * self._rows

    @property
    def width(self) -> int:
        return self._cols * self._pixels_per_side

    @property
    def height(self) -> int:
        return self._rows * self._pixels_per_side

    def _write(self, command: int, data: int) -> None:
        """
        Writes the given command with the given data to the configured :class:`SPI<machine.SPI>`
        :param command: command to write, see :module:`proto_pi<proto_pi>`
        :param data: data to send, refer to the MAX72XX datasheet
        :return: None
        """
        self._cs(0)
        for _ in range(self.device_count):
            self._spi.write(bytearray([command, data]))
        self._cs(1)

    def _write_init(self) -> None:
        """
        Writes the init commands
        :return: None
        """
        for command, data in (
                (_SHUTDOWN, 0),
                (_DISPLAY_TEST, 0),
                (_SCAN_LIMIT, 7),
                (_DECODE_MODE, 0),
                (_SHUTDOWN, 1),
        ):
            self._write(command, data)

    def brightness(self, value: int) -> None:
        f"""
        Set the brightness (intensity) of the display
        :param value: a value between 0 and 15
        :return: None
        """
        if not 0 <= value <= 15:
            raise ValueError("Brightness out of range")
        self._write(_INTENSITY, value)

    def text(self, s: str | String, x: int = 0, y: int = 0, c: int = 1) -> None:
        """
        Prints text to the Matrix
        :param s: text to print
        :param x: `x` position, default: `0`
        :param y: `y` position, default: `0`
        :param c: color to set pixel, default: `1`
        :return: None
        """
        if isinstance(s, str):
            super().text(s, x, y, c)
        elif isinstance(s, String):
            glyphs: list[Glyph] = s.as_glyphs(c)
            for g in glyphs:  # type: Glyph
                x += g.offset
                self.blit(g, x, y, 0)
                x += g.width + g.stride
            return

    def zero(self) -> None:
        """
        Sets all pixels to 0
        :return:
        """
        self.fill(0)

    def shutdown(self) -> None:
        """
        Sends the shutdown command with data `0`
        :return:
        """
        self._write(_SHUTDOWN, 0)

    def wake(self) -> None:
        """
        Sends the shutdown command with data `1`
        :return:
        """
        self._write(_SHUTDOWN, 1)

    def test(self, enable: bool = True) -> None:
        """
        Controls the test mode of the MAX72XX controller
        :param enable: enable or disable test mode
        :return: None
        """
        self._write(_DISPLAY_TEST, int(enable))

    def _get_buffer_index(self, device_id: int, row_number: int) -> int:
        """
        Get the index of the pixel in the buffer for the given device_id and row_number
        :param device_id: ID of the device
        :param row_number: row number
        :return: bytearray index for the given row and device
        """
        assert 0 <= device_id < self.device_count, f"Invalid device_id: {device_id}"
        assert 0 <= row_number < self._pixels_per_side, f"Invalid row_number: {row_number}"
        if self._reverse_ids:
            device_id = self.device_count - device_id - 1
        index = ((device_id // self._cols * self._pixels_per_side + row_number) * self._cols + device_id % self._cols)
        return index

    def _show_device(self, device_id: int) -> None:
        if device_id in self._skip_devices:
            return
        for row in range(8):
            cmd: int = _DIGIT_0 + row  # Command starts at _DIGIT_0 and increases with each row until 8.
            idx: int = self._get_buffer_index(device_id, row)
            assert 0 <= idx < len(self._buffer), f"Index out of range: {idx}"
            data: int = self._buffer[idx]
            self._cs(0)
            for d_id in range(device_id + 1, self.device_count):
                self._spi.write(bytearray([_NOOP, 0]))
            self._spi.write(bytearray([cmd, data]))
            for d_id in range(0, device_id):
                self._spi.write(bytearray([_NOOP, 0]))
            self._cs(1)

    def show(self, *, force: bool = False) -> None:
        """
        Shows the buffer on the Matrix
        :return: None
        """
        if not self.changed and not force:
            return
        for device_id in range(self.device_count):
            self._show_device(device_id)
        self._checksum = self.current_checksum

    def debug(self) -> None:
        for y in range(self._rows * self._pixels_per_side):
            for x in range(self._cols * self._pixels_per_side):
                if self.pixel(x, y):
                    print("*", end="")
                else:
                    print(" ", end="")
            print()
