class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Outcome:
    def __init__(self, name, desc):
        self.test_name = name
        self.test_desc = desc


class Success(Outcome):
    def __init__(self, name, desc):
        super().__init__(name, desc)


class Failure(Outcome):
    def __init__(self, name, desc, msg):
        super().__init__(name, desc)
        self.msg = msg


class Manual(Outcome):
    def __init__(self, name, desc, outputs):
        super().__init__(name, desc)
        self.outputs = outputs


class OutcomeLogger:
    def __init__(self):
        self.logs = []

    def logFailure(self, name, desc, msg):
        print(f"{bcolors.FAIL}Test failed:{bcolors.ENDC} {name}, {desc}, {msg}")
        self.logs.append(Failure(name, desc, msg))

    def logSuccess(self, name, desc):
        self.logs.append(Success(name, desc))

    def logManual(self, name, desc, outputs):
        self.logs.append(Manual(name, desc, outputs))

    def get_logs(self):
        s = ""
        # Ask user to verify manual outputs.
        for i, log in enumerate(self.logs):
            if isinstance(log, Manual):
                print(
                    f"{bcolors.WARNING}[MANUAL]{bcolors.ENDC} {log.test_name}, {log.test_desc} :")
                newline = "\n"
                print(f"{bcolors.BOLD}{newline.join(log.outputs)}{bcolors.ENDC}")
                print("Is this correct? (y/[n])")
                answer = input().lower()
                if (answer == '' or answer == 'y'):
                    self.logs[i] = Success(log.test_name, log.test_desc)
                else:
                    self.logs[i] = Failure(
                        log.test_name, log.test_desc, "Outputs were manually verified and found to be incorrect: " + str(log.outputs))

        for log in self.logs:
            if isinstance(log, Failure):
                s += (
                    f"{bcolors.FAIL}[FAILURE]{bcolors.ENDC} {log.test_name}, {log.test_desc}\n{log.msg}") + "\n"
            elif isinstance(log, Manual):
                s += (
                    f"{bcolors.WARNING}[MANUAL]{bcolors.ENDC} {log.test_name}, {log.test_desc}\n{log.outputs}") + "\n"
            else:
                s += (
                    f"{bcolors.OKGREEN}[SUCCESS]{bcolors.ENDC} {log.test_name}, {log.test_desc}") + "\n"
        s += (f"{len(self.logs)} tests run, {len(list(filter(lambda x: isinstance(x, Failure), self.logs)))} failures.") + "\n"

        return s

    def print_logs(self):
        print(self.get_logs())

    def save_logs(self, filename):
        with open(filename, 'w') as f:
            f.write(self.get_logs())
