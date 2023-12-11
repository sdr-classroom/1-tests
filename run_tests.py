import signal
import sys
import math
import os
import random
import subprocess
import threading
import time
from helpers import get_total_per_user
from enum import Enum

from log import log, allow_debug_logs, warn, fail, set_log_file
from outcome import OutcomeLogger
from test_cases_lab1 import *
from test_cases_lab2 import *
from client import Client, client_full_executable
from server import Server, server_full_executable

sleep_speedup = 1

debug = True
if (debug):
    allow_debug_logs()

# Get project path from command line arguments
project_fullname = sys.argv[1]
project_fullname = os.path.abspath(project_fullname)

project_name = os.path.basename(project_fullname)

working_dir = None


def get_working_dir(project_abs_name=None):
    global working_dir
    if (working_dir != None):
        return working_dir
    elif (project_abs_name == None):
        sys.exit("No working directory nor project name provided")

    working_dir = os.path.join(project_abs_name, "test_outputs")
    if (not os.path.exists(working_dir)):
        os.mkdir(working_dir)
    return working_dir


def compile_server():
    print("Compiling server...")
    global project_fullname
    compile_script = os.path.join(project_fullname, "compile_server.sh")
    print("Script path : ", compile_script)
    os.system(
        f'cd {project_fullname}; {compile_script} {server_full_executable(get_working_dir())}')
    print("Server compiled")


def compile_client():
    print("Compiling client...")
    global project_fullname
    compile_script = os.path.join(project_fullname, "compile_client.sh")
    os.system(
        f'cd {project_fullname}; {compile_script} {client_full_executable(get_working_dir())}')


# def run_command_block(clients, cmd_blocks, block):
#     cmd_blocks.append(block)
#     if (block.pre):
#         block.pre()
#     if (block.username == None):
#         return
#     client = clients[block.username]
#     subprocess = client.subprocess
#     for cmd in block.cmds:
#         subprocess.stdin.write((cmd + "\n").encode())
#         subprocess.stdin.flush()


# def join_client(username):
#     global project_fullname
#     cmd = f"{get_client_fullname()} {username} localhost:3333"
#     # f"go run -race {client_dir} {username} localhost:3333",
#     p = subprocess.Popen(cmd,
#                          stdin=subprocess.PIPE,
#                          stdout=subprocess.PIPE,
#                          shell=True,
#                          cwd=get_working_dir())
#     log(f'Client {username} joined, waiting...')
#     time.sleep(0.7 * sleep_speedup)
#     return Client(username, p)


# def exit_client(client):
#     subprocess = client.subprocess
#     subprocess.stdin.write('exit\n'.encode())
#     subprocess.stdin.write('exit\n'.encode())
#     subprocess.stdin.flush()
#     log(f'client {client.username} exited, killing it...')
#     # time.sleep(0.1 * sleep_speedup)
#     subprocess.kill()
#     # time.sleep(0.1 * sleep_speedup)


# def parse_outputs(cmd_blocks, clients, context):
#     log("Parsing outputs...")
#     per_client_outputs = {}
#     per_client_lines = {}

#     # parse lines for each client
#     for client in clients.values():
#         log(f'Parsing outputs for client {client.username}...')
#         lines = client.subprocess.stdout.readlines()
#         log(f"Got lines for client {client.username}")
#         lines = [line.decode().strip() for line in lines]
#         per_client_lines[client.username] = lines
#         cmd_outputs = '\n'.join(lines).split('>')
#         # filter empty strings
#         cmd_outputs = list(
#             filter(lambda x: x != '', [x.strip() for x in cmd_outputs]))
#         per_client_outputs[client.username] = cmd_outputs

#     # assign outputs to blocks
#     for block in cmd_blocks:
#         outputs = []
#         if block.username != None:
#             outputs = per_client_outputs[block.username]
#         assert (len(block.cmds) <= len(outputs)
#                 ), "Some command did not produce an output"
#         for _ in block.cmds:
#             output = outputs[0]
#             outputs = outputs[1:]
#             block.outputs.append(output)
#         if block.post:
#             block.post(block.outputs, context)
#         # shift the remaining outputs to the next block
#         if (block.username != None):
#             per_client_outputs[block.username] = outputs


