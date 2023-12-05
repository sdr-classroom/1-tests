
debug = False

def allow_debug_logs():
    global debug
    debug = True

def log(*args):
    global debug
    if (debug):
        print(*args)

def warn(*args):
    print("[WARNING] ", *args)

def fail(*args):
    print("[ERROR] ", *args)
    exit(1)