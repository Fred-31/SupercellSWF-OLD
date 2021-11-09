from sc.utils import Reader, Writer



class Tag(Reader, Writer):
    def __init__(self, tag: int = 0) -> None:
        self.tag = tag
    
    def load(self, data: bytes):
        Reader.__init__(self, data)
    
    def save(self):
        Writer.__init__(self)
