import framebuf
import binascii


class Renderable(framebuf.FrameBuffer):
    def __init__(self, width: int, height: int, pixel_format: int = framebuf.MONO_HLSB) -> None:
        self.width: int = width
        self.height: int = height
        self._buffer: bytearray = bytearray(width * height)
        super().__init__(self._buffer, width, height, pixel_format)
        self.fill(0)

    def load_data(self, data: bytearray) -> 'Renderable':
        self._buffer = data
        return self

    @property
    def data(self) -> bytearray:
        return self._buffer

    def debug(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                if self.pixel(x, y):
                    print("*", end="")
                else:
                    print(" ", end="")
            print()

    def mirror(self) -> None:
        for y in range(self.height):
            for x in range(self.width // 2):
                pixel = self.pixel(x, y)
                self.pixel(x, y, self.pixel(self.width - x - 1, y))
                self.pixel(self.width - x - 1, y, pixel)

    def flip(self) -> None:
        for y in range(self.height // 2):
            for x in range(self.width):
                pixel = self.pixel(x, y)
                self.pixel(x, y, self.pixel(x, self.height - y - 1))
                self.pixel(x, self.height - y - 1, pixel)


class Glyph(Renderable):
    """
    A simple class to represent a glyph
    """

    def __init__(self,
                 width: int,
                 height: int,
                 text: str,
                 data: bytearray,
                 color: int = 1,
                 offset: int = 0,
                 stride: int = 1
                 ) -> None:
        self._text: str = text
        self._color: int = color
        self._offset: int = offset
        self._stride: int = stride
        super().__init__(width, height)
        self.load_data(data)

    @property
    def txt(self) -> str:
        return self._text

    @property
    def color(self) -> int:
        return self._color

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def stride(self) -> int:
        return self._stride

    def __repr__(self) -> str:
        return f"<Glyph {self.width}x{self.height}> {self.text}"

    def __str__(self) -> str:
        return self.txt

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Glyph):
            return False
        return self.text == other.text

    def load_data(self, data: bytearray) -> 'Renderable':
        for y in range(self.height):
            for x in range(self.width):
                if data[y] & (1 << (self.width - x - 1)):
                    self.pixel(x, y, 1)
        return self

    def full_width(self) -> int:
        return self.width + self.offset + self.stride

    def print(self, on: str = "*", off: str = " ") -> None:
        for b in self.data:
            print(f"{b:08b}".replace("1", on).replace("0", off))

    def set_color(self, color: int) -> 'Glyph':
        self._color = color
        return self


class Frame(Renderable):
    def __init__(self, width: int, height: int, frame_id: int, data: bytearray) -> None:
        self.id: int = frame_id
        super().__init__(width, height)
        self.load_data(data)

    def load_data(self, data: bytearray) -> 'Renderable':
        pixels: list[bool] = []
        for byte in data:
            for i in range(8):
                pixels.append(bool(byte & (1 << i)))
        for y in range(self.height):
            for x in range(self.width):
                self.pixel(x, y, pixels[y * self.width + x])
        return self

    def as_copy(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0) -> 'Frame':
        width = width if width > 0 else self.width
        height = height if height > 0 else self.height
        copy: Frame = Frame(width, height, self.id, bytearray(width * height))
        for cy in range(height):
            for cx in range(width):
                copy.pixel(cx, cy, self.pixel(x + cx, y + cy))
        return copy

    @staticmethod
    def from_json(data: dict, width: int, height: int) -> 'Frame':
        return Frame(width, height, data["id"], bytearray(binascii.a2b_base64(data['data'])))
