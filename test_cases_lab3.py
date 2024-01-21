import random
from blocks import *

'''
Tests in this file

- 3.0.0 In a single-server setting, `server` returns the initially requested server
- 3.x.x In a multi-server setting, once with all servers up, once with some servers down before the client try to connect
    - 1.x if many clients request connections to the same server, one after the other
        - if they do not disconnect, then after each connection, load should be as balanced as possible
        - if they do disconnect in the meantime, such that the load is not balanced, then subsequent connections should be to the least loaded server
    - 2.x if many clients request connections to arbitrary servers, all at once, then
        - at the end, load should be as balanced as possible.
        - [cannot test] after each connection, load should be as balanced as possible.
    - 3.x if some number of clients initially connect, then disconnect and reconnect some number of times, then
        - at the end, load should be as balanced as possible. This should be run multiple times.
    - 4.x Fault tolerance: if many clients request connections to arbitrary servers, and some of them go down during that time, then
        - at the end, one last client that connects should succeed and be connected to a correct process. This should be run multiple times.
'''

def test_case3_0_0(interface):
    interface.describe("In a single-server setting, `server` returns the initially requested server")

    interface.build_graph([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(11),
    )

    interface.join_client('user0', 3333)

    interface.run_command_blocks(
        wait_block(11),
        assert_server_block('user0', 3333),
        wait_block(1),
    )

def test_case3_1_0(interface):
    interface.describe("In a multi-server setting, if many clients request connections to the same server, one after the other, and they do not disconnect, then after each connection, load should be as balanced as possible")

    num_clients = 10
    interface.build_random_graph(num_clients)

    num_servers = 3
    interface.define_servers([3333 + x for x in range(num_servers)])
    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(11),
    )

    for i in range(num_clients):
        interface.join_client(f'user{i}', 3333)
        interface.run_command_blocks(
            get_server_block(f'user{i}'),
            wait_block(1),
        )

    interface.run_command_blocks(
        assert_server_load_balanced_block(interface.get_all_servers()),
        wait_block(1),
    )

