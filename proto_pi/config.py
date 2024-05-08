import json


class Config:
    def __init__(self, cols: int, rows: int, reverse_ids: bool,
                 brightness: int, skip_devices: list[int], running: bool,
                 preload_animation_path: str):
        self.cols = cols
        self.rows = rows
        self.reverse_ids = reverse_ids
        self.brightness = brightness
        self.skip_devices = skip_devices
        self.running = running
        self.preload_animation_path = preload_animation_path

    @staticmethod
    def from_json(json_data: dict) -> 'Config':
        return Config(
            json_data.get('cols', 0),
            json_data.get('rows', 0),
            json_data.get('reverse', False),
            json_data.get('brightness', 7),
            json_data.get('skip_devices', []),
            json_data.get('running', False),
            json_data.get('preload_animation_path', '')
        )

    def to_json(self) -> dict:
        return {
            'cols': self.cols,
            'rows': self.rows,
            'reverse': self.reverse_ids,
            'brightness': self.brightness,
            'skip_devices': self.skip_devices,
            'running': self.running,
            'preload_animation_path': self.preload_animation_path
        }

    def save(self, path: str):
        with open(path, 'w') as config_file:
            # noinspection PyTypeChecker
            json.dump(self.to_json(), config_file)

    @staticmethod
    def load(path: str) -> 'Config':
        with open(path) as config_file:
            # noinspection PyTypeChecker
            return Config.from_json(json.load(config_file))
