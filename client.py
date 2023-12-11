from log import fail, log, warn
import subprocess
import os
import time

"""
Represents a client, hence its username together with the subprocess running the actual client executable, to which inputs are sent and from which outputs are read.
"""
class Client:
    def __init__(self, username, port, cwd):
        self.username = username
        self.subprocess = None
        self.port = port
        self.cwd = cwd

    def join(self):
        if self.subprocess:
            fail("Client already joined")
        
        global project_fullname
        cmd = f"{client_full_executable(self.cwd)} {self.username} localhost:3333"
        # f"go run -race {client_dir} {username} localhost:3333",
        self.subprocess = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            shell=True,
                            cwd=self.cwd)
        log(f'Client {self.username} joined, waiting...')
        # time.sleep(0.7)

    def exit(self):
        if not self.subprocess:
            fail("Client not joined when trying to exit")
        subprocess = self.subprocess
        subprocess.stdin.write('exit\n'.encode())
        subprocess.stdin.flush()
        log(f'client {self.username} exited, killing it...')
        # time.sleep(0.1 * sleep_speedup)
        subprocess.kill()
        # time.sleep(0.1 * sleep_speedup)

def client_full_executable(cwd):
    return os.path.join(cwd, "client")
