from .tag import Tag

from .matrix import Matrix2x3
from .color_transform import ColorTransform



class TransformStorage(Tag):
    def __init__(self, tag: int = 42) -> None:
        super().__init__(tag)

        self.matrices: list = []
        self.color_transforms: list = []
    
    def load(self, data: bytes):
        super().load(data)

        matrices_count = self.read_unsigned_short()
        color_transforms_count = self.read_unsigned_short()

        self.matrices = [_cls() for _cls in [Matrix2x3] * matrices_count]
        self.color_transforms = [_cls() for _cls in [ColorTransform] * color_transforms_count]
    
    def save(self):
        super().save()

        self.write_unsigned_short(len(self.matrices))
        self.write_unsigned_short(len(self.color_transforms))
    
    @property
    def has_avaible(self):
        return len(self.matrices) < 65534 and len(self.color_transforms) < 65534
    
    @property
    def avaible_matrices(self):
        return 65534 - len(self.matrices)
    
    @property
    def avaible_color_transforms(self):
        return 65534 - len(self.color_transforms)
