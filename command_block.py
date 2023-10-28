
"""
Represents a sequence of commands to be run on a given client, along with a callback to be run before running the command, and a callback to be run once the command has run.
"""
class CommandBlock:
    """
    username: The username of the client to run the commands on. If no client is open for that username when this command block is run, a new client will be opened.
    pre: A callback that will be run before the commands are executed on the client. It takes no arguments.
    cmds: A list of commands to be run on the client.
    post: A callback that will be run after the commands are executed on the client. It will run once all commands in the test case are executed. It takes two arguments: the outputs of the commands in this block, and the context of the test case. The context is simply a dictionary that can be used to store any data that needs to be shared from one command block to the next.
    """
    def __init__(self, username=None, pre=None, cmds=[], post=None):
        assert (username == None or isinstance(
            username, str)), "username must be a string"
        self.username = username
        self.hasRun = False
        self.cmds = cmds
        self.outputs = []
        self.post = post
        self.pre = pre

    def __repr__(self):
        return f'CommandBlock(username={self.username}, cmds={self.cmds}, outputs={self.outputs})'

