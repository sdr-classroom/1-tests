

import random
from blocks import *


def test_case1(interface):
    interface.describe("Paying someone should create a debt and a credit.")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)

    interface.run_command_blocks(
        pay_block('user1', 10, ['user0']),
        wait_block(1),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 10),
        wait_block(1),
    )


def test_case2(interface):
    interface.describe(
        "Paying someone and oneself should create a debt and a credit only to the other person.")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)

    interface.run_command_blocks(
        pay_block('user1', 10, ['user0', 'user1']),
        wait_block(1),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 5),
        wait_block(1),
    )


def test_case3(interface):
    interface.describe(
        "Paying multiple people including oneself should equally distribute debt.")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)

    interface.run_command_blocks(
        pay_block('user0', 30, ['user0', 'user1', 'user2']),
        wait_block(1),
        assert_debts_equal_constant_block('user0', 'user1', 'user0', 10),
        assert_debts_equal_constant_block('user0', 'user2', 'user0', 10),
        wait_block(1),
    )


def test_case4(interface):
    interface.describe("Paying oneself should change nothing")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)

    interface.run_command_blocks(
        pay_block('user1', 10, ['user1']),
        wait_block(1),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 0),
        wait_block(1),
    )


def test_case5(interface):
    interface.describe(
        "Paying someone that then pays back should change nothing")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)

    interface.run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 10, ['user0']),
        wait_block(1),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 0),
        assert_debts_equal_constant_block('user0', 'user1', 'user0', 0),
        wait_block(1),
    )


def test_case6(interface):
    interface.describe(
        "Paying someone that then pays back more should create a debt and a credit.")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)

    interface.run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 15, ['user0']),
        wait_block(1),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 5),
        assert_debts_equal_constant_block('user0', 'user1', 'user0', 0),
        wait_block(1),
    )


def test_case7(interface):
    interface.describe(
        "A payment chain of A -> B -> C -> A with all amounts equal should result in no change.")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)

    users = interface.get_users()

    interface.run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 10, ['user2']),
        pay_block('user2', 10, ['user0']),
        wait_block(1),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        wait_block(1),
    )


def test_case8(interface):
    interface.describe(
        "A payment chain of A -> B -> C with all amounts equal should result in debt from A to C.")

    interface.build_graph([[0, 0, 0],
                           [0, 0, 0],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)

    users = interface.get_users()

    interface.run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 10, ['user2']),
        wait_block(1),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        assert_debts_equal_constant_block('user0', 'user2', 'user0', 10),
        wait_block(1),
    )


def test_case9(interface):
    interface.describe(
        "After a long sequence of concurrent transactions, the graph should be correct and simplified.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)
    interface.join_client('user3', 3333)
    interface.join_client('user4', 3333)
    interface.join_client('user5', 3333)

    users = interface.get_users()

    for i in range(100):
        random_user = random.choice(users)
        random_amount = random.randint(1, 10)
        random_benefitors = random.sample(users, random.randint(1, len(users)))
        actual_benefitors = [b for b in random_benefitors if b != random_user]
        total_random_amount = random_amount * len(random_benefitors)
        interface.run_command_blocks(
            pay_block(random_user, total_random_amount, random_benefitors))

    interface.run_command_blocks(
        wait_block(1),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        wait_block(1),
    )


def test_case10(interface):
    interface.describe(
        "`Get` request with no user specified uses current user.")

    interface.build_graph([[0, 0, 20],
                           [0, 0, 10],
                           [0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)

    interface.run_command_blocks(
        get_user_debts_block("user0"),
        wait_block(1)
    )


def test_case11(interface):
    interface.describe(
        "Connecting and getting debts with invalid username should fail.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.get_users()

    client = interface.join_client('unknown_user', 3333)

    try:
        interface.run_command_blocks(
            get_user_debts_block(client.username, log_for_manual=True),
            wait_block(1))
    except Exception as e:
        if type(e) == BrokenPipeError:
            interface.set_should_skip_output_parsing(True)
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError because client should not have started due to wrong username, instead got {type(e)}"

    try:
        time.sleep(1)
        interface.exit_client(client)
    except Exception as e:
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError, got {type(e)}"


def test_case12(interface):
    interface.describe("Getting debts for invalid username should fail.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)

    interface.run_command_blocks(
        get_user_debts_block("user0", user="unknown_user", log_for_manual=True),
        wait_block(1))


def test_case13(interface):
    interface.describe("Connecting as unknown user and paying should fail.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    users = interface.get_users()

    client = interface.join_client('unknown_user', 3333)
    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)

    try:
        interface.run_command_blocks(
            pay_block(client.username, 10, [
                      'user1', 'user2'], log_manual=True),
            wait_block(1),
            get_debts_graph_block('user0', users),
            assert_graph_is_simplified_block(),
            wait_block(1),
        )
    except Exception as e:
        if type(e) == BrokenPipeError:
            interface.set_should_skip_output_parsing(True)
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError because client should not have started due to wrong username, instead got {type(e)}"

    time.sleep(3)

    try:
        interface.exit_client(client)
    except Exception as e:
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError, got {type(e)}"


def test_case14(interface):
    interface.describe("Paying for an unknown user should fail.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)

    users = interface.get_users()

    interface.run_command_blocks(
        pay_block("user0", 10, ['user1', 'unknown_user',
                  'user2'], log_manual=True),
        wait_block(1),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        wait_block(1),
    )


def test_case15(interface):
    interface.describe("Paying with negative number should fail.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)

    users = interface.get_users()

    interface.run_command_blocks(
        pay_block("user0", -10, ['user1', 'user2'], log_manual=True),
        wait_block(1),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        wait_block(1)
    )


def test_case16(interface):
    interface.describe(
        "Paying with amount 0 should not change anything, and is allowed to fail.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)
    interface.join_client('user1', 3333)
    interface.join_client('user2', 3333)

    users = interface.get_users()

    interface.run_command_blocks(
        pay_block("user0", 0, ['user1', 'user2']),
        wait_block(1),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        wait_block(1)
    )


def test_case17(interface):
    interface.describe("Running wrong command should fail.")

    interface.build_graph([[0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0]])

    interface.define_servers([3333])
    interface.start_all_servers()

    interface.init_context()

    interface.join_client('user0', 3333)

    users = interface.get_users()

    interface.run_command_blocks(
        wrong_command_block('user0', 'unknown_command', True),
        wait_block(1),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        wait_block(1)
    )
