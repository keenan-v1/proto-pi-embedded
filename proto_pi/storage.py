import sys
import os


class File:
    def __init__(self, file_name: str):
        self.file_name = file_name
        

class AnimationConfiguration(File):
    def __init__(self, name: str):
        super().__init__(name)


class ImageData(File):
    def __init__(self, name: str):
        super().__init__(name)