def test_case3_1_1(interface):
    interface.describe("In a multi-server setting, if many clients request connections to the same server, one after the other, and they do disconnect in the meantime, such that the load is not balanced, then subsequent connections should be to the least loaded server")

    num_clients = 10
    num_new_clients = 10
    interface.build_random_graph(num_clients + num_new_clients)

    num_servers = 3
    interface.define_servers([3333 + x for x in range(num_servers)])
    interface.start_all_servers()

    servers = interface.get_all_servers()

    interface.init_context()

    # Connecting them all
    for i in range(num_clients):
        interface.join_client(f'user{i}', 3333)
    interface.run_command_blocks(
        wait_block(11),
    )
    
    # Disconnecting half of them
    clients_to_disconnect = random.sample(range(num_clients), num_clients // 2)
    for i in clients_to_disconnect:
        interface.exit_client_by_name(f'user{i}')
    interface.run_command_blocks(
        wait_block(11),
    )

    # Getting the server of the remaining clients
    remaining_clients = [f'user{i}' for i in range(num_clients) if i not in clients_to_disconnect]
    for username in remaining_clients:
        interface.run_command_blocks(
            get_server_block(username),
            wait_block(1),
        )

    # We should now have an imbalanced load. We connect new clients and see if they are assigned to the least loaded server.
    interface.run_command_blocks(
        snapshot_server_loads_block(servers),
    )
    
    # Connecting new clients
    for i in range(num_new_clients):
        username = f'user{num_clients + i}'
        remaining_clients.append(username)
        interface.join_client(username, 3333)
        interface.run_command_blocks(
            get_server_block(username),
            assert_new_connection_to_least_loaded_block(),
            snapshot_server_loads_block(servers),
        )

    interface.run_command_blocks(
        wait_block(11),
    )
    
def test_case3_2_0(interface):
    interface.describe("In a multi-server setting, if many clients request connections to arbitrary servers, all at once, then at the end, load should be as balanced as possible.")

    num_clients = 10
    interface.build_random_graph(num_clients)

    num_servers = 3
    interface.define_servers([3333 + x for x in range(num_servers)])
    interface.start_all_servers()

    interface.init_context()

    for i in range(num_clients):
        interface.join_client(f'user{i}', 3333 + random.randint(0, num_servers - 1))

    interface.run_command_blocks(
        wait_block(11),
    )

    for i in range(num_clients):
        interface.run_command_blocks(
            get_server_block(f'user{i}'),
        )
    
    interface.run_command_blocks(
        assert_server_load_balanced_block(interface.get_all_servers()),
        wait_block(1),
    )

def test_case3_3_0(interface):
    interface.describe("In a multi-server setting, if some number of clients initially connect, then disconnect and reconnect some number of times, then at the end, load should be as balanced as possible.")

    interface.run_many_times(5)

    num_clients = 10
    num_reconnects = 30
    interface.build_random_graph(num_clients)

    num_servers = 4
    interface.define_servers([3333 + x for x in range(num_servers)])
    interface.start_all_servers()

    interface.init_context()

    for i in range(num_clients):
        interface.join_client(f'user{i}', 3333)
        interface.run_command_blocks(
            wait_block(1),
        )

    interface.run_command_blocks(
        wait_block(11),
    )

    disconnected_clients = []
    for i in range(num_reconnects * 2):
        random_client = random.randint(0, num_clients - 1)
        if random_client in disconnected_clients:
            interface.join_client(f'user{random_client}', 3333)
            disconnected_clients.remove(random_client)
        else:
            interface.exit_client_by_name(f'user{random_client}')
            disconnected_clients.append(random_client)
        
    for disconnected_client in disconnected_clients:
        interface.join_client(f'user{disconnected_client}', 3333)

    for i in range(num_clients):
        interface.run_command_blocks(
            get_server_block(f'user{i}'),
        )

    interface.run_command_blocks(
        wait_block(1),
        assert_server_load_balanced_block(interface.get_all_servers()),
        wait_block(1),
    )


def test_case3_4_0(interface):
    interface.describe("In a multi-server setting, if many clients request connections to arbitrary servers, and some of them go down during that time, then at the end, load should be balanced for remaining servers.")

    num_clients = 10

    num_servers = 6
    num_servers_down = num_servers // 2

    # to ensure that all new clients will cover all remaining servers : in worst case, only one remaining server has 1 more client than the others, so we need `remaining-1` to cover those, and then `remaining` to cover all again so that the very last one is garanteed to be covered.
    num_new_clients = 2 * (num_servers - num_servers_down) - 1
    interface.build_random_graph(num_clients + num_new_clients)

    interface.define_servers([3333 + x for x in range(num_servers)])
    interface.start_all_servers()

    interface.init_context()

    interface.run_command_blocks(
        wait_block(3),
    )

    interface.run_many_times(5)

    ports_to_fail = [s + 3333 for s in random.sample(range(num_servers), num_servers_down)]

    print(f"Ports to fail: {ports_to_fail}")

    actions = []
    for i in range(num_clients):
        actions.append(lambda _ : interface.join_client(f'user{i}', 3333 + random.randint(0, num_servers - 1)))

    for port in ports_to_fail:
        actions.append(lambda _ : interface.stop_server(port))

    # shuffle actions
    random.shuffle(actions)

    for action in actions:
        action(None)
    
    remaining_servers = [s for s in interface.get_all_servers() if s.port not in ports_to_fail]

    interface.run_command_blocks(
        wait_block(30),
    )

    for i in range(num_new_clients):
        id = num_clients + i
        server = random.choice(remaining_servers)
        # print(f"Joining user{id} to server {server.port}")
        interface.join_client(f'user{id}', server)
    
    for i in range(num_new_clients):
        id = num_clients + i
        interface.run_command_blocks(
            get_server_block(f'user{id}'),
        )
    
    interface.run_command_blocks(
        wait_block(1),
        assert_server_load_balanced_block(remaining_servers)
    )