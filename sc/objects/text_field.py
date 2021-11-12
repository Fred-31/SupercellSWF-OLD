from .tag import Tag



class TextField(Tag):
    def __init__(self, tag: int = 7) -> None:
        super().__init__(tag)

        self.export_id: int = 0

        self.text: str = None

        self.font: str = None
        self.font_width: int = 0
        self.font_size: int = 0

        self.font_color: list = [255, 255, 255, 255]
        self.font_outline_color: list = [0, 0, 0, 255]

        self.left_corner: int = 0
        self.top_corner: int = 0
        self.right_corner: int = 0
        self.bottom_corner: int = 0

        self.italic: bool = False
        self.ansi: bool = False
        self.shiftJIS: bool = False
        self.modifier4: bool = False
        self.modifier5: bool = False
        self.wideCodes: bool = False
        self.modifier7: bool = False

        self.transform1: int = 0
        self.transform2: int = 0
        self.transform3: int = 0
    
    def load(self, data: bytes):
        super().load(data)

        self.export_id = self.read_unsigned_short()

        self.font = self.read_ascii()
        self.font_color = self.read_bgra()

        self.italic = self.read_bool()
        self.ansi = self.read_bool()
        self.shiftJIS = self.read_bool()
        self.modifier4 = self.read_bool() # unused

        self.font_width = self.read_unsigned_char()
        self.font_size = self.read_unsigned_char()

        self.left_corner = self.read_short()
        self.top_corner = self.read_short()
        self.right_corner = self.read_short()
        self.bottom_corner = self.read_short()
        
        self.modifier5 = self.read_bool()

        self.text = self.read_ascii()

        if self.tag == 7:
            return
        
        self.wideCodes = self.read_bool()

        if self.tag == 20:
            return
        elif self.tag in (21, 25, 33, 44):
            self.font_outline_color = self.read_bgra()
        
        if self.tag in (33, 44):
            self.transform1 = self.read_short()
            self.transform2 = self.read_short()

            if self.tag == 44:
                self.transform3 = self.read_short()
                self.modifier7 = self.read_bool()
    
    def save(self):
        super().save()

        self.write_unsigned_short(self.export_id)
        self.write_ascii(self.font)

        self.write_bgra(self.font_color)

        self.write_bool(self.italic)
        self.write_bool(self.ansi)
        self.write_bool(self.shiftJIS)
        self.write_bool(self.modifier4) # unused

        self.write_unsigned_char(self.font_width)
        self.write_unsigned_char(self.font_size)

        self.write_short(self.left_corner)
        self.write_short(self.top_corner)
        self.write_short(self.right_corner)
        self.write_short(self.bottom_corner)

        self.write_bool(self.modifier5)

        self.write_ascii(self.text)

        if self.tag == 7:
            return

        self.write_bool(self.wideCodes)

        if self.tag == 20:
            return
        elif self.tag in (21, 25, 33, 44):
            self.write_bgra(self.font_outline_color)
        
        if self.tag in (33, 44):
            self.write_short(self.transform1)
            self.write_short(self.transform2)

            if self.tag == 44:
                self.write_short(self.transform3)
                self.write_bool(self.modifier7)