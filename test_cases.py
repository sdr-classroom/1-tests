


import random
from blocks import *
from helpers import get_users_from_graph


def test_case1(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Paying someone should create a debt and a credit.")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    run_command_blocks(
        pay_block('user1', 10, ['user0']),
        wait_block(0.2),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 10),
    )


def test_case2(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe(
        "Paying someone and oneself should create a debt and a credit only to the other person.")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    run_command_blocks(
        pay_block('user1', 10, ['user0', 'user1']),
        wait_block(0.2),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 5),
    )


def test_case3(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe(
        "Paying multiple people including oneself should equally distribute debt.")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    run_command_blocks(
        pay_block('user0', 30, ['user0', 'user1', 'user2']),
        wait_block(0.2),
        assert_debts_equal_constant_block('user0', 'user1', 'user0', 10),
        assert_debts_equal_constant_block('user0', 'user2', 'user0', 10),
    )


def test_case4(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Paying oneself should change nothing")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    run_command_blocks(
        pay_block('user1', 10, ['user1']),
        wait_block(0.2),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 0),
    )


def test_case5(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Paying someone that then pays back should change nothing")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 10, ['user0']),
        wait_block(0.2),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 0),
        assert_debts_equal_constant_block('user0', 'user1', 'user0', 0),
    )


def test_case6(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe(
        "Paying someone that then pays back more should create a debt and a credit.")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 15, ['user0']),
        wait_block(0.2),
        assert_debts_equal_constant_block('user0', 'user0', 'user1', 5),
        assert_debts_equal_constant_block('user0', 'user1', 'user0', 0),
    )


def test_case7(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe(
        "A payment chain of A -> B -> C -> A with all amounts equal should result in no change.")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    users = get_users_from_graph(graph)

    run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 10, ['user2']),
        pay_block('user2', 10, ['user0']),
        wait_block(0.2),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
    )


def test_case8(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe(
        "A payment chain of A -> B -> C with all amounts equal should result in debt from A to C.")

    graph = build_graph([[0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0]])

    users = get_users_from_graph(graph)

    run_command_blocks(
        pay_block('user0', 10, ['user1']),
        pay_block('user1', 10, ['user2']),
        wait_block(0.2),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block(),
        assert_debts_equal_constant_block('user0', 'user2', 'user0', 10),
    )


def test_case9(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe(
        "After a long sequence of concurrent transactions, the graph should be correct and simplified.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    for i in range(100):
        random_user = random.choice(users)
        random_amount = random.randint(1, 10)
        random_benefitors = random.sample(users, random.randint(1, len(users)))
        actual_benefitors = [b for b in random_benefitors if b != random_user]
        total_random_amount = random_amount * len(actual_benefitors)
        run_command_blocks(
            pay_block(random_user, total_random_amount, random_benefitors))

    run_command_blocks(
        wait_block(1),
        get_debts_graph_block('user0', users),
        wait_block(0.2),
        assert_graph_is_simplified_block(),
    )


def test_case10(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("`Get` request with no user specified uses current user.")

    graph = build_graph([[0, 0, 20],
                         [0, 0, 10],
                         [0, 0, 0]])

    run_command_blocks(
        get_user_debts_block("user0")
    )


def test_case11(describe, build_graph, run_command_blocks, join_client, exit_client, set_should_skip_output_parsing):
    describe("Connecting and getting debts with invalid username should fail.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    client = join_client('unknown_user')

    try:
        run_command_blocks(get_user_debts_block(
            client.username, log_for_manual=True))
    except Exception as e:
        if type(e) == BrokenPipeError:
            set_should_skip_output_parsing(True)
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError because client should not have started due to wrong username, instead got {type(e)}"

    try:
        time.sleep(1)
        exit_client(client)
    except Exception as e:
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError, got {type(e)}"


def test_case12(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Getting debts for invalid username should fail.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    run_command_blocks(get_user_debts_block(
        "user0", user="unknown_user", log_for_manual=True))


def test_case13(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Connecting as unknown user and paying should fail.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    client = join_client('unknown_user')

    try:
        run_command_blocks(
            pay_block(client.username, 10, [
                      'user1', 'user2'], log_manual=True),
            wait_block(0.2),
            get_debts_graph_block('user0', users),
            assert_graph_is_simplified_block()
        )
    except Exception as e:
        if type(e) == BrokenPipeError:
            should_skip_output_parsing(True)
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError because client should not have started due to wrong username, instead got {type(e)}"

    time.sleep(3)

    try:
        exit_client(client)
    except Exception as e:
        assert type(
            e) == BrokenPipeError, f"Expected BrokenPipeError, got {type(e)}"


def test_case14(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Paying for an unknown user should fail.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    run_command_blocks(
        pay_block("user0", 10, ['user1', 'unknown_user',
                  'user2'], log_manual=True),
        wait_block(0.2),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block()
    )


def test_case15(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Paying with negative number should fail.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    run_command_blocks(
        pay_block("user0", -10, ['user1', 'user2'], log_manual=True),
        wait_block(0.2),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block()
    )


def test_case16(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe(
        "Paying with amount 0 should not change anything, and is allowed to fail.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    run_command_blocks(
        pay_block("user0", 0, ['user1', 'user2']),
        wait_block(0.2),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block()
    )


def test_case17(describe, build_graph, run_command_blocks, join_client, exit_client, should_skip_output_parsing):
    describe("Running wrong command should fail.")

    graph = build_graph([[0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0, 0]])

    users = get_users_from_graph(graph)

    run_command_blocks(
        wrong_command_block('user0', 'unknown_command', True),
        wait_block(0.2),
        get_debts_graph_block('user0', users),
        assert_graph_is_simplified_block()
    )

