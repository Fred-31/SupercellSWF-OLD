from .tag import Tag



class MovieClipModifiers(Tag):
    def __init__(self, tag: int = 37) -> None:
        super().__init__(tag)
    
    def load(self, data: bytes, swf):
        super().load(data)

        modifiers_count = self.read_unsigned_short()
        swf._movie_clip_modifiers = [_cls() for _cls in [MovieClipModifier] * modifiers_count]
    
    def save(self, swf):
        super().save()

        self.write_unsigned_short(len(swf.movie_clip_modifiers))


class MovieClipModifier(Tag):
    def __init__(self, tag: int = 38) -> None:
        super().__init__(tag)

        self.export_id: int = 0
    
    def load(self, data: bytes):
        super().load(data)

        self.export_id = self.read_unsigned_short()
    
    def save(self):
        super().save()

        self.write_unsigned_short(self.export_id)
