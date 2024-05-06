import json
import os
import random
from _thread import allocate_lock

from proto_pi import Command
from proto_pi.matrix import Matrix
from proto_pi.rendering import Frame
import time


class Region:
    def __init__(self, name: str, x: int, y: int, mirror: bool = False, flip: bool = False) -> None:
        self._name: str = name
        self._x: int = x
        self._y: int = y
        self._mirror: bool = mirror
        self._flip: bool = flip
        self._frames: list[Frame] = []

    def add_frame(self, frame: Frame) -> None:
        copy: Frame = frame.as_copy()
        if self.mirror:
            copy.mirror()
        if self.flip:
            copy.flip()
        self._frames.append(copy)

    def get_frame(self, frame_id: int) -> Frame:
        return self._frames[frame_id]

    @property
    def flip(self) -> bool:
        return self._flip

    @property
    def name(self) -> str:
        return self._name

    @property
    def mirror(self) -> bool:
        return self._mirror

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def __str__(self) -> str:
        return f"({self.name}: {self.x},{self.y} {'(M)' if self.mirror else ''}"

    @staticmethod
    def from_json(data: dict) -> 'Region':
        return Region(
            data.get("name", "default"),
            data.get("x", 0),
            data.get("y", 0),
            data.get("mirror", False),
            data.get("flip", False),
        )


