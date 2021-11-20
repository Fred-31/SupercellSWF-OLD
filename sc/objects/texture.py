from .tag import Tag

from PIL import Image



class SWFTexture(Tag):
    def __init__(self, tag: int = 1) -> None:
        super().__init__(tag)

        self.pixel_type: int = 0
        self.width: int = 0
        self.height: int = 0

        self.image: Image = None
    
    def from_image(self, image: Image):
        self.width, self.height = image.size

        mode = image.mode
        if mode == "RGBA":
            self.pixel_type = 0
        elif mode == "RGB":
            self.pixel_type = 4
        elif mode == "LA":
            self.pixel_type = 6
        elif mode == "L":
            self.pixel_type = 10
        else:
            raise TypeError(f"Unsupported Image mode for SWFTexture, {mode}")

        self.image = image
    
    def load(self, data: bytes, swf):
        super().load(data)

        self.pixel_type = self.read_unsigned_char()
        self.width = self.read_unsigned_short()
        self.height = self.read_unsigned_short()

        if not swf.external_texture_file:
            pixels = []
            read_pixel = None
            if self.pixel_type in (0, 1):
                mode = "RGBA"
                def read_pixel():
                    return self.read_unsigned_char(), self.read_unsigned_char(), self.read_unsigned_char(), self.read_unsigned_char()
            
            elif self.pixel_type == 2:
                mode = "RGBA"
                def read_pixel():
                    p = self.read_unsigned_short()
                    return (p >> 12 & 15) << 4, (p >> 8 & 15) << 4, (p >> 4 & 15) << 4, (p >> 0 & 15) << 4
            
            elif self.pixel_type == 3:
                mode = "RGBA"
                def read_pixel():
                    p = self.read_unsigned_short()
                    return (p >> 11 & 31) << 3, (p >> 6 & 31) << 3, (p >> 1 & 31) << 3, (p & 255) << 7
            
            elif self.pixel_type == 4:
                mode = "RGB"
                def read_pixel():
                    p = self.read_unsigned_short()
                    return (p >> 11 & 31) << 3, (p >> 5 & 63) << 2, (p & 31) << 3
            
            elif self.pixel_type == 6:
                mode = "LA"
                def read_pixel():
                    p = self.read_unsigned_short()
                    return p & 255, p >> 8
            
            elif self.pixel_type == 10:
                mode = "L"
                def read_pixel():
                    return self.read_unsigned_char()
            
            else:
                raise TypeError(f"Unknown SWFTexture pixel type, {self.pixel_type}")

            image = Image.new(mode, (self.width, self.height))

            if read_pixel is not None:
                for y in range(self.height):
                    for x in range(self.width):
                        pixels.append(read_pixel())
            
                image.putdata(pixels)
            
            if self.tag in (27, 28):
                loaded_img = image.load()
                pixel_index = 0
                chunk_size = 32

                x_chunks_count = self.width // chunk_size
                y_chunks_count = self.height // chunk_size
                x_rest = self.width % chunk_size
                y_rest = self.height % chunk_size

                for y_chunk in range(y_chunks_count):
                    for x_chunk in range(x_chunks_count):
                        for y in range(chunk_size):
                            for x in range(chunk_size):
                                loaded_img[x_chunk * chunk_size + x, y_chunk * chunk_size + y] = pixels[pixel_index]
                                pixel_index += 1

                    for y in range(chunk_size):
                        for x in range(x_rest):
                            loaded_img[(self.width - x_rest) + x, y_chunk * chunk_size + y] = pixels[pixel_index]
                            pixel_index += 1
                
                for x_chunk in range(x_chunks_count):
                    for y in range(y_rest):
                        for x in range(chunk_size):
                            loaded_img[x_chunk * chunk_size + x, (self.height - y_rest) + y] = pixels[pixel_index]
                            pixel_index += 1

                for y in range(y_rest):
                    for x in range(x_rest):
                        loaded_img[x + (self.width - x_rest), y + (self.height - y_rest)] = pixels[pixel_index]
                        pixel_index += 1
            
            self.image = image
    
    def save(self, swf):
        super().save()

        if self.image is not None:
            self.from_image(self.image)

        self.write_unsigned_char(self.pixel_type)
        self.write_unsigned_short(self.width)
        self.write_unsigned_short(self.height)

        if not swf.external_texture_file:
            if self.image is None:
                raise TypeError("SWFTexture has no Image!")

            write_pixel = None
            if self.pixel_type in (0, 1):
                def write_pixel(pixel):
                    r, g, b, a = pixel
                    self.write_unsigned_char(r)
                    self.write_unsigned_char(g)
                    self.write_unsigned_char(b)
                    self.write_unsigned_char(a)
            
            if self.pixel_type == 2:
                def write_pixel(pixel):
                    r, g, b, a = pixel
                    self.write_unsigned_short(a >> 4 | b >> 4 << 4 | g >> 4 << 8 | r >> 4 << 12)
            
            if self.pixel_type == 3:
                def write_pixel(pixel):
                    r, g, b, a = pixel
                    self.write_unsigned_short(a >> 7 | b >> 3 << 1 | g >> 3 << 6 | r >> 3 << 11)
            
            if self.pixel_type == 4:
                def write_pixel(pixel):
                    r, g, b = pixel
                    self.write_unsigned_short(b >> 3 | g >> 2 << 5 | r >> 3 << 11)
            
            if self.pixel_type == 6:
                def write_pixel(pixel):
                    l, a = pixel
                    self.write_unsigned_short(l >> 8 | a)
            
            if self.pixel_type == 10:
                def write_pixel(pixel):
                    self.write_unsigned_char(pixel)

            if write_pixel is not None:
                pixels = self.image.getdata()

                if self.tag in (27, 28):
                    pixels = []
                    loaded_img = self.image.load()
                    chunk_size = 32

                    x_chunks_count = self.width // chunk_size
                    y_chunks_count = self.height // chunk_size
                    x_rest = self.width % chunk_size
                    y_rest = self.height % chunk_size

                    for y_chunk in range(y_chunks_count):
                        for x_chunk in range(x_chunks_count):
                            for y in range(chunk_size):
                                for x in range(chunk_size):
                                    pixels.append(loaded_img[x + (x_chunk * chunk_size), y + (y_chunk * chunk_size)])

                        for y in range(chunk_size):
                            for x in range(x_rest):
                                pixels.append(loaded_img[x + (self.width - x_rest), y + (y_chunk * chunk_size)])

                    for x_chunk in range(self.width // chunk_size):
                        for y in range(y_rest):
                            for x in range(chunk_size):
                                pixels.append(loaded_img[x + (x_chunk * chunk_size), y + (self.height - y_rest)])

                    for y in range(y_rest):
                        for x in range(x_rest):
                            pixels.append(loaded_img[x + (self.width - x_rest), y + (self.height - y_rest)])
                
                for y in range(self.height):
                    for x in range(self.width):
                        write_pixel(pixels[y * self.width + x])
