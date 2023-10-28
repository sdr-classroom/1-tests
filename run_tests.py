import signal
import sys
import math
import os
import random
import subprocess
import threading
import time
from helpers import get_total_per_user

from log import log, allow_debug_logs
from outcome import OutcomeLogger
from test_cases import *
from client import Client

sleep_speedup = 1

debug = False
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

def get_client_fullname():
    return os.path.join(get_working_dir(), "client")

def get_server_fullname():
    return os.path.join(get_working_dir(), "server")

def compile_server():
    print("Compiling server...")
    global project_fullname
    compile_script = os.path.join(project_fullname, "compile_server.sh")
    print("Script path : ", compile_script)
    os.system(f'cd {project_fullname}; {compile_script} {get_server_fullname()}')
    print("Server compiled")

def compile_client():
    print("Compiling client...")
    global project_fullname
    compile_script = os.path.join(project_fullname, "compile_client.sh")
    os.system(f'cd {project_fullname}; {compile_script} {get_client_fullname()}')

def write_config_file(filename, graph, port):
    global debug
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
        f.write(', '.join(users) + ']}\n')


def run_command_block(clients, cmd_blocks, block):
    cmd_blocks.append(block)
    if (block.pre):
        block.pre()
    if (block.username == None):
        return
    client = clients[block.username]
    subprocess = client.subprocess
    for cmd in block.cmds:
        subprocess.stdin.write((cmd + "\n").encode())
        subprocess.stdin.flush()


def join_client(username):
    global project_fullname
    cmd = f"{get_client_fullname()} {username} localhost:3333"
    # f"go run -race {client_dir} {username} localhost:3333",
    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         shell=True,
                         cwd=get_working_dir())
    log(f'Client {username} joined, waiting...')
    time.sleep(0.7 * sleep_speedup)
    return Client(username, p)


def exit_client(client):
    subprocess = client.subprocess
    subprocess.stdin.write('exit\n'.encode())
    subprocess.stdin.write('exit\n'.encode())
    subprocess.stdin.flush()
    log(f'client {client.username} exited, killing it...')
    # time.sleep(0.1 * sleep_speedup)
    subprocess.kill()
    # time.sleep(0.1 * sleep_speedup)


def parse_outputs(cmd_blocks, clients, context):
    log("Parsing outputs...")
    per_client_outputs = {}
    per_client_lines = {}

    # parse lines for each client
    for client in clients.values():
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

    # assign outputs to blocks
    for block in cmd_blocks:
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
            block.post(block.outputs, context)
        # shift the remaining outputs to the next block
        if (block.username != None):
            per_client_outputs[block.username] = outputs


def start_server(config_filename, port):
    # use lsof to find the process id of the server listening on the port, then kill it.
    os.system(f'lsof -t -i:{port} | xargs kill')
    log(f"Killed anything listening on {port}")
    # srv_cmd = f"go run -race {server_dir} {config_filename}".split()
    srv_cmd = f"{get_server_fullname()} {config_filename}".split()
    srv_proc = subprocess.Popen(srv_cmd, cwd=get_working_dir())
    log("Server started, waiting...")
    time.sleep(1 * sleep_speedup)
    return srv_proc


def stop_server(srv_proc, port):
    log("Stopping server...")
    srv_proc.kill()
    log("Server stopped")
    # time.sleep(0.1 * sleep_speedup)


def matrix_to_graph(matrix):
    n = len(matrix)
    graph = {}
    for i in range(n):
        ui = "user" + str(i)
        graph[ui] = {}
        assert len(matrix[i]) == n, "Matrix must be square"
        for j in range(n):
            uj = "user" + str(j)
            if (matrix[i][j] != 0):
                graph[ui][uj] = matrix[i][j]
    return graph


def run_test_case(logger, test_case):
    print(f"Running test case {test_case.__name__}...")

    name = test_case.__name__

    port = None
    srv_proc = None
    context = None
    graph = {}
    command_blocks = []
    connected_clients = {}
    all_clients = {}

    desc = None

    def start_server_wrapper():
        nonlocal port
        nonlocal srv_proc
        nonlocal context

        port = 3333

        config_filename = f"config_{name}.json"
        config_fullname = os.path.join(get_working_dir(), config_filename)
        write_config_file(config_fullname, graph, port)

        srv_proc = start_server(config_fullname, port)

        expected_total_debts = get_total_per_user(graph)
        context = {
            "expected_totals": expected_total_debts,
            "manual_outputs": []
        }

        return srv_proc

    def check_server_started():
        nonlocal srv_proc
        if not srv_proc:
            srv_proc = start_server_wrapper()

    def build_graph(matrix):
        nonlocal graph
        graph = matrix_to_graph(matrix)
        return graph

    def join_client_wrapper(username):
        check_server_started()

        client = join_client(username)
        connected_clients[username] = client
        all_clients[username] = client
        return client

    def exit_client_wrapper(client):
        connected_clients.pop(client.username)
        exit_client(client)

    def run_command_blocks_wrapper(*blocks):
        check_server_started()

        for block in blocks:
            if (block == None):
                continue
            username = block.username
            if (username != None):
                if username not in connected_clients:
                    join_client_wrapper(username)
            run_command_block(connected_clients, command_blocks, block)

    def describe(new_desc):
        nonlocal desc
        desc = new_desc

    should_skip_output_parsing = False

    def set_should_skip_output_parsing(should_skip):
        nonlocal should_skip_output_parsing
        should_skip_output_parsing = should_skip

    try:
        test_case(describe, build_graph, run_command_blocks_wrapper,
                  join_client_wrapper, exit_client_wrapper, set_should_skip_output_parsing)

        time.sleep(2)

        for client in connected_clients.values():
            exit_client(client)
        connected_clients.clear()

        if (not should_skip_output_parsing):
            parse_outputs(command_blocks, all_clients, context)

        stop_server(srv_proc, port)

        if (context["manual_outputs"] == []):
            logger.logSuccess(name, desc)
    except Exception as e:
        logger.logFailure(name, desc, repr(e))
        stop_server(srv_proc, port)
        # Get type of error
        t = type(e)

    if (context["manual_outputs"] != []):
        logger.logManual(name, desc, context["manual_outputs"])


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

    logger.print_logs()
