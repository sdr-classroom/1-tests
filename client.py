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
        self.exited = True

    def join(self):
        # warn(f"Joining client {self.username}.")
        
        self.exited = False
        
        if self.subprocess:
            fail("Client already joined")
        
        global project_fullname
        cmd = f"{client_full_executable(self.cwd)} {self.username} 127.0.0.1:{self.port}"
        # f"go run -race {client_dir} {username} localhost:3333",
        self.subprocess = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            shell=True,
                            cwd=self.cwd)
        os.set_blocking(self.subprocess.stdout.fileno(), False)
        
        log(f'Client {self.username} joined, waiting...')
        # time.sleep(0.7)

    def exit(self):
        # warn(f"Exiting client {self.username}.")

        if self.exited:
            warn(f"Client {self.username} already exited when trying to exit it.")
            return
        self.exited = True
        if not self.subprocess:
            fail("Client not joined when trying to exit")
        subprocess = self.subprocess
        subprocess.stdin.write('exit\n'.encode())
        try:
            subprocess.stdin.flush()
        except BrokenPipeError:
            warn(f"Broken pipe error occurred when trying to flush the stdin of client {self.username} right before exiting it.")
        log(f'client {self.username} exited, killing it...')
        # time.sleep(0.1 * sleep_speedup)
        subprocess.kill()
        # time.sleep(0.1 * sleep_speedup)

def client_full_executable(cwd):
    return os.path.join(cwd, "client")
