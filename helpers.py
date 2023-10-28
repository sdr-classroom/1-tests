"""
Given a graph of the form {user: {other_user: amount, ...}, ...}, return a list of all users mentionned in the graph.
"""
def get_users_from_graph(graph):
    users = set()
    for username, other_users in graph.items():
        users.add(username)
        for other_user in other_users.keys():
            users.add(other_user)
    # Sorted alphabetically
    users = list(users)
    users.sort()
    return users

"""
Given a graph of the form {user: {other_user: amount, ...}, ...}, return a dictionary of the form {user: total, ...} where total is the total amount of money that user owes to other users.
"""
def get_total_per_user(graph):
    totals = {}
    for username in get_users_from_graph(graph):
        totals[username] = 0
    for username, other_users in graph.items():
        for other_user, amount in other_users.items():
            totals[username] += amount
            totals[other_user] -= amount
    return totals