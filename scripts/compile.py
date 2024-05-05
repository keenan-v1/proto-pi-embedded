#!/usr/bin/env python3
import glob
import os
import argparse
import json
from typing import Any
import yaml
import base64
from PIL import Image


class Region:
    def __init__(self) -> None:
        self.name: str = ''
        self.x: int = 0
        self.y: int = 0
        self.mirror: bool = False
        self.flip: bool = False
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'mirror': self.mirror,
            'flip': self.flip
        }


class Frame:
    def __init__(self, frame_id: int = 0) -> None:
        self.id: int = frame_id
        self.width: int = 0
        self.height: int = 0
        self.data: bytearray = bytearray()
    
    def set_frame(self, image: Image.Image) -> None:        
        self.width, self.height = image.size
        current_byte = 0
        for i in range(0, self.width * self.height):
            pixel = image.getpixel((i % self.width, i // self.width))
            if pixel == (0, 0, 0, 255):
                current_byte |= 1 << (i % 8)
            if i % 8 == 7:
                self.data.append(current_byte)
                current_byte = 0
        
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'data': base64.b64encode(self.data).decode('utf-8')
        }


class Animation:
    def __init__(self) -> None:
        self.name: str = ''
        self.regions: list[Region] = []
        self.frames: list[Frame] = []
        self.duration: float = 0
        self.hold: float = 0
        self.loop: bool = False
        self.reverse: bool = False
        
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'width': self.frames[0].width,
            'height': self.frames[0].height,
            'regions': [region.to_dict() for region in self.regions],
            'frames': [frame.to_dict() for frame in self.frames],
            'duration': self.duration,
            'hold': self.hold,
            'loop': self.loop,
            'reverse': self.reverse
        }


class ConfigValue:
    def __init__(self, name: str, value: Any) -> None:
        self.name: str = name
        self.value: Any = value
    
    def as_int(self) -> int:
        if not isinstance(self.value, int):
            raise Exception(f"Value of '{self.name}' must be an integer")
        return self.value
    
    def as_float(self) -> float:
        if not isinstance(self.value, float) and not isinstance(self.value, int):
            raise Exception(f"Value of '{self.name}' must be a float")
        return self.value
    
    def as_str(self) -> str:
        if not isinstance(self.value, str):
            raise Exception(f"Value of '{self.name}' must be a string")
        return self.value
    
    def as_list(self) -> list:
        if not isinstance(self.value, list):
            raise Exception(f"Value of '{self.name}' must be a list")
        return self.value
    
    def as_dict(self) -> dict:
        if not isinstance(self.value, dict):
            raise Exception(f"Value of '{self.name}' must be a dictionary")
        return self.value

    def as_bool(self) -> bool:
        if not isinstance(self.value, bool):
            raise Exception(f"Value of '{self.name}' must be true or false")
        return self.value


class ConfigParser:
    def __init__(self, config_file: str) -> None:
        with open(config_file) as f:
            self.config: dict[str, Any | dict] = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None, config: dict | None = None) -> ConfigValue:
        key_parts = key.split('.')
        node = self.config if config is None else config
        for part in key_parts:
            if part not in node:
                if default is None:
                    raise Exception(f"Key '{key}' not found in config file")
                else:
                    return ConfigValue(key, default)
            node = node[part]
        return ConfigValue(key, node)
    
    def populate(self, obj: Any, ignored_fields: list[str] | None = None, config: dict | None = None) -> None:
        if ignored_fields is None:
            ignored_fields = []
        node = self.config if config is None else config
        for key, value in node.items():
            if key in ignored_fields:
                continue
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                raise Exception(f"Attribute '{key}' not found in object '{obj}'")


class AnimationConfig(ConfigParser):
    def __init__(self, config_file: str) -> None:
        super().__init__(config_file)
        self.frames: list[Image.Image] = []
        for frame in self.get('frames').as_list():
            self.frames.append(Image.open(frame))

    def populate(self, obj: Animation, ignored_fields: list[str] | None = None, config: dict | None = None) -> None:
        super().populate(obj, ['frames', 'regions'])
        obj.frames = [Frame(i) for i in range(len(self.frames))]
        for i, frame in enumerate(self.frames):
            obj.frames[i].set_frame(frame)
        for region in self.get('regions').as_list():
            r = Region()
            super().populate(r, config=region)
            obj.regions.append(r)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile Animations")
    parser.add_argument("-i", "--input", required=True, help="Input folder")
    parser.add_argument("-o", "--output", required=True, help="Output folder")
    return parser.parse_args()


def get_animations(folder_name: str) -> list[Animation]:
    animations: list[Animation] = []
    files = glob.glob(os.path.join(folder_name, "*.yaml"))
    for file in files:
        animation_config = AnimationConfig(file)
        animation = Animation()
        animation_config.populate(animation)
        animations.append(animation)

    return animations


def main():
    args = parse_args()
    animations = get_animations(args.input)
    for animation in animations:
        output_path = os.path.join(args.output, f"{animation.name}.json")
        with open(output_path, 'w') as f:
            json.dump(animation.to_dict(), f)


if __name__ == '__main__':
    main()
