from .tag import Tag

from .texture import SWFTexture

from PIL import Image, ImageDraw



class Shape(Tag):
    def __init__(self, tag: int = 18) -> None:
        super().__init__(tag)

        self.export_id: int = 0
        self._bitmaps: list = []
    
    @property
    def bitmaps(self):
        return self._bitmaps
    
    def load(self, data: bytes, swf):
        super().load(data)

        self.export_id = self.read_unsigned_short()
        bitmaps_count = self.read_unsigned_short()

        self._bitmaps = [_cls() for _cls in [Bitmap] * bitmaps_count]

        # Find usage
        points_count = 4 * bitmaps_count
        if self.tag == 18:
            points_count = self.read_unsigned_short()
        
        bitmap_id = 0
        while True:
            bitmap_tag = self.read_unsigned_char()
            bitmap_length = self.read_unsigned_int()
            bitmaps_data = self.read(bitmap_length)

            if bitmap_tag == 0:
                break

            if bitmap_tag in (4, 17, 22):
                bitmap = Bitmap(bitmap_tag)
                bitmap.load(bitmaps_data, swf)

                self._bitmaps[bitmap_id] = bitmap
                bitmap_id += 1

            elif bitmap_tag == 6:
                raise TypeError("SHAPE_DRAW_COLOR_FILL_COMMAND_TAG no longer support")
            
            else:
                raise TypeError(f"Unknown tag in Shape, {bitmap_tag}")
    
    def create_bitmap(self, texture: SWFTexture, twips: list, uvs: list):
        bitmap = Bitmap()

        if len(twips) != len(uvs):
            raise TypeError("All twips must have texture coordinates!")

        bitmap.texture = texture
        bitmap.twips = twips
        bitmap.uvs = uvs

        self._bitmaps.append(bitmap)
    
    def save(self, swf):
        super().save()

        self.write_unsigned_short(self.export_id)
        self.write_unsigned_short(len(self.bitmaps))

        if self.tag == 18:
            points_count = 0
            for bitmap in self.bitmaps:
                points_count += len(bitmap.twips)
            self.write_unsigned_short(points_count)
        
        for bitmap in self.bitmaps:
            bitmap.save(swf)

            self.write_unsigned_char(bitmap.tag)
            self.write_int(len(bitmap.buffer))
            self.write(bitmap.buffer)
        
        self.write(bytes(5))


class Bitmap(Tag):
    def __init__(self, tag: int = 22) -> None:
        super().__init__(tag)

        self.texture: SWFTexture = None

        self.twips: list = []
        self.uvs: list = []
    
    def load(self, data: bytes, swf):
        super().load(data)

        self.texture = swf.textures[self.read_unsigned_char()]

        points_count = 4
        if self.tag != 4:
            points_count = self.read_unsigned_char()
        
        for i in range(points_count):
            x = self.read_twip()
            y = self.read_twip()
            self.twips.append([x, y])
        
        for i in range(points_count):
            x = self.read_unsigned_short() / 0xFFFF * self.texture.width
            y = self.read_unsigned_short() / 0xFFFF * self.texture.height
            self.uvs.append([x, y])
    
    def save(self, swf):
        super().save()

        if self.texture is None:
            raise TypeError("Bitmap has no SWFTexture!")
        
        if len(self.twips) != len(self.uvs):
            raise TypeError("All twips must have texture coordinates!")
        
        self.write_unsigned_char(swf.textures.index(self.texture))

        if self.tag == 4:
            points_count = 4
        else:
            points_count = len(self.twips)
            self.write_unsigned_char(points_count)
        
        for x in range(points_count):
            self.write_twip(self.twips[x][0])
            self.write_twip(self.twips[x][1])
        
        for x in range(points_count):
            self.write_unsigned_short(round(self.uvs[x][0] * 0xFFFF / self.texture.width))
            self.write_unsigned_short(round(self.uvs[x][1] * 0xFFFF / self.texture.height))
    
    def to_image(self, fp: str):
        if not self.texture.image:
            return
        
        region_size = self.texture.width, self.texture.height
        
        mask = Image.new("1", region_size, 0)
        polygon = []
        for uv in self.uvs:
            polygon.append((
                int(round(uv[0])),
                int(round(uv[1]))
            ))
        
        ImageDraw.Draw(mask).polygon(polygon, fill=1)

        region = Image.new(self.texture.image.mode, region_size)
        region.paste(self.texture.image, None, mask)

        bbox = region.getbbox()
        if bbox:
            region = region.crop(region.getbbox())

        region.save(fp, "PNG")
