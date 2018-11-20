from .scpiparser import SCPIParser

class SCPIDevice():
    def __init__(self):
        print("SCPIDevice")
        self._parser = SCPIParser()
