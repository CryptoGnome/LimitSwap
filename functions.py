import sys
import argparse
from datetime import datetime

# color styles
class style():  # Class of different text colours - default is white
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    INFO = '\033[36m'
    DEBUG = '\033[35m'

#
# START - COMMAND LINE ARGUMENTS
#
parser = argparse.ArgumentParser()

# USER COMMAND LINE ARGUMENTS
parser.add_argument("--pump", type=int, help="Holds the position as long as the price is going up. Sells when the price has gone down PUMP percent")
parser.add_argument("-p", "--password", type=str, help="Password to decrypt private keys (WARNING: your password could be saved in your command prompt history)")
parser.add_argument("--reject_already_existing_liquidity", action='store_true', help="If liquidity is found on the first check, reject that pair.")
parser.add_argument("-s", "--settings", type=str, help="Specify the file to user for settings (default: settings.json)", default="./settings.json")
parser.add_argument("-t", "--tokens", type=str, help="Specify the file to use for tokens to trade (default: tokens.json)", default="./tokens.json")
parser.add_argument("-pp", "--price_precision", type=str, help="Determine how many digits after comma you want the bot to display (default: 10)", default="10")
parser.add_argument("-v", "--verbose", action='store_true', help="Print detailed messages to stdout")
parser.add_argument("-pc", "--password_on_change", action='store_true', help="Ask user password again if you change tokens.json")
parser.add_argument("-sm", "--slow_mode", action='store_true', help="Bot will only check price 2 times/s. Use it if you're on a RPC with rate limit")

# DEVELOPER COMMAND LINE ARGUMENTS
# --dev - general argument for developer options
# --debug - to display the "printt_debug" lines
# --sim_buy tx - simulates the buying process, you must provide a transaction of a purchase of the token
# --sim_sell tx - simulates the buying process, you must provide a transaction of a purchase of the token
# --benchmark - run benchmark mode
parser.add_argument("--dev", action='store_true', help=argparse.SUPPRESS)
parser.add_argument("--sim_buy", type=str, help=argparse.SUPPRESS)
parser.add_argument("--sim_sell", type=str, help=argparse.SUPPRESS)
parser.add_argument("--debug", action='store_true', help=argparse.SUPPRESS)
parser.add_argument("--benchmark", action='store_true', help=argparse.SUPPRESS)
parser.add_argument("--analyze", type=str, help="analyze a Tx hash")

command_line_args = parser.parse_args()

#
# END - COMMAND LINE ARGUMENTS
#

# Function to cleanly exit on SIGINT
def signal_handler(sig, frame):
    sys.exit(0)

def timestamp():
    dt_object = datetime.now().strftime('%m-%d %H:%M:%S.%f')
    return dt_object