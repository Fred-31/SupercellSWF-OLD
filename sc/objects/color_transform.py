from .tag import Tag



class ColorTransform(Tag):
    def __init__(self, tag: int = 9) -> None:
        super().__init__(tag)

        self.addition: list = [0, 0, 0, 255]
        self.multiplier: list = [0, 0, 0]
    
    def load(self, data: bytes):
        super().load(data)
        
        self.addition = self.read_bgra()
        self.multiplier = self.read_bgr()
    
    def save(self):
        super().save()

        self.write_bgra(self.addition)
        self.write_bgr(self.multiplier)
