import time
import math
from helpers import get_total_per_user
from log import log

from command_block import CommandBlock

"""
Given the output of a `get` command, return a dictionary of the form {username: amount, ...} where amount is the amount of money associated with that user. This can be used for both `get debts` and `get credit` commands.
"""
def parse_get_cmd_output(output):
    amounts = {}
    lines = output.strip().split('\n')
    sum = 0
    for i, line in enumerate(lines):
        if (':' not in line):
            continue
        username, amount = line.split(': ')
        try:
            amount = float(amount)
        except ValueError:
            assert False, "Amount cannot be parsed as a float"
        if (i == len(lines) - 1):
            assert line.startswith(
                'Total: '), "Last line of `get` must be the total"
            assert math.isclose(
                sum, amount), "Sum of amounts must be equal to the total"
        else:
            sum += amount
            amounts[username] = amount
    return amounts

def assert_debts_equal_credits_block(client, owing_user, owed_user):
    def assert_debts_equal_credits(owing_user,
                                   owed_user,
                                   get_debts_output,
                                   get_credits_output):
        owings_debts = parse_get_cmd_output(get_debts_output)
        oweds_credits = parse_get_cmd_output(get_credits_output)
        assert owing_user in oweds_credits, f"User {owing_user} owes money to {owed_user}, but is not listed in the credits of {owed_user}. Actual credits of {owed_user}: {oweds_credits}"
        assert owed_user in owings_debts, f"User {owed_user} that is owed money is not listed as debt to {owing_user}. Actual debts of {owing_user}: {owings_debts}"
        assert oweds_credits[owing_user] == owings_debts[
            owed_user], f"User {owing_user} has debt {owings_debts[owed_user]} to {owed_user}, but user {owed_user} has a credit of {oweds_credits[owing_user]} for {owing_user}"

    return CommandBlock(
        client,
        cmds=[
            f'get debts {owing_user}',
            f'get credit {owed_user}'
        ],
        post=lambda outputs, context: assert_debts_equal_credits(
            owing_user,
            owed_user,
            outputs[0],
            outputs[1]))


def assert_debts_equal_constant_block(client, owing_user, owed_user, expected_amount):
    def assert_debts_equal_credits(owing_user,
                                   owed_user,
                                   get_debts_output,
                                   get_credits_output):
        owings_debts = parse_get_cmd_output(get_debts_output)
        oweds_credits = parse_get_cmd_output(get_credits_output)
        if (expected_amount != 0):
            assert owing_user in oweds_credits, f"User {owing_user} owes money to {owed_user}, but is not listed in the credits of {owed_user}. Actual credits of {owed_user}: {oweds_credits}"
            assert owed_user in owings_debts, f"User {owed_user} that is owed money is not listed as debt to {owing_user}. Actual debts of {owing_user}: {owings_debts}"
            assert oweds_credits[owing_user] == owings_debts[
                owed_user], f"User {owing_user} has debt {owings_debts[owed_user]} to {owed_user}, but user {owed_user} has a credit of {oweds_credits[owing_user]} for {owing_user}"
            assert oweds_credits[owing_user] == expected_amount, f"Amount owed by {owing_user} to {owed_user} is {oweds_credits[owing_user]}, but expected {expected_amount}"
        else:
            assert owed_user not in owings_debts, f"User {owing_user} owes no money to {owed_user}, yet {owed_user} is listed as a debt of {owing_user}."
            assert owing_user not in oweds_credits, f"User {owing_user} owes no money to {owed_user}, yet {owing_user} is listed as a credit of {owed_user}."

    return CommandBlock(
        client,
        cmds=[
            f'get debts {owing_user}',
            f'get credit {owed_user}'
        ],
        post=lambda outputs, context: assert_debts_equal_credits(
            owing_user,
            owed_user,
            outputs[0],
            outputs[1]))



def pay_block(client, amount, all_benefitors, log_manual=False):
    def change_expected_totals(outputs, context):
        if log_manual:
            context["manual_outputs"].append(*outputs)
            return
        log(f"{client} pays {amount} for {all_benefitors}")
        expected_totals = context["expected_totals"]
        benefitors = [b for b in all_benefitors if b != client]
        if (benefitors != []):
            per_benefitor_amount = amount / len(all_benefitors)
            for benefitor in benefitors:
                expected_totals[benefitor] += per_benefitor_amount
            expected_totals[client] -= per_benefitor_amount * len(benefitors)
            log(f"Expected totals: {expected_totals}")

    return CommandBlock(
        client,
        cmds=[f'pay {amount} for {", ".join(all_benefitors)}'],
        post=lambda outputs, context: change_expected_totals(outputs, context))


def get_debts_graph_block(client, users):
    def construct_graph_from_outputs(outputs, context):
        graph = {}
        for i, user in enumerate(users):
            graph[user] = parse_get_cmd_output(outputs[i])
        context["graph"] = graph

    return CommandBlock(
        client,
        cmds=[f'get debts {user}' for user in users],
        post=lambda outputs, context: construct_graph_from_outputs(
            outputs, context)
    )



def wrong_command_block(client, command, log_for_manual=False):
    def post(outputs, context):
        if log_for_manual:
            context["manual_outputs"].append(*outputs)

    return CommandBlock(
        client,
        cmds=[command],
        post=post
    )

def assert_graph_is_simplified_block():
    # Test that no user is due and owed money
    # Test that the total number of edges is less than the total number of users
    def assert_graph_is_simplified(context):
        graph = context["graph"]
        assert graph != None, "graph is not in context when asserting that it is simplified"
        owing_users = set()
        owed_users = set()
        for user in graph.keys():
            for other_user, amount in graph[user].items():
                # no negative edges
                assert amount >= 0, f"User {user} has a negative debt to {other_user}"
                # no self edges
                assert user != other_user, f"User {user} has a debt to themself"
                owed_users.add(other_user)
                owing_users.add(user)
        # no user is both owing and owed money
        for owing_user in owing_users:
            assert owing_user not in owed_users, f"User {owing_user} is both owing and owed money"

        assert_graph_is_equivalent(context)

    def assert_graph_is_equivalent(context):
        actual_graph = context["graph"]
        expected_totals = context["expected_totals"]
        actual_totals = get_total_per_user(actual_graph)
        for user, expected_total in expected_totals.items():
            assert user in actual_totals, f"User {user} is not in the actual debt graph"
            assert math.isclose(
                expected_total, actual_totals[user], abs_tol=0.001), f"User {user} has a total debt of {actual_totals[user]}, but expected was {expected_total}"

    return CommandBlock(
        None,
        cmds=[],
        post=lambda _, context: assert_graph_is_simplified(context)
    )


def wait_block(duration):
    return CommandBlock(pre=lambda: time.sleep(duration))



def get_user_debts_block(client, user=None, log_for_manual=False):
    username = user if user else client

    def post(outputs, context):
        if log_for_manual:
            context["manual_outputs"].append(*outputs)
            return

        debts = parse_get_cmd_output(outputs[0])
        sum = 0
        for amount in debts.values():
            sum += amount
        assert math.isclose(sum, context["expected_totals"][username]
                            ), f"User {username} has a total debt of {sum}, but expected was {context['expected_totals'][username]}"

    command = f'get debts {user}' if user else 'get debts'

    return CommandBlock(
        client,
        cmds=[command],
        post=post
    )
