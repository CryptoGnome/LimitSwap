# -*- coding: utf-8 -*-
from toolz.functoolz import do
from web3 import Web3
from time import sleep, time
import json
from jsmin import jsmin
from decimal import Decimal
import os
import web3
from web3.exceptions import ABIFunctionNotFound, TransactionNotFound, BadFunctionCallOutput
import logging
from datetime import datetime
from functools import lru_cache
from cachetools import cached, LRUCache, TTLCache
from hexbytes import HexBytes
import sys
import requests
import cryptocode, re, pwinput
import argparse
import signal
import apprise


# DEVELOPER CONSIDERATIONS
#
#  =-= START README =-= START README =-= START README =-= START README =-= START README =-=
#    MAJOR TOKEN LOGIC CHANGE =-= MAJOR TOKEN LOGIC CHANGE =-= MAJOR TOKEN LOGIC CHANGE
#
#  There has been a major change to the way token logic is handled. Please review load_tokens_file
#  The program_defined_values allows us to move token specifica variables in and out of functions
#  Allowing us to do interesting things like continue to check for liquidity on one token while
#  Buying and Selling another.
#
#     MAJOR TOKEN LOGIC CHANGE =-= MAJOR TOKEN LOGIC CHANGE =-= MAJOR TOKEN LOGIC CHANGE
# =-= END README =-= END README =-= END README =-= END README =-= END README =-= END README  =-=
#
#
# USER INTERACTION - Do not depend on user interaction. If you develop a setting that is going to require
#    user interaction while the bot is running, warn the user before hand. Accept a value before the check
#    for liquidity, and provide a command line flag. Basically, provide ways for the bot to continue it's
#    entire process from buying all the way to selling multiple positions and multiple pairs with zero user
#    interaction.
#
# HANDLING NEW ENTRIES IN settings.json - When adding a new configuration item in settings.json be sure to
#    review comment "COMMAND LINE ARGUMENTS" and the functions load_settings_file and save_settings.
#    Do not assume a user has changed their settings.json file to work with the new version, your additions
#    should be backwards compatible and have safe default values if possible
#
# HANDLING NEW ENTRIES IN tokens.json - When adding a new configuration item in tokens.json be sure to
#    review comment "COMMAND LINE ARGUMENTS" and the functions load_tokens_file and save_tokens_file
#    Do not assume a user has changed their tokens.json file to work with the new version, your additions
#    should be backwards compatible and have safe default values if possible

#
# GLOBALS
#
# Global used for printt_repeating to track how many repeated messages have been printed to console
repeated_message_quantity = 0

# Global used for run()
tokens_json_already_loaded = 0

# Global used to save program_defined_values before update of tokens.json
_COST_PER_TOKEN_saved = []
_PREVIOUS_TOKEN_BALANCE_saved = []

# Global used for WATCH_STABLE_PAIRS
set_of_new_tokens = []

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


# Function to cleanly exit on SIGINT
def signal_handler(sig, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def timestamp():
    timestamp = time()
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object


#
# START - COMMAND LINE ARGUMENTS
#
parser = argparse.ArgumentParser()

# USER COMMAND LINE ARGUMENTS
parser.add_argument("--pump", type=int,  help="Holds the position as long as the price is going up. Sells when the price has gone down PUMP percent")
parser.add_argument("-p", "--password", type=str, help="Password to decrypt private keys (WARNING: your password could be saved in your command prompt history)")
parser.add_argument("--reject_already_existing_liquidity", action='store_true', help="If liquidity is found on the first check, reject that pair.")
parser.add_argument("-s", "--settings", type=str, help="Specify the file to user for settings (default: settings.json)",default="./settings.json")
parser.add_argument("-t", "--tokens", type=str, help="Specify the file to use for tokens to trade (default: tokens.json)", default="./tokens.json")
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

command_line_args = parser.parse_args()


#
# END - COMMAND LINE ARGUMENTS
#

def printt(*print_args, write_to_log=False):
    # Function: printt
    # ----------------------------
    # provides normal print() functionality but also prints our timestamp
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    print(timestamp(), ' '.join(map(str, print_args)))
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))


def printt_v(*print_args, write_to_log=False):
    # Function: printt
    # ----------------------------
    # provides normal print() functionality but also prints our timestamp and pays attention to user set verbosity.
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    if command_line_args.verbose == True:
        print(timestamp(), ' '.join(map(str, print_args)))
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))


def printt_err(*print_args, write_to_log=True):
    # Function: printt_err
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an error
    #
    # print_args - normal arguments that would be passed to the print() function
    # write_to_log - wether or not to write the same text to the log file
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.RED, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))


def printt_warn(*print_args, write_to_log=False):
    # Function: printt_warn
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display a warning
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.YELLOW, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))


def printt_ok(*print_args, write_to_log=False):
    # Function: printt_ok
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an OK text
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.GREEN, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))


def printt_info(*print_args, write_to_log=False):
    # Function: printt_info
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an INFO text in yellow
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.INFO, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))


def printt_debug(*print_args, write_to_log=False):
    # Function: printt_warn
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display a warning
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing
    
    if bot_settings['_NEED_NEW_LINE'] == True: print()
    if command_line_args.debug == True:
        print(timestamp(), " ", style.DEBUG, ' '.join(map(str, print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str, print_args)))


def printt_repeating(token_dict, message, print_frequency=500):
    #     Function: printt_r
    #     --------------------
    #     Function to manage a generic repeating message
    #
    #     token_dict - one element of the tokens{} dictionary
    #     message - the message to be printed
    #
    #     returns: nothing
    
    global repeated_message_quantity

    if message == token_dict['_LAST_MESSAGE'] and settings['VERBOSE_PRICING'] == 'false' and print_frequency >= repeated_message_quantity:
        bot_settings['_NEED_NEW_LINE'] = False
        repeated_message_quantity += 1
    else:
        printt_err(message, write_to_log=False)
        repeated_message_quantity = 0
    
    token_dict['_LAST_MESSAGE'] = message


def printt_sell_price(token_dict, token_price):
    #     Function: printt_sell_price
    #     --------------------
    #     Formatted buying information
    #
    #     token_dict - one element of the tokens{} dictionary
    #     token_price - the current price of the token we want to buy
    #
    #     returns: nothing
    printt_debug(token_dict)
    printt_debug("token_dict['_TRADING_IS_ON'] 266:", token_dict['_TRADING_IS_ON'], "for token:", token_dict['SYMBOL'])
    printt_debug("_PREVIOUS_QUOTE :", token_dict['_PREVIOUS_QUOTE'], "for token:", token_dict['SYMBOL'])
    
    if token_dict['USECUSTOMBASEPAIR'] == 'false':
        price_message = token_dict['_PAIR_SYMBOL'] + " Price: " + "{0:.24f}".format(token_price) + " " + base_symbol + " - Buy:" + str(token_dict['BUYPRICEINBASE'])
    
    else:
        price_message = token_dict['_PAIR_SYMBOL'] + " Price: " + "{0:.24f}".format(token_price) + " " + token_dict['BASESYMBOL'] + " - Buy:" + str(token_dict['BUYPRICEINBASE'])
    
    price_message = price_message + " Sell:" + str(token_dict['_CALCULATED_SELLPRICEINBASE']) + " Stop:" + str(token_dict['_CALCULATED_STOPLOSSPRICEINBASE'])
    # price_message = price_message + " ATH:" + "{0:.24f}".format(token_dict['_ALL_TIME_HIGH']) + " ATL:" + "{0:.24f}".format(token_dict['_ALL_TIME_LOW'])

    if token_dict['USECUSTOMBASEPAIR'] == 'false':
        price_message = price_message + " - Token balance: " + str("{0:.4f}".format(token_dict['_TOKEN_BALANCE'])) + " (= " + "{0:.2f}".format(float(token_price) * float(token_dict['_BASE_PRICE']) * float(token_dict['_TOKEN_BALANCE'])) + " $)"
    else:
        price_message = price_message + " - Token balance: " + str("{0:.4f}".format(token_dict['_TOKEN_BALANCE'])) + " (= " + "{0:.2f}".format(float(token_price) * float(token_dict['_TOKEN_BALANCE'])) + " " + token_dict['BASESYMBOL'] + ")"


    if price_message == token_dict['_LAST_PRICE_MESSAGE'] and settings['VERBOSE_PRICING'] == 'false':
        bot_settings['_NEED_NEW_LINE'] = False
    elif token_price > token_dict['_PREVIOUS_QUOTE']:
        printt_ok(price_message)
        token_dict['_TRADING_IS_ON'] = True
    elif token_price < token_dict['_PREVIOUS_QUOTE']:
        printt_err(price_message)
        token_dict['_TRADING_IS_ON'] = True
    else:
        printt(price_message)
    
    token_dict['_LAST_PRICE_MESSAGE'] = price_message


def printt_buy_price(token_dict, token_price):
    #     Function: printt_buy_price
    #     --------------------
    #     Formatted buying information
    #
    #     token_dict - one element of the tokens{} dictionary
    #     token_price - the current price of the token we want to buy
    #
    #     returns: nothing
    
    printt_sell_price(token_dict, token_price)


def load_settings_file(settings_path, load_message=True):
    # Function: load_settings_file
    # ----------------------------
    # loads the settings file defined by command_line_args.settings, sets sane defaults if variables aren't found in settings file
    # exits with an error message if necessary variables are not found in the settings files
    #
    # settings_path = the path of the file to load settings from
    #
    # returns: a dictionary with the settings from the file loaded
    
    if load_message == True:
        print(timestamp(), "Loading settings from", settings_path)

    with open(settings_path, ) as js_file:
        f = jsmin(js_file.read())
    all_settings = json.loads(f)
    
    
    settings = bot_settings = {}
    
    # Walk all settings and find the first exchange settings. This will keep us backwards compatible
    for settings_set in all_settings:
        if 'EXCHANGE' in settings_set:
            settings = settings_set
        elif 'EXCHANGE' not in settings_set:
            bot_settings = settings_set
    
    #
    # INITIALIZE BOT SETTINGS
    #
    
    if len(bot_settings) > 0:
        print(timestamp(), "Global settings detected in settings.json.")
    
    # There are values that we will set internally. They must all begin with _
    # _NEED_NEW_LINE - set to true when the next printt statement will need to print a new line before data
    
    default_true_settings = [
    ]
    
    program_defined_values = {
        '_NEED_NEW_LINE': False
    }
    
    for default_true in default_true_settings:
        if default_true not in settings:
            print(timestamp(), default_true,
                  "not found in settings.json, settings a default value of false.")
            bot_settings[default_true] = "true"
        else:
            bot_settings[default_true] = bot_settings[default_true].lower()
    for value in program_defined_values:
        if value not in bot_settings: bot_settings[value] = program_defined_values[value]
    
    #
    # INITIALIZE EXCHANGE SETTINGS
    #
    
    if len(settings) == 0:
        print(timestamp(), "No exchange settings found in settings.json. Exiting.")
        exit(11)
    
    default_false_settings = [
        'UNLIMITEDSLIPPAGE',
        'USECUSTOMNODE',
        'PASSWORD_ON_CHANGE',
        'SLOW_MODE',
        'ENABLE_APPRISE_NOTIFICATIONS'
    ]
    
    default_true_settings = [
        'PREAPPROVE',
        'VERBOSE_PRICING'
    ]
    
    # These settings must be defined by the user and we will lower() them
    required_user_settings = [
        'EXCHANGE'
    ]
    
    for default_false in default_false_settings:
        if default_false not in settings:
            print(timestamp(), default_false, "not found in settings.json, settings a default value of false.")
            settings[default_false] = "false"
        else:
            settings[default_false] = settings[default_false].lower()
    
    for default_true in default_true_settings:
        if default_true not in settings:
            print(timestamp(), default_true, "not found in settings.json, settings a default value of true.")
            settings[default_true] = "true"
        else:
            settings[default_true] = settings[default_true].lower()
    
    # Keys that must be set
    for required_setting in required_user_settings:
        if required_setting not in settings:
            print(timestamp(), "ERROR:", required_setting, "not found in settings.json")
            exit(-1)
        else:
            settings[required_setting] = settings[required_setting].lower()
    
    return bot_settings, settings


def apprise_notification(token, parameter):
    printt_debug("ENTER pushsafer_notification")

    apobj = apprise.Apprise()

    if settings['APPRISE_PARAMETERS'] == "":
        printt_err("APPRISE_PARAMETERS setting is missing - please enter it")
        return
    
    apprise_parameter = settings['APPRISE_PARAMETERS']
    printt_debug("apprise_parameter:", apprise_parameter)
    for key in apprise_parameter:
        apobj.add(key)
    
    try:
        if parameter == 'buy_success':
            message = "SUCCESS : your " + token['SYMBOL'] + " buy Tx is confirmed. Price:" + str("{:.10f}".format(token['_QUOTE']))
            title = "BUY Success"
            
            apobj.notify(
                body=message,
                title=title,
            )
            
        elif parameter == 'buy_failure':
            message = "FAILURE : your " + token['SYMBOL'] + " buy Tx failed"
            title = "BUY Failure"
            
            apobj.notify(
                body=message,
                title=title,
            )

        elif parameter == 'sell_success':
            message = "SUCCESS : your " + token['SYMBOL'] + " sell Tx is confirmed. Price:" + str("{:.10f}".format(token['_QUOTE']))
            title = "SELL Success"
            
            apobj.notify(
                body=message,
                title=title,
            )

        elif parameter == 'sell_failure':
            message = "FAILURE : your " + token['SYMBOL'] + " sell Tx failed"
            title = "SELL Failure"

            apobj.notify(
                body=message,
                title=title,
            )
            
            
    except Exception as ee:
        printt_err("APPRISE - an Exception occured : check your logs")
        logging.exception(ee)


def get_file_modified_time(file_path, last_known_modification=0):
    modified_time = os.path.getmtime(file_path)
    
    if modified_time != 0 and last_known_modification == modified_time:
        printt_debug(file_path, "has been modified.")
    
    return last_known_modification


def reload_bot_settings(bot_settings_dict):
    # Function: reload_settings_file()
    # ----------------------------
    # Reloads and/or initializes settings that need to be updated when run is re-executed.
    # See load_settings_file for the details of these attributes
    #
    program_defined_values = {
        '_NEED_NEW_LINE': False,
        '_QUERIES_PER_SECOND': 'Unknown'
    }
    
    for value in program_defined_values:
        bot_settings_dict[value] = program_defined_values[value]


