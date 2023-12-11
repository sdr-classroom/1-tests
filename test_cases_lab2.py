import random
from blocks import *


def test_case2_1_0(interface):
    interface.describe(
        "Clear command on someone with no debts should change nothing.")

    interface.build_graph([[0, 0, 0],
                           [2, 0, 0],
                           [3, 0, 0]])

    interface.define_servers([3333, 3334])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)

    interface.run_command_blocks(
        wait_block(1),
        clear_block('user0', [-5, 2, 3]),
        wait_block(1),
        get_debts_graph_block('user0', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(1)
    )


def test_case2_1_1(interface):
    interface.describe(
        "Clear command on someone with one debt should remove debt.")

    interface.build_graph([[0, 0, 0],
                           [2, 0, 0],
                           [3, 0, 0]])

    interface.define_servers([3333, 3334])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user1', 3333)

    interface.run_command_blocks(
        clear_block('user1', [-3, 0, 3]),
        wait_block(1),
        get_debts_graph_block('user1', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(1),
    )


def test_case2_1_2(interface):
    interface.describe(
        "Clear command on someone with many debts should remove all debts.")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [3, 2, 0]])

    interface.define_servers([3333, 3334])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user2', 3333)

    interface.run_command_blocks(
        clear_block('user2', [0, 0, 0]),
        wait_block(1),
        get_debts_graph_block('user2', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(1),
    )


def test_case2_2_0(interface):
    interface.describe("Servers agree on initial graph.")

    interface.build_graph([
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 3, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0, 0, 5, 6],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ])

    interface.define_servers([3333, 3334, 3335])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3334)
    interface.join_client('user2', 3335)

    interface.run_command_blocks(
        wait_block(1),
        get_debts_graph_block('user0', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(0.3),
        get_debts_graph_block('user1', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(0.3),
        get_debts_graph_block('user2', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(1),
    )


def test_case2_2_1(interface):
    interface.describe("Servers agree after single pay request.")

    interface.build_graph([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ])

    interface.define_servers([3333, 3334, 3335])
    interface.start_all_servers()

    interface.init_context()

    u0 = interface.join_client('user0', 3333)
    interface.run_command_blocks(
        wait_block(0.5),
        pay_block('user0', 10, ['user1', 'user2']),
        wait_block(1),
        get_debts_graph_block('user0', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(0.5),
    )
    interface.exit_client(u0)

    u1 = interface.join_client('user1', 3334)
    interface.run_command_blocks(
        wait_block(0.3),
        get_debts_graph_block('user1', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(0.5),
    )
    interface.exit_client(u1)

    u2 = interface.join_client('user2', 3335)
    interface.run_command_blocks(
        wait_block(0.3),
        get_debts_graph_block('user2', interface.get_users()),
        assert_graph_is_simplified_block(),
        wait_block(1),
    )
    interface.exit_client(u2)


def test_case2_3_x(interface, server_count, client_count_per_server):
    interface.describe(
        f"{server_count} servers with {client_count_per_server} clients each should handle concurrent pay requests and agree on a correct result.")

    user_count = server_count * client_count_per_server
    interface.build_random_graph(user_count)

    interface.define_servers([3333 + i for i in range(server_count)])
    interface.start_all_servers()

    interface.init_context()

    clients = []
    for i in range(user_count):
        clients.append(interface.join_client(
            f'user{i}', 3333 + i % server_count))

    pay_count_per_client = 10

    def random_pay_block(src):
        users = interface.get_users()
        random_dests = random.sample(users, random.randint(1, len(users)))
        random_amount = random.randint(1, 20) * len(random_dests)
        return pay_block(src, random_amount, random_dests)

    interface.run_command_blocks(
        wait_block(0.5),
        *[random_pay_block(f'user{i}') for i in range(user_count)
          for _ in range(pay_count_per_client)],
        wait_block(2),
    )

    for i in range(server_count):
        interface.run_command_blocks(
            get_debts_graph_block(f'user{i}', interface.get_users()),
            assert_graph_is_simplified_block(),
            wait_block(0.5),
        )

    interface.run_command_blocks(
        wait_block(2),
    )


def test_case2_3_0(interface):
    test_case2_3_x(interface, 3, 1)


def test_case2_3_1(interface):
    test_case2_3_x(interface, 3, 3)


def test_case2_3_2(interface):
    test_case2_3_x(interface, 10, 5)


def test_case2_4_x(interface, server_count, client_count_per_server):
    interface.describe(
        f"{server_count} servers with {client_count_per_server} clients each should handle concurrent pay and clear requests and agree on a result.")

    user_count = server_count * client_count_per_server
    interface.build_random_graph(user_count)

    interface.define_servers([3333 + i for i in range(server_count)])
    interface.start_all_servers()

    interface.init_context()

    clients = []
    for i in range(user_count):
        clients.append(interface.join_client(
            f'user{i}', 3333 + i % server_count))

    pay_count_per_client = 10

    def pay_or_clear_block(src):
        clear_prob = 0.1
        if random.random() < clear_prob:
            # Note : expected totals are now incorrect, and shouldn't be checked in this test.
            return clear_block(src, [0] * user_count)
        else:
            return random_pay_block(src)

    def random_pay_block(src):
        users = interface.get_users()
        random_dests = random.sample(users, random.randint(1, len(users)))
        random_amount = random.randint(1, 20) * len(random_dests)
        return pay_block(src, random_amount, random_dests)

    interface.run_command_blocks(
        wait_block(0.5),
        *[pay_or_clear_block(f'user{i}') for i in range(user_count)
          for _ in range(pay_count_per_client)],
        wait_block(2),
    )

    interface.run_command_blocks(
        get_debts_graph_block(f'user0', interface.get_users()),
        assert_graph_is_simplified_block(assert_equivalence=False),
        snapshot_graph_block(),
        wait_block(1)
    )

    for i in range(1, server_count):
        interface.run_command_blocks(
            get_debts_graph_block(f'user{i}', interface.get_users()),
            assert_graph_equals_snapshot_block(),
        )

    interface.run_command_blocks(
        wait_block(2),
    )

def test_case2_4_0(interface):
    test_case2_4_x(interface, 3, 1)

def test_case2_4_1(interface):
    test_case2_4_x(interface, 3, 3)

def test_case2_4_2(interface):
    test_case2_4_x(interface, 10, 5)



'''
This file tests the following test cases
- [x] clear command
    - on a single server, a single user makes a clear request ; all their debts only should be cleared.
- inter-server agreement and concurrency
    - [x] 3 servers loaded with given initial state agree on that set. Tested through a single user connecting to one after the other and doing only get commands
    - [x] one client paying on one server should create a debt and a credit on all other servers. Tested through a single user connecting to one after the other and doing only get commands except for the first command.
    - [x] with x,y = (3,1), (3,3), (10,5)
        - x servers, y client on each, making many pay requests concurrently. The servers should reach a correct result, without deadlocking
        - x servers, y client on each, making many pay and clear requests concurrently. All servers should agree on a final result. No tests of correctness of results, since it depends on the order of events and those are non-deterministic. Only agreement is checked.
- intra-server concurrency
    - Multiple clients connected to the same server should be able to make pay and pay requests concurrently and reach a correct result, without deadlocking
'''
