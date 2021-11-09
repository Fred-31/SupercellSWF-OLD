from .tag import Tag

from math import sqrt, radians, degrees, atan2, sin, cos



class Matrix2x3(Tag):
    def __init__(self, tag: int = 8) -> None:
        super().__init__(tag)

        self.matrix: list = [
            [1.0, 0.0, 0.0], # x
            [0.0, 1.0, 0.0]  # y
        ]
    
    def translate(self, position: list):
        x, y = position

        self.matrix[0][2] += self.matrix[0][0] * x + self.matrix[1][0] * y
        self.matrix[1][2] += self.matrix[0][1] * x + self.matrix[1][1] * y

    def scale(self, scaling: list):
        x, y = scaling

        self.matrix[0][0] *= x
        self.matrix[0][1] *= x

        self.matrix[1][0] *= y
        self.matrix[1][1] *= y

    def rotate(self, angle: float):
        angle = radians(-angle)

        c = cos(angle)
        s = sin(angle)

        v1_1 = self.matrix[0][0] * c + self.matrix[1][0] * s
        v1_2 = self.matrix[0][1] * c + self.matrix[1][1] * s

        v2_1 = self.matrix[0][0] * -s + self.matrix[1][0] * c
        v2_2 = self.matrix[0][1] * s + self.matrix[1][1] * c

        self.matrix[0][0] = v1_1
        self.matrix[0][1] = v1_2
        self.matrix[1][0] = v2_1
        self.matrix[1][1] = v2_2

    def get_translation(self):
        return self.matrix[0][2], self.matrix[1][2]

    def get_scale(self):
        x = sqrt(self.matrix[0][0] ** 2 + self.matrix[1][0] ** 2)
        y = sqrt(self.matrix[0][1] ** 2 + self.matrix[1][1] ** 2)

        return x, y

    def get_rotation(self):
        return degrees(atan2(self.matrix[1][0], self.matrix[0][0]))
    
    def load(self, data: bytes):
        super().load(data)

        self.matrix = self.read_matrix2x3()
    
    def save(self):
        super().save()

        self.write_matrix2x3(self.matrix)
