class Command:
    def __init__(self, command: str) -> None:
        self._command: str = command

    @property
    def command(self) -> str:
        return self._command

    def execute(self, arg: any = None) -> None:
        pass
