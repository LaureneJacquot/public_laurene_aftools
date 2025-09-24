import os 
from pathlib import Path

if "WORKPLACE" not in os.environ:
    raise Exception("WORKPLACE not set. Please specify a folder to work in.")
if "INTERPRO_RESULTS_DIR" not in os.environ:
    raise Exception("INTERPRO_RESULTS_DIR not set. Please specify a folder to access for Interpro results.")
if not "INTERPRO_COOKIES" in os.environ: 
    raise Exception("INTERPRO_COOKIES not set. Please specify a cookie to access Interpro.")


WORKPLACE = os.environ['WORKPLACE']
INTERPRO_RESULTS_DIR = os.environ['INTERPRO_RESULTS_DIR']
INTERPRO_COOKIES = os.environ.get('INTERPRO_COOKIES', '')


class my_colors : 
    HEADER = "\033[38;5;218m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[38;5;140m"
    OKGREEN = "\033[38;5;121m"
    WARNING = "\033[94m" #change this back to 93 
    FAIL = "\033[38;5;198m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Display :
    def __init__(self, quiet=False):
        self.quiet = quiet
        
    def __call__(self, label="", value="", color: my_colors=my_colors.OKCYAN, end=None, adjust=30) -> None:
        if self.quiet: return
        if label.isspace() or label == "":
            print(label)
            return
        label = label.ljust(adjust) if adjust > 0 else label
        print(f"{color}{label}{my_colors.ENDC}{value}",end=end)

    def header(self, *args, end="\n"): 
        self.__print(*args, color=my_colors.HEADER, end=end)

    def info(self, *args, end="\n"):
        self.__print(*args, color=my_colors.OKCYAN, end=end)

    def warning(self, *args, end="\n"):
        self.__print(*args, color=my_colors.WARNING, end=end)

    def error(self, *args, end="\n"):
        self.__print(*args, color=my_colors.FAIL, end=end)
    
    def print(self, *args, end="\n"):
        self.__print(*args, end=end)

    def __print(self, *args, color="", end):
        if self.quiet: return
        # check if all args are strings
        if all(isinstance(arg, str) for arg in args):
            msg = ",".join(list(args))
            print(f"{color}{msg}{my_colors.ENDC}", end=end)
        else:
            for arg in args:
                print(f"{color}{arg}{my_colors.ENDC}", end='')
            print(end, end=end)

    def ok(self, *args, end="\n"):
        self.__print(*args, color=my_colors.OKGREEN, end=end)



display = Display()