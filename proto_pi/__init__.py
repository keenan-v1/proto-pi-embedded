import json
import time
from _thread import start_new_thread

from machine import SPI, Pin

from proto_pi.animation import AnimationController
from proto_pi.config import Config
from proto_pi.fonts import Fonts, String
from proto_pi.matrix import Matrix


class Device:
    def __init__(self, config_file: str) -> None:
        self._config: Config = Config.load(config_file)
        spi = SPI(1, sck=Pin(48), mosi=Pin(38))
        cs = Pin(6, Pin.OUT)
        self._matrix: Matrix = Matrix(spi, cs, self._config.cols, self._config.rows,
                                      reverse_ids=self._config.reverse_ids, skip_devices=self._config.skip_devices)
        self._matrix.brightness(self._config.brightness)
        self._matrix.zero()
        self._matrix.show(force=True)
        self._animation_controller: AnimationController = AnimationController(self._matrix)
        if self._config.preload_animation_path:
            self._animation_controller.load_baked(self._config.preload_animation_path)

    def show_device_ids(self) -> None:
        self.stop()
        self.clear()

        id_range = range(self._matrix.device_count) if not self._config.reverse_ids else range(self._matrix.device_count - 1, -1, -1)

        for device_id in id_range:
            if device_id in self._config.skip_devices:
                continue
            d_id = device_id if not self._config.reverse_ids else self._matrix.device_count - device_id - 1
            row: int = d_id // self._config.cols
            col: int = d_id % self._config.cols
            device_str: String = String(Fonts.Compact, f"{device_id:02d}")
            self._matrix.text(device_str, col * 8, row * 8, 1)
        self._matrix.show(force=True)

    def debug(self) -> None:
        self._matrix.debug()

    def stop(self) -> None:
        self._config.running = False

    def clear(self) -> None:
        self._matrix.zero()
        self._matrix.show(force=True)

    def start(self) -> None:
        self._config.running = True
        start_new_thread(self.run, ())

    def command(self, json_str: str) -> None:
        self._animation_controller.process_command(json.loads(json_str))

    def run(self):
        while self._config.running:
            self._animation_controller.tick()
            self._matrix.show()
            time.sleep(1/45)
