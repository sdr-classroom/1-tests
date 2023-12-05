import subprocess
import time
from log import log
import os

"""
Represents a server
"""
class Server:
    def __init__(self, testcase_name, port, ports, debug, cwd):
        self.name = testcase_name + "_" + str(port)
        self.port = port
        self.ports = ports
        self.debug = debug
        self.proc = None
        self.cwd = cwd

    def start(self, graph):
        config_filename = f"config_{self.name}.json"
        config_fullname = os.path.join(self.cwd, config_filename)
        write_config_file(config_fullname, graph, self.port, self.ports, self.debug)
        
        # use lsof to find the process id of the server listening on the port, then kill it.
        os.system(f'lsof -t -i:{self.port} | xargs kill')
        log(f"Killed anything listening on {self.port}")
        # srv_cmd = f"go run -race {server_dir} {config_filename}".split()
        srv_cmd = f"{server_full_executable(self.cwd)} {config_filename}".split()
        srv_proc = subprocess.Popen(srv_cmd, cwd=self.cwd)
        log("Server started, waiting...")
        time.sleep(1)
        return srv_proc
    
    def stop(self):
        if self.proc:
            self.proc.kill()
            log("Server stopped")
            self.proc = None
        else:
            log("Server not running")
    
def server_full_executable(cwd):
    return os.path.join(cwd, "server")

def write_config_file(filename, graph, port, ports, debug):
    with open(filename, 'w') as f:
        debugStr = 'true' if debug else 'false'
        f.write(f'{{"debug": {debugStr}, "port": {port}, "users": [')
        users = []
        for username in graph.keys():
            user = f'{{"username": "{username}", "debts": ['
            debts = []
            for other_user, amount in graph[username].items():
                debts.append(
                    f'{{"username": "{other_user}", "amount": {amount}}}')
            user += ', '.join(debts) + ']}'
            users.append(user)
        f.write(', '.join(users) + '], ')
        f.write('"servers": [' + ', '.join([f'"127.0.0.1:{p}"' for p in ports]) + ']}\n')
