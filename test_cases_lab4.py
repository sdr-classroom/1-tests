import random
from blocks import *

'''
Automated tests, for a clique, a tree, and a sparse graph, test that
	- If i'm the only connected client, I only see myself as connected
	- After connecting multiple clients but not all, they are shown as online
	- If multiple users are connected, they can run `users` concurrently and get a correct result
	- After connecting multiple clients and having some leave, only those left are shown online
	- After connecting multiple clients, getting users and having some leave, only those left should be shown by a new `users` call.
'''

graph_types = ['clique', 'tree', 'sparse']

def define_probe_neighbors_graph(interface, graph_type):
    if graph_type == 'clique':
        interface.define_clique_probe_graph()
    elif graph_type == 'tree':
        interface.define_tree_probe_graph()
    elif graph_type == 'sparse':
        interface.define_random_probe_graph()

def test_case4_0_x(interface, graph_type):
    interface.describe("(On " + graph_type + ") If i'm the only connected client, I only see myself as connected")

    # interface.run_many_times(4)

    interface.build_graph([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ])
    
    interface.define_servers([3333, 3334])
    
    define_probe_neighbors_graph(interface, graph_type)
    
    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(1),
    )

    interface.join_client('user0', 3333)

    interface.run_command_blocks(
        wait_block(1),
        assert_connected_users_block('user0', ['user0'], interface.get_users()),
        wait_block(1),
    )

def test_case4_0_0(interface):
    test_case4_0_x(interface, 'clique')

def test_case4_0_1(interface):
    test_case4_0_x(interface, 'tree')

def test_case4_0_2(interface):
    test_case4_0_x(interface, 'sparse')

def test_case4_1_x(interface, graph_type):
    interface.describe("(On " + graph_type + ") After connecting multiple clients but not all, they are shown as online")

    # interface.run_many_times(4)

    num_clients = 5
    num_connected_clients = 3
    interface.build_random_graph(num_clients)
    
    interface.define_servers([3333, 3334, 3335])
    
    define_probe_neighbors_graph(interface, graph_type)
    
    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(1),
    )

    for i in range(num_connected_clients):
        interface.join_client(f'user{i}', 3333)

    interface.run_command_blocks(
        wait_block(10),
        assert_connected_users_block(f'user0', [f'user{i}' for i in range(num_connected_clients)], interface.get_users()),
        wait_block(1),
    )

def test_case4_1_0(interface):
    test_case4_1_x(interface, 'clique')

def test_case4_1_1(interface):
    test_case4_1_x(interface, 'tree')

def test_case4_1_2(interface):
    test_case4_1_x(interface, 'sparse')


def test_case4_2_x(interface, graph_type):
    interface.describe("(On " + graph_type + ") If multiple users are connected, they can run `users` concurrently and get a correct result")

    num_clients = 5
    num_connected_clients = 3
    random_connected_clients = [f"user{i}" for i in random.sample(range(num_clients), num_connected_clients)]

    interface.build_random_graph(num_clients)

    ports = [3333, 3334, 3335]

    interface.define_servers(ports)

    define_probe_neighbors_graph(interface, graph_type)

    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(1),
    )

    # Connecting clients
    for client in random_connected_clients:
        interface.join_client(client, random.choice(ports))
    
    interface.run_command_blocks(
        wait_block(10),
    )

    blocks = [assert_connected_users_block(client, random_connected_clients, interface.get_users()) for client in random_connected_clients]

    interface.run_command_blocks(*blocks)

    interface.run_command_blocks(wait_block(1))

def test_case4_2_0(interface):
    test_case4_2_x(interface, 'clique')

def test_case4_2_1(interface):
    test_case4_2_x(interface, 'tree')

def test_case4_2_2(interface):
    test_case4_2_x(interface, 'sparse')


def test_case4_3_x(interface, graph_type):
    interface.describe("(On " + graph_type + ") After connecting multiple clients and having some leave, only those left are shown online")

    num_clients = 10
    num_connected_clients = 7
    num_disconnecting_clients = 3
    random_connected_clients = [f"user{i}" for i in random.sample(range(num_clients), num_connected_clients)]

    interface.build_random_graph(num_clients)

    ports = [3333, 3334, 3335]

    interface.define_servers(ports)

    define_probe_neighbors_graph(interface, graph_type)

    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(1),
    )

    # Connecting clients
    for client in random_connected_clients:
        interface.join_client(client, random.choice(ports))
    
    interface.run_command_blocks(
        wait_block(10),
    )

    # Disconnecting clients
    disconnecting_clients = random.sample(random_connected_clients, num_disconnecting_clients)
    for client in disconnecting_clients:
        interface.exit_client_by_name(client)
    remaining_clients = list(set(random_connected_clients) - set(disconnecting_clients))
    
    print(f"Initiallly connected: {random_connected_clients}\nNow connected: {remaining_clients}")
    
    interface.run_command_blocks(
        wait_block(10),
    )

    interface.run_command_blocks(
        wait_block(1),
        assert_connected_users_block(random.choice(remaining_clients), remaining_clients, interface.get_users()),
        wait_block(1),
    )

def test_case4_3_0(interface):
    test_case4_3_x(interface, 'clique')

def test_case4_3_1(interface):
    test_case4_3_x(interface, 'tree')

def test_case4_3_2(interface):
    test_case4_3_x(interface, 'sparse')

def test_case4_4_x(interface, graph_type):
    interface.describe("(On " + graph_type + ") After connecting multiple clients, getting users and having some leave, only those left should be shown by a new `users` call.")

    num_clients = 10
    num_connected_clients = 7
    num_disconnecting_clients = 3
    random_connected_clients = [f"user{i}" for i in random.sample(range(num_clients), num_connected_clients)]

    interface.build_random_graph(num_clients)

    ports = [3333, 3334, 3335]

    interface.define_servers(ports)

    define_probe_neighbors_graph(interface, graph_type)

    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(1),
    )

    # Connecting clients
    for client in random_connected_clients:
        interface.join_client(client, random.choice(ports))
    
    interface.run_command_blocks(
        wait_block(10),
    )

    # Getting users
    interface.run_command_blocks(
        wait_block(1),
        assert_connected_users_block(random.choice(random_connected_clients), random_connected_clients, interface.get_users()),
        wait_block(1),
    )

    # Disconnecting clients
    disconnecting_clients = random.sample(random_connected_clients, num_disconnecting_clients)
    for client in disconnecting_clients:
        interface.exit_client_by_name(client)
    remaining_clients = list(set(random_connected_clients) - set(disconnecting_clients))
    
    print(f"Initiallly connected: {random_connected_clients}\nNow connected: {remaining_clients}")
    
    interface.run_command_blocks(
        wait_block(5),
    )

    interface.run_command_blocks(
        wait_block(1),
        assert_connected_users_block(random.choice(remaining_clients), remaining_clients, interface.get_users()),
        wait_block(1),
    )

def test_case4_4_0(interface):
    test_case4_4_x(interface, 'clique')

def test_case4_4_1(interface):
    test_case4_4_x(interface, 'tree')

def test_case4_4_2(interface):
    test_case4_4_x(interface, 'sparse')
