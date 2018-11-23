from .command import SCPICommand

class SCPIDevice():
    def __init__(self, name=""):
        self._command_list = SCPICommand
