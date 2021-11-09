from .tag import Tag

from .matrix import Matrix2x3
from .color_transform import ColorTransform



class MovieClip(Tag):
    def __init__(self, tag: int = 12) -> None:
        super().__init__(tag)

        self.export_id: int = 0

        self.fps: int = 30
        self.binds: list = []
        self.blends: list = []
        self.names: list = []

        self.transform_storage_id: int = 0

        self._frames: list = []
        self.scaling_grid: ScalingGrid = None
    
    @property
    def frames(self):
        return self._frames

    def bind(self, obj: Tag, blend: int = 0, name: str = None):
        self.binds.append(obj)
        self.blends.append(blend)
        self.names.append(name)

    def keyframe(
            self,
            frame_index: int,
            bind_index: int,
            translation: list = None,
            scale: list = None,
            rotation: float = None,
            addition: list = None,
            multiplier: list = None,
            alpha: int = None
        ):
        if len(self.frames) < frame_index + 1:
            while len(self.frames) != frame_index + 1:
                self._frames.append(Frame())
        
        if bind_index not in self._frames[frame_index].resources:
            self._frames[frame_index].resources[bind_index] = {}
        
        matrix = None
        color_transform = None

        if translation is not None or scale is not None or rotation is not None and matrix is None:
            matrix = Matrix2x3()
        
        if addition is not None or multiplier is not None or alpha is not None and color_transform is None:
            color_transform = ColorTransform()
        
        if translation is not None:
            matrix.translate(translation)
        
        if scale is not None:
            matrix.scale(scale)
        
        if rotation is not None:
            matrix.rotate(rotation)
        
        if addition is not None:
            color_transform.addition[:3] = addition
        
        if multiplier is not None:
            color_transform.multiplier = multiplier
        
        if alpha is not None:
            color_transform.addition[3] = alpha

        self._frames[frame_index].resources[bind_index]["matrix"] = matrix
        self._frames[frame_index].resources[bind_index]["color_transform"] = color_transform

    def frame_name(self, frame_index: int, name: str):
        self._frames[frame_index].name = name
    
    def scale(self, x: float, y: float, width: float, height: float):
        self.scaling_grid = ScalingGrid()

        self.scaling_grid.x = x
        self.scaling_grid.y = y

        self.scaling_grid.width = width + x
        self.scaling_grid.height = height + y

    def load(self, data: bytes, swf):
        super().load(data)

        self.export_id = self.read_unsigned_short()
        self.fps = self.read_unsigned_char()

        if self.tag == 3:
            raise TypeError("TAG_MOVIE_CLIP no longer support")
        
        if self.tag == 14:
            raise TypeError("TAG_MOVIE_CLIP_4 no longer support")

        frames_count = self.read_unsigned_short()
        self._frames = [_cls() for _cls in [Frame] * frames_count]

        transforms = []
        for x in range(self.read_int()):
            transforms.append({
                "bind_id": self.read_unsigned_short(),
                "matrix_id": self.read_unsigned_short(),
                "color_transform_id": self.read_unsigned_short()
            })
        
        binds_count = self.read_unsigned_short()

        for x in range(binds_count):
            bind_id = self.read_unsigned_short()
            self.binds.append(swf.get_object_by_id(bind_id))
        
        if self.tag in (35, 12):
            for x in range(binds_count):
                self.blends.append(self.read_unsigned_char())
        
        for x in range(binds_count):
            self.names.append(self.read_ascii())
        
        frame_id = 0
        current_transform = 0
        while True:
            frame_tag = self.read_unsigned_char()
            frame_length = self.read_unsigned_int()
            frame_data = self.read(frame_length)

            if frame_tag == 0:
                break

            if frame_tag == 11:
                frame = Frame(frame_tag)
                resources_count = frame.load(frame_data)

                for x in range(resources_count):
                    transform = transforms[current_transform + x]

                    resource = {
                        "matrix": None,
                        "color_transform": None
                    }

                    if transform["matrix_id"] != 0xFFFF:
                        resource["matrix"] = swf.transforms[self.transform_storage_id].matrices[transform["matrix_id"]]
                    
                    if transform["color_transform_id"] != 0xFFFF:
                        resource["color_transform"] = swf.transforms[self.transform_storage_id].color_transforms[transform["color_transform_id"]]

                    frame.resources[transform["bind_id"]] = resource
                
                current_transform += resources_count

                self._frames[frame_id] = frame
                frame_id += 1
            
            elif frame_tag == 31:
                scaling_grid = ScalingGrid(frame_tag)
                scaling_grid.load(frame_data)

                self.scaling_grid = scaling_grid

            elif frame_tag == 41:
                self.transform_storage_id = TransformStorageIndex(frame_tag).load(frame_data)

            else:
                raise TypeError(f"Unknown tag in MovieClip, {frame_tag}")
    
    @property
    def matrices_count(self):
        result = 0
        for frame in self.frames:
            for bind_id in frame.resources:
                result += 1 if frame.resources[bind_id]["matrix"] else 0
        return result
    
    @property
    def color_transforms_count(self):
        result = 0
        for frame in self.frames:
            for bind_id in frame.resources:
                result += 1 if frame.resources[bind_id]["color_transform"] else 0
        return result
    
    def save(self, swf):
        super().save()

        self.write_unsigned_short(self.export_id)
        self.write_unsigned_char(self.fps)

        if self.tag == 3:
            raise TypeError("TAG_MOVIE_CLIP no longer support")
        
        if self.tag == 14:
            raise TypeError("TAG_MOVIE_CLIP_4 no longer support")
        
        self.write_unsigned_short(len(self.frames))

        transforms = []
        for frame in self.frames:
            for bind_id in frame.resources:
                resource = frame.resources[bind_id]

                matrix_id = 0xFFFF
                color_transform_id = 0xFFFF

                if resource["matrix"] is not None:
                    matrix_id = swf.transforms[self.transform_storage_id].matrices.index(resource["matrix"])
                
                if resource["color_transform"] is not None:
                    color_transform_id = swf.transforms[self.transform_storage_id].color_transforms.index(resource["color_transform"])
                
                transforms.append({
                    "bind_id": bind_id,
                    "matrix_id": matrix_id,
                    "color_transform_id": color_transform_id
                })
        
        self.write_int(len(transforms))
        for transform in transforms:
            self.write_unsigned_short(transform["bind_id"])
            self.write_unsigned_short(transform["matrix_id"])
            self.write_unsigned_short(transform["color_transform_id"])
        
        self.write_unsigned_short(len(self.binds))

        for obj in self.binds:
            self.write_unsigned_short(obj.export_id)
        
        if self.tag in (35, 12):
            for blend in self.blends:
                self.write_unsigned_char(blend)
        
        for name in self.names:
            self.write_ascii(name)
        
        if bool(self.transform_storage_id):
            index = TransformStorageIndex()
            index.save(self.transform_storage_id)

            self.write_unsigned_char(index.tag)
            self.read_unsigned_int(len(index.buffer))
            self.write(index.buffer)
        
        for frame in self.frames:
            frame.save()

            self.write_unsigned_char(frame.tag)
            self.write_unsigned_int(len(frame.buffer))
            self.write(frame.buffer)
        
        if self.scaling_grid:
            self.scaling_grid.save()

            self.write_unsigned_char(self.scaling_grid.tag)
            self.read_unsigned_int(len(self.scaling_grid.buffer))
            self.write(self.scaling_grid.buffer)
        
        self.write(bytes(5))


