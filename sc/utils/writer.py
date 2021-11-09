from io import BytesIO



class Writer(BytesIO):
    def __init__(self, buffer: bytes = b"", endian: str = "little") -> None:
        super().__init__(buffer)
        self.endian = endian
    
    @property
    def buffer(self):
        return self.getvalue()
    
    @buffer.setter
    def buffer(self, data: bytes):
        self.seek(0)
        self.truncate(0)
        self.write(data)
    
    def write_custom_type(self, value: int, size: int) -> None:
        self.write(value.to_bytes(size, self.endian, signed = True))
    
    def write_unsigned_custom_type(self, value: int, size: int) -> None:
        self.write(value.to_bytes(size, self.endian, signed = False))
    
    def write_char(self, value: int) -> None:
        self.write_custom_type(value, 1)
    
    def write_unsigned_char(self, value: int) -> None:
        self.write_unsigned_custom_type(value, 1)
    
    def write_short(self, value: int) -> None:
        self.write_custom_type(value, 2)
    
    def write_unsigned_short(self, value: int) -> None:
        self.write_unsigned_custom_type(value, 2)
    
    def write_int(self, value: int) -> None:
        self.write_custom_type(value, 4)
    
    def write_unsigned_int(self, value: int) -> None:
        self.write_unsigned_custom_type(value, 4)
    
    def write_long(self, value: int) -> None:
        self.write_custom_type(value, 8)
    
    def write_unsigned_long(self, value: int) -> None:
        self.write_unsigned_custom_type(value, 8)
    
    def write_bool(self, value: bool) -> None:
        self.write_unsigned_char(int(value))
    
    def write_ascii(self, string: str = None) -> None:
        if string:
            self.write_unsigned_char(len(string))
            self.write(string.encode())
        else:
            self.write_unsigned_char(0xff)
    
    def write_twip(self, value: float):
        self.write_int(int(round(value * 20)))
    
    def write_matrix2x3(self, matrix: list):
        self.write_int(int(round(matrix[0][0] * 1024)))
        self.write_int(int(round(matrix[0][1] * 1024)))
        self.write_int(int(round(matrix[1][0] * 1024)))
        self.write_int(int(round(matrix[1][1] * 1024)))

        self.write_twip(matrix[0][2])
        self.write_twip(matrix[1][2])
    
    def write_bgra(self, color: list):
        r, g, b, a = color
        self.write_unsigned_char(b)
        self.write_unsigned_char(g)
        self.write_unsigned_char(r)
        self.write_unsigned_char(a)
    
    def write_bgr(self, color: list):
        r, g, b = color
        self.write_unsigned_char(b)
        self.write_unsigned_char(g)
        self.write_unsigned_char(r)
