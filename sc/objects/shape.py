from .tag import Tag

from .texture import SWFTexture

from PIL import Image, ImageDraw



class Point:
    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = x
        self.y = y

    @property
    def coordinate(self):
        return self.x, self.y
    
    @coordinate.setter
    def coordinate(self, new: list):
        self.x, self.y = new


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

        points_count = len(twips)
        
        bitmap.twips = [_cls() for _cls in [Point] * points_count]
        bitmap.uvs = [_cls() for _cls in [Point] * points_count]

        for i, twip in enumerate(twips):
            bitmap.twips[i].coordinate = twip
        
        for i, uv in enumerate(uvs):
            bitmap.uvs[i].coordinate = uv

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
    
    def to_image(self):
        # Creating shape region
        left = 0
        top = 0
        right = 0
        bottom = 0

        for bitmap in self.bitmaps:
            left = min(left, min(point.x for point in bitmap.twips))
            top = min(top, min(point.y for point in bitmap.twips))
            right = max(right, max(point.x for point in bitmap.twips))
            bottom = max(bottom, max(point.y for point in bitmap.twips))
        
        result_size = round(right - left), round(bottom - top)
        image = Image.new("RGBA", result_size)

        # Adding bitmap regions
        for bitmap in self.bitmaps:
            bitmap_image = bitmap.to_image()

            bitmap_left = min(point.x for point in bitmap.twips)
            bitmap_top = min(point.y for point in bitmap.twips)

            x = int(bitmap_left + abs(left))
            y = int(bitmap_top + abs(top))

            image.paste(bitmap_image, (x, y), bitmap_image)
        
        return image


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
        
        self.twips = [_cls() for _cls in [Point] * points_count]
        self.uvs = [_cls() for _cls in [Point] * points_count]
        
        for i in range(points_count):
            x = self.read_twip()
            y = self.read_twip()
            self.twips[i].coordinate = (x, y)
        
        for i in range(points_count):
            x = self.read_unsigned_short() / 0xFFFF * self.texture.width
            y = self.read_unsigned_short() / 0xFFFF * self.texture.height

            x = int(round(x))
            y = int(round(y))

            self.uvs[i].coordinate = (x, y)
    
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
            self.write_twip(self.twips[x].x)
            self.write_twip(self.twips[x].y)
        
        for x in range(points_count):
            self.write_unsigned_short(int(round(self.uvs[x].x * 0xFFFF / self.texture.width)))
            self.write_unsigned_short(int(round(self.uvs[x].y * 0xFFFF / self.texture.height)))
    
    def to_image(self):
        if not self.texture.image:
            return
        
        # Creating region
        region_size = self.texture.width, self.texture.height
        
        mask = Image.new("1", region_size, 0)
        polygon = [point.coordinate for point in self.uvs]
        
        ImageDraw.Draw(mask).polygon(polygon, fill=1)

        region = Image.new("RGBA", region_size)
        region.paste(self.texture.image, None, mask)

        bbox = region.getbbox()
        if bbox:
            region = region.crop(bbox)
        
        # Apply region transforms
        left = min(point.x for point in self.twips)
        right = max(point.x for point in self.twips)
        top = min(point.y for point in self.twips)
        bottom = max(point.y for point in self.twips)

        result_size = round(right - left), round(bottom - top)
        angle, mirroring = calculate_rotation(self)

        if angle in (90, 270):
            result_size = result_size[::-1]
        
        if mirroring:
            region = region.transform(region.size, Image.EXTENT, (region.size[0], 0, 0, region.size[1]))
        
        region = region.resize(result_size, Image.ANTIALIAS).rotate(angle, expand=True)

        return region


def calculate_rotation(region):
    def calc_sum(points):
        x1, y1 = points[(z + 1) % num_points].coordinate
        x2, y2 = points[z].coordinate
        return (x1 - x2) * (y1 + y2)

    sum_sheet = 0
    sum_shape = 0
    num_points = len(region.twips)

    for z in range(num_points):
        sum_sheet += calc_sum(region.uvs)
        sum_shape += calc_sum(region.twips)

    sheet_orientation = -1 if (sum_sheet < 0) else 1
    shape_orientation = -1 if (sum_shape < 0) else 1

    mirroring = int(not (shape_orientation == sheet_orientation))

    sheet_pos_0 = region.uvs[0]
    sheet_pos_1 = region.uvs[1]
    shape_pos_0 = region.twips[0]
    shape_pos_1 = region.twips[1]

    if sheet_pos_0 == sheet_pos_1:
        sheet_pos_0 = Point(sheet_pos_0.x + 1, sheet_pos_0.y)

    if mirroring:
        shape_pos_0 = Point(shape_pos_0.x * -1, shape_pos_0.y)
        shape_pos_1 = Point(shape_pos_1.x * -1, shape_pos_1.y)

    if sheet_pos_1.x > sheet_pos_0.x:
        sheet_x = 1
    elif sheet_pos_1.x < sheet_pos_0.x:
        sheet_x = 2
    else:
        sheet_x = 3

    if sheet_pos_1.y < sheet_pos_0.y:
        sheet_y = 1
    elif sheet_pos_1.y > sheet_pos_0.y:
        sheet_y = 2
    else:
        sheet_y = 3

    if shape_pos_1.x > shape_pos_0.x:
        shape_x = 1
    elif shape_pos_1.x < shape_pos_0.x:
        shape_x = 2
    else:
        shape_x = 3

    if shape_pos_1.y > shape_pos_0.y:
        shape_y = 1
    elif shape_pos_1.y < shape_pos_0.y:
        shape_y = 2
    else:
        shape_y = 3

    rotation = 0
    if sheet_x == shape_x and sheet_y == shape_y:
        rotation = 0
    elif sheet_x == 3:
        if sheet_x == shape_y:
            if sheet_y == shape_x:
                rotation = 1
            else:
                rotation = 3
        else:
            rotation = 2
    elif sheet_y == 3:
        if sheet_y == shape_x:
            if sheet_x == shape_y:
                rotation = 3
            else:
                rotation = 1
        else:
            rotation = 2
    elif sheet_x != shape_x and sheet_y != shape_y:
        rotation = 2
    elif sheet_x == sheet_y:
        if sheet_x != shape_x:
            rotation = 3
        elif sheet_y != shape_y:
            rotation = 1
    elif sheet_x != sheet_y:
        if sheet_x != shape_x:
            rotation = 1
        elif sheet_y != shape_y:
            rotation = 3

    if sheet_orientation == -1 and rotation in (1, 3):
        rotation += 2
        rotation %= 4

    return rotation * 90, mirroring
