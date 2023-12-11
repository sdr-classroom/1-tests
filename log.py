import atexit

debug = False
logfile = None

def set_log_file(filename):
    global logfile
    if filename == None:
        exit_handler()
        logfile = None
        return
    logfile = open(filename, 'w')

def exit_handler():
    if logfile:
        logfile.close()

atexit.register(exit_handler)

def allow_debug_logs():
    global debug
    debug = True

def log(*args):
    global debug
    if (debug):
        print(*args)
    else:
        print(*args, file=logfile)

def warn(*args):
    print("[WARNING] ", *args)
    global debug
    if not debug:
        print("[WARNING] ", *args, file=logfile)

def fail(*args):
    print("[ERROR] ", *args)
    global debug
    if not debug:
        print("[ERROR] ", *args, file=logfile)
    exit(1)
