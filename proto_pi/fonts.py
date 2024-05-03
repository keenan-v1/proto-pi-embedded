from proto_pi.rendering import Glyph


class Font:
    def __init__(self, font: dict[str, Glyph]) -> None:
        self._auto_capitalize: bool = False
        self._default_glyph: Glyph = list(font.values())[0]
        self._font: dict[str, Glyph] = font

    @property
    def max_width(self) -> int:
        return max([g.full_width() for g in self._font.values()])

    @property
    def max_height(self) -> int:
        return max([g.height for g in self._font.values()])

    def width(self, text: str) -> int:
        return sum([self._font[c].full_width() for c in text])

    def auto_capitalize(self, value: bool = True) -> 'Font':
        self._auto_capitalize = value
        return self

    def set_default(self, glyph: Glyph) -> 'Font':
        self._default_glyph = glyph
        return self

    def get(self, key: str, default: Glyph | None = None) -> Glyph:
        if self._auto_capitalize:
            key = key.upper()
        return self._font.get(key, default if default is not None else self._default_glyph)


class Fonts:
    Compact: Font = Font({
        "█": Glyph(3, 5, "█", bytearray([0b111, 0b111, 0b111, 0b111, 0b111])),

        "0": Glyph(3, 5, "0", bytearray([0b111, 0b101, 0b101, 0b101, 0b111])),
        "1": Glyph(1, 5, "1", bytearray([0b1, 0b1, 0b1, 0b1, 0b1])),
        "2": Glyph(3, 5, "2", bytearray([0b111, 0b001, 0b111, 0b100, 0b111])),
        "3": Glyph(3, 5, "3", bytearray([0b111, 0b001, 0b111, 0b001, 0b111])),
        "4": Glyph(3, 5, "4", bytearray([0b101, 0b101, 0b111, 0b001, 0b001])),
        "5": Glyph(3, 5, "5", bytearray([0b111, 0b100, 0b111, 0b001, 0b111])),
        "6": Glyph(3, 5, "6", bytearray([0b111, 0b100, 0b111, 0b101, 0b111])),
        "7": Glyph(3, 5, "7", bytearray([0b111, 0b001, 0b001, 0b001, 0b001])),
        "8": Glyph(3, 5, "8", bytearray([0b111, 0b101, 0b111, 0b101, 0b111])),
        "9": Glyph(3, 5, "9", bytearray([0b111, 0b101, 0b111, 0b001, 0b111])),

        "A": Glyph(3, 5, "A", bytearray([0b111, 0b101, 0b111, 0b101, 0b101])),
        "B": Glyph(3, 5, "B", bytearray([0b110, 0b101, 0b110, 0b101, 0b110])),
        "C": Glyph(3, 5, "C", bytearray([0b111, 0b100, 0b100, 0b100, 0b111])),
        "D": Glyph(3, 5, "D", bytearray([0b110, 0b101, 0b101, 0b101, 0b110])),
        "E": Glyph(3, 5, "E", bytearray([0b111, 0b100, 0b111, 0b100, 0b111])),
        "F": Glyph(3, 5, "F", bytearray([0b111, 0b100, 0b111, 0b100, 0b100])),
        "G": Glyph(3, 5, "G", bytearray([0b111, 0b100, 0b101, 0b101, 0b111])),
        "H": Glyph(3, 5, "H", bytearray([0b101, 0b101, 0b111, 0b101, 0b101])),
        "I": Glyph(3, 5, "I", bytearray([0b111, 0b010, 0b010, 0b010, 0b111])),
        "J": Glyph(3, 5, "J", bytearray([0b111, 0b001, 0b001, 0b101, 0b111])),
        "K": Glyph(3, 5, "K", bytearray([0b101, 0b101, 0b110, 0b101, 0b101])),
        "L": Glyph(3, 5, "L", bytearray([0b100, 0b100, 0b100, 0b100, 0b111])),
        "M": Glyph(3, 5, "M", bytearray([0b101, 0b111, 0b111, 0b101, 0b101])),
        "N": Glyph(3, 5, "N", bytearray([0b101, 0b101, 0b111, 0b111, 0b101])),
        "O": Glyph(3, 5, "O", bytearray([0b111, 0b101, 0b101, 0b101, 0b111])),
        "P": Glyph(3, 5, "P", bytearray([0b111, 0b101, 0b111, 0b100, 0b100])),
        "Q": Glyph(3, 5, "Q", bytearray([0b111, 0b101, 0b101, 0b111, 0b001])),
        "R": Glyph(3, 5, "R", bytearray([0b111, 0b101, 0b111, 0b110, 0b101])),
        "S": Glyph(3, 5, "S", bytearray([0b111, 0b100, 0b111, 0b001, 0b111])),
        "T": Glyph(3, 5, "T", bytearray([0b111, 0b010, 0b010, 0b010, 0b010])),
        "U": Glyph(3, 5, "U", bytearray([0b101, 0b101, 0b101, 0b101, 0b111])),
        "V": Glyph(3, 5, "V", bytearray([0b101, 0b101, 0b101, 0b101, 0b010])),
        "W": Glyph(3, 5, "W", bytearray([0b101, 0b101, 0b101, 0b111, 0b101])),
        "X": Glyph(3, 5, "X", bytearray([0b101, 0b101, 0b010, 0b101, 0b101])),
        "Y": Glyph(3, 5, "Y", bytearray([0b101, 0b101, 0b010, 0b010, 0b010])),
        "Z": Glyph(3, 5, "Z", bytearray([0b111, 0b001, 0b010, 0b100, 0b111])),

        " ": Glyph(1, 5, " ", bytearray([0b0, 0b0, 0b0, 0b0, 0b0]), stride=0),
        ".": Glyph(1, 5, ".", bytearray([0b0, 0b0, 0b0, 0b0, 0b1]), offset=-1, stride=0),
        ",": Glyph(2, 6, ",", bytearray([0b00, 0b00, 0b00, 0b00, 0b01, 0b10]), offset=-2, stride=0),
        ":": Glyph(1, 5, ":", bytearray([0b0, 0b1, 0b0, 0b1, 0b0]), offset=-1, stride=0),
        "!": Glyph(1, 5, "!", bytearray([0b1, 0b1, 0b1, 0b0, 0b1]), offset=-1, stride=0),
        "?": Glyph(3, 5, "?", bytearray([0b111, 0b001, 0b010, 0b000, 0b010]), offset=-1, stride=0),
        "'": Glyph(1, 5, "'", bytearray([0b1, 0b1, 0b0, 0b0, 0b0]), offset=-1, stride=0),
        '"': Glyph(3, 5, '"', bytearray([0b101, 0b101, 0b000, 0b000, 0b000]), offset=-1, stride=0),
        "-": Glyph(2, 5, "-", bytearray([0b00, 0b00, 0b11, 0b00, 0b00]), offset=-1, stride=0),
        "+": Glyph(3, 5, "+", bytearray([0b000, 0b010, 0b111, 0b010, 0b000]), offset=-1, stride=0),
        "/": Glyph(3, 5, "/", bytearray([0b001, 0b001, 0b010, 0b100, 0b100]), offset=-1, stride=0),
    }).auto_capitalize(True)


class String:
    def __init__(self, font: Font, text: str | None = None) -> None:
        self._font: Font = font
        self._text: str = text if text is not None else ""

    def __add__(self, other: 'String' | Glyph) -> 'String':
        if isinstance(other, Glyph):
            return String(self._font, self._text + other.txt)
        return String(self._font, self._text + other._text)

    def __repr__(self):
        return f"<String {self._text}>"

    def __str__(self):
        return self._text

    def as_glyphs(self, color: int = 1) -> list[Glyph]:
        return [self._font.get(c).set_color(color) for c in self._text]