# def start_server(config_filename, port):
#     # use lsof to find the process id of the server listening on the port, then kill it.
#     os.system(f'lsof -t -i:{port} | xargs kill')
#     log(f"Killed anything listening on {port}")
#     # srv_cmd = f"go run -race {server_dir} {config_filename}".split()
#     srv_cmd = f"{get_server_fullname()} {config_filename}".split()
#     srv_proc = subprocess.Popen(srv_cmd, cwd=get_working_dir())
#     log("Server started, waiting...")
#     time.sleep(1 * sleep_speedup)
#     return srv_proc


# def stop_server(srv_proc):
#     log("Stopping server...")
#     srv_proc.kill()
#     log("Server stopped")
#     # time.sleep(0.1 * sleep_speedup)

class TestCaseState(Enum):
    INIT = 1
    RUNNING = 2
    MANUAL_GRADING = 3
    SUCCESSFUL = 4
    FAILED = 5


class TestCaseInterface:
    def __init__(self, name):
        global debug
        
        self.name = name
        self.context = None
        self.graph = {}
        self.servers = {}
        self.command_blocks = []
        self.connected_clients = {}
        self.all_clients = {}
        self.desc = None
        self.should_skip_output_parsing = False
        # Create path for the test case
        self.test_case_dir = os.path.join(get_working_dir(), name)
        if not debug:
            if (not os.path.exists(self.test_case_dir)):
                os.mkdir(self.test_case_dir)
            if (not debug):
                set_log_file(os.path.join(self.test_case_dir, "test_logs.txt"))
        # self.state = TestCaseState.INIT

    def check_init_complete(self):
        if (self.context == None):
            fail("Context not initialized. Call initContext() first.")
        if (self.graph == {}):
            fail("Graph not initialized. Call build_graph() first.")
        if (self.servers == {}):
            fail("Servers not initialized. Call start_servers() first.")
        return True

    def init_context(self):
        expected_total_debts = get_total_per_user(self.graph)
        self.context = {
            "expected_totals": expected_total_debts,
            "manual_outputs": []
        }

    def define_servers(self, ports):
        self.servers = {}
        for port in ports:
            if (port in self.servers):
                fail(f"Server already started on port {port}")
            self.servers[port] = Server(
                self.name, port, ports, debug, get_working_dir())

    def start_all_servers(self):
        wait_block(1).pre()
        for server in self.servers.values():
            port = server.port
            os.system(f'lsof -t -i:{port} | xargs kill')
            log(f"Killed anything listening on {port}")
        for server in self.servers.values():
            server.start(self.graph)

    def start_server(self, port):
        if (not port in self.servers):
            fail(f"No server defined for port {port}")
        self.servers[port].start(self.graph)

    def stop_server(self, port):
        if (port not in self.servers):
            fail(f"No server running on port {port}; just returning.")
        self.servers[port].stop()

    def stop_all_servers(self):
        for port in self.servers.keys():
            self.stop_server(port)

    def build_graph(self, matrix):
        n = len(matrix)
        self.graph = {}
        for i in range(n):
            ui = "user" + str(i)
            self.graph[ui] = {}
            assert len(matrix[i]) == n, "Matrix must be square"
            for j in range(n):
                uj = "user" + str(j)
                if (matrix[i][j] != 0):
                    self.graph[ui][uj] = matrix[i][j]
        return self.graph

    def build_random_graph(self, user_count):
        matrix = [[0 for _ in range(user_count)] for _ in range(user_count)]
        owed_users = random.sample(range(user_count), user_count // 2)
        owing_users = [i for i in range(user_count) if i not in owed_users]

        for i in range(user_count):
            for j in range(user_count):
                has_debt = random.random() < 0.5
                if i == j or not has_debt:
                    continue
                if i in owing_users and j in owed_users:
                    matrix[i][j] = random.randint(0, 100)

        self.build_graph(matrix)

    def get_users(self):
        users = set()
        for username, other_users in self.graph.items():
            users.add(username)
            for other_user in other_users.keys():
                users.add(other_user)
        # Sorted alphabetically
        users = list(users)
        users.sort()
        return users

    def join_client(self, username, port):
        client = Client(username, port, get_working_dir())
        client.join()
        self.connected_clients[username] = client
        self.all_clients[username] = client
        return client

    def get_client(self, username):
        return self.all_clients[username]

    def exit_client(self, client):
        client.exit()
        self.connected_clients.pop(client.username)

    def exit_all_clients(self):
        clients_to_exit = list(self.connected_clients.values())
        for client in clients_to_exit:
            self.exit_client(client)
        self.connected_clients.clear()

    def describe(self, new_desc):
        self.desc = new_desc

    def set_should_skip_output_parsing(self, should_skip):
        self.should_skip_output_parsing = should_skip

    def run_command_block(self, block):
        # if (self.state != TestCaseState.RUNNING and self.state != TestCaseState.INIT):
        #     fail("Cannot run command block after test case has finished")
        # if (not self.check_init_complete()):
        #     fail("Cannot run command block before initialization")
        # self.state = TestCaseState.RUNNING

        if (not self.check_init_complete()):
            fail("Cannot run command block before initialization")

        self.command_blocks.append(block)
        if (block.pre):
            block.pre()
        if (block.username == None):
            return
        client = self.get_client(block.username)
        subprocess = client.subprocess
        if (subprocess == None):
            fail(
                f"Client {block.username} does not have a subprocess when trying to run a block")
        for cmd in block.cmds:
            subprocess.stdin.write((cmd + "\n").encode())
            subprocess.stdin.flush()

    def run_command_blocks(self, *blocks):
        for block in blocks:
            if (block == None):
                continue
            username = block.username
            if (username != None):
                if username not in self.connected_clients:
                    fail(
                        f"Client {username} not connected when trying to run a block")
            self.run_command_block(block)

    def parse_outputs(self):
        # if (self.state != TestCaseState.RUNNING):
        #     fail("Cannot parse outputs before running command blocks")

        if (self.should_skip_output_parsing):
            log("Skipping output parsing because of flag")
            return

        log("Parsing outputs...")
        per_client_outputs = {}
        per_client_lines = {}

        # parse lines for each client
        for client in self.all_clients.values():
            log(f'Parsing outputs for client {client.username}...')
            lines = client.subprocess.stdout.readlines()
            log(f"Got lines for client {client.username}")
            lines = [line.decode().strip() for line in lines]
            per_client_lines[client.username] = lines
            cmd_outputs = '\n'.join(lines).split('>')
            # filter empty strings
            cmd_outputs = list(
                filter(lambda x: x != '', [x.strip() for x in cmd_outputs]))
            per_client_outputs[client.username] = cmd_outputs

        log(f"[{self.name}] {self.desc}")
        for client in self.all_clients.values():
            log(f"{client.username}:")
            log(f"\tInput")
            for block in self.command_blocks:
                if (block.username != client.username):
                    continue
                for command in block.cmds:
                    log("\t| " + command)
            log(f"\tOutput")
            for line in per_client_lines[client.username]:
                log("\t| " + line)

        # assign outputs to blocks
        for block in self.command_blocks:
            outputs = []
            if block.username != None:
                outputs = per_client_outputs[block.username]
            assert (len(block.cmds) <= len(outputs)
                    ), "Some command did not produce an output"
            for _ in block.cmds:
                output = outputs[0]
                outputs = outputs[1:]
                block.outputs.append(output)
            if block.post:
                block.post(block.outputs, self.context)
            # shift the remaining outputs to the next block
            if (block.username != None):
                per_client_outputs[block.username] = outputs

        # def log_manual(self):
        #     if (self.context["manual_outputs"] == []):
        #         return
        #     log("Manual outputs:")
        #     for output in self.context["manual_outputs"]:
        #         log(output)


def run_test_case(logger, test_case):
    print(f"====================================================================================")
    print(f"Running test case {test_case.__name__}...")

    name = test_case.__name__

    # port = None
    # context = None
    # graph = {}
    # srv_procs = {}
    # command_blocks = []
    # connected_clients = {}
    # all_clients = {}

    # desc = None

    # def start_servers_wrapper(ports):
    #     nonlocal context
    #     nonlocal srv_procs

    #     for port in ports:
    #         if (port in srv_procs):
    #             warn(f"Server already started on port {port}; just returning the already started one.")
    #             continue

    #         config_filename = f"config_{name}.json"
    #         config_fullname = os.path.join(get_working_dir(), config_filename)
    #         write_config_file(config_fullname, graph, port, ports)

    #         srv_proc = start_server(config_fullname, port)

    #         expected_total_debts = get_total_per_user(graph)
    #         context = {
    #             "expected_totals": expected_total_debts,
    #             "manual_outputs": []
    #         }

    #         srv_procs[port] = srv_proc

    #     return srv_proc

    # def stop_server_wrapper(port, proc_server):
    #     nonlocal srv_procs

    #     stop_server(proc_server)

    #     srv_procs.pop(port)

    # def build_graph(matrix):
    #     nonlocal graph
    #     graph = matrix_to_graph(matrix)
    #     return graph

    # def join_client_wrapper(username, port=3333):
    #     client = join_client(username)
    #     connected_clients[username] = client
    #     all_clients[username] = client
    #     return client

    # def exit_client_wrapper(client):
    # connected_clients.pop(client.username)
    # exit_client(client)

    # def run_command_blocks_wrapper(*blocks):
    #     for block in blocks:
    #         if (block == None):
    #             continue
    #         username = block.username
    #         if (username != None):
    #             if username not in connected_clients:
    #                 join_client_wrapper(username)
    #         run_command_block(connected_clients, command_blocks, block)

    # def describe(new_desc):
    #     nonlocal desc
    #     desc = new_desc

    # should_skip_output_parsing = False

    # def set_should_skip_output_parsing(should_skip):
    #     nonlocal should_skip_output_parsing
    #     should_skip_output_parsing = should_skip

    try:
        interface = TestCaseInterface(name)

        test_case(interface)

        interface.run_command_blocks(wait_block(0.5))

        time.sleep(2)

        interface.exit_all_clients()

        # for client in connected_clients.values():
        #     exit_client(client)
        # connected_clients.clear()

        interface.parse_outputs()

        # if (not should_skip_output_parsing):
        #     parse_outputs(command_blocks, all_clients, context)

        interface.stop_all_servers()

        # for port, srv_proc in srv_procs.items():
        #     stop_server(srv_proc)

        if (interface.context["manual_outputs"] == []):
            logger.logSuccess(interface.name, interface.desc)
    except Exception as e:
        logger.logFailure(interface.name, interface.desc, repr(e))
        interface.stop_all_servers()
        # Get type of error
        t = type(e)

    if (interface.context["manual_outputs"] != []):
        logger.logManual(interface.name, interface.desc,
                         interface.context["manual_outputs"])


def run_all_tests(project_dir):
    logger = OutcomeLogger()

    get_working_dir(project_dir)

    compile_server()
    compile_client()

    run_test_case(logger, test_case1)
    run_test_case(logger, test_case2)
    run_test_case(logger, test_case3)
    run_test_case(logger, test_case4)
    run_test_case(logger, test_case5)
    run_test_case(logger, test_case6)
    run_test_case(logger, test_case7)
    run_test_case(logger, test_case8)
    run_test_case(logger, test_case9)
    run_test_case(logger, test_case10)
    run_test_case(logger, test_case11)
    run_test_case(logger, test_case12)
    run_test_case(logger, test_case13)
    run_test_case(logger, test_case14)
    run_test_case(logger, test_case15)
    run_test_case(logger, test_case16)
    run_test_case(logger, test_case17)

    run_test_case(logger, test_case2_1_0)
    run_test_case(logger, test_case2_1_1)
    run_test_case(logger, test_case2_1_2)

    run_test_case(logger, test_case2_2_0)
    run_test_case(logger, test_case2_2_1)

    run_test_case(logger, test_case2_3_0)
    run_test_case(logger, test_case2_3_1)
    run_test_case(logger, test_case2_3_2)

    run_test_case(logger, test_case2_4_0)
    run_test_case(logger, test_case2_4_1)
    run_test_case(logger, test_case2_4_2)

    set_log_file(None)

    logger.print_logs()


run_all_tests(project_fullname)