def load_tokens_file(tokens_path, load_message=True):
    # Function: load_tokens_File
    # ----------------------------
    # loads the token definition file defined by command_line_args.settings, sets sane defaults if variables aren't found in settings file
    # exits with an error message if necessary variables are not found in the settings files
    #
    # IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE
    # Any additional options added to this function must also be considered for change in reload_tokens_file()
    #
    # tokens_path: the path of the file to load tokens from
    # load_message: if true we print to stdout that we're loading settings from the file
    # last_modified: perform this function only if he file has been modified since this date
    #
    # returns: 1. a dictionary of dictionaries in json format containing details of the tokens we're rading
    #          2. the timestamp for the last modification of the file
    
    # Any new token configurations that are added due to "WATCH_STABLES_PAIRS" configuration will be added to this array. After we are done
    # loading all settings from tokens.json, we'll append this list to the token list
    
    printt_debug("ENTER load_tokens_file")
    
    global set_of_new_tokens

    if load_message == True:
        print(timestamp(), "Loading tokens from", tokens_path)

    with open(tokens_path, ) as js_file:
        t = jsmin(js_file.read())
    tokens = json.loads(t)

    required_user_settings = [
        'ADDRESS',
        'BUYAMOUNTINBASE',
        'BUYPRICEINBASE',
        'SELLPRICEINBASE'
    ]
    
    default_true_settings = [
        'LIQUIDITYINNATIVETOKEN'
    ]
    
    default_false_settings = [
        'ENABLED',
        'USECUSTOMBASEPAIR',
        'HASFEES',
        'RUGDOC_CHECK',
        'MULTIPLEBUYS',
        'KIND_OF_SWAP',
        'ALWAYS_CHECK_BALANCE',
        'WAIT_FOR_OPEN_TRADE',
        'WATCH_STABLES_PAIRS'
    ]
    
    default_value_settings = {
        'SLIPPAGE': 49,
        'BUYAMOUNTINTOKEN': 0,
        'MAXTOKENS': 0,
        'MOONBAG': 0,
        'MINIMUM_LIQUIDITY_IN_DOLLARS': 10000,
        'MAX_BASE_AMOUNT_PER_EXACT_TOKENS_TRANSACTION': 0.5,
        'SELLAMOUNTINTOKENS': 'all',
        'GAS': 8,
        'MAX_GAS': 99999,
        'BOOSTPERCENT': 50,
        'GASLIMIT': 1000000,
        'BUYAFTER_XXX_SECONDS': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX': 0,
        'MAX_FAILED_TRANSACTIONS_IN_A_ROW': 2,
        'MAX_SUCCESS_TRANSACTIONS_IN_A_ROW': 2,
        'GASPRIORITY_FOR_ETH_ONLY': 1.5,
        'STOPLOSSPRICEINBASE': 0,
        'BUYCOUNT': 0,
        '_STABLE_BASES': {}
    }
    
    # There are values that we will set internally. They must all begin with _
    # _LIQUIDITY_CHECKED    - false if we have yet to check liquidity for this token
    # _INFORMED_SELL        - set to true when we've already informed the user that we're selling this position
    # _LIQUIDITY_READY      - a flag to test if we've found liquidity for this pair
    # _LIQUIDITY_CHECKED    - a flag to test if we've check for the amount of liquidity for this pair
    # _INFORMED_SELL        - a flag to store that we've printed to console that we are going to be selling the position
    # _REACHED_MAX_TOKENS   - flag to look at to determine if the user's wallet has reached the maximum number of flags
    #                         this flag is used for conditionals throughout the run of this bot. Be sure to set this
    #                         flag after enough tokens that brings the number of token up to the MAXTOKENS. In other words
    #                         done depend on (if MAXTOKENS < _TOKEN_BALANCE) conditionals
    # _GAS_TO_USE           - the amount of gas the bot has estimated it should use for the purchase of a token
    #                         this number is calculated every bot start up
    # _FAILED_TRANSACTIONS  - the number of times a transaction has failed for this token
    # _SUCCESS_TRANSACTIONS - the number of times a transaction has succeeded for this token
    # _REACHED_MAX_SUCCESS_TX  - flag to look at to determine if the user's wallet has reached the maximum number of flags
    #                         this flag is used for conditionals throughout the run of this bot. Be sure to set this
    #                         flag after enough tokens that brings the number of token up to the MAX_SUCCESS_TRANSACTIONS_IN_A_ROW. In other words
    #                         done depend on (if MAX_SUCCESS_TRANSACTIONS_IN_A_ROW < _REACHED_MAX_SUCCESS_TX) conditionals
    # _TRADING_IS_ON        - defines if trading is ON of OFF on a token. Used with WAIT_FOR_OPEN_TRADE parameter
    # _RUGDOC_DECISION      - decision of the user after RugDoc API check
    # _TOKEN_BALANCE        - the number of traded tokens the user has in his wallet
    # _PREVIOUS_TOKEN_BALANCE - the number of traded tokens the user has in his wallet before BUY order
    # _BASE_BALANCE         - balance of Base token, calculated at bot launch and after a BUY/SELL
    # _BASE_PRICE           - price of Base token, calculated at bot launch with calculate_base_price
    # _BASE_USED_FOR_TX     - amount of base balance used to make the Tx transaction
    # _PAIR_TO_DISPLAY      - token symbol / base symbol
    # _CUSTOM_BASE_BALANCE  - balance of Custom Base token, calculated at bot launch and after a BUY/SELL
    # _QUOTE                - holds the token's quote
    # _PREVIOUS_QUOTE       - holds the ask price for a token the last time a price was queried, this is used
    #                         to determine the direction the market is going
    # _COST_PER_TOKEN       - the calculated/estimated price the bot paid for the number of tokens it traded
    # _CALCULATED_SELLPRICEINBASE           - the calculated sell price created with build_sell_conditions()
    # _CALCULATED_STOPLOSSPRICEINBASE       - the calculated stoploss price created with build_sell_conditions()
    # _ALL_TIME_HIGH        - the highest price a token has had since the bot was started
    # _ALL_TIME_LOW         - the lowest price a token has had since the bot was started
    # _CONTRACT_DECIMALS    - the number of decimals a contract uses. Used to speed up some of our processes
    #                         instead of querying the contract for the same information repeatedly.
    # _BASE_DECIMALS        - the number of decimals of custom base pair. Used to speed up some of our processes
    #                         instead of querying the contract for the same information repeatedly.
    # _WETH_DECIMALS        - the number of decimals of weth. Used to speed up some of our processes
    #                         instead of querying the contract for the same information repeatedly.
    # _LAST_PRICE_MESSAGE   - a copy of the last pricing message printed to console, used to determine the price
    #                         should be printed again, or just a dot
    # _LAST_MESSAGE         - a place to store a copy of the last message printed to conside, use to avoid
    #                         repeated liquidity messages
    # _GAS_IS_CALCULATED    - if gas needs to be calculated by wait_for_open_trade, this parameter is set to true
    # _EXCHANGE_BASE_SYMBOL - this is the symbol for the base that is used by the exchange the token is trading on
    # _PAIR_SYMBOL          - the symbol for this TOKEN/BASE pair

    program_defined_values = {
        '_LIQUIDITY_READY': False,
        '_LIQUIDITY_CHECKED': False,
        '_INFORMED_SELL': False,
        '_REACHED_MAX_TOKENS': False,
        '_TRADING_IS_ON': False,
        '_RUGDOC_DECISION': "",
        '_GAS_TO_USE': 0,
        '_GAS_IS_CALCULATED': False,
        '_FAILED_TRANSACTIONS': 0,
        '_SUCCESS_TRANSACTIONS': 0,
        '_REACHED_MAX_SUCCESS_TX': False,
        '_TOKEN_BALANCE': 0,
        '_PREVIOUS_TOKEN_BALANCE': 0,
        '_BASE_BALANCE': 0,
        '_BASE_PRICE': calculate_base_price(),
        '_BASE_USED_FOR_TX': 0,
        '_PAIR_TO_DISPLAY': "Pair",
        '_CUSTOM_BASE_BALANCE': 0,
        '_QUOTE': 0,
        '_PREVIOUS_QUOTE': 0,
        '_ALL_TIME_HIGH': 0,
        '_COST_PER_TOKEN': 0,
        '_CALCULATED_SELLPRICEINBASE': 99999,
        '_CALCULATED_STOPLOSSPRICEINBASE': 0,
        '_ALL_TIME_LOW': 0,
        '_CONTRACT_DECIMALS': 0,
        '_BASE_DECIMALS': 0,
        '_WETH_DECIMALS': 0,
        '_LAST_PRICE_MESSAGE': 0,
        '_LAST_MESSAGE' : 0,
        '_FIRST_SELL_QUOTE' : 0,
        '_BUILT_BY_BOT' : False,
        '_EXCHANGE_BASE_SYMBOL' : settings['_EXCHANGE_BASE_SYMBOL'],
        '_PAIR_SYMBOL' : ''
    }
    
    for token in tokens:
        
        # Keys that must be set
        for required_key in required_user_settings:
            if required_key not in token:
                printt_err(required_key, "not found in configuration file in configuration for to token", token['SYMBOL'])
                printt_err("Be careful, sometimes new parameter are added : please check default tokens.json file")
                sleep(20)
                exit(-1)
        
        for default_false in default_false_settings:
            if default_false not in token:
                printt_v(default_false, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of false")
                token[default_false] = "false"
            else:
                token[default_false] = token[default_false].lower()
        
        for default_true in default_true_settings:
            if default_true not in token:
                printt_v(default_true, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of true")
                token[default_true] = "true"
            else:
                token[default_true] = token[default_true].lower()
        
        for default_key in default_value_settings:
            if default_key not in token:
                printt_v(default_key, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a value of", default_value_settings[default_key])
                token[default_key] = default_value_settings[default_key]
            elif default_key == 'SELLAMOUNTINTOKENS':
                default_value_settings[default_key] = default_value_settings[default_key].lower()
        
        # Set program values only if they haven't been set already
        if '_LIQUIDITY_READY' not in token:
            for value in program_defined_values:
                token[value] = program_defined_values[value]
        
        for key in token:
            if (isinstance(token[key], str)):
                if re.search(r'^\d*\.\d+$', str(token[key])):
                    token[key] = float(token[key])
                elif re.search(r'^\d+$', token[key]):
                    token[key] = int(token[key])
    
        if token['WATCH_STABLES_PAIRS'] == 'true' and token['USECUSTOMBASEPAIR'] == 'false':
            if token['_COST_PER_TOKEN'] == 0 :
                build_sell_conditions(token, 'before_buy')
            else:
                build_sell_conditions(token, 'after_buy')


            for new_token_dict in build_extended_base_configuration(token):
                set_of_new_tokens.append(new_token_dict)
        elif token['WATCH_STABLES_PAIRS'] == 'true':
            printt("")
            printt_warn ("Ignoring WATCH_STABLES_PAIRS", "for", token['SYMBOL'], ": WATCH_STABLES_PAIRS = true and USECUSTOMBASEPAIR = true is unsupported.")
            printt("")


        if token['USECUSTOMBASEPAIR'] == 'false':
            token['_PAIR_SYMBOL'] = token['SYMBOL'] + '/' + token['_EXCHANGE_BASE_SYMBOL']
        else:
            token['_PAIR_SYMBOL'] = token['SYMBOL'] + '/' + token['BASESYMBOL']
    # Add any tokens generated by "WATCH_STABLES_PAIRS" to the tokens list.
    for token_dict in set_of_new_tokens:
        tokens.append(token_dict)
    return tokens


def reload_tokens_file(tokens_path, load_message=True):
    # Function: reload_tokens_File
    # ----------------------------
    # loads the token definition file defined by command_line_args.settings, sets sane defaults if variables aren't found in settings file
    # exits with an error message if necessary variables are not found in the settings files
    #
    # IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE - IMPORTANT NOTE
    # Any additional options added to this function must also be considered for change in reload_tokens_file()
    #
    # tokens_path: the path of the file to load tokens from
    # load_message: if true we print to stdout that we're loading settings from the file
    # last_modified: perform this function only if he file has been modified since this date
    #
    # returns: 1. a dictionary of dictionaries in json format containing details of the tokens we're rading
    #          2. the timestamp for the last modification of the file
    
    # Any new token configurations that are added due to "WATCH_STABLES_PAIRS" configuration will be added to this array. After we are done
    # loading all settings from tokens.json, we'll append this list to the token list
    
    printt_debug("ENTER reload_tokens_file")
    
    global _COST_PER_TOKEN_saved
    global _PREVIOUS_TOKEN_BALANCE_saved
    global set_of_new_tokens

    set_of_new_tokens = []

    if load_message == True:
        print(timestamp(), "Reloading tokens from", tokens_path)

    with open(tokens_path, ) as js_file:
        t = jsmin(js_file.read())
    tokens = json.loads(t)
    
    printt_debug("tokens1:", tokens)

    required_user_settings = [
        'ADDRESS',
        'BUYAMOUNTINBASE',
        'BUYPRICEINBASE',
        'SELLPRICEINBASE'
    ]

    default_true_settings = [
        'LIQUIDITYINNATIVETOKEN'
    ]

    default_false_settings = [
        'ENABLED',
        'USECUSTOMBASEPAIR',
        'HASFEES',
        'RUGDOC_CHECK',
        'MULTIPLEBUYS',
        'KIND_OF_SWAP',
        'ALWAYS_CHECK_BALANCE',
        'WAIT_FOR_OPEN_TRADE',
        'WATCH_STABLES_PAIRS'
    ]

    default_value_settings = {
        'SLIPPAGE': 49,
        'BUYAMOUNTINTOKEN': 0,
        'MAXTOKENS': 0,
        'MOONBAG': 0,
        'MINIMUM_LIQUIDITY_IN_DOLLARS': 10000,
        'MAX_BASE_AMOUNT_PER_EXACT_TOKENS_TRANSACTION': 0.5,
        'SELLAMOUNTINTOKENS': 'all',
        'GAS': 8,
        'MAX_GAS': 99999,
        'BOOSTPERCENT': 50,
        'GASLIMIT': 1000000,
        'BUYAFTER_XXX_SECONDS': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX': 0,
        'XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX': 0,
        'MAX_FAILED_TRANSACTIONS_IN_A_ROW': 2,
        'MAX_SUCCESS_TRANSACTIONS_IN_A_ROW': 2,
        'GASPRIORITY_FOR_ETH_ONLY': 1.5,
        'STOPLOSSPRICEINBASE': 0,
        'BUYCOUNT': 0,
        '_STABLE_BASES': {}
    }
    
    program_defined_values = {
        '_LIQUIDITY_READY': False,
        '_LIQUIDITY_CHECKED': False,
        '_INFORMED_SELL': False,
        '_REACHED_MAX_TOKENS': False,
        '_TRADING_IS_ON': False,
        '_RUGDOC_DECISION': "",
        '_GAS_TO_USE': 0,
        '_GAS_IS_CALCULATED': False,
        '_FAILED_TRANSACTIONS': 0,
        '_SUCCESS_TRANSACTIONS': 0,
        '_REACHED_MAX_SUCCESS_TX': False,
        '_TOKEN_BALANCE': 0,
        '_PREVIOUS_TOKEN_BALANCE': _PREVIOUS_TOKEN_BALANCE_saved,
        '_BASE_BALANCE': 0,
        '_BASE_PRICE': 0,
        '_BASE_USED_FOR_TX': 0,
        '_PAIR_TO_DISPLAY': "Pair",
        '_CUSTOM_BASE_BALANCE': 0,
        '_QUOTE': 0,
        '_PREVIOUS_QUOTE': 0,
        '_ALL_TIME_HIGH': 0,
        '_COST_PER_TOKEN': _COST_PER_TOKEN_saved,
        '_CALCULATED_SELLPRICEINBASE': 99999,
        '_CALCULATED_STOPLOSSPRICEINBASE': 0,
        '_ALL_TIME_LOW': 0,
        '_CONTRACT_DECIMALS': 0,
        '_BASE_DECIMALS': 0,
        '_WETH_DECIMALS': 0,
        '_LAST_PRICE_MESSAGE': 0,
        '_LAST_MESSAGE': 0,
        '_FIRST_SELL_QUOTE': 0,
        '_BUILT_BY_BOT': False,
        '_EXCHANGE_BASE_SYMBOL': settings['_EXCHANGE_BASE_SYMBOL'],
        '_PAIR_SYMBOL': ''
    }

    for token in tokens:
    
        # Keys that must be set
        for required_key in required_user_settings:
            if required_key not in token:
                printt_err(required_key, "not found in configuration file in configuration for to token", token['SYMBOL'])
                printt_err("Be careful, sometimes new parameter are added : please check default tokens.json file")
                sleep(20)
                exit(-1)
    
        for default_false in default_false_settings:
            if default_false not in token:
                printt_v(default_false, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of false")
                token[default_false] = "false"
            else:
                token[default_false] = token[default_false].lower()
    
        for default_true in default_true_settings:
            if default_true not in token:
                printt_v(default_true, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a default value of true")
                token[default_true] = "true"
            else:
                token[default_true] = token[default_true].lower()
    
        for default_key in default_value_settings:
            if default_key not in token:
                printt_v(default_key, "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a value of", default_value_settings[default_key])
                token[default_key] = default_value_settings[default_key]
            elif default_key == 'SELLAMOUNTINTOKENS':
                default_value_settings[default_key] = default_value_settings[default_key].lower()
    
        # Set program values only if they haven't been set already
        if '_LIQUIDITY_READY' not in token:
            for value in program_defined_values:
                token[value] = program_defined_values[value]
    
        for key in token:
            if (isinstance(token[key], str)):
                if re.search(r'^\d*\.\d+$', str(token[key])):
                    token[key] = float(token[key])
                elif re.search(r'^\d+$', token[key]):
                    token[key] = int(token[key])
    
        if token['WATCH_STABLES_PAIRS'] == 'true' and token['USECUSTOMBASEPAIR'] == 'false':
            if token['_COST_PER_TOKEN'] == 0 :
                build_sell_conditions(token, 'before_buy')
            else:
                build_sell_conditions(token, 'after_buy')


            for new_token_dict in build_extended_base_configuration(token):
                set_of_new_tokens.append(new_token_dict)
        elif token['WATCH_STABLES_PAIRS'] == 'true':
            printt_warn("Ignoring WATCH_STABLES_PAIRS", "for", token['SYMBOL'], ": WATCH_STABLES_PAIRS = true and USECUSTOMBASEPAIR = true is unsupported.")
    
        if token['USECUSTOMBASEPAIR'] == 'false':
            token['_PAIR_SYMBOL'] = token['SYMBOL'] + '/' + token['_EXCHANGE_BASE_SYMBOL']
        else:
            token['_PAIR_SYMBOL'] = token['SYMBOL'] + '/' + token['BASESYMBOL']

    # Add any tokens generated by "WATCH_STABLES_PAIRS" to the tokens list.
    for token_dict in set_of_new_tokens:
        tokens.append(token_dict)

    printt_debug("EXIT reload_tokens_file")
    return tokens




def token_list_report(tokens, all_pairs=False):
    # Function: token_list_report
    # ----------------------------
    # takes our tokens and reports on the ones that are still enabled
    #
    # tokens: array of dicts representing the tokens to trade in the format absorbed by load_tokens_file
    # all_pairs: If False (default) reports all enabled pairs - if True reports on all pairs
    #
    # returns: an array of all SYMBOLS we are trading
    
    token_list = ""
    tokens_trading = 0
    
    for token in tokens:
        if all_pairs == True or token["ENABLED"] == 'true':
            tokens_trading += 1
            if token_list != "":
                token_list = token_list + " "
            if token['USECUSTOMBASEPAIR'] == 'false':
                token_list = token_list + token['_PAIR_SYMBOL']
            else:
                token_list = token_list + token['_PAIR_SYMBOL']
    
    if all_pairs == False:
        printt("Quantity of tokens attempting to trade:", tokens_trading, "(" , token_list , ")")
    else:
        printt("Quantity of tokens attempting to trade:", len(tokens), "(", token_list, ")")


def check_release():
    try:
        url = 'https://api.github.com/repos/tsarbuig/LimitSwap/releases/latest'
        r = (requests.get(url).json()['tag_name'] + '\n')
        printt("Checking Latest Release Version on Github, Please Make Sure You are Staying Updated = ", r, write_to_log=True)
    except Exception:
        r = "github api down, please ignore"
    
    return r


"""""""""""""""""""""""""""
//PRELOAD
"""""""""""""""""""""""""""
print(timestamp(), "Preloading Data")
bot_settings, settings = load_settings_file(command_line_args.settings)

directory = './abi/'
filename = "standard.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    standardAbi = json.load(json_file)

directory = './abi/'
filename = "lp.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    lpAbi = json.load(json_file)

directory = './abi/'
filename = "router.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    routerAbi = json.load(json_file)

directory = './abi/'
filename = "factory2.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    factoryAbi = json.load(json_file)

directory = './abi/'
filename = "koffee.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    koffeeAbi = json.load(json_file)

directory = './abi/'
filename = "pangolin.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    pangolinAbi = json.load(json_file)

directory = './abi/'
filename = "joeRouter.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    joeRouter = json.load(json_file)

directory = './abi/'
filename = "bakeryRouter.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    bakeryRouter = json.load(json_file)

directory = './abi/'
filename = "protofiabi.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    protofiabi = json.load(json_file)
    
directory = './abi/'
filename = "protofirouter.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    protofirouter = json.load(json_file)

    
"""""""""""""""""""""""""""
// LOGGING
"""""""""""""""""""""""""""
os.makedirs('./logs', exist_ok=True)

# define dd/mm/YY date to create  logging files with date of the day
# get current date and time
current_datetime = datetime.today().strftime("%Y-%m-%d")
str_current_datetime = str(current_datetime)
# create an LOGS file object along with extension
file_name = "./logs/logs-" + str_current_datetime + ".log"
if not os.path.exists(file_name):
    open(file_name, 'w').close()
    
# create an EXCEPTIONS file object along with extension
file_name2 = "./logs/exceptions-" + str_current_datetime + ".log"
if not os.path.exists(file_name2):
    open(file_name2, 'w').close()
    
log_format = '%(levelname)s: %(asctime)s %(message)s'
logging.basicConfig(filename=file_name,
                    level=logging.INFO,
                    format=log_format)

logger1 = logging.getLogger('1')
logger1.addHandler(logging.FileHandler(file_name2))

printt("**********************************************************************************************************************", write_to_log=True)
printt("For Help & To Learn More About how the bot works please visit our wiki here: https://cryptognome.gitbook.io/limitswap/", write_to_log=False)
printt("**********************************************************************************************************************", write_to_log=False)

# Check for version
#
version = '4.2.1.2'
printt("YOUR BOT IS CURRENTLY RUNNING VERSION ", version, write_to_log=True)
check_release()

"""""""""""""""""""""""""""
//NETWORKS SELECT
"""""""""""""""""""""""""""

if settings['EXCHANGE'] == 'pancakeswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
        print(timestamp(), 'Using custom node.')
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"
    
    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)
    
    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Binance Smart Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    
    if settings['EXCHANGEVERSION'] == "1":
        routerAddress = Web3.toChecksumAddress("0x05fF2B0DB69458A0750badebc4f9e13aDd608C7F")
        factoryAddress = Web3.toChecksumAddress("0xbcfccbde45ce874adcb698cc183debcf17952812")
    elif settings['EXCHANGEVERSION'] == "2":
        routerAddress = Web3.toChecksumAddress("0x10ED43C718714eb63d5aA57B78B54704E256024E")
        factoryAddress = Web3.toChecksumAddress("0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73")
    
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
    base_symbol = "BNB "
    rugdocchain = '&chain=bsc'
    modified = False

    settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier' : 0},
                                 'BUSD':{ 'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier' : 0},
                                 'USDC':{ 'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier' : 0}}

if settings['EXCHANGE'].lower() == 'pancakeswaptestnet':
    
    if settings['USECUSTOMNODE'].lower() == 'true':
        my_provider = settings['CUSTOMNODE']
        print(timestamp(), 'Using custom node.')
    else:
        my_provider = "https://data-seed-prebsc-1-s2.binance.org:8545"
    
    if not my_provider:
        print(timestamp(), 'Custom node empty. Exiting')
        exit(1)
    
    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))
    
    print(timestamp(), "Binance Smart Chain testnet Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    
    if settings['EXCHANGEVERSION'] == "1":
        routerAddress = Web3.toChecksumAddress("0x05fF2B0DB69458A0750badebc4f9e13aDd608C7F")
        factoryAddress = Web3.toChecksumAddress("0xbcfccbde45ce874adcb698cc183debcf17952812")
    elif settings['EXCHANGEVERSION'] == "2":
        routerAddress = Web3.toChecksumAddress("0xD99D1c33F9fC3444f8101754aBC46c52416550D1")
        factoryAddress = Web3.toChecksumAddress("0x6725F303b657a9451d8BA641348b6761A6CC7a17")
    
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0xae13d989dac2f0debff460ac112a837c89baa7cd")
    base_symbol = "BNBt"
    rugdocchain = '&chain=bsc'
    modified = False
    
    settings['_EXCHANGE_BASE_SYMBOL'] = 'BNBt'
    settings['_STABLE_BASES'] = {'BUSD':{ 'address': '0x8301f2213c0eed49a7e28ae4c3e91722919b8b47', 'multiplier' : 0},
                                 'DAI ':{ 'address': '0x8a9424745056eb399fd19a0ec26a14316684e274', 'multiplier' : 0}}


if settings['EXCHANGE'].lower() == 'traderjoe':
    
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://api.avax.network/ext/bc/C/rpc"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "AVAX Smart Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    
    routerAddress = Web3.toChecksumAddress("0x60aE616a2155Ee3d9A68541Ba4544862310933d4")
    factoryAddress = Web3.toChecksumAddress("0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10")
    
    routerContract = client.eth.contract(address=routerAddress, abi=joeRouter)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7")
    base_symbol = "AVAX"
    rugdocchain = '&chain=avax'
    modified = True
    
    settings['_EXCHANGE_BASE_SYMBOL'] = 'AVAX'
    settings['_STABLE_BASES'] = {'MIM ':{ 'address': '0x130966628846bfd36ff31a822705796e8cb8c18d', 'multiplier' : 0},
                                 'USDT':{ 'address': '0xc7198437980c041c805a1edcba50c1ce5db95118', 'multiplier' : 0}}

if settings["EXCHANGE"] == 'pangolin':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://api.avax.network/ext/bc/C/rpc"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
    exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "AVAX Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106")
    factoryAddress = Web3.toChecksumAddress("0xefa94DE7a4656D787667C749f7E1223D71E9FD88")
    routerContract = client.eth.contract(address=routerAddress, abi=pangolinAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7")
    base_symbol = "AVAX"
    rugdocchain = '&chain=avax'
    modified = True
    settings['_EXCHANGE_BASE_SYMBOL'] = 'AVAX'
    settings['_STABLE_BASES'] = {'MIM ': {'address': '0x130966628846bfd36ff31a822705796e8cb8c18d', 'multiplier': 0},
                                 'USDT': {'address': '0xc7198437980c041c805a1edcba50c1ce5db95118', 'multiplier': 0}}

if settings['EXCHANGE'] == 'pinkswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
        print(timestamp(), 'Using custom node.')
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"
    
    if not my_provider:
        print(timestamp(), 'Custom node empty. Exiting')
        exit(1)
    
    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))
    
    print(timestamp(), "Binance Smart Chain Connected =", client.isConnected())
    print(timestamp(), "Loading PinkSwap Smart Contracts...")
    
    routerAddress = Web3.toChecksumAddress("0x319EF69a98c8E8aAB36Aea561Daba0Bf3D0fa3ac")
    factoryAddress = Web3.toChecksumAddress("0x7d2ce25c28334e40f37b2a068ec8d5a59f11ea54")
    
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    
    weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = False
    
    settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier' : 0},
                                 'BUSD':{ 'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier' : 0},
                                 'USDC':{ 'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier' : 0}}

if settings['EXCHANGE'] == 'biswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
        print(timestamp(), 'Using custom node.')
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"
    
    if not my_provider:
        print(timestamp(), 'Custom node empty. Exiting')
        exit(1)
    
    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))
    
    print(timestamp(), "Binance Smart Chain Connected =", client.isConnected())
    print(timestamp(), "Loading BiSwap Smart Contracts...")
    
    routerAddress = Web3.toChecksumAddress("0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8")
    factoryAddress = Web3.toChecksumAddress("0x858E3312ed3A876947EA49d572A7C42DE08af7EE")
    
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    
    weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier' : 0},
                                 'BUSD':{ 'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier' : 0},
                                 'USDC':{ 'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier' : 0}}

elif settings['EXCHANGE'].lower() == 'babyswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
        my_provider = settings['CUSTOMNODE']
        print(timestamp(), 'Using custom node.')
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"

    if not my_provider:
        print(timestamp(), 'Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Binance Smart Chain Connected =", client.isConnected())
    print(timestamp(), "Loading BabySwap Smart Contracts...")

    routerAddress = Web3.toChecksumAddress("0x325E343f1dE602396E256B67eFd1F61C3A6B38Bd")
    factoryAddress = Web3.toChecksumAddress("0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da")

    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)

    weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier' : 0},
                                 'BUSD':{ 'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier' : 0},
                                 'USDC':{ 'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier' : 0}}

if settings['EXCHANGE'] == 'bakeryswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
        print(timestamp(), 'Using custom node.')
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"

    if not my_provider:
        print(timestamp(), 'Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Binance Smart Chain Connected =", client.isConnected())
    print(timestamp(), "Loading BakerySwap Smart Contracts...")

    routerAddress = Web3.toChecksumAddress("0xCDe540d7eAFE93aC5fE6233Bee57E1270D3E330F")
    factoryAddress = Web3.toChecksumAddress("0x01bF7C66c6BD861915CdaaE475042d3c4BaE16A7")

    routerContract = client.eth.contract(address=routerAddress, abi=bakeryRouter)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)

    weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = True
    settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier' : 0},
                                 'BUSD':{ 'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier' : 0},
                                 'USDC':{ 'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier' : 0}}

if settings['EXCHANGE'] == 'apeswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Binance Smart Chain Connected =", client.isConnected())
    print(timestamp(), "Loading ApeSwap Smart Contracts...")
    
    routerAddress = Web3.toChecksumAddress("0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7")
    factoryAddress = Web3.toChecksumAddress("0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6")
    
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    
    weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
    busd = Web3.toChecksumAddress("0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56")
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier' : 0},
                                 'BUSD':{ 'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier' : 0},
                                 'USDC':{ 'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier' : 0}}

elif settings["EXCHANGE"] == 'uniswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Uniswap Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
    factoryAddress = Web3.toChecksumAddress("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    base_symbol = "ETH"
    rugdocchain = '&chain=eth'
    modified = False

    settings['_EXCHANGE_BASE_SYMBOL'] = 'ETH'
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0xdac17f958d2ee523a2206206994597c13d831ec7', 'multiplier' : 0},
                                 'USDC':{ 'address': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'multiplier' : 0}}

elif settings["EXCHANGE"] == 'uniswaptestnet':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rinkeby-light.eth.linkpool.io/"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Uniswap Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
    factoryAddress = Web3.toChecksumAddress("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0xc778417e063141139fce010982780140aa0cd5ab")
    base_symbol = "ETH"
    rugdocchain = '&chain=eth'
    modified = False

elif settings["EXCHANGE"] == 'kuswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpc-mainnet.kcc.network"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Kucoin Chain Connected =", client.isConnected())
    print(timestamp(), "Loading KuSwap Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0xa58350d6dee8441aa42754346860e3545cc83cda")
    factoryAddress = Web3.toChecksumAddress("0xAE46cBBCDFBa3bE0F02F463Ec5486eBB4e2e65Ae")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0x4446Fc4eb47f2f6586f9fAAb68B3498F86C07521")
    base_symbol = "KCS"
    rugdocchain = '&chain=kcc'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'KCS'
    settings['_STABLE_BASES'] = {'USD ':{ 'address': '0x0039f574ee5cc39bdd162e9a88e3eb1f111baf48', 'multiplier' : 0}}


