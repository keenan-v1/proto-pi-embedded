import json
import select
import sys
import time

from proto_pi.matrix import Matrix
from machine import Pin, SPI
from proto_pi.animation import AnimationController
from _thread import start_new_thread

spi = SPI(1, sck=Pin(48), mosi=Pin(38))
cs = Pin(6, Pin.OUT)
display = Matrix(spi, cs, 3, 3, reverse_ids=True)
display.brightness(7)
display.zero()
display.show(force=True)


def run(animation_controller: AnimationController):
    animation_controller.is_loading = True
    animation_controller.process_command(json.loads(sys.stdin.readline()))
    animation_controller.is_loading = False


def main():
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    animation_controller = AnimationController(display)
    animation_controller.load_baked("/data")

    while True:
        if poll.poll(0) and not animation_controller.is_loading:
            start_new_thread(run, (animation_controller,))
        animation_controller.tick()
        display.show()
        time.sleep(1/30)


if __name__ == "__main__":
    main()
