
debug = False

def allow_debug_logs():
    global debug
    debug = True

def log(*args):
    global debug
    if (debug):
        print(*args)