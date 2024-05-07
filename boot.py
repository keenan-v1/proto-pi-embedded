import json

import select
import sys
import time

from proto_pi.matrix import Matrix
from machine import Pin, SPI
from proto_pi.animation import AnimationController
from _thread import start_new_thread

with open('config.json') as config_file:
    # noinspection PyTypeChecker
    device_config: dict = json.load(config_file)

spi = SPI(1, sck=Pin(48), mosi=Pin(38))
cs = Pin(6, Pin.OUT)
cols: int = device_config.get('cols', 0)
rows: int = device_config.get('rows', 0)
reverse_ids: bool = device_config.get('reverse', False)
brightness: int = device_config.get('brightness', 7)
skip_devices: list[int] = device_config.get('skip_devices', [])
display = Matrix(spi, cs, cols, rows, reverse_ids=reverse_ids, skip_devices=skip_devices)
display.brightness(brightness)
display.zero()
display.show(force=True)


def run(animation_controller: AnimationController):
    animation_controller.is_loading = True
    animation_controller.process_command(json.loads(sys.stdin.readline()))
    animation_controller.is_loading = False


def stop():
    update_config("running", False)


def start():
    update_config("running", True)


def update_config(key: str, value):
    device_config[key] = value
    with open('config.json', 'w') as config_file:
        json.dump(device_config, config_file)


def main():
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    animation_controller = AnimationController(display)
    animation_controller.load_baked("/data")

    while device_config["running"]:
        if poll.poll(0) and not animation_controller.is_loading:
            start_new_thread(run, (animation_controller,))
        animation_controller.tick()
        display.show()
        time.sleep(1/45)


if __name__ == "__main__":
    main()
