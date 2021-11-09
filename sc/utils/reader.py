from io import BytesIO



class Reader(BytesIO):
    def __init__(self, buffer: bytes, endian: str = "little") -> None:
        super().__init__(buffer)
        self.endian = endian
    
    @property
    def buffer(self):
        return self.getvalue()
    
    def read_custom_type(self, size: int) -> int:
        return int.from_bytes(self.read(size), self.endian, signed = True)
    
    def read_unsigned_custom_type(self, size: int) -> int:
        return int.from_bytes(self.read(size), self.endian, signed = False)
    
    def read_char(self) -> int:
        return self.read_custom_type(1)
    
    def read_unsigned_char(self) -> int:
        return self.read_unsigned_custom_type(1)
    
    def read_short(self) -> int:
        return self.read_custom_type(2)
    
    def read_unsigned_short(self) -> int:
        return self.read_unsigned_custom_type(2)
    
    def read_int(self) -> int:
        return self.read_custom_type(4)
    
    def read_unsigned_int(self) -> int:
        return self.read_unsigned_custom_type(4)
    
    def read_long(self) -> int:
        return self.read_custom_type(8)
    
    def read_unsigned_long(self) -> int:
        return self.read_unsigned_custom_type(8)
    
    def read_bool(self) -> bool:
        return self.read_unsigned_char()
    
    def read_ascii(self) -> str:
        size = self.read_unsigned_char()
        if size != 0xff:
            return self.read(size).decode()
        return None
    
    def read_twip(self):
        return self.read_int() / 20
    
    def read_matrix2x3(self):
        scale_x = self.read_int() / 1024
        rotation_x = self.read_int() / 1024
        rotation_y = self.read_int() / 1024
        scale_y = self.read_int() / 1024

        x, y = self.read_twip(), self.read_twip()

        return [
            [scale_x, rotation_x, x],
            [scale_y, rotation_y, y]
        ]
    
    def read_bgra(self):
        b = self.read_unsigned_char()
        g = self.read_unsigned_char()
        r = self.read_unsigned_char()
        a = self.read_unsigned_char()
        return [r, g, b, a]
    
    def read_bgr(self):
        b = self.read_unsigned_char()
        g = self.read_unsigned_char()
        r = self.read_unsigned_char()
        return [r, g, b]