class Animation:
    def __init__(self,
                 name: str,
                 regions: list[Region],
                 frames: list[Frame],
                 duration: float,
                 hold: float,
                 random_hold: dict[str, float],
                 loop: bool,
                 reverse: bool
                 ) -> None:
        self._name: str = name
        self._regions: list[Region] = regions
        self._frames: list[Frame] = frames
        self._loop: bool = loop
        self._reverse: bool = reverse
        self._is_playing: bool = False
        self._is_reversing: bool = False
        self._frame_id: int = 0
        self._duration_millis: int = int(duration * 1000)
        self._hold_millis: int = int(hold * 1000)
        self._random_hold: dict[str, float] = random_hold
        self._start_millis: int = 0
        for region in self.regions:
            for frame in self.frames:
                region.add_frame(frame)

    def __str__(self):
        return \
            f"Animation({self.frames}, {self.duration}, {self.hold}, {self.loop}, {self.reverse})"

    @staticmethod
    def from_json(data: dict) -> 'Animation':
        width: int = data.get("width", 8)
        height: int = data.get("height", 8)
        return Animation(
            data.get("name", "default"),
            [Region.from_json(region) for region in data.get("regions", [])],
            [Frame.from_json(frame, width, height) for frame in data.get("frames", [])],
            data.get("duration", 0),
            data.get("hold", 0),
            data.get("randomHold", {'start': 0, 'end': 0}),
            data.get("loop", False),
            data.get("reverse", False)
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def reverse(self) -> bool:
        return self._reverse

    @property
    def loop(self) -> bool:
        return self._loop

    @property
    def regions(self) -> list[Region]:
        return self._regions

    @property
    def frames(self) -> list[Frame]:
        return self._frames

    @property
    def duration(self) -> float:
        return self._duration_millis / 1000

    @property
    def hold(self) -> int:
        if self._hold_millis > 0:
            return self._hold_millis
        start: float = self._random_hold.get("start", 0)
        end: float = self._random_hold.get("end", 0)
        if end != 0 and start < end:
            return int(random.uniform(start, end) * 1000)
        return 0

    @property
    def playing(self) -> bool:
        return self._is_playing

    @property
    def _frame_millis(self) -> int:
        frame_count = len(self.frames)
        if self.reverse:
            frame_count = frame_count * 2 - 1
        return self._duration_millis // frame_count

    @property
    def _next_millis(self) -> int:
        if not self._is_playing:
            return 0
        is_last_frame = self._frame_id == len(self.frames) - 1 if not self._is_reversing else self._frame_id == 0
        if self.hold > 0 and is_last_frame:
            return self.hold
        frame_id = self._frame_id + 1
        next_millis = frame_id * self._frame_millis if not self._is_reversing \
            else (len(self.frames) * 2 - frame_id) * self._frame_millis
        if self.loop and self._is_reversing and is_last_frame:
            next_millis -= self._frame_millis
        return next_millis

    @property
    def _current_millis(self) -> int:
        return time.time_ns() // 1_000_000 - self._start_millis

    @property
    def current_frame(self) -> Frame:
        return self.frames[self._frame_id]

    @property
    def current_frame_id(self) -> int:
        return self._frame_id

    @property
    def should_advance(self) -> bool:
        return self._current_millis >= self._next_millis > 0 and self._is_playing

    def play(self):
        self._is_playing = True
        self._start_millis = time.time_ns() // 1_000_000
        self._frame_id = 0
        self._is_reversing = False

    def pause(self):
        self._is_playing = False

    def resume(self):
        self._is_playing = True
        self._start_millis = time.time_ns() // 1_000_000 - self._current_millis

    def stop(self):
        self._is_playing = False
        self._frame_id = 0
        self._is_reversing = False
        self._start_millis = 0

    def advance_frame(self) -> None:
        if not self.should_advance:
            return

        if self._frame_id == len(self.frames) - 1 and self.reverse and not self._is_reversing:
            self._is_reversing = True
            self._frame_id = len(self.frames) - 2
            return

        is_last_frame = self._frame_id == len(self.frames) - 1 if not self._is_reversing else self._frame_id == 0
        if is_last_frame and not self.loop:
            self.stop()
            return
        elif is_last_frame and self.loop:
            if self._is_reversing:
                self._is_reversing = False
            self._frame_id = 0
            self._start_millis = time.time_ns() // 1_000_000
            return
        else:
            self._frame_id += 1 if not self._is_reversing else -1


class AnimationCommand(Command):
    def __init__(self, name: str):
        super().__init__(name)

    @staticmethod
    def _check_arg(arg: any) -> 'AnimationController':
        if arg is None or not isinstance(arg, AnimationController):
            raise ValueError("Invalid argument, expected AnimationController")
        return arg


class TestCommand(AnimationCommand):
    def __init__(self, name: str):
        super().__init__(name)

    def execute(self, arg=None) -> None:
        controller: AnimationController = self._check_arg(arg)
        controller.clear_animations()
        controller.clear_display()
        controller.test_display()
        controller.tick()


class PlayCommand(AnimationCommand):
    def __init__(self, data: dict):
        super().__init__("play")
        self._animation_name: str = data.get("animation")
        if not self._animation_name:
            raise ValueError("Invalid data, missing 'animation'")

    def execute(self, arg=None) -> None:
        controller: AnimationController = self._check_arg(arg)
        animation = controller.animations.get(self._animation_name)
        if animation:
            animation.play()
        else:
            print(f"Animation '{self._animation_name}' not found")


class StopCommand(AnimationCommand):
    def __init__(self, data: dict):
        super().__init__("stop")
        self._animation_name: str = data.get("animation")
        if not self._animation_name:
            raise ValueError("Invalid data, missing 'animation'")

    def execute(self, arg=None) -> None:
        controller: AnimationController = self._check_arg(arg)
        animation = controller.animations.get(self._animation_name)
        if animation:
            animation.stop()
        else:
            print(f"Animation '{self._animation_name}' not found")


class PauseCommand(AnimationCommand):
    def __init__(self, data: dict):
        super().__init__("pause")
        self._animation_name: str = data.get("animation")
        if not self._animation_name:
            raise ValueError("Invalid data, missing 'animation'")

    def execute(self, arg=None) -> None:
        controller: AnimationController = self._check_arg(arg)
        animation = controller.animations.get(self._animation_name)
        if animation:
            animation.pause()
        else:
            print(f"Animation '{self._animation_name}' not found")


class ResumeCommand(AnimationCommand):
    def __init__(self, data: dict):
        super().__init__("resume")
        self._animation_name: str = data.get("animation")
        if not self._animation_name:
            raise ValueError("Invalid data, missing 'animation'")

    def execute(self, arg=None) -> None:
        controller: AnimationController = self._check_arg(arg)
        animation = controller.animations.get(self._animation_name)
        if animation:
            animation.resume()
        else:
            print(f"Animation '{self._animation_name}' not found")


class LoadCommand(AnimationCommand):
    def __init__(self, data: dict):
        super().__init__("load")
        self._animation: Animation = Animation.from_json(data.get("animation", {}))
        self._play_on_load: bool = data.get("play", False)

    def execute(self, arg=None) -> None:
        controller: AnimationController = self._check_arg(arg)
        controller.add_animation(self._animation)
        if self._play_on_load:
            self._animation.play()
        print(f"Loaded animation '{self._animation.name}'")


class ClearCommand(AnimationCommand):
    def __init__(self, data: dict):
        super().__init__("clear")
        self._target: str = data.get("target", "display")
        self._regions: list[dict[str, int]] = data.get("regions", [])

    def execute(self, arg=None) -> None:
        controller: AnimationController = self._check_arg(arg)
        if self._target == "display":
            controller.clear_display()
        elif self._target == "region":
            if len(self._regions) == 0:
                print("No regions to clear")
                return
            for region in self._regions:
                x: int = region.get("x", 0)
                y: int = region.get("y", 0)
                w: int = region.get("w", 0)
                h: int = region.get("h", 0)
                controller.clear_region(x, y, w, h)
        elif self._target == "animations":
            controller.clear_animations()
        else:
            print(f"Invalid target '{self._target}'")


class AnimationCommandFactory:
    @staticmethod
    def create(data: dict) -> AnimationCommand:
        command: str = data.get("command")
        payload: dict = data.get("payload", {})
        if not command:
            raise ValueError("Invalid data, missing 'command'")
        if command == "test":
            return TestCommand("test")
        if command == "play":
            return PlayCommand(payload)
        if command == "stop":
            return StopCommand(payload)
        if command == "pause":
            return PauseCommand(payload)
        if command == "resume":
            return ResumeCommand(payload)
        if command == "load":
            return LoadCommand(payload)
        if command == "clear":
            return ClearCommand(payload)
        raise ValueError(f"Invalid command '{command}'")


class AnimationController:
    def __init__(self, display: Matrix):
        self.is_loading: bool = False
        self._animations_lock = allocate_lock()
        self._display: Matrix = display
        self._animations: dict[str, Animation] = {}

    @property
    def animations(self) -> dict[str, Animation]:
        with self._animations_lock:
            return self._animations

    def add_animation(self, animation: Animation):
        with self._animations_lock:
            self._animations[animation.name] = animation

    def load_baked(self, folder_name: str):
        for file_name in os.listdir(folder_name):
            if file_name.endswith(".json"):
                with open(f"{folder_name}/{file_name}", "r") as f:
                    animation: Animation = Animation.from_json(json.load(f))
                    self.add_animation(animation)
                    animation.play()

    def clear_animations(self):
        with self._animations_lock:
            self._animations.clear()

    def clear_display(self):
        self._display.zero()

    def test_display(self):
        self._display.fill(1)

    def clear_region(self, x: int, y: int, w: int, h: int):
        if w == 0:
            w = self._display.width
        if h == 0:
            h = self._display.height
        self._display.fill_rect(x, y, w, h, 0)

    def tick(self):
        with self._animations_lock:
            for animation in set(self._animations.values()):
                if animation.playing:
                    for region in animation.regions:
                        self._display.blit(region.get_frame(animation.current_frame_id), region.x, region.y)
                    animation.advance_frame()

    def process_command(self, data: dict):
        command: AnimationCommand = AnimationCommandFactory.create(data)
        command.execute(self)
        print(f"Processed command '{command.command}'")
