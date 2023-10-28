"""
Represents a client, hence its username together with the subprocess running the actual client executable, to which inputs are sent and from which outputs are read.
"""
class Client:
    def __init__(self, username, subprocess):
        self.username = username
        self.subprocess = subprocess