class Frame(Tag):
    def __init__(self, tag: int = 11) -> None:
        super().__init__(tag)

        self.name: str = None
        self.resources: dict = {}
    
    def load(self, data: bytes):
        super().load(data)

        resources_count = self.read_unsigned_short()
        self.name = self.read_ascii()

        return resources_count
    
    def save(self):
        super().save()

        self.write_unsigned_short(len(list(self.resources.items())))
        self.write_ascii(self.name)


class ScalingGrid(Tag):
    def __init__(self, tag: int = 31) -> None:
        super().__init__(tag)

        self.x: float = 0.0
        self.y: float = 0.0

        self.width: float = 0.0
        self.height: float = 0.0
    
    def load(self, data: bytes):
        super().load(data)

        self.x = self.read_twip()
        self.y = self.read_twip()

        self.width = self.read_twip() + self.x
        self.height = self.read_twip() + self.y
    
    def save(self):
        super().save()

        self.write_twip(self.x)
        self.write_twip(self.y)

        self.write_twip(self.width - self.x)
        self.write_twip(self.height - self.y)


class TransformStorageIndex(Tag):
    def __init__(self, tag: int = 41) -> None:
        super().__init__(tag)
    
    def load(self, data: bytes):
        super().load(data)

        return self.read_unsigned_char()
    
    def save(self, index: int):
        super().save()

        self.write_unsigned_char(index)
