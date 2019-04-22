class SingletonDecorator:
    # from: http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Singleton.html
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)
        return self.instance


class bcolors:
    # Obtained from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @ staticmethod
    def print(out, c):
        print(c + str(out) + bcolors.ENDC)