elif settings["EXCHANGE"] == 'koffeeswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpc-mainnet.kcc.network"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Kucoin Chain Connected =", client.isConnected())
    print(timestamp(), "Loading KoffeeSwap Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0xc0fFee0000C824D24E0F280f1e4D21152625742b")
    factoryAddress = Web3.toChecksumAddress("0xC0fFeE00000e1439651C6aD025ea2A71ED7F3Eab")
    routerContract = client.eth.contract(address=routerAddress, abi=koffeeAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0x4446Fc4eb47f2f6586f9fAAb68B3498F86C07521")
    base_symbol = "KCS"
    rugdocchain = '&chain=kcc'
    modified = True
    settings['_EXCHANGE_BASE_SYMBOL'] = 'KCS'
    settings['_STABLE_BASES'] = {'USD ':{ 'address': '0x0039f574ee5cc39bdd162e9a88e3eb1f111baf48', 'multiplier' : 0}}

elif settings["EXCHANGE"] == 'spookyswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpcapi.fantom.network"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "FANTOM Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0xF491e7B69E4244ad4002BC14e878a34207E38c29")
    factoryAddress = Web3.toChecksumAddress("0x152eE697f2E276fA89E96742e9bB9aB1F2E61bE3")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83")
    base_symbol = "FTM"
    rugdocchain = '&chain=ftm'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'FTM'
    settings['_STABLE_BASES'] = {'USDC':{ 'address': '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 'multiplier' : 0},
                                 'USDT': {'address': '0x049d68029688eabf473097a2fc38ef61633a3c7a', 'multiplier': 0}}

elif settings["EXCHANGE"] == 'protofi':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpcapi.fantom.network"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "FANTOM Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0xF4C587a0972Ac2039BFF67Bc44574bB403eF5235")
    factoryAddress = Web3.toChecksumAddress("0x39720E5Fe53BEEeb9De4759cb91d8E7d42c17b76")
    routerContract = client.eth.contract(address=routerAddress, abi=protofirouter)
    factoryContract = client.eth.contract(address=factoryAddress, abi=protofiabi)
    weth = Web3.toChecksumAddress("0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83")
    base_symbol = "FTM"
    rugdocchain = '&chain=ftm'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'FTM'
    settings['_STABLE_BASES'] = {'USDC':{ 'address': '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 'multiplier' : 0},
                                 'USDT': {'address': '0x049d68029688eabf473097a2fc38ef61633a3c7a', 'multiplier': 0}}

elif settings["EXCHANGE"] == 'spiritswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpcapi.fantom.network"
    
    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "FANTOM Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52")
    factoryAddress = Web3.toChecksumAddress("0xEF45d134b73241eDa7703fa787148D9C9F4950b0")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83")
    base_symbol = "FTM"
    rugdocchain = '&chain=ftm'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'FTM'
    settings['_STABLE_BASES'] = {'USDC':{ 'address': '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 'multiplier' : 0},
                                 'USDT': {'address': '0x049d68029688eabf473097a2fc38ef61633a3c7a', 'multiplier': 0}}

elif settings["EXCHANGE"] == 'quickswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://polygon-rpc.com"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Matic Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")
    factoryAddress = Web3.toChecksumAddress("0x5757371414417b8c6caad45baef941abc7d3ab32")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
    base_symbol = "MATIC"
    rugdocchain = '&chain=poly'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'MATIC'
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', 'multiplier' : 0}}


elif settings["EXCHANGE"] == 'waultswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpc-waultfinance-mainnet.maticvigil.com/v1/0bc1bb1691429f1eeee66b2a4b919c279d83d6b0"

    if not my_provider:
        printt_err('Custom node empty. Exiting')
        exit(1)

    if my_provider[0].lower() == 'h':
        print(timestamp(), 'Using HTTPProvider')
        client = Web3(Web3.HTTPProvider(my_provider))
    elif my_provider[0].lower() == 'w':
        print(timestamp(), 'Using WebsocketProvider')
        client = Web3(Web3.WebsocketProvider(my_provider))
    else:
        print(timestamp(), 'Using IPCProvider')
        client = Web3(Web3.IPCProvider(my_provider))

    print(timestamp(), "Matic Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0x3a1D87f206D12415f5b0A33E786967680AAb4f6d")
    factoryAddress = Web3.toChecksumAddress("0xa98ea6356A316b44Bf710D5f9b6b4eA0081409Ef")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
    base_symbol = "MATIC"
    rugdocchain = '&chain=poly'
    modified = False
    settings['_EXCHANGE_BASE_SYMBOL'] = 'MATIC'
    settings['_STABLE_BASES'] = {'USDT':{ 'address': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', 'multiplier' : 0}}


def get_password():
    # Function: get_password
    # ----------------------------
    # Handles the decision making logic concerning private key encryption and asking the user for their password.
    #
    # returns: the user's password
    
    settings_changed = False
    setnewpassword = False
    
    # Check to see if the user has a version of the settings file before private key encryption existed
    if 'ENCRYPTPRIVATEKEYS' not in settings:
        response = ""
        settings_changed = True
        while response != "y" and response != "n":
            print("\nWould you like to use a password to encrypt your private keys?")
            response = input("You will need to input this password each time LimitSwap is executed (y/n): ")
        
        if response == "y":
            settings['ENCRYPTPRIVATEKEYS'] = "true"
            setnewpassword = True
        else:
            settings['ENCRYPTPRIVATEKEYS'] = "false"
            
            # If the user wants to encrypt their private keys, but we don't have an encrypted private key recorded, we need to ask for a password
    elif settings['ENCRYPTPRIVATEKEYS'] == "true" and not settings['PRIVATEKEY'].startswith('aes:'):
        print("\nPlease create a password to encrypt your private keys.")
        setnewpassword = True
    
    # Set a new password when necessary
    if setnewpassword == True:
        settings_changed = True
        passwords_differ = True
        while passwords_differ:
            pwd = pwinput.pwinput(prompt="\nType your new password: ")
            pwd2 = pwinput.pwinput(prompt="\nType your new password again: ")
            
            if pwd != pwd2:
                print("Error, password mismatch. Try again.")
            else:
                passwords_differ = False
    
    # The user already has encrypted private keys. Accept a password so we can unencrypt them
    elif settings['ENCRYPTPRIVATEKEYS'] == "true":
        
        if command_line_args.password:
            pwd = command_line_args.password
        else:
            pwd = pwinput.pwinput(prompt="\nPlease specify the password to decrypt your keys: ")
    
    else:
        pwd = ""
    
    if not pwd.strip():
        print()
        print("X WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING=-= WARNING X")
        print("X       You are running LimitSwap without encrypting your private keys.          X")
        print("X     Private keys are stored on disk unencrypted and can be accessed by         X")
        print("X anyone with access to the file system, including the Systems/VPS administrator X")
        print("X       and anyone with physical access to the machine or hard drives.           X")
        print("X WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING=-= WARNING X")
        print()
    
    if settings_changed == True:
        save_settings(settings, pwd)
    
    return pwd


# RUGDOC CONTROL IMPLEMENTATION

# Rugdoc's answers interpretations
interpretations = {
    "UNKNOWN": (style.RED + 'The status of this token is unknown. '
                            '                           This is usually a system error but could also be a bad sign for the token. Be careful.'),
    "OK": (style.GREEN + 'RUGDOC API RESULT : OK \n'
                         '                           √ Honeypot tests passed. RugDoc program was able to buy and sell it successfully. This however does not guarantee that it is not a honeypot.'),
    "NO_PAIRS": (style.RED + 'RUGDOC API RESULT : NO_PAIRS \n'
                             '                           ⚠ Could not find any trading pair for this token on the default router and could thus not test it.'),
    "SEVERE_FEE": (style.RED + 'RUGDOC API RESULT : SEVERE_FEE \n'
                               '                           /!\ /!\ A severely high trading fee (over 50%) was detected when selling or buying this token.'),
    "HIGH_FEE": (style.YELLOW + 'RUGDOC API RESULT : HIGH_FEE \n'
                                '                           /!\ /!\ A high trading fee (Between 20% and 50%) was detected when selling or buying this token. Our system was however able to sell the token again.'),
    "MEDIUM_FEE": (style.YELLOW + 'RUGDOC API RESULT : MEDIUM_FEE \n'
                                  '                           /!\ A trading fee of over 10% but less then 20% was detected when selling or buying this token. Our system was however able to sell the token again.'),
    "APPROVE_FAILED": (style.RED + 'RUGDOC API RESULT : APPROVE_FAILED \n'
                                   '                           /!\ /!\ /!\ Failed to approve the token.\n This is very likely a honeypot.'),
    "SWAP_FAILED": (style.RED + 'RUGDOC API RESULT : SWAP_FAILED \n'
                                '                           /!\ /!\ /!\ Failed to sell the token. \n This is very likely a honeypot.'),
    "chain not found": (style.RED + 'RUGDOC API RESULT : chain not found \n'
                                    '                           /!\ Sorry, rugdoc API does not work on this chain... (it does not work on ETH, mainly) \n')
}


def save_settings(settings, pwd):
    if len(pwd) > 0:
        encrypted_settings = settings.copy()
        encrypted_settings['LIMITWALLETPRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['LIMITWALLETPRIVATEKEY'], pwd)
        encrypted_settings['PRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY'], pwd)
        if settings['PRIVATEKEY2'] != 'null':
            encrypted_settings['PRIVATEKEY2'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY2'], pwd)
        if settings['PRIVATEKEY3'] != 'null':
            encrypted_settings['PRIVATEKEY3'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY3'], pwd)
        if settings['PRIVATEKEY4'] != 'null':
            encrypted_settings['PRIVATEKEY4'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY4'], pwd)
        if settings['PRIVATEKEY5'] != 'null':
            encrypted_settings['PRIVATEKEY5'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY5'], pwd)
    
    # TODO: MASSAGE OUTPUT - LimitSwap currently loads settings.json as a [0] element, so we need to massage our
    #                  settings.json output so that it's reasable. This should probably be fixed by us importing
    #                  the entire json file, instead of just the [0] element.
    
    print(timestamp(), "Writing settings to file.")
    
    if settings['ENCRYPTPRIVATEKEYS'] == "true":
        output_settings = encrypted_settings
    else:
        output_settings = settings
    
    with open(command_line_args.settings, 'w') as f:
        f.write("[\n")
        f.write(json.dumps(output_settings, indent=4))
        f.write("\n]\n")


def build_extended_base_configuration(token_dict):
    # Function: build_extended_base_configuration
    # ----------------------------
    # Check the user defined token list for the _STABLE_BASES and build configurations for each
    #
    # returns: an array of dictionaries containing the configuration build of the token
    #          that can be parsed and or added to the the token configuration for trading

    printt_debug("ENTER build_extended_base_configuration")
    
    
    new_token_set = []

    # Giving values for the native pair
    token_dict['_BUILT_BY_BOT'] = True
    token_dict['LIQUIDITYINNATIVETOKEN'] = "true"
    # Giving values for the stables pair
    for stable_token in settings['_STABLE_BASES']:
        new_token = token_dict.copy()
        new_token.update({
                        'BUYAMOUNTINBASE': token_dict['BUYAMOUNTINBASE'] * settings['_STABLE_BASES'][stable_token]['multiplier'],
                        "BUYPRICEINBASE": token_dict['BUYPRICEINBASE'] * settings['_STABLE_BASES'][stable_token]['multiplier'],
                        "SELLPRICEINBASE": float(token_dict['_CALCULATED_SELLPRICEINBASE']) * float(settings['_STABLE_BASES'][stable_token]['multiplier']),
                        "STOPLOSSPRICEINBASE": float(token_dict['_CALCULATED_STOPLOSSPRICEINBASE']) * float(settings['_STABLE_BASES'][stable_token]['multiplier']),
                        "MINIMUM_LIQUIDITY_IN_DOLLARS": token_dict['MINIMUM_LIQUIDITY_IN_DOLLARS'],
                        "USECUSTOMBASEPAIR": "true",
                        "LIQUIDITYINNATIVETOKEN": "false",
                        "BASESYMBOL": stable_token,
                        "_BASE_PRICE": settings['_STABLE_BASES'][stable_token]['multiplier'],
                        "BASEADDRESS": settings['_STABLE_BASES'][stable_token]['address'],
                        "_PAIR_SYMBOL" : token_dict['SYMBOL'] + '/' + stable_token,
                        "_BUILT_BY_BOT" : True
                        })
        
        # If these keys have special character on them, they represent percentages and we shouldn't copy them.
        if not re.search('^(\d+\.){0,1}\d+(x|X|%)$', str(token_dict['SELLPRICEINBASE'])):
            new_token['SELLPRICEINBASE'] = float(token_dict['SELLPRICEINBASE']) * float(settings['_STABLE_BASES'][stable_token]['multiplier'])
        if not re.search('^(\d+\.){0,1}\d+(x|X|%)$', str(token_dict['STOPLOSSPRICEINBASE'])):
            new_token['STOPLOSSPRICEINBASE'] = float(token_dict['STOPLOSSPRICEINBASE']) * float(settings['_STABLE_BASES'][stable_token]['multiplier'])
            
        new_token_set.append(new_token)
        
    return new_token_set


def parse_wallet_settings(settings, pwd):
    # Function: load_wallet_settings
    # ----------------------------
    # Handles the process of deciding whether or not the user's private key needs to be decrypted
    # Accepts user input for new private keys and wallet addresses
    #
    # returns: none (exits on incorrect password)
    
    settings_changed = False
    
    # Check for limit wallet information
    if " " in settings['LIMITWALLETADDRESS'] or settings['LIMITWALLETADDRESS'] == "":
        settings_changed = True
        settings['LIMITWALLETADDRESS'] = input("Please provide the wallet address where you have your LIMIT: ")
    
    # Check for limit wallet private key
    if " " in settings['LIMITWALLETPRIVATEKEY'] or settings['LIMITWALLETPRIVATEKEY'] == "":
        settings_changed = True
        settings['LIMITWALLETPRIVATEKEY'] = input("Please provide the private key for the wallet where you have your LIMIT: ")
    
    # If the limit wallet private key is already set and encrypted, decrypt it
    elif settings['LIMITWALLETPRIVATEKEY'].startswith('aes:'):
        printt("Decrypting limit wallet private key.")
        settings['LIMITWALLETPRIVATEKEY'] = settings['LIMITWALLETPRIVATEKEY'].replace('aes:', "", 1)
        settings['LIMITWALLETPRIVATEKEY'] = cryptocode.decrypt(settings['LIMITWALLETPRIVATEKEY'], pwd)
        
        if settings['LIMITWALLETPRIVATEKEY'] == False:
            printt_err("ERROR: Your private key decryption password is incorrect")
            printt_err("Please re-launch the bot and try again")
            sleep(10)
            sys.exit()
    
    # Check for trading wallet information
    if " " in settings['WALLETADDRESS'] or settings['WALLETADDRESS'] == "":
        settings_changed = True
        settings['WALLETADDRESS'] = input("Please provide the wallet address for your trading wallet: ")
    
    # Check for trading wallet private key
    if " " in settings['PRIVATEKEY'] or settings['PRIVATEKEY'] == "":
        settings_changed = True
        settings['PRIVATEKEY'] = input("Please provide the private key for the wallet you want to trade with: ")
    
    # If the trading wallet private key is already set and encrypted, decrypt it
    elif settings['PRIVATEKEY'].startswith('aes:'):
        print(timestamp(), "Decrypting trading wallet private key.")
        settings['PRIVATEKEY'] = settings['PRIVATEKEY'].replace('aes:', "", 1)
        settings['PRIVATEKEY'] = cryptocode.decrypt(settings['PRIVATEKEY'], pwd)
    
    # add of 2nd wallet
    if settings['WALLETADDRESS2'] == 'no_utility' or settings['PRIVATEKEY2'].startswith('aes:'):
        stoptheprocess = 1
    else:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to add a 2nd wallet to use MULTIPLEBUYS feature ? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS2'] or settings['WALLETADDRESS2'] == "null":
                settings_changed = True
                settings['WALLETADDRESS2'] = input("Please provide the 2nd trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY2'] or settings['PRIVATEKEY2'] == "null":
                settings_changed = True
                settings['PRIVATEKEY2'] = input("Please provide the 2nd private key for the 2nd trading wallet: ")
            stoptheprocess = 0
        else:
            settings['WALLETADDRESS2'] = "no_utility"
            stoptheprocess = 1
    
    # add of 3nd wallet
    if stoptheprocess != 1:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to a 3rd wallet to use MULTIPLEBUYS feature ? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS3'] or settings['WALLETADDRESS3'] == "null":
                settings_changed = True
                settings['WALLETADDRESS3'] = input("Please provide the 3rd trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY3'] or settings['PRIVATEKEY3'] == "null":
                settings_changed = True
                settings['PRIVATEKEY3'] = input("Please provide the 3rd private key for the 3rd trading wallet: ")
            stoptheprocess = 0
        else:
            stoptheprocess = 1
    
    # add of 4th wallet
    if stoptheprocess != 1:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to a 4th wallet to use MULTIPLEBUYS feature ? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS4'] or settings['WALLETADDRESS4'] == "null":
                settings_changed = True
                settings['WALLETADDRESS4'] = input("Please provide the 4th trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY4'] or settings['PRIVATEKEY4'] == "null":
                settings_changed = True
                settings['PRIVATEKEY4'] = input("Please provide the 4th private key for the 4th trading wallet: ")
            stoptheprocess = 0
        else:
            stoptheprocess = 1
    
    # add of 5th wallet
    if stoptheprocess != 1:
        decision = ""
        while decision != "y" and decision != "n":
            decision = input(style.BLUE + "\nWould you like to a 5th wallet to use MULTIPLEBUYS feature ? (y/n): ")
        
        if decision == "y":
            print(style.RESET + " ")
            # Check for trading wallet information
            if " " in settings['WALLETADDRESS5'] or settings['WALLETADDRESS5'] == "null":
                settings_changed = True
                settings['WALLETADDRESS5'] = input("Please provide the 5th trading wallet address: ")
            
            # Check for trading wallet private key
            if " " in settings['PRIVATEKEY5'] or settings['PRIVATEKEY5'] == "null":
                settings_changed = True
                settings['PRIVATEKEY5'] = input("Please provide the 5th private key for the 5th trading wallet: ")
    
    if settings_changed == True:
        save_settings(settings, pwd)
    print(style.RESET + " ")


@lru_cache(maxsize=None)
def decimals(address):
    # Function: decimals
    # ----------------------------
    # calculate how many decimals this token has
    #
    # address - token contract
    #
    # returns: returns the number of tokens for this contract

    try:
        balanceContract = client.eth.contract(address=Web3.toChecksumAddress(address), abi=standardAbi)
        decimals = balanceContract.functions.decimals().call()
        DECIMALS = 10 ** decimals
    except ABIFunctionNotFound:
        DECIMALS = 10 ** 18
    except ValueError as ve:
        logging.exception(ve)
        print("Please check your SELLPRICE values. ERROR in checking decimals")
    return DECIMALS


def check_logs():
    print(timestamp(), "Quickly Checking Log Size")
    with open(file_name) as f:
        line_count = 0
        for line in f:
            line_count += 1
        if line_count > 300:
            with open(file_name, "r") as f:
                lines = f.readlines()
            
            with open(file_name, "w") as f:
                f.writelines(lines[20:])
    
    f.close()


def decode_key():
    printt_debug("ENTER decode_key")
    private_key = settings['LIMITWALLETPRIVATEKEY']
    acct = client.eth.account.privateKeyToAccount(private_key)
    addr = acct.address
    return addr


def auth():
    my_provider2 = 'https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161'
    client2 = Web3(Web3.HTTPProvider(my_provider2))
    print(timestamp(), "Connected to Ethereum BlockChain =", client2.isConnected())
    address = Web3.toChecksumAddress("0x1712aad2c773ee04bdc9114b32163c058321cd85")
    abi = standardAbi
    balanceContract = client2.eth.contract(address=address, abi=abi)
    decimals = balanceContract.functions.decimals().call()
    DECIMALS = 10 ** decimals
    
    # Exception for incorrect Key Input
    try:
        decode = decode_key()
    except Exception:
        printt_err("There is a problem with your private key: please check if it's correct. Don't enter your seed phrase!")
    
    wallet_address = Web3.toChecksumAddress(decode)
    balance = balanceContract.functions.balanceOf(wallet_address).call()
    true_balance = balance / DECIMALS
    printt("Current Tokens Staked = ", true_balance, write_to_log=False)
    return true_balance


def approve(address, amount):
    print(timestamp(), "Approving", address)
    
    eth_balance = Web3.fromWei(client.eth.getBalance(settings['WALLETADDRESS']), 'ether')
    
    if base_symbol == "ETH":
        minimumbalance = 0.05
    else:
        minimumbalance = 0.01
    
    if eth_balance > minimumbalance:
        printt("Estimating Gas Cost Using Web3")
        # Estimates GAS price and use a +20% factor
        if settings['EXCHANGE'] == 'uniswaptestnet':
            # Special condition on uniswaptestnet to make GAS > Priority Gas
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(200) / 100)
            printt("Current Gas Price =", gas)
        else:
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            printt("Current Gas Price = ", gas)
            
        contract = client.eth.contract(address=Web3.toChecksumAddress(address), abi=standardAbi)
        transaction = contract.functions.approve(routerAddress, amount).buildTransaction({
            'gasPrice': Web3.toWei(gas, 'gwei'),
            'gas': 300000,
            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
        })
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY'])
        
        try:
            return client.eth.sendRawTransaction(signed_txn.rawTransaction)
        finally:
            printt("Transaction Hash = ", Web3.toHex(client.keccak(signed_txn.rawTransaction)), write_to_log=True)
            tx_hash = client.toHex(client.keccak(signed_txn.rawTransaction))
            return tx_hash
    else:
        printt_err(
            "You have less than 0.05 ETH or 0.01 BNB/FTM/MATIC/etc. token in your wallet, bot needs more to cover fees : please add some more in your wallet")
        sleep(10)
        sys.exit()


def check_approval(token, address, allowance_to_compare_with, condition):
    printt_debug("ENTER check_approval()")
    printt("Checking Approval Status", address)
    contract = client.eth.contract(address=Web3.toChecksumAddress(address), abi=standardAbi)
    actual_allowance = contract.functions.allowance(Web3.toChecksumAddress(settings['WALLETADDRESS']), routerAddress).call()
    
    printt_debug("actual_allowance 1591          :", actual_allowance)
    printt_debug("allowance_to_compare_with 1592 :", allowance_to_compare_with)
    
    allowance_request = 115792089237316195423570985008687907853269984665640564039457584007913129639935
    
    if actual_allowance < allowance_to_compare_with or actual_allowance == 0:
        if settings["EXCHANGE"] == 'quickswap':
            if actual_allowance == 0:
                tx = approve(address, allowance_request)
                wait_for_tx(token, tx, address)
            
            else:
                print("Revert to Zero To change approval")
                tx = approve(address, 0)
                wait_for_tx(token, tx, address)
                tx = approve(address, allowance_request)
                wait_for_tx(token, tx, address)

        else:
            if condition == 'base_approve':
                printt_info("---------------------------------------------------------------------------------------------")
                printt_info("Your base token is not approved --> LimitSwap will now APPROVE it, or it won't be able to buy")
                printt_info("---------------------------------------------------------------------------------------------")
            elif condition == 'preapprove':
                printt_info("-----------------------------------------------------------------------------")
                printt_info("You have selected PREAPPROVE = true --> LimitSwap will now APPROVE this token")
                printt_info("-----------------------------------------------------------------------------")
            elif condition == 'txfail':
                printt_info("----------------------------------------------------------------------------------")
                printt_info("You have failed to sell tokens --> LimitSwap will chack if it needs to be APPROVED")
                printt_info("----------------------------------------------------------------------------------")
            else:
                printt_info("-------------------------------------")
                printt_info("LimitSwap will now APPROVE this token")
                printt_info("-------------------------------------")

            tx = approve(address, allowance_request)
            wait_for_tx(token, tx, address)
            printt_ok("---------------------------------------------------------")
            printt_ok("  Token is now approved : LimitSwap can sell this token", write_to_log=True)
            printt_ok("---------------------------------------------------------")
        
        return allowance_request
    
    else:
        printt_ok("Token is already approved --> LimitSwap can sell this token ")
        return actual_allowance


def check_bnb_balance():
    balance = client.eth.getBalance(settings['WALLETADDRESS'])
    printt("Current Wallet Balance is :", Web3.fromWei(balance, 'ether'), base_symbol, write_to_log=True)
    return balance


def check_balance(address, symbol='UNKNOWN_TOKEN', display_quantity=True):
    # Function: check_balance
    # --------------------
    # check and display the number of tokens in the user's wallet
    #
    # address - the contract address of the token we're looking for
    # symbol  - the symbol of the token we're looking for
    # display_quantity - boolean to report on the number of tokens
    #
    # returns: the wallet's token balance
    
    printt_debug("ENTER: check_balance() for " + address)
    
    address = Web3.toChecksumAddress(address)
    DECIMALS = decimals(address)
    balanceContract = client.eth.contract(address=address, abi=standardAbi)
    
    balance = balanceContract.functions.balanceOf(settings['WALLETADDRESS']).call()
    if display_quantity == True:
        printt("Current Wallet Balance is: ", str(balance / DECIMALS), symbol, write_to_log=True)
    else:
        printt_debug("display_quantity=False --> Do not display balance")
    printt_debug("EXIT: check_balance()")
    return balance


@lru_cache(maxsize=None)
def fetch_pair(inToken, outToken, contract):
    printt_debug("ENTER fetch_pair")
    pair = contract.functions.getPair(inToken, outToken).call()
    printt_debug("Pair Address = ", pair)
    return pair


PAIR_HASH={}
def fetch_pair2(inToken, outToken, contract):
    printt_debug("ENTER fetch_pair2")
    pair=PAIR_HASH.get((inToken,outToken))
    if pair is None:
        pair = contract.functions.getPair(inToken, outToken).call()
        if pair != '0x0000000000000000000000000000000000000000':
            PAIR_HASH[(inToken,outToken)] = pair
    printt_debug("Pair Address = ", pair)
    return pair

@lru_cache(maxsize=None)
def getContractLP(pair_address):
    printt_debug("ENTER getContractLP")
    return client.eth.contract(address=pair_address, abi=lpAbi)


# We use cache to check price of Custom Base pair for price calculation. Price will be updated every 30s (ttl = 30)
@cached(cache=TTLCache(maxsize=128, ttl=30))
def getReserves_with_cache(pair_contract):
    return pair_contract.functions.getReserves().call()


def sync(inToken, outToken):
    pair = fetch_pair2(inToken, outToken, factoryContract)
    syncContract = client.eth.contract(address=Web3.toChecksumAddress(pair), abi=lpAbi)
    sync = syncContract.functions.sync().call()


def check_pool(inToken, outToken, DECIMALS_OUT):
    # This function is made to calculate Liquidity of a token
    printt_debug("ENTER check_pool")
    # be careful, we cannot put cache and use fetch_pair, because we need to detect when pair_address != 0x0000000000000000000000000000000000000000
    # pair_address = fetch_pair2(inToken, outToken, factoryContract) --> we don't do that until we're sure

    DECIMALS_IN = 1000000000000000000

    printt_debug("DECIMALS_IN : ", DECIMALS_IN)
    printt_debug("DECIMALS_OUT: ", DECIMALS_OUT)

    pair_address = factoryContract.functions.getPair(inToken, outToken).call()
    if pair_address == '0x0000000000000000000000000000000000000000':
        printt_debug("check_pool condition 1 quick exit")
        return 0
    
    pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
    
    reserves = pair_contract.functions.getReserves().call()

    # Tokens are ordered by the token contract address
    # The token contract address can be interpreted as a number
    # And the smallest one will be token0 internally
    
    ctnb1 = int(inToken, 16)
    ctnb2 = int(outToken, 16)
    
    if (ctnb1 > ctnb2):
        printt_debug("reserves[0] is for outToken:")
        pooled = reserves[0] / DECIMALS_IN
    else:
        printt_debug("reserves[0] is for inToken:")
        pooled = reserves[1] / DECIMALS_OUT
    
    printt_debug("Debug reserves[0] :", reserves[0] / DECIMALS_IN)
    printt_debug("Debug reserves[1] :", reserves[1] / DECIMALS_OUT)
    printt_debug("Debug check_pool pooled :", pooled, "in token:", outToken)
    
    return pooled


def check_rugdoc_api(token):
    # Use Rugdoc API to check if token is a honeypot or not
    rugresponse = requests.get(
        'https://honeypot.api.rugdoc.io/api/honeypotStatus.js?address=' + token['ADDRESS'] + rugdocchain)
    # sending get request and saving the response as response object

    if rugresponse.status_code == 200:
        d = json.loads(rugresponse.content)
        for key, value in interpretations.items():
            if d["status"] in key:
                honeypot_status = value
                honeypot_code = key
                printt(honeypot_status)
                print(style.RESET + " ")

    else:
        printt_warn(
            "Sorry, Rugdoc's API does not work on this token (Rugdoc does not work on ETH chain for instance)")

    token['_RUGDOC_DECISION'] = ""
    while token['_RUGDOC_DECISION'] != "y" and token['_RUGDOC_DECISION'] != "n":
        printt("What is your decision?")
        token['_RUGDOC_DECISION'] = input("                           Would you like to snipe this token? (y/n): ")

    if token['_RUGDOC_DECISION'] == "y":
        print(style.RESET + " ")
        printt_ok("OK let's go!!")
    else:
        print(style.RESET + " ")
        printt("DISABLING", token['SYMBOL'])
        token['ENABLED'] = 'false'
        token['_QUOTE'] = 0


def wait_for_open_trade(token, inToken, outToken):
    printt_debug("ENTER wait_for_open_trade")

    printt("-----------------------------------------------------------------------------------------------------------------------------", write_to_log=True)
    printt("WAIT_FOR_OPEN_TRADE is enabled", write_to_log=True)
    printt("", write_to_log=True)

    if token['WAIT_FOR_OPEN_TRADE'] == 'true' or token['WAIT_FOR_OPEN_TRADE'] == 'true_after_buy_tx_failed':
        printt("It works with 2 ways:", write_to_log=True)
        printt("1/ Bot will scan mempool to detect Enable Trading functions", write_to_log=True)
        printt("2/ Bot will wait for price to move before making a BUY order", write_to_log=True)
        printt(" ", write_to_log=True)
        printt("---- Why those 2 ways ? ----", write_to_log=True)
        printt("Because we need to enter in the code the functions used by the teams to make trading open", write_to_log=True)
        printt("And there is a LOT of ways to do that, so we cannot be 100% to detect it in the mempool", write_to_log=True)
        printt(" ", write_to_log=True)
        printt_err("---- WE NEED YOUR HELP FOR THAT ----", write_to_log=True)
        printt_err("To detect Enable Trading in mempool, we need to enter in the code the functions used by the teams to make trading open:", write_to_log=True)
        printt(" ", write_to_log=True)
        printt("Please give us some examples of function used here: https://github.com/tsarbuig/LimitSwap/issues/1", write_to_log=True)
        printt(" ", write_to_log=True)
        printt(" ", write_to_log=True)
        printt_err("---- BE CAREFUL ----", write_to_log=True)
        printt_err("to make WAIT_FOR_OPEN_TRADE work, you need to SNIPE ON THE SAME LIQUIDITY PAIR that liquidity added by the team:", write_to_log=True)
        printt(" ", write_to_log=True)
        printt("Explanation : if you try to snipe in BUSD and liquidity is in BNB, price will move because of price movement between BUSD and BNB", write_to_log=True)
        printt("--> if liquidity is in BNB or ETH, use LIQUIDITYINNATIVETOKEN = true and USECUSTOMBASEPAIR = false", write_to_log=True)
        printt(" ", write_to_log=True)
        printt("When you will have read all this message and understood how it works, enter the value 'true_no_message' or 'true_after_buy_tx_failed_no_message' in your WAIT_FOR_OPEN_TRADE setting", write_to_log=True)
        printt(" ", write_to_log=True)
        printt("------------------------------------------------------------------------------------------------------------------------------", write_to_log=True)

    if token['WAIT_FOR_OPEN_TRADE'] == 'mempool' or token['WAIT_FOR_OPEN_TRADE'] == 'mempool_after_buy_tx_failed':
        printt("It will scan mempool to detect Enable Trading functions", write_to_log=True)
        printt(" ", write_to_log=True)
        printt_err("---- WE NEED YOUR HELP FOR THAT ----", write_to_log=True)
        printt_err("To detect Enable Trading in mempool, we need to enter in the code the functions used by the teams to make trading open:", write_to_log=True)
        printt(" ", write_to_log=True)
        printt("Please give us some examples of function used here: https://github.com/tsarbuig/LimitSwap/issues/1", write_to_log=True)
        printt(" ", write_to_log=True)
        printt("------------------------------------------------------------------------------------------------------------------------------", write_to_log=True)

    openTrade = False
    
    token['_PREVIOUS_QUOTE'] = check_price(inToken, outToken, token['USECUSTOMBASEPAIR'], token['LIQUIDITYINNATIVETOKEN'], int(token['_CONTRACT_DECIMALS']), int(token['_BASE_DECIMALS']))

    tx_filter = client.eth.filter({"filter_params": "pending", "address": inToken})
    
    list_of_methodId = ["0xc9567bf9", "0x8a8c523c", "0x0d295980", "0xbccce037", "0x4efac329", "0x7b9e987a", "0x6533e038", "0x8f70ccf7", "0xa6334231", "0x48dfea0a", "0xc818c280", "0xade87098", "0x0099d386", "0xfb201b1d"]

    while openTrade == False:
    
        if token['WAIT_FOR_OPEN_TRADE'] == 'true' or token['WAIT_FOR_OPEN_TRADE'] == 'true_no_message' or token['WAIT_FOR_OPEN_TRADE'] == 'true_after_buy_tx_failed' or token['WAIT_FOR_OPEN_TRADE'] == 'true_after_buy_tx_failed_no_message':
            pprice = check_price(inToken, outToken, token['USECUSTOMBASEPAIR'], token['LIQUIDITYINNATIVETOKEN'], int(token['_CONTRACT_DECIMALS']), int(token['_BASE_DECIMALS']))
    
            if pprice != float(token['_PREVIOUS_QUOTE']):
                token['_TRADING_IS_ON'] = True
                printt_ok("Token price:", pprice, "--> IT HAS MOVED :)")
                printt_ok("PRICE HAS MOVED --> trading is enabled --> Bot will buy")
                break

            printt("Token price:", pprice)
        
        
        try:
            for tx_event in tx_filter.get_new_entries():

                txHash = tx_event['transactionHash']
                txHashDetails = client.eth.get_transaction(txHash)
                # printt_debug(txHashDetails)
                txFunction = txHashDetails.input[:10]
                if txFunction.lower() in list_of_methodId:
                    openTrade = True
                    token['_GAS_IS_CALCULATED'] = True
                    token['_GAS_TO_USE'] = int(txHashDetails.gasPrice) / 1000000000
                    printt_ok("OPEN TRADE FUNCTION DETECTED --> Trading is enabled --> Bot will buy")
                    printt_ok("MethodID: ", txFunction, " Block: ", tx_event['blockNumber'], " Found Signal", "in txHash:", txHash.hex())
                    printt_ok("GAS will be the same as liquidity adding event. GAS=", token['_GAS_TO_USE'])
                    break
                else:
                    printt("Found something in mempool - MethodID: ", txFunction, " Block: ", tx_event['blockNumber'])
        except Exception as e:
            printt_err("Wait_for_open_trade Error. It can happen with Public node : private node is recommended. Still, let's continue.")
            continue
            
    # Examples of tokens and functions used
    #

    # https://bscscan.com/tx/0x468008dd3439b1802784f11a29dd82f195a2a239e381fa83c29dcc39b85024fb
    # https://etherscan.io/tx/0xfe242a303b80301d8b173b1c54fa80de222263252682b9507d3cba79342f2e19
    # https://etherscan.io/tx/0x80ce8f1f2be8c40db151d40d8571ec42dcb550f088abdfed5dce7bfc67d8a935
    # https://etherscan.io/tx/0xffcb84f9519c2d598f1121a6e84cf7c3f4271c4e3514552858be796518ed7e95
    # https://etherscan.io/tx/0x6938ea87626efbef08c542d72a166192baaf1f1c112001fdb9a107520b140a9f
    # https://etherscan.io/tx/0xa95d6013647b5e0efc6f7b4920d891dfa162447a0dbb0ea6ac5b252ecb8946ae
    # https://etherscan.io/tx/0x65d66d1e7d3ff3d8fc67308d105aac6722b00da23f116c89a5420544db5b875d
    # Function: openTrading()
    # MethodID: 0xc9567bf9

    # https://etherscan.io/tx/0x303143b2015a398050a50e4dc2ef16668b974c06db2fd4c4e4abbe64f0c2d592
    # https://etherscan.io/tx/0x9fbec460367b783afee66446eacf45a1159c9bdfaccb414eca7fb5716bee230b
    # https://etherscan.io/tx/0xa2b0a8ae04254befd4c463f4abacc50ebe0e3c99b829e95f6e2a9353aab959cf
    # https://etherscan.io/tx/0x5ef0fe0ffb7a6f12c0cdfa4e57f9e951b0577a90611008d864e72fdcde057fac
    # https://etherscan.io/tx/0xa2b0a8ae04254befd4c463f4abacc50ebe0e3c99b829e95f6e2a9353aab959cf
    # https://etherscan.io/tx/0x8a7e1fbcebb948307c726ba6a6d519c2b423ab62f6490ce451d54aa21152138b
    # Function: enableTrading()
    # MethodID: 0x8a8c523c

    # https://bscscan.com/tx/0x19cac49bf8319689a7620935bf9466e469317992b994ec9692697a9ef71e3ace
    # https://bscscan.com/tx/0xa98ae84de5aee32d216d734b790131a845548c7e5013085688dccd58c9b5b277
    # Function: tradingStatus
    # methodId = "0x0d295980"

    # WitcherVerse - 0xD2f71875d66188F96BaDBF98a5F020894209E34b
    # https://bscscan.com/tx/0xb42089396c1b1f887cb79e0cf48ae785aa92fa66f0645c759244f70b2a2834f9
    # Function: preSaleAfter()
    # methodId = "0xbccce037"

    # https://bscscan.com/tx/0x5b8d8d70b6d1e591d0620a50247deef38bb924de0c38307cc9c5b77839f68bcc
    # Function: snipeListing() ** *
    # MethodID: 0x4efac329

    # https://bscscan.com/tx/0x0c528819b84a7336c3ff1cc72290ba8ca48555b932383fcbe6722a703a6b72a4
    # https://bscscan.com/tx/0x7f526b56a20bf34a7af29137747c9e153c4563f5af4d084d8682893b20e56bd8
    # Function: SetupEnableTrading
    # MethodID: 0x7b9e987a

    # https://bscscan.com/tx/0x5b2c05e60789350c578ab2d01d3963266dba47aed8e9750c7d2dc78660438091
    # Function: enabledTradingOnly
    # MethodID: 0x6533e038

    # https://etherscan.io/tx/0xb78202678abf65936f9a4a2be8ee267dbefe28d5df49d1390c4dc55a09c206b0
    # Function: setTrading(bool _tradingOpen)
    # MethodID: 0x8f70ccf7

    # https://etherscan.io/tx/0xd4a9333c99f3f2b5f09afe80f9b63061e1bc0e4feb9a563a833fe94c7ee096c0
    # Function: allowtrading()
    # MethodID: 0xa6334231

    # https://etherscan.io/tx/0x7c5c49ec152783dcb6e2c7602154c2cd80542d27ff11587db46df18ec3c6994c
    # Function: openTrading(address[] lockSells, uint256 duration)
    # MethodID: 0x48dfea0a
    
    # https://bscscan.com/tx/0x037c3c2f37e5ba0cda7eb877799900ec2ab6d07969b4cbec6d1e6c89412c84db
    # Function: setBotProtectionDisableForever()
    # MethodID: 0xc818c280

def get_tokens_purchased(tx_hash):
    # Function: get_tokens_purchased
    # ----------------------------
    # provides the number of tokens purchased in a transaction
    #
    # tx_hash = the transaction hash
    #
    # returns: number of tokens purchased
    
    # Get transaction object
    tx = client.eth.get_transaction(tx_hash)
    contract = client.eth.contract(address=tx["to"], abi=lpAbi)
    
    # decode input data using contract object's decode_function_input() method
    func_obj, func_params = contract.decode_function_input(tx["input"])
    print(func_params)
    exit(0)


def build_sell_conditions(token_dict, condition):
    # Function: build_sell_conditions
    # ----------------------------
    # This function is designed to be called anytime sell conditions need to be adjusted for a token
    #
    # buy - provides the opportunity to specify a buy price, otherwise token_dict['_COST_PER_TOKEN'] is used
    # sell - provides the opportunity to specify a buy price, otherwise token_dict['SELLPRICEINBASE'] is used
    # stop - provides the opportunity to specify a buy price, otherwise token_dict['STOPLOSSPRICEINBASE'] is used

    printt_debug("ENTER build_sell_conditions() with", condition, "parameter")
    
    sell = token_dict['SELLPRICEINBASE']
    stop = token_dict['STOPLOSSPRICEINBASE']

    # Calculates cost per token
    # TODO : solve problem here https://t.me/LimitSwap/102375
    if float(token_dict['_TOKEN_BALANCE']) > 0:
        if token_dict['KIND_OF_SWAP'] == 'base':
            token_dict['_COST_PER_TOKEN'] = float(token_dict['BUYAMOUNTINBASE']) / float((token_dict['_TOKEN_BALANCE'] - token_dict['_PREVIOUS_TOKEN_BALANCE']))
        elif token_dict['KIND_OF_SWAP'] == 'tokens':
            token_dict['_COST_PER_TOKEN'] = float(token_dict['_BASE_USED_FOR_TX']) / float(token_dict['BUYAMOUNTINTOKEN'])
        else:
            printt_err("Wrong value in KIND_OF_SWAP parameter")
    printt_debug(token_dict['SYMBOL'], " cost per token was: ", token_dict['_COST_PER_TOKEN'])

    # Check to see if the SELLPRICEINBASE is a percentage of the purchase
    if re.search('^(\d+\.){0,1}\d+%$', str(sell)):
        sell = sell.replace("%","")
        if condition == 'before_buy':
            printt("")
            printt_err("--------------------------------------------------------------------------------------------------")
            printt_err("Be careful, updating sellprice with % in real-time WORKS ONLY FOR ONE TOKEN for the moment")
            printt_err("--> do NOT change your tokens.json if you have more than 1 token or if you use WATCH_STABLES_PAIRS")
            printt_err("    or close the bot after BUY order is made, or your calculated SELLPRICE will be lost!")
            printt_err("--------------------------------------------------------------------------------------------------")
            printt("")
            printt_info("Since you have put a % in SELLPRICE, and bot did not buy yet, we will set SELLPRICE = 99999 so as the bot not to sell if you stop and run it again.")
            token_dict['_CALCULATED_SELLPRICEINBASE'] = 99999
        else:
            token_dict['_CALCULATED_SELLPRICEINBASE'] = token_dict['_COST_PER_TOKEN'] * (float(sell) / 100)
            printt_info("")
            printt_info(token_dict['SYMBOL'], " cost per token was: ", token_dict['_COST_PER_TOKEN'])
            printt_info("--> SELLPRICEINBASE = ", token_dict['SELLPRICEINBASE'],"*", token_dict['_COST_PER_TOKEN'], "= ", token_dict['_CALCULATED_SELLPRICEINBASE'])
            printt_info("")
            printt_err("DO NOT CLOSE THE BOT OR THIS INFORMATION WILL BE LOST")
    # Otherwise, don't adjust the sell price in base
    else:
        token_dict['_CALCULATED_SELLPRICEINBASE'] = sell
    # Check to see if the STOPLOSSPRICEINBASE is a percentage of the purchase
    if re.search('^(\d+\.){0,1}\d+%$', str(stop)):
        stop = stop.replace("%","")
        if condition == 'before_buy':
            printt_info("Since you have put a % in SELLPRICE, and bot did not buy yet, we will set STOPLOSSPRICE = 0.")
            token_dict['_CALCULATED_STOPLOSSPRICEINBASE'] = 0
        else:
            token_dict['_CALCULATED_STOPLOSSPRICEINBASE'] = token_dict['_COST_PER_TOKEN'] * (float(stop) / 100)
            printt_info("--> STOPLOSSPRICEINBASE = ", token_dict['STOPLOSSPRICEINBASE'],"*", token_dict['_COST_PER_TOKEN'], "= ", token_dict['_CALCULATED_STOPLOSSPRICEINBASE'])
            printt_info("")

    # Otherwise, don't adjust the sell price in base
    else:
        token_dict['_CALCULATED_STOPLOSSPRICEINBASE'] = stop


    printt_debug("1111 token_dict['_CALCULATED_SELLPRICEINBASE']    :", token_dict['_CALCULATED_SELLPRICEINBASE'])
    printt_debug("1111 token_dict['_CALCULATED_STOPLOSSPRICEINBASE']:", token_dict['_CALCULATED_STOPLOSSPRICEINBASE'])
    printt_debug(token_dict)

    
    
def check_liquidity_amount(token, DECIMALS_OUT, DECIMALS_weth):
    # Function: check_liquidity_amount
    # ----------------------------
    # Tells if the liquidity of tokens purchased is enough for trading or not
    #
    # returns:
    #       - 0 if NOT OK for trading
    #       - 1 if OK for trading
    #
    #    There are 4 cases :
    #    1/ LIQUIDITYINNATIVETOKEN = true & USECUSTOMBASEPAIR = false --> we need to check liquidity in ETH / BNB...
    #    2/ LIQUIDITYINNATIVETOKEN = true & USECUSTOMBASEPAIR = true --> we need to check liquidity in ETH / BNB too
    #    3/ LIQUIDITYINNATIVETOKEN = false & USECUSTOMBASEPAIR = true --> we need to check liquidity in the CUSTOM Base Pair
    #    4/ LIQUIDITYINNATIVETOKEN = false & USECUSTOMBASEPAIR = false --> this case in handled line 1830 in the buy() function
    #
    
    printt_debug("ENTER: check_liquidity_amount()")
    
    inToken = Web3.toChecksumAddress(token['ADDRESS'])
    
    # Cases 1 and 2 above : we always use weth as LP pair to check liquidity
    if token["LIQUIDITYINNATIVETOKEN"] == 'true':
        printt_debug("check_liquidity_amount case 1")

        liquidity_amount = check_pool(inToken, weth, token['_BASE_DECIMALS'])
        liquidity_amount_in_dollars = float(liquidity_amount) * float(token['_BASE_PRICE'])
        printt("Current", token['SYMBOL'], "Liquidity =", "{:.2f}".format(liquidity_amount_in_dollars), "$")
        
        if float(token['MINIMUM_LIQUIDITY_IN_DOLLARS']) <= float(liquidity_amount_in_dollars):
            printt_ok("MINIMUM_LIQUIDITY_IN_DOLLARS parameter =", int(token['MINIMUM_LIQUIDITY_IN_DOLLARS']), " --> Enough liquidity detected : Buy Signal Found!")
            return 1
        
        # This position isn't looking good. Inform the user, disable the token and break out of this loop
        else:
            printt_warn("------------------------------------------------", write_to_log=True)
            printt_warn("NOT ENOUGH LIQUIDITY", write_to_log=True)
            printt_warn("", write_to_log=True)
            printt_warn("- You have set MINIMUM_LIQUIDITY_IN_DOLLARS  =", token['MINIMUM_LIQUIDITY_IN_DOLLARS'], "$", write_to_log=True)
            printt_warn("- Liquidity detected for", token['SYMBOL'], "=", "{:.2f}".format(liquidity_amount_in_dollars), "$", write_to_log=True)
            printt_warn("--> Bot will not buy and disable token", write_to_log=True)
            printt_warn("------------------------------------------------", write_to_log=True)
            token['ENABLED'] = 'false'
            token['_QUOTE'] = 0
            return 0
    
    # Case 3 above
    if token["LIQUIDITYINNATIVETOKEN"] == 'false' and token["USECUSTOMBASEPAIR"] == 'true':
        # This case is a little bit more complicated. We need to:
        # 1/ calculate Custom Base token price in ETH/BNB...
        # 2/ convert this Custom Base token price in $
        
        outToken = Web3.toChecksumAddress(token['BASEADDRESS'])
        printt_debug("check_liquidity_amount case 1")

        liquidity_amount = check_pool(inToken, outToken, token['_BASE_DECIMALS'])
        
        # 1/ calculate Custom Base token price in ETH/BNB...
        # We could have used this also :
        #   custom_base_price_in_base = check_precise_price(outToken, weth, token['_WETH_DECIMALS'], token['_CONTRACT_DECIMALS'], token['_BASE_DECIMALS'])

        custom_base_price_in_base = calculate_custom_base_price(outToken, DECIMALS_OUT, DECIMALS_weth)

        # 2/ convert this Custom Base token price in $
        custom_base_price_in_dollars = float(custom_base_price_in_base) * float(token['_BASE_PRICE'])
        liquidity_amount_in_dollars = float(liquidity_amount) * float(custom_base_price_in_dollars)

        printt("Current", token['SYMBOL'], "Liquidity =", "{:.6f}".format(liquidity_amount_in_dollars), "$")
        
        if float(token['MINIMUM_LIQUIDITY_IN_DOLLARS']) <= float(liquidity_amount_in_dollars):
            printt_ok("MINIMUM_LIQUIDITY_IN_DOLLARS parameter =", int(token['MINIMUM_LIQUIDITY_IN_DOLLARS']), " --> Enough liquidity detected : Buy Signal Found!")
            return 1
        
        # This position isn't looking good. Inform the user, disable the token and break out of this loop
        else:
            printt_warn("------------------------------------------------", write_to_log=True)
            printt_warn("NOT ENOUGH LIQUIDITY", write_to_log=True)
            printt_warn("", write_to_log=True)
            printt_warn("- You have set MINIMUM_LIQUIDITY_IN_DOLLARS  =", token['MINIMUM_LIQUIDITY_IN_DOLLARS'], "$", write_to_log=True)
            printt_warn("- Liquidity detected for", token['SYMBOL'], "=", "{:.2f}".format(liquidity_amount_in_dollars), "$", write_to_log=True)
            printt_warn("--> Bot will not buy and disable token", write_to_log=True)
            printt_warn("------------------------------------------------", write_to_log=True)
            token['ENABLED'] = 'false'
            token['_QUOTE'] = 0
            return 0


def check_price(inToken, outToken, custom, routing, DECIMALS_IN, DECIMALS_OUT):
    # CHECK GET RATE OF THE TOKEn
    printt_debug("ENTER check_price")
    stamp = timestamp()
    
    if custom == 'false':
        # USECUSTOMBASEPAIR = false
        base = base_symbol
    
    if routing == 'true':
        # LIQUIDITYINNATIVETOKEN = true
        if outToken != weth:
            # LIQUIDITYINNATIVETOKEN = true
            # USECUSTOMBASEPAIR = true and token put in BASEADDRESS is different from WBNB / WETH
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS_IN, [inToken, weth, outToken]).call()[-1]
            printt_debug("price_check condition 1: ", price_check)
            tokenPrice = price_check / DECIMALS_OUT
        else:
            # LIQUIDITYINNATIVETOKEN = true
            # USECUSTOMBASEPAIR = false
            # or USECUSTOMBASEPAIR = true and token put in BASEADDRESS is WBNB / WETH (because outToken == weth)
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS_IN, [inToken, weth]).call()[-1]
            printt_debug("price_check condition 2: ", price_check)
            tokenPrice = price_check / DECIMALS_OUT
    
    else:
        # LIQUIDITYINNATIVETOKEN = false
        if outToken != weth:
            # LIQUIDITYINNATIVETOKEN = false
            # USECUSTOMBASEPAIR = true and token put in BASEADDRESS is different from WBNB / WETH
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS_IN, [inToken, outToken]).call()[-1]
            printt_debug("price_check3: ", price_check)
            tokenPrice = price_check / DECIMALS_OUT
        else:
            # LIQUIDITYINNATIVETOKEN = false
            # USECUSTOMBASEPAIR = true and token put in BASEADDRESS is WBNB / WETH (because outToken == weth)
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS_IN, [inToken, weth]).call()[-1]
            printt_debug("price_check4: ", price_check)
            tokenPrice = price_check / DECIMALS_OUT
    
    printt_debug("tokenPrice: ", tokenPrice)
    return tokenPrice


ORDER_HASH = {}
def check_precise_price(inToken, outToken, DECIMALS_weth, DECIMALS_IN, DECIMALS_OUT):
    # This function is made to calculate price of a token
    # It was first developed by the user Juan Lopez : thanks a lot :)
    # and then improved by Tsarbuig to make it work on custom base pair
    
    printt_debug("ENTER check_precise_price")

    if outToken != weth:
        printt_debug("ENTER check_precise_price condition 1")
        # First step : calculates the price of token in ETH/BNB
        pair_address = fetch_pair2(inToken, weth, factoryContract)
        pair_contract = getContractLP(pair_address)
        reserves = pair_contract.functions.getReserves().call()

        if ORDER_HASH.get(pair_address) is None:
            value0 = pair_contract.functions.token0().call()
            ORDER_HASH[pair_address] = (value0 == inToken)
        if not ORDER_HASH[pair_address]:
            tokenPrice1 = Decimal((reserves[0] / DECIMALS_weth) / (reserves[1] / DECIMALS_IN))
        else:
            tokenPrice1 = Decimal((reserves[1] / DECIMALS_weth) / (reserves[0] / DECIMALS_IN))
        printt_debug("tokenPrice1: ", tokenPrice1)
        
        # ------------------------------------------------------------------------
        # Second step : calculates the price of Custom Base pair in ETH/BNB
        pair_address = fetch_pair2(outToken, weth, factoryContract)
        pair_contract = getContractLP(pair_address)
        # We use cache to check price of Custom Base pair for price calculation. Price will be updated every 30s (ttl = 30)
        reserves = getReserves_with_cache(pair_contract)


        if ORDER_HASH.get(pair_address) is None:
            value0 = pair_contract.functions.token0().call()
            ORDER_HASH[pair_address] = (value0 == outToken)
        if not ORDER_HASH[pair_address]:
            tokenPrice2 = Decimal((reserves[0] / DECIMALS_weth) / (reserves[1] / DECIMALS_OUT))
        else:
            tokenPrice2 = Decimal((reserves[1] / DECIMALS_weth) / (reserves[0] / DECIMALS_OUT))
        printt_debug("tokenPrice2: ", tokenPrice2)
        
        # ------------------------------------------------------------------------
        # Third step : division
        #
        # Example with BUSD pair :
        #  - First step : token price = 0.000005 BNB
        #  - Second step : BUSD price = 1/500 BUSD
        #  --> Token price in BUSD = 0.00005 / (1/500) = 0.00005 * 500 = 0.00250 BUSD
        tokenPrice = tokenPrice1 / tokenPrice2
        
        
    else:
        printt_debug("ENTER check_precise_price condition 2")
        # USECUSTOMBASEPAIR = true and token put in BASEADDRESS is WBNB / WETH (because outToken == weth)
        # or USECUSTOMBASEPAIR = false
        pair_address = fetch_pair2(inToken, weth,factoryContract)
        printt_debug("check_precise_price pair_address:", pair_address)
        pair_contract = getContractLP(pair_address)
        reserves = pair_contract.functions.getReserves().call()
        
        if ORDER_HASH.get(pair_address) is None:
            value0 = pair_contract.functions.token0().call()
            ORDER_HASH[pair_address] = (value0 == inToken)
        if not ORDER_HASH[pair_address]:
            tokenPrice = Decimal((reserves[0] / DECIMALS_OUT) / (reserves[1] / DECIMALS_IN))
        else:
            tokenPrice = Decimal((reserves[1] / DECIMALS_OUT) / (reserves[0] / DECIMALS_IN))
        printt_debug("tokenPrice2: ", tokenPrice)
    
    return tokenPrice


def check_precise_price_new(inToken, outToken, DECIMALS_weth, DECIMALS_IN, DECIMALS_OUT):
    # This function is currently being reviewed and improved
    
    printt_debug("ENTER check_precise_price_new")
    pair_address = fetch_pair2(inToken, outToken, factoryContract)
    if pair_address != '0x0000000000000000000000000000000000000000':
        printt_debug("ENTER check_precise_price_new condition 0 direct pool LP")
        # First step : calculates the price of token in ETH/BNB
        
        pair_contract = getContractLP(pair_address)
        reserves = pair_contract.functions.getReserves().call()
        
        if ORDER_HASH.get(pair_address) is None:
            #value0 = pair_contract.functions.token0().call()
            ORDER_HASH[pair_address] = (inToken.lower() < outToken.lower())
        if not ORDER_HASH[pair_address]:
            tokenPrice1 = Decimal((reserves[0] / DECIMALS_OUT) / (reserves[1] / DECIMALS_IN))
        else:
            tokenPrice1 = Decimal((reserves[1] / DECIMALS_OUT) / (reserves[0] / DECIMALS_IN))
        return tokenPrice1
    
    if outToken != weth:
        printt_debug("ENTER check_precise_price_new condition 1")
        # First step : calculates the price of token in ETH/BNB
        
        pair_address = fetch_pair2(inToken, weth, factoryContract)
        pair_contract = getContractLP(pair_address)
        reserves = pair_contract.functions.getReserves().call()
        
        if ORDER_HASH.get(pair_address) is None:
            #value0 = pair_contract.functions.token0().call()
            ORDER_HASH[pair_address] = (inToken.lower() < weth.lower())
        if not ORDER_HASH[pair_address]:
            tokenPrice1 = Decimal((reserves[0] / DECIMALS_weth) / (reserves[1] / DECIMALS_IN))
        else:
            tokenPrice1 = Decimal((reserves[1] / DECIMALS_weth) / (reserves[0] / DECIMALS_IN))
        printt_debug("tokenPrice1: ", tokenPrice1)
        
        # ------------------------------------------------------------------------
        # Second step : calculates the price of Custom Base pair in ETH/BNB
        pair_address = fetch_pair2(outToken, weth, factoryContract)
        pair_contract = getContractLP(pair_address)
        reserves = pair_contract.functions.getReserves().call()

        if ORDER_HASH.get(pair_address) is None:
            #value0 = pair_contract.functions.token0().call()
            ORDER_HASH[pair_address] = (outToken.lower() < weth.lower())
        if not ORDER_HASH[pair_address]:
            tokenPrice2 = Decimal((reserves[0] / DECIMALS_weth) / (reserves[1] / DECIMALS_OUT))
        else:
            tokenPrice2 = Decimal((reserves[1] / DECIMALS_weth) / (reserves[0] / DECIMALS_OUT))
        printt_debug("tokenPrice2: ", tokenPrice2)
        
        # ------------------------------------------------------------------------
        # Third step : division
        # Example with BUSD pair :
        #  - First step : token price = 0.000005 BNB
        #  - Second step : BUSD price = 1/500 BUSD
        #  --> Token price in BUSD = 0.00005 / (1/500) = 0.00005 * 500 = 0.00250 BUSD
        tokenPrice = tokenPrice1 / tokenPrice2
    
    else:
        printt_debug("ENTER check_precise_price_new condition 2")
        # USECUSTOMBASEPAIR = true and token put in BASEADDRESS is WBNB / WETH (because outToken == weth)
        # or USECUSTOMBASEPAIR = false
        pair_address = fetch_pair2(inToken, weth, factoryContract)
        pair_contract = getContractLP(pair_address)
        reserves = pair_contract.functions.getReserves().call()
        
        if ORDER_HASH.get(pair_address) is None:
            value0 = pair_contract.functions.token0().call()
            ORDER_HASH[pair_address] = (value0 == inToken)
        if not ORDER_HASH[pair_address]:
            tokenPrice = Decimal((reserves[0] / DECIMALS_OUT) / (reserves[1] / DECIMALS_IN))
        else:
            tokenPrice = Decimal((reserves[1] / DECIMALS_OUT) / (reserves[0] / DECIMALS_IN))
        printt_debug("tokenPrice2: ", tokenPrice)
    
    return tokenPrice



@cached(cache=TTLCache(maxsize=128, ttl=30))
def calculate_base_price():
    # This function is made to calculate price of base token (ETH / BNB / AVAX / FTM / KCS...)
    # Price will be updated every 30s

    printt_debug("ENTER: calculate_base_price")

    if base_symbol == "BNB" or base_symbol == "BNB ":
        DECIMALS_STABLES = 1000000000000000000
        DECIMALS_BNB = 1000000000000000000

        # BUSD
        pair_address = '0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16'
        pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
        reserves = pair_contract.functions.getReserves().call()
        basePrice = Decimal((reserves[1] / DECIMALS_STABLES) / (reserves[0] / DECIMALS_BNB))
        printt_debug("BNB PRICE: ", "{:.6f}".format(basePrice))

    elif base_symbol == "BNBt":
        DECIMALS_STABLES = 1000000000000000000
        DECIMALS_BNB = 1000000000000000000

        # Fixed price of 500$ for BNB on testnet
        basePrice = Decimal(500)
        printt_debug("BNBt PRICE: ", "{:.6f}".format(basePrice))

    elif base_symbol == "ETH":
        DECIMALS_STABLES = 1000000
        DECIMALS_ETH = 1000000000000000000

        # USDT
        pair_address = '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852'
        printt_debug("pair_address:", pair_address)
        pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
        reserves = pair_contract.functions.getReserves().call()
        basePrice = Decimal((reserves[1] / DECIMALS_STABLES) / (reserves[0] / DECIMALS_ETH))
        printt_debug("ETH PRICE: ", "{:.6f}".format(basePrice))
    
    elif base_symbol == "ETHt":
        DECIMALS_STABLES = 1000000
        DECIMALS_BNB = 1000000000000000000

        # Fixed price of 3500$ for ETH on testnet
        basePrice = Decimal(3500)
        printt_debug("BNBt PRICE: ", "{:.6f}".format(basePrice))

    elif base_symbol == "AVAX":
        DECIMALS_STABLES = 1000000
        DECIMALS_ETH = 1000000000000000000
    
        # USDT 0xc7198437980c041c805a1edcba50c1ce5db95118
        pair_address = '0xe28984e1EE8D431346D32BeC9Ec800Efb643eef4'
        printt_debug("pair_address:", pair_address)
        pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
        reserves = pair_contract.functions.getReserves().call()
        basePrice = Decimal((reserves[1] / DECIMALS_STABLES) / (reserves[0] / DECIMALS_ETH))
        printt_debug("AVAX PRICE: ", "{:.6f}".format(basePrice))

    elif base_symbol == "AVAXt":
        DECIMALS_STABLES = 1000000
        DECIMALS_BNB = 1000000000000000000

        # Fixed price of 80 for AVAX on testnet
        basePrice = Decimal(80)
        printt_debug("BNBt PRICE: ", "{:.6f}".format(basePrice))

    elif base_symbol == "FTM":
        DECIMALS_STABLES = 1000000
        DECIMALS_ETH = 1000000000000000000
    
        # USDC 0x04068da6c83afcfa0e13ba15a6696662335d5b75
        pair_address = '0x2b4C76d0dc16BE1C31D4C1DC53bF9B45987Fc75c'

        printt_debug("pair_address:", pair_address)
        pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
        reserves = pair_contract.functions.getReserves().call()
        basePrice = Decimal((reserves[0] / DECIMALS_STABLES) / (reserves[1] / DECIMALS_ETH))
        printt_debug("FTM PRICE: ", "{:.6f}".format(basePrice))

    elif base_symbol == "KCS":
        DECIMALS_STABLES = 1000000000000000000
        DECIMALS_ETH = 1000000000000000000
    
        # USD 0x0039f574ee5cc39bdd162e9a88e3eb1f111baf48
    
        #address = Web3.toChecksumAddress('0x0039f574ee5cc39bdd162e9a88e3eb1f111baf48')
        #pair_address = fetch_pair2(address, weth, factoryContract)
    
        pair_address = '0x6c31e0F5c07b81A87120cc58c4dcc3fbafb00367'

        printt_debug("pair_address:", pair_address)
        pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
        reserves = pair_contract.functions.getReserves().call()
        basePrice = Decimal((reserves[0] / DECIMALS_STABLES) / (reserves[1] / DECIMALS_ETH))
        printt_debug("KCS PRICE: ", "{:.6f}".format(basePrice))
        
    elif base_symbol == "MATIC":
        DECIMALS_STABLES = 1000000
        DECIMALS_ETH = 1000000000000000000
    
        # USDT 0xc2132d05d31c914a87c6611c10748aeb04b58e8f
        # https://polygonscan.com/token/0xc2132d05d31c914a87c6611c10748aeb04b58e8f
        
        pair_address = '0x604229c960e5CACF2aaEAc8Be68Ac07BA9dF81c3'
        pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
        reserves = pair_contract.functions.getReserves().call()
        basePrice = Decimal((reserves[1] / DECIMALS_STABLES) / (reserves[0] / DECIMALS_ETH))
        printt_debug("MATIC PRICE: ", "{:.6f}".format(basePrice))
    
    else:
        printt_err("Unknown chain... please add it to calculate_base_price")
        basePrice = 0
    
    for stable_token in settings['_STABLE_BASES']:
        settings['_STABLE_BASES'][stable_token]['multiplier'] = float(basePrice)
    printt_debug("basePrice:", basePrice)

    printt(base_symbol, "price:", "{:.2f}".format(basePrice), "$")
    
    return basePrice


@cached(cache=TTLCache(maxsize=128, ttl=30))
def calculate_custom_base_price(outToken, DECIMALS_OUT, DECIMALS_weth):
    # This function is made to calculate price of custom base token in ETH/BNB...
    
    printt_debug("ENTER: calculate_custom_base_price")

    pair_address = fetch_pair2(outToken, weth, factoryContract)
    # pair_address = factoryContract.functions.getPair(outToken, weth).call()
    pair_contract = getContractLP(pair_address)
    # pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
    
    # We use cache to check price of Custom Base pair for price calculation. Price will be updated every 30s (ttl = 30)
    reserves = getReserves_with_cache(pair_contract)

    if ORDER_HASH.get(pair_address) is None:
        value0 = pair_contract.functions.token0().call()
        ORDER_HASH[pair_address] = (value0 == outToken)
    if not ORDER_HASH[pair_address]:
        custombasePrice = Decimal((reserves[0] / DECIMALS_weth) / (reserves[1] / DECIMALS_OUT))
    else:
        custombasePrice = Decimal((reserves[1] / DECIMALS_weth) / (reserves[0] / DECIMALS_OUT))
    
    printt_debug("custombasePrice: ", custombasePrice)

    return custombasePrice


def calculate_base_balance(token):
    # Function: calculate_base_balance
    # --------------------
    # calculate base balance
    # it is done before and after buy/sell so as the bot to be faster to make transactions
    #
    
    printt_debug("ENTER: calculate_base_balance()")

    # STEP 1 - Determine if wallet has minimum base balance
    # Bot will get your balance, and show an error if there is a problem with your node.
    if base_symbol == "ETH":
        minimumbalance = 0.05
    else:
        minimumbalance = 0.03

    try:
        eth_balance = Web3.fromWei(client.eth.getBalance(settings['WALLETADDRESS']), 'ether')
    except Exception as e:
        printt_err("ERROR with your node : please check logs.", write_to_log=True)
        logger1.exception(e)
        sys.exit()

    if eth_balance < minimumbalance:
        printt_err("You have less than 0.05 ETH or 0.03 BNB/FTM/MATIC/etc. token in your wallet, bot needs more to cover fees : please add some more in your wallet")
        printt_err("We know it can seem a lot, but the smart contracts used by Exchanges have automatic controls of minimal balance.")
        sleep(10)
        exit(1)

    # STEP 2 - update token['_BASE_BALANCE'] or token['_CUSTOM_BASE_BALANCE']
    if token['USECUSTOMBASEPAIR'].lower() == 'false':
        token['_BASE_BALANCE'] = Web3.fromWei(check_bnb_balance(), 'ether')
        printt_debug("token['_BASE_BALANCE'] in calculate_base_balance:", token['_BASE_BALANCE'])
    else:
        address = Web3.toChecksumAddress(token['BASEADDRESS'])
        DECIMALS = decimals(address)
        balance_check = check_balance(token['BASEADDRESS'], token['BASESYMBOL'])
        token['_CUSTOM_BASE_BALANCE'] = balance_check / DECIMALS
        printt_debug("balance 2959 case2:", token['_CUSTOM_BASE_BALANCE'])


def calculate_gas(token):
    # Function: calculate_gas
    # --------------------
    # calculate gas to use based on user settings and blockchain
    #
    # token - one element of the tokens{} dictionary
    #
    # returns - 0
    #         - sets token['_GAS_TO_USE'] to gas that should be used for transaction
    
    printt_debug("ENTER: calculate_gas()")
    
    if int(token['GASLIMIT']) < 250000:
        printt_info(
            "Your GASLIMIT parameter is too low : LimitSwap has forced it to 300000 otherwise your transaction would fail for sure. We advise you to raise it to 1000000.")
        token['GASLIMIT'] = 300000
    
    if token['GAS'] == 'boost' or token['GAS'] == 'BOOST' or token['GAS'] == 'Boost':
        if base_symbol == "BNB" or base_symbol == "BNB ":
            gas_price = 10
        else:
            gas_check = client.eth.gasPrice
            gas_price = gas_check / 1000000000
        
        printt_info("")
        printt_info("Current Gas Price =", gas_price)
        token['_GAS_TO_USE'] = (gas_price * ((int(token['BOOSTPERCENT'])) / 100)) + gas_price
        printt_info("Transaction for", token['SYMBOL'], "will be created with gas =", token['_GAS_TO_USE'])
        printt_info("")
    else:
        token['_GAS_TO_USE'] = int(token['GAS'])
    
    printt_debug("EXIT: calculate_gas()")
    return 0


def make_the_buy(inToken, outToken, buynumber, pwd, amount, gas, gaslimit, gaspriority, routing, custom, slippage, DECIMALS):
    # Function: make_the_buy
    # --------------------
    # creates BUY order with the good condition
    #
    # returns - nothing
    #
    printt_debug("ENTER make_the_buy")

    printt_ok("--------------------------------------------------------------------------------")
    printt_ok("KIND_OF_SWAP = base  --> bot will use BUYAMOUNTINBASE")
    printt_ok(" ")
    printt_ok("Did you know? You can now swap exact amount of tokens with KIND_OF_SWAP = tokens ")
    printt_ok("--------------------------------------------------------------------------------")

    # Choose proper wallet.
    if buynumber == 0:
        walletused = settings['WALLETADDRESS']
    if buynumber == 1:
        walletused = settings['WALLETADDRESS2']
    if buynumber == 2:
        walletused = settings['WALLETADDRESS3']
    if buynumber == 3:
        walletused = settings['WALLETADDRESS4']
    if buynumber == 4:
        walletused = settings['WALLETADDRESS5']
    
    
    if custom.lower() == 'false':
        # if USECUSTOMBASEPAIR = false
        
        if routing.lower() == 'false':
            # LIQUIDITYINNATIVETOKEN = false
            # USECUSTOMBASEPAIR = false
            printt_err("You have selected LIQUIDITYINNATIVETOKEN = false , so you must choose USECUSTOMBASEPAIR = true")
            printt_err("Please read Wiki carefully, it's very important you can lose money!!")
            sleep(10)
            sys.exit()
        else:
            # LIQUIDITYINNATIVETOKEN = true
            # USECUSTOMBASEPAIR = false
            amount_out = routerContract.functions.getAmountsOut(amount, [weth, outToken]).call()[-1]
            
            if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                amountOutMin = 0
            else:
                amountOutMin = int(amount_out * (1 - (slippage / 100)))

            deadline = int(time() + + 60)
            

            # THIS SECTION IS FOR MODIFIED CONTRACTS : EACH EXCHANGE NEEDS TO BE SPECIFIED
            # USECUSTOMBASEPAIR = false
            if modified == True:
                
                if settings["EXCHANGE"].lower() == 'koffeeswap':
                    printt_debug("make_the_buy condition 1", write_to_log=True)
                    transaction = routerContract.functions.swapExactKCSForTokens(
                        amountOutMin,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })
                
                elif settings["EXCHANGE"].lower() == 'pangolin' or settings["EXCHANGE"].lower() == 'traderjoe':
                    printt_debug("make_the_buy condition 2", write_to_log=True)
                    transaction = routerContract.functions.swapExactAVAXForTokens(
                        amountOutMin,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })

                elif settings["EXCHANGE"].lower() == 'bakeryswap':
                    printt_debug("make_the_buy condition 11", write_to_log=True)
                    transaction = routerContract.functions.swapExactBNBForTokens(
                        amountOutMin,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })

            
            else:
                # USECUSTOMBASEPAIR = false
                # This section is for exchange with Modified = false --> uniswap / pancakeswap / apeswap, etc.
                
                # Special condition on Uniswap, to implement EIP-1559

                if settings["EXCHANGE"].lower() == 'uniswap' or settings["EXCHANGE"].lower() == 'uniswaptestnet':
    
                    printt_debug("make_the_buy condition 3", write_to_log=True)
                    
                    transaction = routerContract.functions.swapExactETHForTokens(
                        amountOutMin,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                        'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                        'gas': gaslimit,
                        'value': amount,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused),
                        'type': "0x02"
                    })
                
                else:
                    # USECUSTOMBASEPAIR = false
                    # for all the rest of exchanges with Modified = false
                    
                    printt_debug("make_the_buy condition 4", write_to_log=True)
                    transaction = routerContract.functions.swapExactETHForTokens(
                        amountOutMin,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })
    
    else:
        # USECUSTOMBASEPAIR = true
        if inToken == weth:
            # USECUSTOMBASEPAIR = true
            # but user chose to put WETH or WBNB contract as CUSTOMBASEPAIR address
            amount_out = routerContract.functions.getAmountsOut(amount, [weth, outToken]).call()[-1]
            
            if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                amountOutMin = 0
            else:
                amountOutMin = int(amount_out * (1 - (slippage / 100)))
            
            deadline = int(time() + + 60)
            
            if settings["EXCHANGE"].lower() == 'uniswap' or settings["EXCHANGE"].lower() == 'uniswaptestnet':
                # Special condition on Uniswap, to implement EIP-1559
                printt_debug("make_the_buy condition 5", write_to_log=True)
                transaction = routerContract.functions.swapExactTokensForTokens(
                    amount,
                    amountOutMin,
                    [weth, outToken],
                    Web3.toChecksumAddress(walletused),
                    deadline
                ).buildTransaction({
                    'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                    'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                    'gas': gaslimit,
                    'from': Web3.toChecksumAddress(walletused),
                    'nonce': client.eth.getTransactionCount(walletused),
                    'type': "0x02"
                })
            
            else:
                printt_debug("make_the_buy condition 6", write_to_log=True)
                transaction = routerContract.functions.swapExactTokensForTokens(
                    amount,
                    amountOutMin,
                    [weth, outToken],
                    Web3.toChecksumAddress(walletused),
                    deadline
                ).buildTransaction({
                    'gasPrice': Web3.toWei(gas, 'gwei'),
                    'gas': gaslimit,
                    'from': Web3.toChecksumAddress(walletused),
                    'nonce': client.eth.getTransactionCount(walletused)
                })
        
        else:
            # LIQUIDITYINNATIVETOKEN = true
            # USECUSTOMBASEPAIR = true
            # Base Pair different from weth
            
            # We display a warning message if user tries to swap with too much money
            if (str(inToken).lower() == '0xe9e7cea3dedca5984780bafc599bd69add087d56' or str(
                    inToken).lower() == '0x55d398326f99059ff775485246999027b3197955' or str(
                inToken).lower() == '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d' or str(
                inToken).lower() == '0xdac17f958d2ee523a2206206994597c13d831ec7' or str(
                inToken).lower() == '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48') and (int(amount) / 1000000000000000000) > 2999:
                printt_info("YOU ARE TRADING WITH VERY BIG AMOUNT, BE VERY CAREFUL YOU COULD LOSE MONEY!!! TEAM RECOMMEND NOT TO DO THAT")
            
            if routing.lower() == 'true':
                amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth, outToken]).call()[-1]
                
                if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                    amountOutMin = 100
                else:
                    amountOutMin = int(amount_out * (1 - (slippage / 100)))
                    
                deadline = int(time() + + 60)

                if settings["EXCHANGE"].lower() == 'uniswap' or settings["EXCHANGE"].lower() == 'uniswaptestnet':
                    # USECUSTOMBASEPAIR = true
                    # Base Pair different from weth
                    # LIQUIDITYINNATIVETOKEN = true
                    
                    # Special condition on Uniswap, to implement EIP-1559
                    printt_debug("make_the_buy condition 7", write_to_log=True)
                    transaction = routerContract.functions.swapExactTokensForTokens(
                        amount,
                        amountOutMin,
                        [inToken, weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                        'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                        'gas': gaslimit,
                        'value': amount,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused),
                        'type': "0x02"
                    })
                
                else:
                    # USECUSTOMBASEPAIR = true
                    # Base Pair different from weth
                    # LIQUIDITYINNATIVETOKEN = true
                    # Exchange different from Uniswap
                    printt_debug("make_the_buy condition 8", write_to_log=True)
                    transaction = routerContract.functions.swapExactTokensForTokens(
                        amount,
                        amountOutMin,
                        [inToken, weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })
            
            else:
                # LIQUIDITYINNATIVETOKEN = false
                # USECUSTOMBASEPAIR = true
                # Base Pair different from weth
                
                # We display a warning message if user tries to swap with too much money
                if (str(inToken).lower() == '0xe9e7cea3dedca5984780bafc599bd69add087d56' or str(
                        inToken).lower() == '0x55d398326f99059ff775485246999027b3197955' or str(
                    inToken).lower() == '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d' or str(
                    inToken).lower() == '0xdac17f958d2ee523a2206206994597c13d831ec7' or str(
                    inToken).lower() == '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48') and (
                        int(amount) / DECIMALS) > 2999:
                    printt_info(
                        "YOU ARE TRADING WITH VERY BIG AMOUNT, BE VERY CAREFUL YOU COULD LOSE MONEY!!! TEAM RECOMMEND NOT TO DO THAT")
                
                amount_out = routerContract.functions.getAmountsOut(amount, [inToken, outToken]).call()[-1]
                
                if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                    amountOutMin = 100
                else:
                    amountOutMin = int(amount_out * (1 - (slippage / 100)))

                deadline = int(time() + + 60)
                
                if settings["EXCHANGE"].lower() == 'uniswap' or settings["EXCHANGE"].lower() == 'uniswaptestnet':
                    # LIQUIDITYINNATIVETOKEN = false
                    # USECUSTOMBASEPAIR = true
                    # Base Pair different from weth
                    # Special condition on Uniswap, to implement EIP-1559
                    printt_debug("make_the_buy condition 9", write_to_log=True)
                    transaction = routerContract.functions.swapExactTokensForTokens(
                        amount,
                        amountOutMin,
                        [inToken, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                        'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                        'gas': gaslimit,
                        'value': amount,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused),
                        'type': "0x02"
                    })
                
                else:
                    # LIQUIDITYINNATIVETOKEN = false
                    # USECUSTOMBASEPAIR = true
                    # Base Pair different from weth
                    # Exchange different from Uniswap
                    printt_debug("make_the_buy condition 10", write_to_log=True)

                    transaction = routerContract.functions.swapExactTokensForTokens(
                        amount,
                        amountOutMin,
                        [inToken, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })
    
    sync(inToken, outToken)
    
    if buynumber == 0:
        # No need to decrypt PRIVATEKEY because it was already decrypted in parse_wallet_settings()
        # Leave it like that because it's also used in Pre-Approve
        #
        # settings['PRIVATEKEY'] = settings['PRIVATEKEY'].replace('aes:', "", 1)
        # settings['PRIVATEKEY'] = cryptocode.decrypt(settings['PRIVATEKEY'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY'])
    if buynumber == 1:
        settings['PRIVATEKEY2'] = settings['PRIVATEKEY2'].replace('aes:', "", 1)
        settings['PRIVATEKEY2'] = cryptocode.decrypt(settings['PRIVATEKEY2'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY2'])
    if buynumber == 2:
        settings['PRIVATEKEY3'] = settings['PRIVATEKEY3'].replace('aes:', "", 1)
        settings['PRIVATEKEY3'] = cryptocode.decrypt(settings['PRIVATEKEY3'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY3'])
    if buynumber == 3:
        settings['PRIVATEKEY4'] = settings['PRIVATEKEY4'].replace('aes:', "", 1)
        settings['PRIVATEKEY4'] = cryptocode.decrypt(settings['PRIVATEKEY4'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY4'])
    if buynumber == 4:
        settings['PRIVATEKEY5'] = settings['PRIVATEKEY5'].replace('aes:', "", 1)
        settings['PRIVATEKEY5'] = cryptocode.decrypt(settings['PRIVATEKEY5'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY5'])
    
    try:
        return client.eth.sendRawTransaction(signed_txn.rawTransaction)
    finally:
        printt("Transaction Hash = ", Web3.toHex(client.keccak(signed_txn.rawTransaction)), write_to_log=True)

        tx_hash = client.toHex(client.keccak(signed_txn.rawTransaction))
        return tx_hash


def make_the_buy_exact_tokens(token_dict, inToken, outToken, buynumber, pwd, gaslimit, routing, custom, slippage, DECIMALS_FOR_AMOUNT, basebalance):
    # Function: make_the_buy_exact_tokens
    # --------------------
    # creates BUY order with the good condition
    #
    # returns - nothing
    #
    printt_debug("ENTER make_the_buy_exact_tokens")

    amount = int(float(token_dict['BUYAMOUNTINTOKEN']) * DECIMALS_FOR_AMOUNT)

    printt_debug("make_the_buy_exact_tokens amount:", amount, write_to_log=True)
    gas = token_dict['_GAS_TO_USE']
    gaslimit = token_dict['GASLIMIT']
    custom = token_dict['USECUSTOMBASEPAIR']
    routing = token_dict['LIQUIDITYINNATIVETOKEN']
    gaspriority = token_dict['GASPRIORITY_FOR_ETH_ONLY']
    token_symbol = token_dict['SYMBOL']

    
    # implementing an ugly fix for those shitty tokens with decimals = 9 to solve https://github.com/CryptoGnome/LimitSwap/issues/401
    # if DECIMALS == 1000000000:
    #     DECIMALS = 1000000000 * DECIMALS
    #     printt_debug("DECIMALS after fix applied for those shitty tokens with decimals = 9:", DECIMALS)

    DECIMALS = 1000000000000000000

    # Choose proper wallet.
    if buynumber == 0:
        walletused = settings['WALLETADDRESS']
    if buynumber == 1:
        walletused = settings['WALLETADDRESS2']
    if buynumber == 2:
        walletused = settings['WALLETADDRESS3']
    if buynumber == 3:
        walletused = settings['WALLETADDRESS4']
    if buynumber == 4:
        walletused = settings['WALLETADDRESS5']
    
    
    # We calculate Base Balance, to compare it with amount_in and display an error if user does not have enough balance

    base_balance_before_buy = basebalance * DECIMALS
    
    if custom.lower() == 'false':
        # if USECUSTOMBASEPAIR = false
        
        if routing.lower() == 'false':
            # LIQUIDITYINNATIVETOKEN = false
            # USECUSTOMBASEPAIR = false
            printt_err("You have selected LIQUIDITYINNATIVETOKEN = false , so you must choose USECUSTOMBASEPAIR = true")
            printt_err("Please read Wiki carefully, it's very important you can lose money!!")
            sleep(10)
            sys.exit()
        else:
            # LIQUIDITYINNATIVETOKEN = true
            # USECUSTOMBASEPAIR = false
            amount_in = routerContract.functions.getAmountsIn(amount, [weth, outToken]).call()[0]

            # Store this amount in _BASE_USED_FOR_TX, for use in build_sell_conditions() later
            token_dict['_BASE_USED_FOR_TX'] = amount_in / DECIMALS
            
            # Check if you have enough Base tokens in you wallet to make this order
            if amount_in > base_balance_before_buy:
                printt_err("- You have          ", base_balance_before_buy / DECIMALS, base_symbol, "in your wallet ")
                printt_err("- But you would need", amount_in / DECIMALS, base_symbol, "to buy this amount of tokens ")
                printt_err("--> buy cancelled ")
                sleep(10)
                sys.exit()
            
            # Check if the amount of Base tokens is not superior to MAX_BASE_AMOUNT_PER_EXACT_TOKENS_TRANSACTION
            if (amount_in / DECIMALS) > token_dict['MAX_BASE_AMOUNT_PER_EXACT_TOKENS_TRANSACTION']:
                printt_err("- This transaction would need", "{:.6f}".format(amount_in / DECIMALS), base_symbol, "to be done")
                printt_err("- And you asked the bot not to use more than", token_dict['MAX_BASE_AMOUNT_PER_EXACT_TOKENS_TRANSACTION'], base_symbol)
                printt_err("--> buy cancelled ")
                sleep(10)
                sys.exit()

            deadline = int(time() + + 60)

            printt_ok("-----------------------------------------------------------", write_to_log=True)
            printt_ok("KIND_OF_SWAP = tokens  --> bot will use BUYAMOUNTINTOKEN")
            printt_ok("")
            printt_warn("WARNING : buying exact amount of tokens only works with LIQUIDITYINNATIVETOKEN = true and USECUSTOMBASEPAIR = false")
            printt_ok("")
            printt_ok("Amount of tokens to buy        :", amount / DECIMALS_FOR_AMOUNT, token_symbol, write_to_log=True)
            printt_ok("Amount of base token to be used:", amount_in / DECIMALS, base_symbol, write_to_log=True)
            printt_ok("Current Base token balance     :", base_balance_before_buy / DECIMALS, base_symbol, write_to_log=True)
            printt_ok("(be careful you must have enough to pay fees in addition to this)", write_to_log=True)
            printt_ok("-----------------------------------------------------------", write_to_log=True)
            
            
            
            # THIS SECTION IS FOR MODIFIED CONTRACTS : EACH EXCHANGE NEEDS TO BE SPECIFIED
            # USECUSTOMBASEPAIR = false
            if modified == True:
                
                if settings["EXCHANGE"].lower() == 'koffeeswap':
                    printt_debug("make_the_buy_exact_tokens condition 1", write_to_log=True)
                    transaction = routerContract.functions.swapKCSForExactTokens(
                        amount,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount_in,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })
                
                elif settings["EXCHANGE"].lower() == 'pangolin' or settings["EXCHANGE"].lower() == 'traderjoe':
                    printt_debug("make_the_buy_exact_tokens condition 2", write_to_log=True)
                    transaction = routerContract.functions.swapAVAXForExactTokens(
                        amount,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount_in,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })

                elif settings["EXCHANGE"].lower() == 'bakeryswap':
                    printt_debug("make_the_buy_exact_tokens condition 11", write_to_log=True)
                    transaction = routerContract.functions.swapBNBForExactTokens(
                        amount,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount_in,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })

            else:
                # USECUSTOMBASEPAIR = false
                # This section is for exchange with Modified = false --> uniswap / pancakeswap / apeswap, etc.
                
                # Special condition on Uniswap, to implement EIP-1559
                
                if settings["EXCHANGE"].lower() == 'uniswap' or settings["EXCHANGE"].lower() == 'uniswaptestnet':
                    printt_debug("make_the_buy_exact_tokens condition 3", write_to_log=True)
                    
                    transaction = routerContract.functions.swapETHForExactTokens(
                        amount,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                        'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                        'gas': gaslimit,
                        'value': amount_in,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused),
                        'type': "0x02"
                    })
                
                else:
                    # USECUSTOMBASEPAIR = false
                    # for all the rest of exchanges with Modified = false
                    
                    printt_debug("make_the_buy_exact_tokens condition 4", write_to_log=True)

                    transaction = routerContract.functions.swapETHForExactTokens(
                        amount,
                        [weth, outToken],
                        Web3.toChecksumAddress(walletused),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'value': amount_in,
                        'from': Web3.toChecksumAddress(walletused),
                        'nonce': client.eth.getTransactionCount(walletused)
                    })

    else:
        # USECUSTOMBASEPAIR = true
        printt_err("Sorry, swap for exact tokens is only available for USECUSTOMBASEPAIR = false. Exiting.")
        sys.exit()

    
    if buynumber == 0:
        # No need to decrypt PRIVATEKEY because it was already decrypted in parse_wallet_settings()
        # Leave it like that because it's also used in Pre-Approve
        #
        # settings['PRIVATEKEY'] = settings['PRIVATEKEY'].replace('aes:', "", 1)
        # settings['PRIVATEKEY'] = cryptocode.decrypt(settings['PRIVATEKEY'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY'])
    if buynumber == 1:
        settings['PRIVATEKEY2'] = settings['PRIVATEKEY2'].replace('aes:', "", 1)
        settings['PRIVATEKEY2'] = cryptocode.decrypt(settings['PRIVATEKEY2'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY2'])
    if buynumber == 2:
        settings['PRIVATEKEY3'] = settings['PRIVATEKEY3'].replace('aes:', "", 1)
        settings['PRIVATEKEY3'] = cryptocode.decrypt(settings['PRIVATEKEY3'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY3'])
    if buynumber == 3:
        settings['PRIVATEKEY4'] = settings['PRIVATEKEY4'].replace('aes:', "", 1)
        settings['PRIVATEKEY4'] = cryptocode.decrypt(settings['PRIVATEKEY4'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY4'])
    if buynumber == 4:
        settings['PRIVATEKEY5'] = settings['PRIVATEKEY5'].replace('aes:', "", 1)
        settings['PRIVATEKEY5'] = cryptocode.decrypt(settings['PRIVATEKEY5'], pwd)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY5'])
    
    try:
        return client.eth.sendRawTransaction(signed_txn.rawTransaction)
    finally:
        printt("Transaction Hash = ", Web3.toHex(client.keccak(signed_txn.rawTransaction)), write_to_log=True)
        
        tx_hash = client.toHex(client.keccak(signed_txn.rawTransaction))
        return tx_hash


def wait_for_tx(token_dict, tx_hash, address, max_wait_time=60):
    # Function: wait_for_tx
    # --------------------
    # waits for a transaction to complete.
    #
    # token_dict - one element of the tokens{} dictionary
    # tx_hash - the transaction hash
    # address - the wallet address sending the transaction
    # max_wait_time - the maximum amoun of time in seconds to wait for a transaction to complete
    #
    # returns: 0 - txn_receipt['status'] on unknown
    #          1 - txn_receipt['status'] on success (sometimes reverted)
    #          2 - failed with an empty log (rejected by contract)
    #         -1 -  transaction failed due to unknown reason
    
    if max_wait_time > 0:
        exit_timestamp = time() + max_wait_time
    
    loop_iterations = 0
    got_receipt = False
    
    while got_receipt == False and exit_timestamp > time():
        
        if loop_iterations == 0:
            print(timestamp(), style.INFO, " Checking for transaction confirmation", style.RESET, sep='', end='',
                  flush=True)
        elif loop_iterations == 1:
            print(style.INFO, " (waiting ", max_wait_time, " seconds)", style.RESET, sep='', end="", flush=True)
        else:
            print(style.INFO, ".", style.RESET, sep='', end="", flush=True)
            sleep(1)
        loop_iterations = loop_iterations + 1
        
        try:
            txn_receipt = client.eth.wait_for_transaction_receipt(tx_hash, 1)
            got_receipt = True
        except Exception as e:
            txn_receipt = None
    
    print('')
    if got_receipt == True and len(txn_receipt['logs']) != 0:
        return_value = txn_receipt['status']
        # printt_ok("Transaction was successful with a status code of", return_value)
    
    elif got_receipt == True and len(txn_receipt['logs']) == 0:
        return_value = 2
        # printt_err("Transaction was rejected by contract with a status code of", txn_receipt['status'])
    
    elif txn_receipt is not None and txn_receipt['blockHash'] is not None:
        return_value = txn_receipt['status']
        # printt_warn("Transaction receipt returned with an unknown status and a status code of", return_value)
    
    else:
        # We definitely get this far if the node is down
        return_value = -1
    
    return return_value


def preapprove_base(token):
    # we approve the base pair, so as the bot is able to use it to buy token
    
    printt_debug("ENTER - preapprove_base()")
    
    printt("LimitSwap will now check approval of your Base or Custom Base for", token['SYMBOL'], ", to ensure you can use it")
    
    if token['USECUSTOMBASEPAIR'].lower() == 'false':
        balanceweth = Web3.fromWei(client.eth.getBalance(settings['WALLETADDRESS']), 'ether')
        check_approval(token, weth, balanceweth * decimals(weth), 'base_approve')
    else:
        balancebase = Web3.fromWei(check_balance(token['BASEADDRESS'], token['BASESYMBOL'], display_quantity=False), 'ether')
        check_approval(token, token['BASEADDRESS'], balancebase * decimals(token['BASEADDRESS']), 'base_approve')
 
    printt_debug("EXIT - preapprove_base()")


def buy(token_dict, inToken, outToken, pwd):
    # Function: buy
    # ----------------------------
    # purchases the amount of tokens specified for the contract specified
    #
    # token_dict - one element of the tokens{} dictionary
    # inToken - The contract address of the token we are looking to buy
    # outToken - The contract address of the toekn we are looking to sell
    #
    # returns: transaction hash
    #
    
    printt_debug("ENTER buy()")
    
    # Map variables until all code is cleaned up.
    amount = token_dict['BUYAMOUNTINBASE']
    slippage = token_dict['SLIPPAGE']
    gaslimit = token_dict['GASLIMIT']
    boost = token_dict['BOOSTPERCENT']
    fees = token_dict["HASFEES"]
    custom = token_dict['USECUSTOMBASEPAIR']
    symbol = token_dict['SYMBOL']
    routing = token_dict['LIQUIDITYINNATIVETOKEN']
    gaspriority = token_dict['GASPRIORITY_FOR_ETH_ONLY']
    multiplebuys = token_dict['MULTIPLEBUYS']
    buycount = token_dict['BUYCOUNT']
    CONTRACT_DECIMALS = token_dict['_CONTRACT_DECIMALS']

    # Check for amount of failed transactions before buy (MAX_FAILED_TRANSACTIONS_IN_A_ROW parameter)
    printt_debug("debug _FAILED_TRANSACTIONS:", token_dict['_FAILED_TRANSACTIONS'])
    if token_dict['_FAILED_TRANSACTIONS'] >= int(token_dict['MAX_FAILED_TRANSACTIONS_IN_A_ROW']):
        printt_err("---------------------------------------------------------------", write_to_log=True)
        printt_err("DISABLING", token_dict['SYMBOL'], write_to_log=True)
        printt_err("This token has reached maximum FAILED SIMULTANIOUS TRANSACTIONS", write_to_log=True)
        printt_err("---------------------------------------------------------------", write_to_log=True)
        token_dict['ENABLED'] = 'false'
        return False
    
    # Check for amount of success transactions before buy (MAX_FAILED_TRANSACTIONS_IN_A_ROW parameter)
    printt_debug("debug _SUCCESS_TRANSACTIONS:", token_dict['_SUCCESS_TRANSACTIONS'])
    if token_dict['_SUCCESS_TRANSACTIONS'] >= int(token_dict['MAX_SUCCESS_TRANSACTIONS_IN_A_ROW']):
        printt_ok("---------------------------------------------------------------", write_to_log=True)
        printt_ok("DISABLING", token_dict['SYMBOL'], write_to_log=True)
        printt_ok("This token has reached maximum SUCCESS SIMULTANIOUS TRANSACTIONS", write_to_log=True)
        printt_ok("---------------------------------------------------------------", write_to_log=True)
        token_dict['ENABLED'] = 'false'
        return False
    
    # Check if bot needs to wait before buy (BUYAFTER_XXX_SECONDS parameter)
    elif token_dict['BUYAFTER_XXX_SECONDS'] != 0:
        printt_info("Bot will wait", token_dict['BUYAFTER_XXX_SECONDS'], " seconds before buy, as you entered in BUYAFTER_XXX_SECONDS parameter")
        sleep(token_dict['BUYAFTER_XXX_SECONDS'])
        
    if int(gaslimit) < 250000:
        printt_info( "Your GASLIMIT parameter is too low : LimitSwap has forced it to 300000 otherwise your transaction would fail for sure. We advise you to raise it to 1000000.")
        gaslimit = 300000
    
    # Define balance before BUY
    #
    if custom.lower() == 'false':
        balance = token_dict['_BASE_BALANCE']
    else:
        balance = token_dict['_CUSTOM_BASE_BALANCE']

    printt_debug("Check balance:", balance)
    
    if balance > Decimal(amount) or token_dict['KIND_OF_SWAP'] == 'tokens':
        
        if base_symbol == "ETH" and token_dict['_GAS_IS_CALCULATED'] != True:
            # We calculate the GAS only for ETH, because it changes at every block on ETH.
            # On other blockchains, it's almost constant so ne need for it
            #
            # If WAIT_FOR_OPEN_TRADE was used and detected openTrading transaction in mempool :
            #   1/  _GAS_TO_USE was calculated by wait_for_open_trade  to be the same as openTrading transaction
            #   2/  _GAS_IS_CALCULATED was set to true, to understand that we don't need to re-calculate it again
            #
            # If WAIT_FOR_OPEN_TRADE was not used, let's calculate now how much gas we should use for this token for ETH only
            printt_debug("Need to re-calculate GAS price")
            calculate_gas(token_dict)

        # Stops transaction if GAS > MAXGAS
        printt_debug("_GAS_TO_USE is set to: ", token_dict['_GAS_TO_USE'])
        printt_debug("MAX_GAS is set to    : ", token_dict['MAX_GAS'])

        if token_dict['_GAS_TO_USE'] > token_dict['MAX_GAS']:
            printt_err("GAS = ", token_dict['_GAS_TO_USE'], "is superior to your MAX_GAS parameter (=", token_dict['MAX_GAS'], ") --> bot do not buy", )
            token_dict['ENABLED'] = 'false'
            return False

        gaslimit = int(gaslimit)
        slippage = int(slippage)
        amount = int(float(amount) * 1000000000000000000)
        buynumber = 0

        if multiplebuys.lower() == 'true':
            printt_warn("WARNING - Multiple Buys is an experimental feature : controls are only made for the first wallet")
            amount_of_buys = int(buycount)
            
            while True:
                if buynumber < amount_of_buys:
                    printt("Placing New Buy Order for wallet number:", buynumber)
                    if token_dict['KIND_OF_SWAP'] == 'tokens':
                        make_the_buy_exact_tokens(token_dict, inToken, outToken, buynumber, pwd, gaslimit, routing, custom, slippage, CONTRACT_DECIMALS, balance)
                    else:
                        make_the_buy(inToken, outToken, buynumber, pwd, amount, token_dict['_GAS_TO_USE'], gaslimit, gaspriority, routing, custom, slippage, CONTRACT_DECIMALS)
                    buynumber += 1
                else:
                    printt_ok("All BUYS orders have been sent - Stopping Bot")
                    sys.exit(0)
        else:
            if token_dict['KIND_OF_SWAP'] == 'tokens':
                tx_hash = make_the_buy_exact_tokens(token_dict, inToken, outToken, buynumber, pwd, gaslimit, routing, custom, slippage, CONTRACT_DECIMALS, balance)
            else:
                tx_hash = make_the_buy(inToken, outToken, buynumber, pwd, amount, token_dict['_GAS_TO_USE'], gaslimit, gaspriority, routing, custom, slippage, CONTRACT_DECIMALS)
    
            return tx_hash
    
    else:
        printt_debug(token_dict)
        printt_err("You don't have enough", token_dict['BASESYMBOL'], "in your wallet to make the BUY order of", token_dict['SYMBOL'], "--> bot do not buy", )
        calculate_base_balance(token_dict)
        return False


def sell(token_dict, inToken, outToken):
    # Map variables until all code is cleaned up.
    amount = token_dict['SELLAMOUNTINTOKENS']
    moonbag = token_dict['MOONBAG']
    gas = token_dict['_GAS_TO_USE']
    slippage = token_dict['SLIPPAGE']
    gaslimit = token_dict['GASLIMIT']
    boost = token_dict['BOOSTPERCENT']
    fees = token_dict["HASFEES"]
    custom = token_dict['USECUSTOMBASEPAIR']
    symbol = token_dict['SYMBOL']
    routing = token_dict['LIQUIDITYINNATIVETOKEN']
    gaspriority = token_dict['GASPRIORITY_FOR_ETH_ONLY']
    DECIMALS = token_dict['_CONTRACT_DECIMALS']

    # Check for amount of failed transactions before sell (MAX_FAILED_TRANSACTIONS_IN_A_ROW parameter)
    printt_debug("debug 2419 _FAILED_TRANSACTIONS:", token_dict['_FAILED_TRANSACTIONS'])
    if token_dict['_FAILED_TRANSACTIONS'] >= int(token_dict['MAX_FAILED_TRANSACTIONS_IN_A_ROW']):
        printt_err("---------------------------------------------------------------")
        printt_err("DISABLING", token_dict['SYMBOL'])
        printt_err("This token has reached maximum FAILED SIMULTANIOUS TRANSACTIONS")
        printt_err("---------------------------------------------------------------")
        token_dict['ENABLED'] = 'false'
        return False
    
    # Check for amount of success transactions before buy (MAX_FAILED_TRANSACTIONS_IN_A_ROW parameter)
    printt_debug("debug _SUCCESS_TRANSACTIONS:", token_dict['_SUCCESS_TRANSACTIONS'])
    if token_dict['_SUCCESS_TRANSACTIONS'] >= int(token_dict['MAX_SUCCESS_TRANSACTIONS_IN_A_ROW']):
        printt_ok("---------------------------------------------------------------", write_to_log=True)
        printt_ok("DISABLING", token_dict['SYMBOL'], write_to_log=True)
        printt_ok("This token has reached maximum SUCCESS SIMULTANIOUS TRANSACTIONS", write_to_log=True)
        printt_ok("---------------------------------------------------------------", write_to_log=True)
        token_dict['ENABLED'] = 'false'
        return False
    
    print(timestamp(), "Placing Sell Order " + symbol)
    
    # TODO : do not check balance and use balance = token_dict['_TOKEN_BALANCE']
    balance = check_balance(inToken, symbol)
    # balance = int(token_dict['_TOKEN_BALANCE'] * DECIMALS)
    
    # We ask the bot to check if your allowance is > to your balance. Use a 10000000000000000 multiplier for decimals.
    # UPDATE : disabled for best speed --> put after a Tx failure on sell()
    # check_approval(token_dict, inToken, balance * DECIMALS)
    
    if int(gaslimit) < 250000:
        gaslimit = 300000
        printt_info(
            "Your GASLIMIT parameter is too low: LimitSwap has forced it to 300000 otherwise your transaction would fail for sure. We advise you to raise it to 1000000.")
    
    if balance >= 1:
        
        # Calculate how much gas we should use for this token --> this is done on ETH only, since Gas is almost constant on other chains
        # For the other chains, Gas was calculated at bot launch
        if base_symbol == "ETH":
            calculate_gas(token_dict)
            printt_debug("gas: 2380", token_dict['_GAS_TO_USE'])
            gas = token_dict['_GAS_TO_USE']
        
        # Stops transaction if GAS > MAXGAS
        printt_debug("_GAS_TO_USE is set to: ", token_dict['_GAS_TO_USE'])
        printt_debug("MAX_GAS is set to    : ", token_dict['MAX_GAS'])

        if token_dict['_GAS_TO_USE'] > token_dict['MAX_GAS']:
            printt_err("GAS = ", token_dict['_GAS_TO_USE'], "is superior to your MAX_GAS parameter (=", token_dict['MAX_GAS'], ") --> bot do not sell and disable token", )
            token_dict['ENABLED'] = 'false'
            return False

        
        slippage = int(slippage)
        gaslimit = int(gaslimit)
        moonbag = int(Decimal(moonbag) * DECIMALS)
        printt_debug("2500 amount :", amount)
        printt_debug("2500 moonbag:", moonbag)
        printt_debug("2500 balance:", balance)
        
        #  Example 1 :
        #  ---------------
        #  BALANCE = 50                     |
        #  "SELLAMOUNTINTOKENS": "60",      | --> I sell 47 tokens
        #  "MOONBAG": "3",                  |
        #                                   | -->  if BALANCE < SELLAMOUNTINTOKENS
        #	                                |      then I sell BALANCE - MOONBAG
        #
        #  Example 2 :
        #  ---------------
        #  BALANCE = 50                     |
        #  "SELLAMOUNTINTOKENS": "10",      | --> I sell 10 tokens
        #  "MOONBAG": "3",                  |
        #                                   | -->  if BALANCE -  SELLAMOUNTINTOKENS > MOONBAG
        #	                                |      then I sell SELLAMOUNTINTOKENS
        #
        #  Example 3:
        #  ------------
        #  BALANCE = 10                     |
        #  "SELLAMOUNTINTOKENS": "20",      | --> I sell 7 tokens
        #  "MOONBAG": "3",                  |
        #                                   | -->   if BALANCE -  SELLAMOUNTINTOKENS < MOONBAG
        #                                   |  	    then I sell BALANCE - MOONBAG
        #
        #  Example 4 :
        #  ---------------
        #  BALANCE = 3                      |
        #  "SELLAMOUNTINTOKENS": "ALL",     | --> I sell 0 tokens
        #  "MOONBAG": "3" or "10",          |
        #                                   | -->  if BALANCE <= MOONBAG
        #	                                |      then I sell 0 token and disable trading
        #
        
        if amount == 'all' or amount == 'ALL' or amount == 'All':
            amount = int(Decimal(balance - moonbag))
            printt_debug("2635 amount :", amount)
            if amount <= 0:
                # Example 4
                printt_err("Not enough left to sell, would bust moonbag. Disabling the trade of this token.")
                amount = 0
                token_dict['ENABLED'] = 'false'
                return False
        else:
            amount = Decimal(amount) * DECIMALS
            printt_debug("2546 amount :", amount)
            printt_debug("2546 moonbag:", moonbag)
            printt_debug("2546 balance:", balance)
            
            if balance < amount:
                # Example 1
                printt_warn("You are trying to sell more ", symbol, " than you own in your wallet --> Bot will sell remaining amount, after deducing Moonbag")
                # it is same calculation as with amount == 'all'
                amount = int(Decimal(balance - moonbag))
                printt_debug("2556 amount :", amount)
                printt_debug("2556 moonbag:", moonbag)
                printt_debug("2556 balance:", balance)
                if amount <= 0:
                    printt_err("Not enough left to sell, would bust moonbag. Disabling the trade of this token.")
                    amount = 0
                    token_dict['ENABLED'] = 'false'
                    return False
            
            else:
                if (balance - amount) >= moonbag:
                    # Example 2
                    amount = int(Decimal(amount)) # just to show that we don't change it
                    printt_debug("2563 amount :", amount)
                    printt_debug("2563 moonbag:", moonbag)
                    printt_debug("2563 balance:", balance)
                    printt("Selling", amount / DECIMALS, symbol)
                elif (balance - amount) < moonbag:
                    # Example 3
                    amount = int(Decimal(balance - moonbag))
                    printt_debug("2570 amount :", amount)
                    printt_debug("2570 moonbag:", moonbag)
                    printt_debug("2570 balance:", balance)
                    printt("Selling", amount / DECIMALS , symbol)
                    if amount <= 0:
                        printt_err("Not enough left to sell, would bust moonbag. Disabling the trade of this token.")
                        amount = 0
                        token_dict['ENABLED'] = 'false'
                        return False
                elif balance == moonbag:
                    printt_err("Balance = Moonbag. Disabling the trade of this token.")
                    amount = 0
                    token_dict['ENABLED'] = 'false'
                    return False
                else:
                    printt_err("Not enough left to sell, would bust moonbag. Disabling the trade of this token.")
                    amount = 0
                    token_dict['ENABLED'] = 'false'
                    return False

        if custom.lower() == 'false':
            # USECUSTOMBASEPAIR = false
            sync(inToken, weth)
            
            amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth]).call()[-1]
            
            if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                amountOutMin = 0
            else:
                amountOutMin = int(amount_out * (1 - (slippage / 100)))
            
            deadline = int(time() + + 60)
            
            printt_debug("amount_out 2704  :", amount_out)
            printt_debug("amountOutMin 2704:", amountOutMin)
            if fees.lower() == 'true':
                
                # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
                if modified == True:
                    # USECUSTOMBASEPAIR = false
                    # HASFEES = true
                    
                    if settings["EXCHANGE"].lower() == 'koffeeswap':
                        printt_debug("sell condition 1", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForKCSSupportingFeeOnTransferTokens(
                            amount,
                            amountOutMin,
                            [inToken, weth],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })
                    
                    if settings["EXCHANGE"].lower() == 'pangolin' or settings["EXCHANGE"].lower() == 'traderjoe':
                        printt_debug("sell condition 2", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
                            amount,
                            amountOutMin,
                            [inToken, weth],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })

                    if settings["EXCHANGE"].lower() == 'bakeryswap':
                        printt_debug("sell condition 20", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForBNBSupportingFeeOnTransferTokens(
                            amount,
                            amountOutMin,
                            [inToken, weth],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })

                else:
                    # This section is for exchange with Modified = false --> uniswap / pancakeswap / apeswap, etc.
                    # USECUSTOMBASEPAIR = false
                    # HASFEES = true
                    printt_debug("sell condition 3", write_to_log=True)
                    transaction = routerContract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                        amount,
                        amountOutMin,
                        [inToken, weth],
                        Web3.toChecksumAddress(settings['WALLETADDRESS']),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                        'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                    })
            else:
                # USECUSTOMBASEPAIR = false
                # HASFEES = false
                
                # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
                if modified == True:
                    # USECUSTOMBASEPAIR = false
                    # HASFEES = false
                    # Modified = true
                    
                    if settings["EXCHANGE"].lower() == 'koffeeswap':
                        printt_debug("sell condition 4", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForKCS(
                            amount,
                            amountOutMin,
                            [inToken, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })
                    elif settings["EXCHANGE"].lower() == 'pangolin' or settings["EXCHANGE"].lower() == 'traderjoe':
                        printt_debug("sell condition 5", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForAVAX(
                            amount,
                            amountOutMin,
                            [inToken, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })
                        
                    elif settings["EXCHANGE"].lower() == 'bakeryswap':
                        printt_debug("sell condition 21", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForBNB(
                            amount,
                            amountOutMin,
                            [inToken, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })
                
                else:
                    # USECUSTOMBASEPAIR = false
                    # HASFEES = false
                    # Modified = false --> uniswap / pancakeswap / apeswap, etc.
                    
                    if settings["EXCHANGE"].lower() == 'uniswap' or settings["EXCHANGE"].lower() == 'uniswaptestnet':
                        # Special condition on Uniswap, to implement EIP-1559
                        printt_debug("sell condition 6", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForETH(
                            amount,
                            amountOutMin,
                            [inToken, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                            'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                            'gas': gaslimit,
                            'value': amount,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS']),
                            'type': "0x02"
                        })
                    
                    else:
                        # for all the rest of exchanges with Modified = false
                        printt_debug("sell condition 7", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForETH(
                            amount,
                            amountOutMin,
                            [inToken, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })
        
        else:
            # USECUSTOMBASEPAIR = true
            if outToken == weth:
                # if user has set WETH or WBNB as Custom base pair
                sync(inToken, outToken)
                amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth]).call()[-1]
                
                if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                    amountOutMin = 0
                else:
                    amountOutMin = int(amount_out * (1 - (slippage / 100)))
                    
                deadline = int(time() + + 60)
                
                if fees.lower() == 'true':
                    # USECUSTOMBASEPAIR = true
                    # HASFEES = true
                    
                    if int(gaslimit) < 950000:
                        gaslimit = 950000
                    
                    # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
                    if modified == True:
                        # USECUSTOMBASEPAIR = true
                        # HASFEES = true
                        # Modified = true
                        
                        if settings["EXCHANGE"].lower() == 'koffeeswap':
                            printt_debug("sell condition 8", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForKCSSupportingFeeOnTransferTokens(
                                amount,
                                amountOutMin,
                                [inToken, weth],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'gasPrice': Web3.toWei(gas, 'gwei'),
                                'gas': gaslimit,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                            })
                        
                        elif settings["EXCHANGE"].lower() == 'pangolin' or settings["EXCHANGE"].lower() == 'traderjoe':
                            printt_debug("sell condition 9", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
                                amount,
                                amountOutMin,
                                [inToken, weth],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'gasPrice': Web3.toWei(gas, 'gwei'),
                                'gas': gaslimit,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                            })
                            
                        elif settings["EXCHANGE"].lower() == 'bakeryswap':
                            printt_debug("sell condition 22", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForBNBSupportingFeeOnTransferTokens(
                                amount,
                                amountOutMin,
                                [inToken, weth],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'gasPrice': Web3.toWei(gas, 'gwei'),
                                'gas': gaslimit,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                            })
                            
                    else:
                        # USECUSTOMBASEPAIR = true
                        # HASFEES = true
                        # Modified = false
                        printt_debug("sell condition 10", write_to_log=True)
                        transaction = routerContract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                            amount,
                            amountOutMin,
                            [inToken, weth],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })
                else:
                    # USECUSTOMBASEPAIR = true
                    # HASFEES = false
                    printt_debug("sell condition 11", write_to_log=True)
                    transaction = routerContract.functions.swapExactTokensForTokens(
                        amount,
                        amountOutMin,
                        [inToken, weth],
                        Web3.toChecksumAddress(settings['WALLETADDRESS']),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                        'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                    })
            
            
            else:
                sync(inToken, outToken)
                
                if routing.lower() == 'false' and outToken != weth:
                    # LIQUIDITYINNATIVETOKEN = false
                    # USECUSTOMBASEPAIR = true
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, outToken]).call()[-1]
                    
                    if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                        amountOutMin = 0
                    else:
                        amountOutMin = int(amount_out * (1 - (slippage / 100)))

                    deadline = int(time() + + 60)
                    
                    if fees.lower() == 'true':
                        # LIQUIDITYINNATIVETOKEN = false
                        # USECUSTOMBASEPAIR = true
                        # HASFEES = true
                        if settings["EXCHANGE"].lower() == 'uniswap' or settings[
                            "EXCHANGE"].lower() == 'uniswaptestnet':
                            # Special condition on Uniswap, to implement EIP-1559
                            printt_debug("sell condition 12", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                amountOutMin,
                                [inToken, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                                'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                                'gas': gaslimit,
                                'value': amount,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS']),
                                'type': "0x02"
                            })
                        
                        else:
                            # for all the rest of exchanges
                            printt_debug("sell condition 13", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                amountOutMin,
                                [inToken, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'gasPrice': Web3.toWei(gas, 'gwei'),
                                'gas': gaslimit,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                            })
                    
                    else:
                        # LIQUIDITYINNATIVETOKEN = false
                        # USECUSTOMBASEPAIR = true
                        # HASFEES = false
                        if settings["EXCHANGE"].lower() == 'uniswap' or settings[
                            "EXCHANGE"].lower() == 'uniswaptestnet':
                            # Special condition on Uniswap, to implement EIP-1559
                            printt_debug("sell condition 14", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                amountOutMin,
                                [inToken, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                                'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                                'gas': gaslimit,
                                'value': amount,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS']),
                                'type': "0x02"
                            })
                        
                        else:
                            # for all the rest of exchanges
                            printt_debug("sell condition 15", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                amountOutMin,
                                [inToken, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'gasPrice': Web3.toWei(gas, 'gwei'),
                                'gas': gaslimit,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                            })
                
                elif routing.lower() == 'false' and outToken == weth:
                    # LIQUIDITYINNATIVETOKEN = false
                    # USECUSTOMBASEPAIR = true
                    # but user chose to put WETH or WBNB contract as CUSTOMBASEPAIR address
                    printt_err("ERROR IN YOUR TOKENS.JSON : YOU NEED TO CHOOSE THE PROPER BASE PAIR AS SYMBOL IF YOU ARE TRADING OUTSIDE OF NATIVE LIQUIDITY POOL")
                
                else:
                    printt_debug("amount 2824:", amount)
                    
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth, outToken]).call()[-1]
                    
                    if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                        amountOutMin = 0
                    else:
                        amountOutMin = int(amount_out * (1 - (slippage / 100)))

                    deadline = int(time() + + 60)
                    
                    if fees.lower() == 'true':
                        # HASFEES = true
                        if settings["EXCHANGE"].lower() == 'uniswap' or settings[
                            "EXCHANGE"].lower() == 'uniswaptestnet':
                            # Special condition on Uniswap, to implement EIP-1559
                            printt_debug("sell condition 16", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                amountOutMin,
                                [inToken, weth, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                                'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                                'gas': gaslimit,
                                'value': amount,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS']),
                                'type': "0x02"
                            })
                        
                        else:
                            printt_debug("sell condition 17", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                amountOutMin,
                                [inToken, weth, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'gasPrice': Web3.toWei(gas, 'gwei'),
                                'gas': gaslimit,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                            })
                    
                    else:
                        # HASFEES = false
                        if settings["EXCHANGE"].lower() == 'uniswap' or settings[
                            "EXCHANGE"].lower() == 'uniswaptestnet':
                            # Special condition on Uniswap, to implement EIP-1559
                            printt_debug("sell condition 18", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                amountOutMin,
                                [inToken, weth, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'maxFeePerGas': Web3.toWei(gas, 'gwei'),
                                'maxPriorityFeePerGas': Web3.toWei(gaspriority, 'gwei'),
                                'gas': gaslimit,
                                'value': amount,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS']),
                                'type': "0x02"
                            })
                        else:
                            printt_debug("sell condition 19", write_to_log=True)
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                amountOutMin,
                                [inToken, weth, outToken],
                                Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                deadline
                            ).buildTransaction({
                                'gasPrice': Web3.toWei(gas, 'gwei'),
                                'gas': gaslimit,
                                'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                                'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                            })
        
        sync(inToken, outToken)
        signed_txn = client.eth.account.signTransaction(transaction, private_key=settings['PRIVATEKEY'])
        
        try:
            return client.eth.sendRawTransaction(signed_txn.rawTransaction)
        finally:
            printt("Transaction Hash = ", Web3.toHex(client.keccak(signed_txn.rawTransaction)), write_to_log=True)
            tx_hash = client.toHex(client.keccak(signed_txn.rawTransaction))
            return tx_hash
    else:
        printt("Your", token_dict['SYMBOL'], "balance is very small (< 1), so LimitSwap will not try to sell, so as not to waste fees.")
        return False


def benchmark():
    printt_ok('*** Start Benchmark Mode ***', write_to_log=True)
    printt('This benchmark will use your tokens.json: ADDRESS / LIQUIDITYINNATIVETOKEN / USECUSTOMBASEPAIR / BASEADDRESS')
    rounds = 60
    printt("Benchmark running, we will do", rounds,"tests. Please wait a few seconds...")

# Check RPC Node latency
    k = 0
    if my_provider[0].lower() == 'h' or my_provider[0].lower() == 'w':
        provider = my_provider.replace('wss://', 'https://')
        for i in range(5):
            response = requests.post(provider)
            k = k + response.elapsed.total_seconds()
            sleep(0.05)
        printt('RPC Node average latency :', str(int((k/5)*1000)), 'ms', write_to_log=True)

# Check 'check_price' function speed
    token = load_tokens_file(command_line_args.tokens, False)
    token[0]['_WETH_DECIMALS'] = int(decimals(weth))
    token[0]['_CONTRACT_DECIMALS'] = int(decimals(token[0]['ADDRESS']))
    inToken = Web3.toChecksumAddress(token[0]['ADDRESS'])
    if token[0]['USECUSTOMBASEPAIR'] == 'true':
        printt('Testing with USECUSTOMBASEPAIR ')
    
        token[0]['_BASE_DECIMALS'] = int(decimals(token[0]['BASEADDRESS']))
        outToken = Web3.toChecksumAddress(token[0]['BASEADDRESS'])
    else:
        token[0]['_BASE_DECIMALS'] = int(decimals(weth))
        outToken = weth
        
    start_time = time()
    for i in range(rounds):
        try:
            tmp = check_price(inToken, outToken, token[0]['USECUSTOMBASEPAIR'], token[0]['LIQUIDITYINNATIVETOKEN'], token[0]['_CONTRACT_DECIMALS'], token[0]['_BASE_DECIMALS'])
        except Exception:
            pass

    end_time = time()
    printt('Check_price function     :', round((rounds/(end_time - start_time)), 2), 'query/s Total:', round((end_time - start_time), 2), "s", write_to_log=True)

# Check 'check_precise_price' function speed
    i = 0
    start_time = time()
    for i in range(rounds):
        try:
            tmp = check_precise_price(inToken, outToken, token[0]['_WETH_DECIMALS'], token[0]['_CONTRACT_DECIMALS'], token[0]['_BASE_DECIMALS'])
        except Exception:
            pass
    end_time = time()
    printt('Check_precise_price func :', round((rounds/(end_time - start_time)), 2), 'query/s Total:', round((end_time - start_time), 2), "s", write_to_log=True)

# Check 'check_pool' function speed
    i = 0
    start_time = time()
    for i in range(rounds):
        try:
            check_pool(inToken, weth, token[0]['_BASE_DECIMALS'])
        except Exception:
            pass
    end_time = time()
    printt('Check_pool function      :', round((rounds/(end_time - start_time)), 2), 'query/s Total:', round((end_time - start_time), 2), "s", write_to_log=True)

    printt_ok('*** End Benchmark Mode ***', write_to_log=True)
    sys.exit()
    
    
def run():
    global tokens_json_already_loaded
    global _COST_PER_TOKEN_saved
    global _PREVIOUS_TOKEN_BALANCE_saved
    
    tokens_json_already_loaded = tokens_json_already_loaded + 1
    try:
        
        # Load tokens from file
        if tokens_json_already_loaded == 1:
            tokens = load_tokens_file(command_line_args.tokens, True)
        if tokens_json_already_loaded > 1:
            tokens = reload_tokens_file(command_line_args.tokens, True)
        # Display the number of token pairs we're attempting to trade
        token_list_report(tokens)
        
        # Check to see if the user wants to pre-approve token transactions. If they do, work through that approval process
        # UPDATE 01/01/2022 : removed here, to make the "instantafterbuy" default preapprove behaviour
        # UPDATE 01/04/2022 : after a bug report, I realized that you need to approve the Base pair, so as the bot is able to use it to buy token
        # UPDATE 07/01 : removed as it seems buggy
        # preapprove_base(tokens)
        
        # For each token check to see if the user wants to run a rugdoc check against them.
        #   then run the rugdoctor check and prompt the user if they want to continue trading
        #   the token
        #
        # TODO PRUNE: Prune tokens if the user doesn't want to trade them. Exit only if we don't have any more tokens left
        # TODO ARG: Implement an argument that auto accepts or prunes tokens that are rejected/accepted by the rugdoc check
        for token in tokens:
            
            # Calculate contract / custom base pair / weth decimals
            printt_debug("Pre-calculations for token:", token['ADDRESS'], ": Gas / Decimals / Balance / RugDoc check")
            
            token['_CONTRACT_DECIMALS'] = int(decimals(token['ADDRESS']))
            printt_debug("token['_CONTRACT_DECIMALS']:", token['_CONTRACT_DECIMALS'])

            if token['USECUSTOMBASEPAIR'] == 'true':
                token['_BASE_DECIMALS'] = int(decimals(token['BASEADDRESS']))
            else:
                token['_BASE_DECIMALS'] = int(decimals(weth))

            token['_WETH_DECIMALS'] = int(decimals(weth))
            printt_debug("token['_WETH_DECIMALS']    :", token['_WETH_DECIMALS'])
            
            # Calculate base price
            token['_BASE_PRICE'] = calculate_base_price()
          
            # Calculate sell price
            # If _COST_PER_TOKEN ==0, it means the bot did not buy token yet --> before_buy condition
            if token['_COST_PER_TOKEN'] == 0 :
                build_sell_conditions(token, 'before_buy')
            else:
                build_sell_conditions(token, 'after_buy')
                
            printt_debug("token['_CALCULATED_SELLPRICEINBASE']:", token['_CALCULATED_SELLPRICEINBASE'])
            printt_debug("token['_CALCULATED_STOPLOSSPRICEINBASE']:", token['_CALCULATED_STOPLOSSPRICEINBASE'])
            
            # Determine token name + base symbol to display
            if token['USECUSTOMBASEPAIR'] == 'true':
                token['_PAIR_TO_DISPLAY'] = token['SYMBOL'] + "/" + token['BASESYMBOL']
            else:
                token['_PAIR_TO_DISPLAY'] = token['SYMBOL'] + "/" + base_symbol

            # Check to see if we have any tokens in our wallet already
            token['_TOKEN_BALANCE'] = check_balance(token['ADDRESS'], token['SYMBOL'], display_quantity=False) / token['_CONTRACT_DECIMALS']
            token['_PREVIOUS_TOKEN_BALANCE'] = token['_TOKEN_BALANCE']
            if token['_TOKEN_BALANCE'] > 0:
                printt("")
                printt("Your wallet already owns : ", token['_TOKEN_BALANCE'], token['SYMBOL'], write_to_log=True)
                if token['_TOKEN_BALANCE'] > float(token['MAXTOKENS']):
                    token['_REACHED_MAX_TOKENS'] = True
                    printt("")
                    printt_warn("You have reached MAXTOKENS for token ", token['SYMBOL'], "--> bot stops to buy", write_to_log=True)
                    printt("")

            # Calculate balances prior to buy() to accelerate buy()
            calculate_base_balance(token)
            
            # Calculate how much gas we should use for this token
            calculate_gas(token)
            
            # Call of RugDoc API if parameter is set to True
            if token['RUGDOC_CHECK'] == 'true':
                check_rugdoc_api(token)
                
        load_token_file_increment = 0
        tokens_file_modified_time = os.path.getmtime(command_line_args.tokens)
        first_liquidity_check = True
        
        while True:
            
            # Check to see if the tokens file has changed every 10 iterations
            if load_token_file_increment > 1:
                modification_check = tokens_file_modified_time
                tokens_file_modified_time = os.path.getmtime(command_line_args.tokens)
                if (modification_check != tokens_file_modified_time):
                    #ask for user password to change tokens.json, if --password_on_change or PASSWORD_ON_CHANGE option is used
                    if command_line_args.password_on_change or settings['PASSWORD_ON_CHANGE'] == 'true':
                        pkpassword = pwinput.pwinput(prompt="\nPlease enter your password to change tokens.json: ")
                        
                        if pkpassword != userpassword:
                            printt_err("ERROR: Your private key decryption password is incorrect")
                            printt_err("Please re-launch the bot and try again")
                            sleep(10)
                            sys.exit()

                    tokens_json_already_loaded = tokens_json_already_loaded + 1
                    raise Exception("tokens.json has been changed, reloading.")
            else:
                load_token_file_increment = load_token_file_increment + 1
            
            for token in tokens:
                printt_debug("entering token :", token['SYMBOL'])

                if token['ENABLED'] == 'true':
                    
                    # Set the checksum addressed for the addresses we're working with
                    # inToken is the token you want to BUY (example : CAKE)
                    # TODO: We should do this once and store the values
                    inToken = Web3.toChecksumAddress(token['ADDRESS'])
                    
                    # outToken is the token you want to TRADE WITH (example : ETH or USDT)
                    if token['USECUSTOMBASEPAIR'] == 'true':
                        outToken = Web3.toChecksumAddress(token['BASEADDRESS'])
                    else:
                        outToken = weth
                    
                    #
                    # CHECK LIQUIDITY
                    #
                    # If liquidity has not been found yet (token['_LIQUIDITY_READY'] == False)
                    # Bot will display "Not Listed For Trade Yet... waiting for liquidity to be added on exchange"
                    #
                    # There are 2 cases :
                    # - Case 1: LIQUIDITYINNATIVETOKEN = true  --> we will snipe using ETH / BNB liquidity --> we use check_pool with weth
                    # - Case 2: LIQUIDITYINNATIVETOKEN = false --> we will snipe using Custom Base Pair    --> we use check_pool with outToken
                    #
                    printt_debug("token['_LIQUIDITY_READY']:", token['_LIQUIDITY_READY'], "for token :", token['SYMBOL'])
                    
                    if token['_LIQUIDITY_READY'] == False:
                        try:
                            if token['LIQUIDITYINNATIVETOKEN'] == 'true':
                                #       Case 1/ LIQUIDITYINNATIVETOKEN = true  --> we will snipe using ETH / BNB liquidity --> we use check_pool with weth
                                pool = check_pool(inToken, weth, token['_BASE_DECIMALS'])
                            else:
                                #       Case 2/ LIQUIDITYINNATIVETOKEN = false --> we will snipe using Custom Base Pair    --> we use check_pool with outToken
                                pool = check_pool(inToken, outToken, token['_BASE_DECIMALS'])
        
                            # Setting a minimum of 0.1 quantity of liquidity, to avoid users being scammed
                            if pool > 0.1:
                                token['_LIQUIDITY_READY'] = True
                                printt_ok("Found", "{0:.4f}".format(pool), "liquidity for", token['_PAIR_SYMBOL'])
                                if first_liquidity_check == True and command_line_args.reject_already_existing_liquidity:
                                    printt("Rejecting", token['_PAIR_SYMBOL'], "because it already had liquidity.")
                                    token['ENABLED'] = 'false'
                                pass
                            else:
                                printt_repeating(token, token['_PAIR_SYMBOL'] + " Not Listed For Trade Yet... waiting for liquidity to be added on exchange")
                                printt_debug(token)
                                continue
                        except Exception:
                            printt_repeating(token, token['_PAIR_SYMBOL'] + " Not Listed For Trade Yet... waiting for liquidity to be added on exchange")
                            printt_debug(token)
                            continue
                            
                    #
                    #  PRICE CHECK
                    #    Check the latest price on this token and record information on the price that we may
                    #    need to use later
                    #
                    token['_PREVIOUS_QUOTE'] = token['_QUOTE']
                    
                    if token['LIQUIDITYINNATIVETOKEN'] == 'true':
                        token['_QUOTE'] = check_precise_price(inToken, outToken, token['_WETH_DECIMALS'], token['_CONTRACT_DECIMALS'], token['_BASE_DECIMALS'])
                    else:
                        # if token['LIQUIDITYINNATIVETOKEN'] == 'false', we need to use check_price, because check_precise_price do not work for now
                        # TODO : improve check_precise_price
                        token['_QUOTE'] = check_price(inToken, outToken, token['USECUSTOMBASEPAIR'], token['LIQUIDITYINNATIVETOKEN'], token['_CONTRACT_DECIMALS'], token['_BASE_DECIMALS'])
                    
                    if token['_ALL_TIME_HIGH'] == 0 and token['_ALL_TIME_LOW'] == 0:
                        token['_ALL_TIME_HIGH'] = token['_QUOTE']
                        token['_ALL_TIME_LOW'] = token['_QUOTE']
                    
                    elif token['_QUOTE'] > token['_ALL_TIME_HIGH']:
                        token['_ALL_TIME_HIGH'] = token['_QUOTE']
                    
                    elif token['_QUOTE'] < token['_ALL_TIME_LOW']:
                        token['_ALL_TIME_LOW'] = token['_QUOTE']
                    
                    # If we're still in the market to buy tokens, the print the buy message
                    # added the condition "if token['_PREVIOUS_QUOTE'] != 0" to avoid having a green line in first position and make trading_is_on work
                    if token['_PREVIOUS_QUOTE'] != 0 and token['_QUOTE'] != 0:  # and token['_REACHED_MAX_TOKENS'] == False:
                        printt_buy_price(token, token['_QUOTE'])
                    
                    #
                    # BUY CHECK
                    #   If the liquidity check has returned a quote that is less than our BUYPRICEINBASE and we haven't informrmed
                    #   the user that we've reached the maximum number of tokens, check for other criteria to buy.
                    #
                    
                    if token['_QUOTE'] != 0 and token['_QUOTE'] < Decimal(token['BUYPRICEINBASE']) and token['_REACHED_MAX_SUCCESS_TX'] == False and token['_REACHED_MAX_TOKENS'] == False and token['ENABLED'] == 'true':
    
                        #
                        # OPEN TRADE CHECK
                        #   If the option is selected, bot wait for trading_is_on == True to create a BUY order
                        #
    
                        if token['WAIT_FOR_OPEN_TRADE'].lower() == 'true' or token['WAIT_FOR_OPEN_TRADE'].lower() == 'true_no_message' or token['WAIT_FOR_OPEN_TRADE'] == 'mempool':
                            wait_for_open_trade(token, inToken, outToken)
    
                        printt_debug(token)
                        #
                        # PURCHASE POSITION
                        #   If we've passed all checks, attempt to purchase the token
                        #
                        printt_debug("===========================================")
                        printt_debug("token['_QUOTE']:", token['_QUOTE'])
                        printt_debug("Buy Price:", Decimal(token['BUYPRICEINBASE']))
                        printt_debug("_REACHED_MAX_SUCCESS_TX:", token['_REACHED_MAX_SUCCESS_TX'])
                        printt_debug("_REACHED_MAX_TOKENS:", token['_REACHED_MAX_TOKENS'])
                        printt_debug("===========================================")
                        
                        log_price = "{:.18f}".format(token['_QUOTE'])
                        printt_ok("")
                        printt_ok("-----------------------------------------------------------", write_to_log=True)
                        printt_ok("Buy Signal Found =-= Buy Signal Found =-= Buy Signal Found ", write_to_log=True)
                        printt_ok("", write_to_log=True)
                        printt_ok("Buy price in", token['_PAIR_TO_DISPLAY'], ":", log_price, write_to_log=True)
                        printt_ok("-----------------------------------------------------------", write_to_log=True)
                        printt_ok("")

                        #
                        # LIQUIDITY CHECK
                        #   If the option is selected
                        #
                        
                        if token["MINIMUM_LIQUIDITY_IN_DOLLARS"] != 0:
                            liquidity_result = check_liquidity_amount(token, token['_BASE_DECIMALS'], token['_WETH_DECIMALS'])
                            if liquidity_result == 0:
                                continue
                            else:
                                pass
                        
                        if command_line_args.sim_buy:
                            tx = command_line_args.sim_buy
                        else:
                            tx = buy(token, outToken, inToken, userpassword)

                        if tx != False:
                            txbuyresult = wait_for_tx(token, tx, token['ADDRESS'])
                            printt_debug("wait_for_tx result is : ", txbuyresult)
                            if txbuyresult != 1:
                                # transaction is a FAILURE
                                printt_err("-------------------------------", write_to_log=True)
                                printt_err("   BUY TRANSACTION FAILURE !")
                                printt_err("-------------------------------")
                                printt_err("Type of failures and possible causes:")
                                printt_err("- TRANSFER_FROM_FAILED         --> GASLIMIT too low. Raise it to GASLIMIT = 1000000 at least")
                                printt_err("- TRANSFER_FROM_FAILED         --> Your BASE token is not approved for trade")
                                printt_err("- INSUFFICIENT_OUTPUT_AMOUNT   --> SLIPPAGE too low")
                                printt_err("- TRANSFER_FAILED              --> Trading is not enabled. Use WAIT_FOR_OPEN_TRADE parameter after reading wiki")
                                printt_err("- TRANSFER_FAILED              --> There is a whitelist")
                                printt_err("- Sorry, We are unable to locate this TxnHash --> You don't have enough funds on your wallet to cover fees")
                                printt_err("- ... or your node is not working well")
                                printt_err("-------------------------------")

                                # Apprise notification
                                if settings['ENABLE_APPRISE_NOTIFICATIONS'] == 'true':
                                    apprise_notification(token, 'buy_failure')

                                # increment _FAILED_TRANSACTIONS amount
                                token['_FAILED_TRANSACTIONS'] += 1
                                printt_debug("3813 _FAILED_TRANSACTIONS:", token['_FAILED_TRANSACTIONS'])
                                
                                # Check if Base pair is approved, in case of TRANSFER_FROM_FAILED
                                preapprove_base(token)

                                # If user selected WAIT_FOR_OPEN_TRADE = 'XXX_after_buy_tx_failed" bot enters WAIT_FOR_OPEN_TRADE mode
                                if token['WAIT_FOR_OPEN_TRADE'].lower() == 'true_after_buy_tx_failed' or token['WAIT_FOR_OPEN_TRADE'].lower() == 'true_after_buy_tx_failed_no_message' or token['WAIT_FOR_OPEN_TRADE'] == 'mempool_after_buy_tx_failed':
                                    wait_for_open_trade(token, inToken, outToken)

                            else:
                                # transaction is a SUCCESS
                                printt_ok("----------------------------------", write_to_log=True)
                                printt_ok("SUCCESS : your buy Tx is confirmed", write_to_log=True)
                                printt_ok("", write_to_log=True)

                                # Save previous token balance before recalculating
                                token['_PREVIOUS_TOKEN_BALANCE'] = token['_TOKEN_BALANCE']
                                
                                # Re-calculate balances after buy()
                                calculate_base_balance(token)
                                
                                # Check the balance of our wallet
                                DECIMALS = token['_CONTRACT_DECIMALS']
                                token['_TOKEN_BALANCE'] = check_balance(inToken, token['SYMBOL'],display_quantity=True) / DECIMALS
                                printt_ok("", write_to_log=True)
                                printt_ok("You bought", token['_TOKEN_BALANCE'] - token['_PREVIOUS_TOKEN_BALANCE'], token['SYMBOL'], "tokens", write_to_log=True)
                                printt_ok("----------------------------------", write_to_log=True)
                                
                                # Apprise notification
                                if settings['ENABLE_APPRISE_NOTIFICATIONS'] == 'true':
                                    apprise_notification(token,'buy_success')

                                # if user has chose the option "instantafterbuy", token is approved right after buy order is confirmed.
                                if (settings['PREAPPROVE'] == 'instantafterbuy' or settings['PREAPPROVE'] == 'true'):
                                    check_approval(token, token['ADDRESS'], token['_TOKEN_BALANCE'] * DECIMALS, 'preapprove')

                                # Optional cooldown after SUCCESS buy, if you use XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX parameter
                                if token['XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX'] != 0:
                                    printt_info("Bot will wait", token['XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX'], "seconds after BUY, due to XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX parameter", write_to_log=True)
                                    sleep(token['XXX_SECONDS_COOLDOWN_AFTER_BUY_SUCCESS_TX'])

                                # increment _SUCCESS_TRANSACTIONS amount
                                token['_SUCCESS_TRANSACTIONS'] += 1
                                printt_debug("3840 _SUCCESS_TRANSACTIONS:", token['_SUCCESS_TRANSACTIONS'])
                                
                                # Check if MAX_SUCCESS_TRANSACTIONS_IN_A_ROW is reached or not
                                if token['_SUCCESS_TRANSACTIONS'] >= token['MAX_SUCCESS_TRANSACTIONS_IN_A_ROW']:
                                    token['_REACHED_MAX_SUCCESS_TX'] = True
                                    printt_warn("You have reached MAX_SUCCESS_TRANSACTIONS_IN_A_ROW for", token['SYMBOL'], "token --> disabling trade", write_to_log=True)

                                # Check if MAXTOKENS is reached or not
                                if token['_TOKEN_BALANCE'] > Decimal(token['MAXTOKENS']):
                                    token['_REACHED_MAX_TOKENS'] = True
                                    printt("")
                                    printt_warn("You have reached MAXTOKENS for", token['SYMBOL'], "token --> disabling trade", write_to_log=True)
                                    printt("")

                                # Build sell conditions for the token
                                build_sell_conditions(token, 'after_buy')
                                
                                printt_debug(tokens)

                        else:
                            continue

                    #
                    # SELL CHECK
                    #   If there are already more than MAX_TOKENS in the user's wallet, check to see if we should sell them.
                    #
                    # elif token['_REACHED_MAX_TOKENS'] == True --> UPDATE TsarBuig 27/12/2021 : disable it for now, we need to discuss about this
                    
                    price_conditions_met = False
                    
                    # if token['_INFORMED_SELL'] == False:
                    #     printt_info("You own more tokens than your MAXTOKENS parameter for", token['SYMBOL'],
                    #                 " Looking to sell this position")
                    token['_INFORMED_SELL'] = True

                    # if ALWAYS_CHECK_BALANCE parameter is used, bot will check balance all the time
                    if token['ALWAYS_CHECK_BALANCE'] == 'true':
                        printt_debug("3815 ALWAYS_CHECK_BALANCE is ON")
                        token['_TOKEN_BALANCE'] = check_balance(token['ADDRESS'], token['SYMBOL'],display_quantity=False)

                    printt_debug("_TOKEN_BALANCE 3411", token['_TOKEN_BALANCE'], "for the token:",token['SYMBOL'])
                    # Looking to dump this token as soon as it drops <PUMP> percentage
                    
                    if isinstance(command_line_args.pump, int) and command_line_args.pump > 0:
                        
                        if token['_COST_PER_TOKEN'] == 0 and token['_INFORMED_SELL'] == False:
                            printt_warn("WARNING: You are running a pump on an already purchased position.")
                            sleep(5)

                        # We don't currently have a way to estimate true cost per token, because we are including fees. So, we need
                        # to get two quotes so that we can do trend analysis
                        if token['_FIRST_SELL_QUOTE'] == 0:
                            token['_FIRST_SELL_QUOTE'] = quote

                        else:

                            maximum_gains = token['_ALL_TIME_HIGH'] - token['_FIRST_SELL_QUOTE']
                            minimum_price = token['_ALL_TIME_HIGH'] - (command_line_args.pump * 0.01 * maximum_gains)
                            if quote < minimum_price:
                                printt_err(token['SYMBOL'], "has dropped", command_line_args.pump, "% from it's ATH - SELLING POSITION")
                                price_conditions_met = True


                    elif (token['_QUOTE'] > Decimal(token['_CALCULATED_SELLPRICEINBASE']) or token['_QUOTE'] < Decimal(token['_CALCULATED_STOPLOSSPRICEINBASE'])) and token['_TOKEN_BALANCE'] > 0:
                        price_conditions_met = True
                        
                    if price_conditions_met == True:
                        log_price = "{:.18f}".format(token['_QUOTE'])
                        logging.info("Sell Signal Found @" + str(log_price))
                        printt_ok("--------------------------------------------------------------")
                        printt_ok("Sell Signal Found =-= Sell Signal Found =-= Sell Signal Found ")
                        printt_ok("", write_to_log=True)
                        printt_ok("Sell price in", token['_PAIR_TO_DISPLAY'], ":", log_price, write_to_log=True)
                        printt_ok("--------------------------------------------------------------")
                        
                        tx = sell(token, inToken, outToken)
                        
                        if tx != False:
                            txsellresult = wait_for_tx(token, tx, token['ADDRESS'])
                            
                            printt_debug("tx result 3193 : ", txsellresult)
                            
                            if txsellresult != 1:
                                # transaction is a FAILURE
                                printt_err("--------------------------------")
                                printt_err("   SELL TRANSACTION FAILURE !")
                                printt_err("--------------------------------")
                                printt_err("Type of failures and possible causes:")
                                printt_err("- TRANSFER_FROM_FAILED         --> GASLIMIT too low. Raise it to GASLIMIT = 1000000 at least")
                                printt_err("- TRANSFER_FROM_FAILED         --> Token is not approved for trade. LimitSwap will check approval right now.")
                                printt_err("- INSUFFICIENT_OUTPUT_AMOUNT   --> SLIPPAGE too low")
                                printt_err("- TRANSFER_FAILED              --> Trading is not enabled. Use WAIT_FOR_OPEN_TRADE parameter after reading wiki")
                                printt_err("- TRANSFER_FAILED              --> There is a whitelist")
                                printt_err("- Sorry, We are unable to locate this TxnHash --> You don't have enough funds on your wallet to cover fees")
                                printt_err("- ... or your node is not working well")
                                printt_err("-------------------------------")
                                
                                # increment _FAILED_TRANSACTIONS amount
                                token['_FAILED_TRANSACTIONS'] += 1
                                
                                # Apprise notification
                                if settings['ENABLE_APPRISE_NOTIFICATIONS'] == 'true':
                                    apprise_notification(token,'sell_failure')

                                
                                # We ask the bot to check if your allowance is > to your balance.
                                check_approval(token, inToken, token['_TOKEN_BALANCE'] * 1000000000000000000, 'txfail')

                                printt_debug("3095 _FAILED_TRANSACTIONS:", token['_FAILED_TRANSACTIONS'])
                            else:
                                # transaction is a SUCCESS
                                printt_ok("----------------------------------", write_to_log=True)
                                printt_ok("SUCCESS : your sell Tx is confirmed    ", write_to_log=True)
                                
                                # Apprise notification
                                if settings['ENABLE_APPRISE_NOTIFICATIONS'] == 'true':
                                    apprise_notification(token, 'sell_success')

                                # Optional cooldown after SUCCESS sell, if you use XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX parameter
                                if token['XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX'] != 0:
                                    printt_info("Bot will wait", token['XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX'], "seconds after SELL, due to XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX parameter", write_to_log=True)
                                    sleep(token['XXX_SECONDS_COOLDOWN_AFTER_SELL_SUCCESS_TX'])

                                # Save previous token balance before recalculating
                                token['_PREVIOUS_TOKEN_BALANCE'] = token['_TOKEN_BALANCE']

                                # Re-calculate balances after sell()
                                calculate_base_balance(token)

                                # increment _SUCCESS_TRANSACTIONS amount
                                token['_SUCCESS_TRANSACTIONS'] += 1
                                printt_debug("3900 _SUCCESS_TRANSACTIONS:", token['_SUCCESS_TRANSACTIONS'])

                                # Assumeing we've bought and sold this position, disabling token --> UPDATE TsarBuig : disabling this
                                # printt_info("We have sold our position in", token['SYMBOL'], "DISABLING this token.")
                                # token['ENABLED'] = 'false'
                                
                                # We re-calculate _TOKEN_BALANCE after the sell() order is made
                                token['_TOKEN_BALANCE'] = check_balance(token['ADDRESS'], token['SYMBOL'], display_quantity=True)
                                printt_ok("----------------------------------", write_to_log=True)
                
                                # Check if MAXTOKENS is still reached or not
                                if token['_TOKEN_BALANCE'] < Decimal(token['MAXTOKENS']):
                                    token['_REACHED_MAX_TOKENS'] = False
                                else:
                                    token['_REACHED_MAX_TOKENS'] = True
                                    printt_info("You are still above MAXTOKENS for", token['SYMBOL'], "token --> trade disabled", write_to_log=True)

                else:
                    if settings['VERBOSE_PRICING'] == 'true':
                        printt("Trading for token", token['_PAIR_SYMBOL'], "is disabled")
            first_liquidity_check = False
            sleep(cooldown)
    
    except Exception as ee:
        printt_debug("Debug 4839 - an Exception occured")
        logging.exception(ee)
        printt_debug("tokens_json_already_loaded: ", tokens_json_already_loaded)
        if tokens_json_already_loaded > 0:
            printt_debug("Debug 4841 - reload_tokens_file condition")
            _COST_PER_TOKEN_saved = token['_COST_PER_TOKEN']
            _PREVIOUS_TOKEN_BALANCE_saved = token['_PREVIOUS_TOKEN_BALANCE']
            printt_debug("4838 _COST_PER_TOKEN_saved:", _COST_PER_TOKEN_saved)
            reload_bot_settings(bot_settings)
            sleep(0.01)
            raise RestartAppError("Restarting LimitSwap")
        else:
            raise

class RestartAppError(LookupError):
    '''raise this when there's a need to restart'''

def runLoop():
    while True:
        try:
            run()
        except RestartAppError as e:
            pass

        except Exception as e:
            printt_debug("Debug 3229 - an Exception occured")
            printt_err("ERROR. Please go to /log folder and open your logs: you will find more details.")
            logging.exception(e)
            logger1.exception(e)
            printt("Restarting LimitSwap")
            # Cooldown Logic
            timeout = 10
            nonce = 0
            while nonce<=timeout:
                print(".........Restart Cooldown left " + str(timeout - nonce) + " seconds.............")
                nonce += 1
                sleep(1)
                



try:
    # Benchmark mode
    if command_line_args.benchmark == True: benchmark()
    
    # Get the user password on first run
    userpassword = get_password()
    
    # Handle any processing that is necessary to load the private key for the wallet
    parse_wallet_settings(settings, userpassword)
    
    # The LIMIT balance of the user.
    true_balance = auth()
    
    if true_balance >= 50:
        print(timestamp(), "Professional Subscriptions Active")
        if command_line_args.slow_mode or settings['SLOW_MODE'] == 'true':
            printt_info("RUNNING IN SLOW MODE = price check every 0.5s")
            cooldown = 0.50
        else:
            cooldown = 0.01
        runLoop()
    
    elif true_balance >= 25 and true_balance < 50:
        print(timestamp(), "Trader Subscriptions Active")
        cooldown = 3
        runLoop()
    elif true_balance >= 10 and true_balance < 25:
        print(timestamp(), "Casual Subscriptions Active")
        cooldown = 6
        runLoop()
    else:
        printt_err("10 - 50 LIMIT tokens needed to use this bot, please visit the LimitSwap.com for more info or buy more tokens on Uniswap to use!")
        sleep(10)
        sys.exit()

except Exception as e:
    printt_err("ERROR SETTINGS . Please go to /log folder and open your logs: you will find more details.")
    logging.exception(e)
    logger1.exception(e)
    printt("Restarting LimitSwap")
    # Cooldown Logic
    timeout = 10
    nonce = 0
    while True:
        printt_err("EXCEPTIONAL ERROR - Should not appear")
        print(".........Restart Cooldown left " + str(timeout - nonce) + " seconds.............")
        nonce += 1
        sleep(1)
        if nonce > timeout:
            runLoop()
