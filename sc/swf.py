import os

from sc_compression.signatures import Signatures
from sc_compression import Decompressor, Compressor

from sc.utils import Reader, Writer

from .objects import (
    Tag,
    Export,
    SWFTexture,
    MovieClipModifiers,
    MovieClipModifier,
    Shape,
    TextField,
    TransformStorage,
    Matrix2x3,
    ColorTransform,
    MovieClip
)



class SupercellSWF:
    def __init__(self) -> None:
        self.reader: Reader = None
        self.writer: Writer = None

        self._exports: list = []

        self._textures: list = []
        self._shapes: list = []
        self._movie_clip_modifiers: list = []
        self._text_fields: list = []
        self._transforms: list = []
        self._movie_clips: list = []

        self.use_highres_assets: bool = False
        self.use_lowres_assets: bool = False
        self.external_texture_file: bool = False

    @property
    def exports(self):
        return self._exports
    
    @property
    def textures(self):
        return self._textures
    
    @property
    def movie_clip_modifiers(self):
        return self._movie_clip_modifiers
    
    @property
    def shapes(self):
        return self._shapes
    
    @property
    def text_fields(self):
        return self._text_fields
    
    @property
    def transforms(self):
        return self._transforms
    
    @property
    def movie_clips(self):
        return self._movie_clips
    
    def get_export_by_id(self, export_id: int):
        for export in self.exports:
            if export.export_id == export_id:
                return self.get_object_by_id(export_id)

    def get_export_by_name(self, export_name: str):
        for export in self.exports:
            if export.name == export_name:
                return self.get_object_by_id(export.export_id)

    def get_object_by_id(self, export_id: int):
        for modifier in self.movie_clip_modifiers:
            if modifier.export_id == export_id:
                return modifier
        
        for shape in self.shapes:
            if shape.export_id == export_id:
                return shape
        
        for text_field in self.text_fields:
            if text_field.export_id == export_id:
                return text_field
        
        for movie_clip in self.movie_clips:
            if movie_clip.export_id == export_id:
                return movie_clip
        
        raise TypeError(f"Can't find object with {export_id}!")
    
    def create_export(self, movie_clip: MovieClip, name: str):
        export = Export()

        export.export_id = movie_clip.export_id
        export.name = name

        self._exports.append(export)
        self._create_object(movie_clip)
    
    def _create_object(self, obj: Tag):
        if isinstance(obj, MovieClipModifier):
            if obj not in self.movie_clip_modifiers:
                self._movie_clip_modifiers.append(obj)
        
        elif isinstance(obj, Shape):
            if obj not in self.shapes:
                self._shapes.append(obj)
            
            for bitmap in obj.bitmaps:
                if bitmap.texture not in self.textures:
                    self._textures.append(bitmap.texture)
        
        elif isinstance(obj, TextField):
            if obj not in self.text_fields:
                self._text_fields.append(obj)
        
        elif isinstance(obj, MovieClip):
            if obj not in self.movie_clips:
                self._movie_clips.append(obj)
            
            for bind in obj.binds:
                self._create_object(bind)
            
            transform_storage_id = None
            for transform_storage in self.transforms:
                if transform_storage.has_avaible:
                    if transform_storage.avaible_matrices > obj.matrices_count and transform_storage.avaible_color_transforms > obj.color_transforms_count:
                        transform_storage_id = self.transforms.index(transform_storage)
                        break
            
            if transform_storage_id is None:
                transform_storage = TransformStorage()
                self._transforms.append(transform_storage)
                transform_storage_id = self.transforms.index(transform_storage)
            
            obj.transform_storage_id = transform_storage_id
            
            for frame in obj.frames:
                for bind_id in frame.resources:
                    matrix = frame.resources[bind_id]["matrix"]
                    color_transform = frame.resources[bind_id]["color_transform"]

                    if matrix:
                        if matrix not in self.transforms[transform_storage_id].matrices:
                            self._transforms[transform_storage_id].matrices.append(matrix)
                    
                    if color_transform:
                        if color_transform not in self.transforms[transform_storage_id].color_transforms:
                            self._transforms[transform_storage_id].color_transforms.append(color_transform)

    def load(self, fp: str, load_texture_file: bool = True):
        decompressor = Decompressor()
        content = decompressor.decompress(open(fp, 'rb').read())
        self.reader = Reader(content)

        is_texture_file = os.path.basename(fp).endswith("_tex.sc")

        if is_texture_file:
            # Loading texture file
            while True:
                tag = self.reader.read_unsigned_char()
                length = self.reader.read_unsigned_int()
                data = self.reader.read(length)

                if tag == 0:
                    break

                if tag in (1, 16, 19, 24, 27, 28, 29, 34):
                    texture = SWFTexture(tag)
                    texture.load(data, self)

                    self._textures.append(texture)

                else:
                    raise TypeError(f"Unknown tag in texture file, {tag}")
        else:
            # Loading SWF header
            shapes_count = self.reader.read_unsigned_short()
            self._shapes = [_cls() for _cls in [Shape] * shapes_count]

            movie_clips_count = self.reader.read_unsigned_short()
            self._movie_clips = [_cls() for _cls in [MovieClip] * movie_clips_count]

            textures_count = self.reader.read_unsigned_short()
            self._textures = [_cls() for _cls in [SupercellSWF] * textures_count]

            text_fields_count = self.reader.read_unsigned_short()
            self._text_fields = [_cls() for _cls in [TextField] * text_fields_count]

            self._transforms = [TransformStorage()]

            matrices_count = self.reader.read_unsigned_short()
            self._transforms[0].matrices = [_cls() for _cls in [Matrix2x3] * matrices_count]

            color_transforms_count = self.reader.read_unsigned_short()
            self._transforms[0].color_transforms = [_cls() for _cls in [ColorTransform] * color_transforms_count]

            self._movie_clip_modifiers = []

            self.reader.read(5) # unused

            exports_count = self.reader.read_unsigned_short()
            self._exports = [_cls() for _cls in [Export] * exports_count]

            for x in range(exports_count):
                self._exports[x].export_id = self.reader.read_unsigned_short()
            
            for x in range(exports_count):
                self._exports[x].name = self.reader.read_ascii()
            
            # Loading tags

            texture_id = 0
            transform_storage_id = 0
            matrix_id = 0
            color_transform_id = 0

            loaded_modifiers = 0
            loaded_shapes = 0
            loaded_text_fields = 0
            loaded_movie_clips = 0

            self.use_highres_assets = False
            self.use_lowres_assets = False
            self.external_texture_file = False

            texture_file = None

            while True:
                tag = self.reader.read_unsigned_char()
                length = self.reader.read_unsigned_int()
                data = self.reader.read(length)

                if tag == 0:
                    break

                if tag == 23:
                    self.use_highres_assets = True

                elif tag == 26:
                    self.external_texture_file = True

                    if load_texture_file:
                        texture_fp = os.path.splitext(fp)[0] + "_tex.sc"
                        texture_file = SupercellSWF()
                        texture_file.load(texture_fp)

                        if len(self.textures) != len(texture_file.textures):
                            raise TypeError("Bad textures count in texture file!")

                elif tag == 30:
                    self.use_lowres_assets = True

                elif tag in (1, 16, 19, 24, 27, 28, 29, 34):
                    texture = SWFTexture(tag)
                    texture.load(data, self)

                    if texture_file is None:
                        self._textures[texture_id] = texture
                    else:
                        self._textures[texture_id] = texture_file.textures[texture_id]
                    
                    texture_id += 1

                elif tag == 37:
                    modifiers = MovieClipModifiers(tag)
                    modifiers.load(data, self)

                elif tag in (38, 39, 40):
                    modifier = MovieClipModifier(tag)
                    modifier.load(data)

                    self._movie_clip_modifiers[loaded_modifiers] = modifier
                    loaded_modifiers += 1

                elif tag in (2, 18):
                    shape = Shape(tag)
                    shape.load(data, self)

                    self._shapes[loaded_shapes] = shape
                    loaded_shapes += 1

                elif tag in (7, 15, 20, 21, 25, 33, 44):
                    text_field = TextField(tag)
                    text_field.load(data)

                    self._text_fields[loaded_text_fields] = text_field
                    loaded_text_fields += 1

                elif tag == 42:
                    transform_storage = TransformStorage(tag)
                    transform_storage.load(data)

                    self._transforms.append(transform_storage)

                    transform_storage_id += 1
                    matrix_id = 0
                    color_transform_id = 0

                elif tag == 8:
                    matrix = Matrix2x3(tag)
                    matrix.load(data)

                    self._transforms[transform_storage_id].matrices[matrix_id] = matrix
                    matrix_id += 1

                elif tag == 9:
                    color_transform = ColorTransform(tag)
                    color_transform.load(data)

                    self._transforms[transform_storage_id].color_transforms[color_transform_id] = color_transform
                    color_transform_id += 1

                elif tag in (3, 10, 12, 14, 35):
                    movie_clip = MovieClip(tag)
                    movie_clip.load(data, self)

                    self._movie_clips[loaded_movie_clips] = movie_clip
                    loaded_movie_clips += 1

                else:
                    raise TypeError(f"Unknown tag in SWF file, {tag}")

    def save(self, fp: str, save_texture_file: bool = True):
        compressor = Compressor()
        self.writer = Writer()

        is_texture_file = os.path.basename(fp).endswith("_tex.sc")

        if is_texture_file:
            # Saving texture file
            for texture in self.textures:
                texture.save(self)

                self.writer.write_unsigned_char(texture.tag)
                self.writer.write_unsigned_int(len(texture.buffer))
                self.writer.write(texture.buffer)
            
            self.writer.write(bytes(5))
        else:
            self._movie_clip_modifiers.clear()
            self._shapes.clear()
            self._text_fields.clear()
            self._transforms.clear()

            # Saving SWF header
            for movie_clip in self.movie_clips:
                self._create_object(movie_clip)
            
            self.writer.write_unsigned_short(len(self.shapes))
            self.writer.write_unsigned_short(len(self.movie_clips))
            self.writer.write_unsigned_short(len(self.textures))
            self.writer.write_unsigned_short(len(self.text_fields))

            if not self.transforms:
                self._transforms.append(TransformStorage())
            
            self.writer.write_unsigned_short(len(self.transforms[0].matrices))
            self.writer.write_unsigned_short(len(self.transforms[0].color_transforms))

            self.writer.write(bytes(5)) # unused

            self.writer.write_unsigned_short(len(self.exports))

            for export in self.exports:
                self.writer.write_unsigned_short(export.export_id)
            
            for export in self.exports:
                self.writer.write_ascii(export.name)
            
            # Saving tags
            
            def write_object(obj):
                self.writer.write_unsigned_char(obj.tag)
                self.writer.write_unsigned_int(len(obj.buffer))
                self.writer.write(obj.buffer)
            
            if self.use_highres_assets:
                write_object(Tag(23))
            
            if self.external_texture_file:
                write_object(Tag(26))

                if save_texture_file:
                    texture_fp = os.path.splitext(fp)[0] + "_tex.sc"
                    texture_file = SupercellSWF()
                    texture_file._textures = self._textures
                    texture_file.save(texture_fp)
            
            if self.use_lowres_assets:
                write_object(Tag(30))
            
            for texture in self.textures:
                texture.save(self)
                write_object(texture)
            
            if self.movie_clip_modifiers:
                modifiers = MovieClipModifiers()
                modifiers.save()
                write_object(modifiers)
            
            for modifier in self.movie_clip_modifiers:
                modifier.save(self)
                write_object(modifier)
            
            for shape in self.shapes:
                shape.save(self)
                write_object(shape)
            
            for text_field in self.text_fields:
                text_field.save()
                write_object(text_field)
            
            for transform_storage in self.transforms:
                if bool(self.transforms.index(transform_storage)):
                    transform_storage.save()
                    write_object(transform_storage)
                
                for matrix in transform_storage.matrices:
                    matrix.save()
                    write_object(matrix)
                
                for color_transform in transform_storage.color_transforms:
                    color_transform.save()
                    write_object(color_transform)
            
            for movie_clip in self.movie_clips:
                movie_clip.save(self)
                write_object(movie_clip)
            
            self.writer.write(bytes(5))

        open(fp, 'wb').write(compressor.compress(self.writer.buffer, Signatures.SC, 1))
        # open(fp, 'wb').write(self.writer.buffer) # for tests in 010 Editor
