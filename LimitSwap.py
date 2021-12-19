# -*- coding: utf-8 -*-
from toolz.functoolz import do
from web3 import Web3
from time import sleep, time
import json
from decimal import Decimal
import os
import web3
from web3.exceptions import ABIFunctionNotFound, TransactionNotFound, BadFunctionCallOutput
import logging
from datetime import datetime
import sys
import requests
import cryptocode, re, pwinput
import argparse
import signal

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
parser.add_argument("--pump", type=int,
                    help="Holds the position as long as the price is going up. Sells when the price has gone down PUMP percent")
parser.add_argument("-p", "--password", type=str,
                    help="Password to decrypt private keys (WARNING: your password could be saved in your command prompt history)")
parser.add_argument("-s", "--settings", type=str, help="Specify the file to user for settings (default: settings.json)",
                    default="./settings.json")
parser.add_argument("-t", "--tokens", type=str,
                    help="Specify the file to use for tokens to trade (default: tokens.json)", default="./tokens.json")
parser.add_argument("-v", "--verbose", action='store_true', help="Print detailed messages to stdout")

# DEVELOPER COMMAND LINE ARGUMENTS
# --dev - general argument for developer options
# --sim_buy tx - simulates the buying process, you must provide a transaction of a purchase of the token
# --sim_sell tx - simulates the buying process, you must provide a transaction of a purchase of the token
parser.add_argument("--dev", action='store_true', help=argparse.SUPPRESS)
parser.add_argument("--sim_buy", type=str, help=argparse.SUPPRESS)
parser.add_argument("--sim_sell", type=str, help=argparse.SUPPRESS)
parser.add_argument("--debug", action='store_true', help=argparse.SUPPRESS)

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
        logging.info(' '.join(map(str,print_args)))

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
        logging.info(' '.join(map(str,print_args)))

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
    print(timestamp(), " ", style.RED, ' '.join(map(str,print_args)), style.RESET, sep="")
    
    if write_to_log == True:
        logging.info(' '.join(map(str,print_args)))

def printt_warn(*print_args, write_to_log=False):
    # Function: printt_warn
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display a warning
    #
    # print_args - normal arguments that would be passed to the print() function
    #
    # returns: nothing

    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.YELLOW, ' '.join(map(str,print_args)), style.RESET, sep="")

    if write_to_log == True:
        logging.info(' '.join(map(str,print_args)))

def printt_ok(*print_args, write_to_log=False):
    # Function: printt_ok
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an OK text
    #
    # returns: nothing

    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.GREEN, ' '.join(map(str, print_args)), style.RESET, sep="")

    if write_to_log == True:
        logging.info(' '.join(map(str,print_args)))

def printt_info(*print_args, write_to_log=False):
    # Function: printt_info
    # --------------------
    # provides normal print() functionality but also prints our timestamp and the text highlighted to display an INFO text in yellow
    #
    # returns: nothing

    if bot_settings['_NEED_NEW_LINE'] == True: print()
    print(timestamp(), " ", style.BLUE, ' '.join(map(str, print_args)), style.RESET, sep="")

    if write_to_log == True:
        logging.info(' '.join(map(str,print_args)))

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
        print(timestamp(), " ", style.DEBUG, ' '.join(map(str,print_args)), style.RESET, sep="")

    if write_to_log == True:
        logging.info(' '.join(map(str,print_args)))

# def printt_buyprice(token_dict, token_price):
#     Function: printt_buyprice
#     --------------------
#     Formatted buying information
    
#     token_dict - one element of the tokens{} dictionary
#     token_price - the current price of the token we want to buy
    
#     returns: nothing

#     print(timestamp(), 
#             style.BLUE, token_dict['SYMBOL'], " Price ", token_Price, token.[],
#              "//// your buyprice =", buypriceinbase, base,
#                   "//// your sellprice =", sellpriceinbase, base, "//// your stoplossprice =", stoplosspriceinbase, base)

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

    if message == token_dict['_LAST_MESSAGE'] and bot_settings['VERBOSE_PRICING'] == 'false' and print_frequency >= repeated_message_quantity:
        print (".", end='', flush=True)
        bot_settings['_NEED_NEW_LINE'] = True
        repeated_message_quantity += 1
    else:
        printt_err (message)
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

    price_message = token_dict['SYMBOL'] + " Price:" + str(token_price) + " Buy:" + str(token_dict['BUYPRICEINBASE']) 
    price_message = price_message + " Sell:" + str(token_dict['SELLPRICEINBASE']) + " Stop:" + str(token_dict['STOPLOSSPRICEINBASE'])
    price_message = price_message + " ATH:" + str(token_dict['_ALL_TIME_HIGH']) + " ATL:" + str(token_dict['_ALL_TIME_LOW'])

    if price_message == token_dict['_LAST_PRICE_MESSAGE'] and bot_settings['VERBOSE_PRICING'] == 'false':
        print (".", end='', flush=True)
        bot_settings['_NEED_NEW_LINE'] = True
    elif token_price > token_dict['_PREVIOUS_QUOTE']:
        printt_ok (price_message)
    elif token_price < token_dict['_PREVIOUS_QUOTE']:
        printt_err (price_message)
    else:
        printt (price_message)
    
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

    f = open(settings_path, )
    all_settings = json.load(f)
    f.close()

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
    
    default_true_settings =[
        'VERBOSE_PRICING',
    ]

    program_defined_values = {
        '_NEED_NEW_LINE' : False
    }

    for default_true in default_true_settings:
        if default_true not in settings:
            print(timestamp(),default_true, "not found in settings configuration file, settings a default value of false.")
            bot_settings[default_true] = "true"
        else:
            bot_settings[default_true] = bot_settings[default_true].lower()
    for value in program_defined_values:
        if value not in bot_settings: bot_settings[value] = program_defined_values[value]

    
    #
    # INITIALIZE EXCHANGE SETTINGS
    #

    if len(settings) == 0:
        print(timestamp(), "No exchange settings found in settings.jon. Exiting.")
        exit (11)

    default_false_settings =[
        'UNLIMITEDSLIPPAGE',
        'USECUSTOMNODE'
    ]

    default_true_settings = [
        'PREAPPROVE'
    ]

    # These settings must be defined by the user and we will lower() them
    required_user_settings = [
        'EXCHANGE'
    ]

    for default_false in default_false_settings:
        if default_false not in settings:
            print(timestamp(),default_false, "not found in settings configuration file, settings a default value of false.")
            settings[default_false] = "false"
        else:
            settings[default_false] = settings[default_false].lower()

    for default_true in default_true_settings:
        if default_true not in settings:
            print(timestamp(),default_true, "not found in settings configuration file, settings a default value of true.")
            settings[default_true] = "true"
        else:
            settings[default_true] = settings[default_true].lower()

    # Keys that must be set
    for required_setting in required_user_settings:
        if required_setting not in settings:
            print(timestamp(), "ERROR:", required_setting, "not found in settings configuration file.")
            exit(-1)
        else:
            settings[required_setting] = settings[required_setting].lower()

    return bot_settings, settings

def get_file_modified_time(file_path, last_known_modification=0):
    
    modified_time = os.path.getmtime(file_path)

    if modified_time != 0 and  last_known_modification == modified_time:
        printt_debug(file_path, "has been modified.")
        
    return last_known_modification

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
        
    if load_message == True:
        print(timestamp(), "Loading tokens from", tokens_path)

    s = open(tokens_path, )
    tokens = json.load(s)
    s.close()

    required_user_settings =[
        'ADDRESS',
        'BUYAMOUNTINBASE',
        'BUYPRICEINBASE',
        'SELLPRICEINBASE'
    ]

    default_true_settings = [
        'LIQUIDITYINNATIVETOKEN',
    ]

    default_false_settings = [
        'ENABLED',
        'LIQUIDITYCHECK',
        'LIQUIDITYINNATIVETOKEN',
        'USECUSTOMBASEPAIR',
        'HASFEES',
        'RUGDOC_CHECK'
    ]

    default_value_settings = {
        'SLIPPAGE' : 49,
        'MAXTOKENS' : 0,
        'MOONBAG' : 0,
        'SELLAMOUNTINTOKENS' : 'all',
        'GAS' : 8,
        'BOOSTPERCENT' : 50,
        'GASLIMIT' : 1000000,
        'BUYAFTER_XXX_SECONDS' : 0,
        'MAX_FAILED_TRANSACTIONS_IN_A_ROW' : 2,
        'GASPRIORITY_FOR_ETH_ONLY' : 1.5,
        'STOPLOSSPRICEINBASE' : 0
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
    # _TOKEN_BALANCE'       - the number of traded tokens the user has in her wallet
    # _PREVIOUS_QUOTE'      - holds the ask price for a token the last time a price was queried, this is used
    #                         to determine the direction the market is going
    # _COST_PER_TOKEN'      - the calculated/estimated price the bot paid for the number of tokens it traded
    # _ALL_TIME_HIGH'       - the highest price a token has had since the bot was started
    # _ALL_TIME_LOW'        - the lowest price a token has had since the bot was started
    # _CONTRACT_DECIMALS    - the number of decimals a contract uses. Used to speed up some of our processes
    #                         instead of querying the contract for the same information repeatedly. 
    # _LAST_PRICE_MESSAGE   - a copy of the last pricing message printed to console, used to determine the price
    #                         should be printed again, or just a dot
    # _LAST_MESSAGE         - a place to store a copy of the last message printed to conside, use to avoid
    #                         repeated liquidity messages

    program_defined_values = {
        '_LIQUIDITY_READY' : False,
        '_LIQUIDITY_CHECKED' : False,
        '_INFORMED_SELL' : False,
        '_REACHED_MAX_TOKENS' : False,
        '_GAS_TO_USE' : 0,
        '_FAILED_TRANSACTIONS' : 0,
        '_TOKEN_BALANCE' : 0,
        '_PREVIOUS_QUOTE' : 0,
        '_ALL_TIME_HIGH' : 0,
        '_COST_PER_TOKEN' : 0,
        '_ALL_TIME_LOW' : 0,
        '_CONTRACT_DECIMALS' : 0,
        '_LAST_PRICE_MESSAGE' : 0,
        '_LAST_MESSAGE' : 0

    }
    
    for token in tokens:

        # Keys that must be set
        for required_key in required_user_settings:
            if required_key not in token:
                printt_err (required_key, "not found in configuration file in configuration for to token", token['SYMBOL'])
                printt_err ("Be careful, sometimes new parameter are added : please check default tokens.json file")
                sleep(20)
                exit (-1)

        for default_false in default_false_settings:
            if default_false not in token:
                printt_v(default_false, "not found in configuration file in configuration for to token",
                         token['SYMBOL'], "setting a default value of false")
                token[default_false] = "false"
            else:
                token[default_false] = token[default_false].lower()

        for default_true in default_true_settings:
            if default_true not in token:
                printt_v(default_true, "not found in configuration file in configuration for to token",
                         token['SYMBOL'], "setting a default value of false")
                token[default_true] = "false"
            else:
                token[default_true] = token[default_true].lower()

        for default_key in default_value_settings:
            if default_key not in token:
                printt_v (default_key , "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a value of", default_value_settings[default_key])
                token[default_key] = default_value_settings[default_key]
            elif default_key == 'SELLAMOUNTINTOKENS':
                default_value_settings[default_key] = default_value_settings[default_key].lower()

        # Set program values only if they haven't been set already
        if '_LIQUIDITY_READY' not in token:
            for value in program_defined_values:
                token[value] = program_defined_values[value]

        for key in token:
            if(isinstance(token[key], str)):
                if re.search(r'^\d*\.\d+$', str(token[key])): token[key] = float(token[key])
                elif re.search(r'^\d+$', token[key]): token[key] = int(token[key])





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
        
    if load_message == True:
        print(timestamp(), "Loading tokens from", tokens_path)

    s = open(tokens_path, )
    tokens = json.load(s)
    s.close()

    required_user_settings =[
        'ADDRESS',
        'BUYAMOUNTINBASE',
        'BUYPRICEINBASE',
        'SELLPRICEINBASE'
    ]

    default_true_settings = [
        'LIQUIDITYINNATIVETOKEN',
    ]

    default_false_settings = [
        'ENABLED',
        'LIQUIDITYCHECK',
        'LIQUIDITYINNATIVETOKEN',
        'USECUSTOMBASEPAIR',
        'HASFEES',
        'RUGDOC_CHECK'
    ]

    default_value_settings = {
        'SLIPPAGE' : 49,
        'MAXTOKENS' : 0,
        'MOONBAG' : 0,
        'SELLAMOUNTINTOKENS' : 'all',
        'GAS' : 8,
        'BOOSTPERCENT' : 50,
        'GASLIMIT' : 1000000,
        'BUYAFTER_XXX_SECONDS' : 0,
        'MAX_FAILED_TRANSACTIONS_IN_A_ROW' : 2,
        'GASPRIORITY_FOR_ETH_ONLY' : 1.5,
        'STOPLOSSPRICEINBASE' : 0
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
    # _TOKEN_BALANCE'       - the number of traded tokens the user has in her wallet
    # _PREVIOUS_QUOTE'      - holds the ask price for a token the last time a price was queried, this is used
    #                         to determine the direction the market is going
    # _COST_PER_TOKEN'      - the calculated/estimated price the bot paid for the number of tokens it traded
    # _ALL_TIME_HIGH'       - the highest price a token has had since the bot was started
    # _ALL_TIME_LOW'        - the lowest price a token has had since the bot was started
    # _CONTRACT_DECIMALS    - the number of decimals a contract uses. Used to speed up some of our processes
    #                         instead of querying the contract for the same information repeatedly. 
    # _LAST_PRICE_MESSAGE   - a copy of the last pricing message printed to console, used to determine the price
    #                         should be printed again, or just a dot

    # TODO: document all these variables
    program_defined_values = {
        '_LIQUIDITY_READY' : False,
        '_LIQUIDITY_CHECKED' : False,
        '_INFORMED_SELL' : False,
        '_REACHED_MAX_TOKENS' : False,
        '_GAS_TO_USE' : 0,
        '_FAILED_TRANSACTIONS' : 0,
        '_TOKEN_BALANCE' : 0,
        '_PREVIOUS_QUOTE' : 0,
        '_ALL_TIME_HIGH' : 0,
        '_COST_PER_TOKEN' : 0,
        '_ALL_TIME_LOW' : 0,
        '_CONTRACT_DECIMALS' : 0,
        '_LAST_PRICE_MESSAGE' : 0
    }
    
    for token in tokens:

        # Keys that must be set
        for required_key in required_user_settings:
            if required_key not in token:
                printt_err (required_key, "not found in configuration file in configuration for to token", token['SYMBOL'])
                printt_err ("Be careful, sometimes new parameter are added : please check default tokens.json file")
                sleep(20)
                exit (-1)

        for default_false in default_false_settings:
            if default_false not in token:
                printt_v(default_false, "not found in configuration file in configuration for to token",
                         token['SYMBOL'], "setting a default value of false")
                token[default_false] = "false"
            else:
                token[default_false] = token[default_false].lower()

        for default_true in default_true_settings:
            if default_true not in token:
                printt_v(default_true, "not found in configuration file in configuration for to token",
                         token['SYMBOL'], "setting a default value of false")
                token[default_true] = "false"
            else:
                token[default_true] = token[default_true].lower()

        for default_key in default_value_settings:
            if default_key not in token:
                printt_v (default_key , "not found in configuration file in configuration for to token", token['SYMBOL'], "setting a value of", default_value_settings[default_key])
                token[default_key] = default_value_settings[default_key]
            elif default_key == 'SELLAMOUNTINTOKENS':
                default_value_settings[default_key] = default_value_settings[default_key].lower()

        # Set program values only if they haven't been set already
        if '_LIQUIDITY_READY' not in token:
            for value in program_defined_values:
                token[value] = program_defined_values[value]

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

    for token in tokens:
        if all_pairs == True or token["ENABLED"] == 'true':
            if token_list != "":
                token_list = token_list + " "
            token_list = token_list + token['SYMBOL']

    if all_pairs == False:
        printt("Quantity of tokens attempting to trade:", len(tokens), "(" , token_list , ")")
    else:
        printt("Quantity of tokens attempting to trade:", len(tokens), "(" , token_list , ")")

  

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

"""""""""""""""""""""""""""
//ERROR LOGGING
"""""""""""""""""""""""""""
os.makedirs('./logs', exist_ok=True)

if not os.path.exists('./logs/errors.log'):
    open('./logs/errors.log', 'w').close()

if not os.path.exists('./logs/exceptions.log'):
    open('./logs/exceptions.log', 'w').close()

log_format = '%(levelname)s: %(asctime)s %(message)s'
logging.basicConfig(filename='./logs/errors.log',
                    level=logging.INFO,
                    format=log_format)

logger1 = logging.getLogger('1')
logger1.addHandler(logging.FileHandler('./logs/exceptions.log'))

logging.info("*************************************************************************************")
logging.info("For Help & To Learn More About how the bot works please visit our wiki here:")
logging.info("https://cryptognome.gitbook.io/limitswap/")
logging.info("*************************************************************************************")

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
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = False

if settings['EXCHANGE'].lower() == 'pancakeswaptesnet':

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

    print(timestamp(), "Binance Smart Chain Connected =", client.isConnected())
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
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = False

if settings['EXCHANGE'].lower() == 'traderjoe':

    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://api.avax.network/ext/bc/C/rpc"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings['EXCHANGE'] == 'pinkswap':
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

elif settings['EXCHANGE'] == 'biswap':
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

    routerAddress = Web3.toChecksumAddress("0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8")
    factoryAddress = Web3.toChecksumAddress("0x858E3312ed3A876947EA49d572A7C42DE08af7EE")

    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)

    weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
    base_symbol = "BNB"
    rugdocchain = '&chain=bsc'
    modified = False

elif settings['EXCHANGE'] == 'apeswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"

    client = Web3(Web3.HTTPProvider(my_provider))

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

elif settings["EXCHANGE"] == 'uniswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://pedantic-montalcini:lair-essay-ranger-rigid-hardy-petted@nd-857-678-344.p2pify.com"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings["EXCHANGE"] == 'kuswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpc-mainnet.kcc.network"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings["EXCHANGE"] == 'koffeeswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpc-mainnet.kcc.network"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings["EXCHANGE"] == 'spookyswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpcapi.fantom.network"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings["EXCHANGE"] == 'spiritswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpcapi.fantom.network"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings["EXCHANGE"] == 'quickswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://polygon-rpc.com"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings["EXCHANGE"] == 'waultswap':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpc-waultfinance-mainnet.maticvigil.com/v1/0bc1bb1691429f1eeee66b2a4b919c279d83d6b0"

    client = Web3(Web3.HTTPProvider(my_provider))
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

elif settings["EXCHANGE"] == 'pangolin':
    if settings['USECUSTOMNODE'] == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://api.avax.network/ext/bc/C/rpc"

    client = Web3(Web3.HTTPProvider(my_provider))
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
    "UNKNOWN": (style.RED + '\nThe status of this token is unknown. '
                            'This is usually a system error but could \n also be a bad sign for the token. Be careful.'),
    "OK": (style.GREEN + '\nRUGDOC API RESULT : OK \n'
                         '√ Honeypot tests passed. RugDoc program was able to buy and sell it successfully. This however does not guarantee that it is not a honeypot.'),
    "NO_PAIRS": (style.RED + '\nRUGDOC API RESULT : NO_PAIRS \n'
                             '⚠ Could not find any trading pair for this token on the default router and could thus not test it.'),
    "SEVERE_FEE": (style.RED + '\nRUGDOC API RESULT : SEVERE_FEE \n'
                               '/!\ /!\ A severely high trading fee (over 50%) was detected when selling or buying this token.'),
    "HIGH_FEE": (style.YELLOW + '\nRUGDOC API RESULT : HIGH_FEE \n'
                                '/!\ /!\ A high trading fee (Between 20% and 50%) was detected when selling or buying this token. Our system was however able to sell the token again.'),
    "MEDIUM_FEE": (style.YELLOW + '\nRUGDOC API RESULT : MEDIUM_FEE \n'
                                  '/!\ A trading fee of over 10% but less then 20% was detected when selling or buying this token. Our system was however able to sell the token again.'),
    "APPROVE_FAILED": (style.RED + '\nRUGDOC API RESULT : APPROVE_FAILED \n'
                                   '/!\ /!\ /!\ Failed to approve the token.\n This is very likely a honeypot.'),
    "SWAP_FAILED": (style.RED + '\nRUGDOC API RESULT : SWAP_FAILED \n'
                                '/!\ /!\ /!\ Failed to sell the token. \n This is very likely a honeypot.'),
    "chain not found": (style.RED + '\nRUGDOC API RESULT : chain not found \n'
                                    '/!\ Sorry, rugdoc API does not work on this chain... (it does not work on ETH, mainly) \n')
}


def save_settings(settings, pwd):
    if len(pwd) > 0:
        encrypted_settings = settings.copy()
        encrypted_settings['LIMITWALLETPRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['LIMITWALLETPRIVATEKEY'],
                                                                                  pwd)
        encrypted_settings['PRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY'], pwd)

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
        settings['LIMITWALLETPRIVATEKEY'] = input(
            "Please provide the private key for the wallet where you have your LIMIT: ")

    # If the limit wallet private key is already set and encrypted, decrypt it
    elif settings['LIMITWALLETPRIVATEKEY'].startswith('aes:'):
        printt("Decrypting limit wallet private key.")
        settings['LIMITWALLETPRIVATEKEY'] = settings['LIMITWALLETPRIVATEKEY'].replace('aes:', "", 1)
        settings['LIMITWALLETPRIVATEKEY'] = cryptocode.decrypt(settings['LIMITWALLETPRIVATEKEY'], pwd)

        if settings['LIMITWALLETPRIVATEKEY'] == False:
            print(style.RED + "ERROR: Your private key decryption password is incorrect")
            print(style.RESET + "Please re-launch the bot and try again")
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
        print(timestamp(), "Decrypting limit wallet private key.")
        settings['PRIVATEKEY'] = settings['PRIVATEKEY'].replace('aes:', "", 1)
        settings['PRIVATEKEY'] = cryptocode.decrypt(settings['PRIVATEKEY'], pwd)

    if settings_changed == True:
        save_settings(settings, pwd)
        
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
        print("Please check your SELLPRICE values.")
    return DECIMALS

def check_logs():
    print(timestamp(), "Quickly Checking Log Size")
    with open('./logs/errors.log') as f:
        line_count = 0
        for line in f:
            line_count += 1
        if line_count > 100:
            with open('./logs/errors.log', "r") as f:
                lines = f.readlines()

            with open('./logs/errors.log', "w") as f:
                f.writelines(lines[20:])

    f.close()

def decode_key():
    private_key = settings['LIMITWALLETPRIVATEKEY']
    acct = client.eth.account.privateKeyToAccount(private_key)
    addr = acct.address
    return addr

def check_release():
    try:
        url = 'https://api.github.com/repos/CryptoGnome/LimitSwap/releases/latest'
        r = requests.get(url).json()['tag_name']
        print("Checking Latest Release Version on Github, Please Make Sure You are Staying Updated = ", r)
        logging.info("Checking Latest Release Version on Github, Please Make Sure You are Staying Updated = " + r)
    except Exception:
        r = "github api down, please ignore"

    return r

def auth():
    my_provider2 = 'https://reverent-raman:photo-hamlet-ankle-saved-scared-bobbed@nd-539-402-515.p2pify.com'
    client2 = Web3(Web3.HTTPProvider(my_provider2))
    print(timestamp(), "Connected to Ethereum BlockChain =", client2.isConnected())
    # Insert LIMITSWAP Token Contract Here To Calculate Staked Verification
    address = Web3.toChecksumAddress("0x1712aad2c773ee04bdc9114b32163c058321cd85")
    abi = standardAbi
    balanceContract = client2.eth.contract(address=address, abi=abi)
    decimals = balanceContract.functions.decimals().call()
    DECIMALS = 10 ** decimals

    # Exception for incorrect Key Input
    try:
        decode = decode_key()
    except Exception:
        print("There is a problem with your private key : please check if it's correct. Don't enter seed phrase !")
        logging.info(
            "There is a problem with your private key : please check if it's correct. Don't enter seed phrase !")

    wallet_address = Web3.toChecksumAddress(decode)
    balance = balanceContract.functions.balanceOf(wallet_address).call()
    true_balance = balance / DECIMALS
    print(timestamp(), "Current Tokens Staked =", true_balance)
    logging.info("Current Tokens Staked = " + str(true_balance))
    return true_balance

def approve(address, amount):

    print(timestamp(), "Approving", address)

    eth_balance = Web3.fromWei(client.eth.getBalance(settings['WALLETADDRESS']), 'ether')

    if eth_balance > 0.05:
        print("Estimating Gas Cost Using Web3")
        if settings['EXCHANGE'] == 'uniswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price =", gas)

        elif settings['EXCHANGE'] == 'pancakeswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'] == 'spiritswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'] == 'spookyswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'] == 'pangolin':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'] == 'quickswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'] == 'kuswap' or 'koffeeswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        else:
            print("EXCHANGE NAME IN SETTINGS IS SPELLED INCORRECTLY OR NOT SUPPORTED YET CHECK WIKI!")
            logging.info("EXCHANGE NAME IN SETTINGS IS SPELLED INCORRECTLY OR NOT SUPPORTED YET CHECK WIKI!")
            exit()

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
            print(timestamp(), "Transaction Hash = ", Web3.toHex(client.keccak(signed_txn.rawTransaction)))
            # LOG TX TO JSON
            with open('./transactions.json', 'r') as fp:
                data = json.load(fp)
            tx_hash = client.toHex(client.keccak(signed_txn.rawTransaction))
            tx_input = {"hash": tx_hash}
            data.append(tx_input)
            with open('./transactions.json', 'w') as fp:
                json.dump(data, fp, indent=2)
            fp.close()

            return tx_hash
    else:
        print(timestamp(),
              "You have less than 0.05 ETH/BNB/FTM/MATIC or network gas token in your wallet, bot needs at least 0.05 to cover fees : please add some more in your wallet.")
        logging.info(
            "You have less than 0.05 ETH/BNB/FTM/MATIC or network gas token in your wallet, bot needs at least 0.05 to cover fees : please add some more in your wallet.")
        sleep(10)
        sys.exit()

def check_approval(token, address, allowance_to_compare_with):

    printt("Checking Approval Status", address)
    contract = client.eth.contract(address=Web3.toChecksumAddress(address), abi=standardAbi)
    actual_allowance = contract.functions.allowance(Web3.toChecksumAddress(settings['WALLETADDRESS']), routerAddress).call()

    allowance_request = 115792089237316195423570985008687907853269984665640564039457584007913129639935
    if actual_allowance < allowance_to_compare_with:
        if settings["EXCHANGE"] == 'quickswap':

            print("Revert to Zero To change approval")
            tx = approve(address, 0)
            wait_for_tx(token, tx, address)
            tx = approve(address, allowance_request)
            wait_for_tx(token, tx, address)
        else:
            printt_info("---------------------------------------------------------------------------")
            printt_info("You need to APPROVE this token before selling it : LimitSwap will do it now")
            printt_info("---------------------------------------------------------------------------")

            tx = approve(address, allowance_request)
            wait_for_tx(token, tx, address)
            printt_ok("---------------------------------------------------------")
            printt_ok("  Token is now approved : LimitSwap can sell this token", True)
            printt_ok("---------------------------------------------------------")

        return allowance_request

    else:
        printt_ok("Token is already approved --> LimitSwap can sell this token ")
        return actual_allowance

def check_bnb_balance():
    balance = client.eth.getBalance(settings['WALLETADDRESS'])
    print(timestamp(), "Current Wallet Balance is :", Web3.fromWei(balance, 'ether'), base_symbol)
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

    printt_debug("ENTER: check_balance()")
    balance = 0
    
    address = Web3.toChecksumAddress(address)
    DECIMALS = decimals(address)
    balanceContract = client.eth.contract(address=address, abi=standardAbi)
    
    balance = balanceContract.functions.balanceOf(settings['WALLETADDRESS']).call()

    print(timestamp(), "Current Wallet Balance is: " + str(balance / DECIMALS) + " " + symbol)
    printt_debug("EXIT: check_balance()")
    return balance

def fetch_pair(inToken, outToken):
    print(timestamp(), "Fetching Pair Address")
    pair = factoryContract.functions.getPair(inToken, outToken).call()
    print(timestamp(), "Pair Address = ", pair)
    return pair

def sync(inToken, outToken):
    pair = factoryContract.functions.getPair(inToken, outToken).call()
    syncContract = client.eth.contract(address=Web3.toChecksumAddress(pair), abi=lpAbi)
    sync = syncContract.functions.sync().call()

def check_pool(inToken, outToken, symbol):
    # This function is made to calculate Liquidity of a token
    pair_address = factoryContract.functions.getPair(inToken, outToken).call()
    DECIMALS = decimals(outToken)
    pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
    reserves = pair_contract.functions.getReserves().call()

    # Tokens are ordered by the token contract address
    # The token contract address can be interpreted as a number
    # And the smallest one will be token0 internally

    # print("----------------------------------------------------------------------")

    ctnb1 = int(inToken, 16)
    ctnb2 = int(outToken, 16)

    if (ctnb1 > ctnb2):
        printt_debug ("reserves[0] is for outToken:")
        pooled = reserves[0] / DECIMALS
    else:
        printt_debug ("reserves[0] is for inToken:")
        pooled = reserves[1] / DECIMALS

    printt_debug ("Debug reserves[0] :", reserves[0] / DECIMALS)
    printt_debug ("Debug reserves[1] :", reserves[1] / DECIMALS)
    printt_debug ("Debug LIQUIDITYAMOUNT :", pooled, "in token:", outToken)

    return pooled

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
    print (func_params)
    exit(0)
 
def check_price(inToken, outToken, symbol, base, custom, routing, buypriceinbase, sellpriceinbase, stoplosspriceinbase):
    # CHECK GET RATE OF THE TOKEn

    DECIMALS = decimals(inToken)
    stamp = timestamp()

    if custom == 'false':
        base = base_symbol

    if routing == 'true':
        if outToken != weth:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, weth, outToken]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            # print(stamp, symbol, " Price ", tokenPrice, base, "//// your buyprice =", buypriceinbase, base,
            #       "//// your sellprice =", sellpriceinbase, base, "//// your stoplossprice =", stoplosspriceinbase, base)
        else:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, weth]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            price_output = "{:.18f}".format(tokenPrice)
            # print(stamp, symbol, "Price =", price_output, base, "//// your buyprice =", buypriceinbase, base,
            #       "//// your sellprice =", sellpriceinbase, base, "//// your stoplossprice =", stoplosspriceinbase, base)

    else:
        if outToken != weth:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, outToken]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            # print(stamp, symbol, " Price ", tokenPrice, base, "//// your buyprice =", buypriceinbase, base,
            #       "//// your sellprice =", sellpriceinbase, base, "//// your stoplossprice =", stoplosspriceinbase, base)
        else:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, weth]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            price_output = "{:.18f}".format(tokenPrice)
            # print(stamp, symbol, "Price =", price_output, base, "//// your buyprice =", buypriceinbase, base,
            #       "//// your sellprice =", sellpriceinbase, base, "//// your stoplossprice =", stoplosspriceinbase, base)

    return tokenPrice

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
        printt_info("Your GASLIMIT parameter is too low : LimitSwap has forced it to 300000 otherwise your transaction would fail for sure. We advise you to raise it to 1000000.")
        token['GASLIMIT'] = 300000

    if token['GAS'] == 'boost':
        gas_check = client.eth.gasPrice
        gas_price = gas_check / 1000000000
        token['_GAS_TO_USE'] = (gas_price * ((int(token['BOOSTPERCENT'])) / 100)) + gas_price
    
    else:
        token['_GAS_TO_USE'] = int(token['GAS'])

    printt_debug("EXIT: calculate_gas()")
    return 0

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
            print (timestamp(), style.INFO, " Checking for transaction confirmation", style.RESET, sep='',  end='', flush=True)
        elif loop_iterations == 1:
            print (style.INFO, " (waiting ", max_wait_time, " seconds)", style.RESET, sep='', end="", flush=True)
        else:
            print (style.INFO, ".", style.RESET, sep='', end="", flush=True)
            sleep(1)
        loop_iterations = loop_iterations + 1
        
        try:
            txn_receipt = client.eth.wait_for_transaction_receipt(tx_hash,1)
            got_receipt = True
        except Exception as e:
            txn_receipt = None

    print('')
    if got_receipt == True and len(txn_receipt['logs']) != 0:
        return_value = txn_receipt['status']
        printt_ok("Transaction was successful with a status code of", return_value)
    
    elif got_receipt == True and len(txn_receipt['logs']) == 0:
        token_dict['_FAILED_TRANSACTIONS'] += 1
        return_value = 2
        printt_err("Transaction was rejected by contract with a status code of", txn_receipt['status'])
    
    elif txn_receipt is not None and txn_receipt['blockHash'] is not None:
        return_value = txn_receipt['status']
        printt_warn("Transaction receipt returned with an unknown status and a status code of", return_value)
    
    else:
        # We definitely get this far if the node is down
        print("\n")
        printt_err("Transaction was not confirmed after", max_wait_time, "seconds: something wrong happened.\n"
                    "                           Please check if :\n"
                    "                           - your node is running correctly\n"
                    "                           - you have enough Gaslimit (check 'Gas Used by Transaction') if you have a failed Tx\n")
        token_dict['_FAILED_TRANSACTIONS'] += 1
        return_value = -1

    return return_value

def preapprove(tokens):
    # We ask the bot to check if your allowance is > to your balance. Use a 10000000000000000 multiplier for decimals.

    # First in all the tokens of the tokens.json
    printt_debug("ENTER - preapprove()")

    for token in tokens:

        balance = Web3.fromWei(check_balance(token['ADDRESS'], token['SYMBOL']), 'ether')
        printt_debug("Balance:", balance)
        check_approval(token, token['ADDRESS'], balance * 10000000000000000)
       
        # then of the base pair
        if token['USECUSTOMBASEPAIR'].lower() == 'false':
            balanceweth = Web3.fromWei(client.eth.getBalance(settings['WALLETADDRESS']), 'ether')
            printt_debug("Balanceweth:", balanceweth)
            check_approval(token, weth, balanceweth * 10000000000000000)
        else:
            balancebase = Web3.fromWei(check_balance(token['BASEADDRESS'], token['BASESYMBOL']), 'ether')
            printt_debug("Balancebase:", balancebase)
            check_approval(token, token['BASEADDRESS'], balancebase * 10000000000000000)

    printt_debug("EXIT - preapprove()")

def buy(token_dict, inToken, outToken):
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
    # WARNING: BALANCE CHECK HAS BEEN REMOVED FROM buy() - THIS SHOULD BE IMPLEMENTED IN ANOTHER FUCTION
    #

    # Map variables until all code is cleaned up.
    amount = token_dict['BUYAMOUNTINBASE']
    gas = token_dict['GAS']
    slippage = token_dict['SLIPPAGE']
    gaslimit = token_dict['GASLIMIT']
    boost = token_dict['BOOSTPERCENT']
    fees = token_dict["HASFEES"]
    custom = token_dict['USECUSTOMBASEPAIR']
    symbol = token_dict['SYMBOL']
    base = token_dict['BASESYMBOL']
    routing = token_dict['LIQUIDITYINNATIVETOKEN']
    gaspriority = token_dict['GASPRIORITY_FOR_ETH_ONLY']




    if token_dict['_FAILED_TRANSACTIONS'] >= int(token_dict['MAX_FAILED_TRANSACTIONS_IN_A_ROW']):
        printt_err("---------------------------------------------------------------")
        printt_err("DISABLING", token_dict['SYMBOL'])
        printt_err("This token has reached maximum FAILED SIMULTANIOUS TRANSACTIONS")
        printt_err("---------------------------------------------------------------")
        token_dict['ENABLED'] = 'false'
    elif token_dict['BUYAFTER_XXX_SECONDS'] != 0:
        printt_info("Bot will wait", token_dict['BUYAFTER_XXX_SECONDS'], " seconds before buy, as you entered in BUYAFTER_XXX_SECONDS parameter")
        sleep(token_dict['BUYAFTER_XXX_SECONDS'])

    printt_info("Placing New Buy Order for " + token_dict['SYMBOL'])






    if int(gaslimit) < 250000:
        printt_info("Your GASLIMIT parameter is too low : LimitSwap has forced it to 300000 otherwise your transaction would fail for sure. We advise you to raise it to 1000000.")
        gaslimit = 300000

    if custom.lower() == 'false':
        balance = Web3.fromWei(check_bnb_balance(), 'ether')
        base = base_symbol
    else:
        address = Web3.toChecksumAddress(inToken)
        DECIMALS = decimals(address)
        balance_check = check_balance(inToken, base)
        balance = balance_check / DECIMALS

    if balance > Decimal(amount):
        if gas.lower() == 'boost':
            gas_check = client.eth.gasPrice
            gas_price = gas_check / 1000000000
            gas = (gas_price * ((int(boost)) / 100)) + gas_price
        else:
            gas = int(gas)

        gaslimit = int(gaslimit)
        slippage = int(slippage)
        DECIMALS = decimals(inToken)
        amount = int(float(amount) * DECIMALS)

        if custom.lower() == 'false':
            # if USECUSTOMBASEPAIR = false

            if routing.lower() == 'false':
                # LIQUIDITYINNATIVETOKEN = false
                # USECUSTOMBASEPAIR = false
                printt_err("You have selected LIQUIDITYINNATIVETOKEN = false , so you must choose USECUSTOMBASEPAIR = true \n"
                            "Please read Wiki carefully, it's very important you can lose money!!")
                logging.info("You have selected LIQUIDITYINNATIVETOKEN = false , so you must choose USECUSTOMBASEPAIR = true. Please read Wiki carefully, it's very important you can lose money!!")
                sleep(10)
                sys.exit()
            else:
                # LIQUIDITYINNATIVETOKEN = true
                # USECUSTOMBASEPAIR = false
                amount_out = routerContract.functions.getAmountsOut(amount, [weth, outToken]).call()[-1]
                if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                    min_tokens = 100
                else:
                    min_tokens = int(amount_out * (1 - (slippage / 100)))

                deadline = int(time() + + 60)

                # THIS SECTION IS FOR MODIFIED CONTRACTS : EACH EXCHANGE NEEDS TO BE SPECIFIED
                # USECUSTOMBASEPAIR = false
                if modified == True:

                    if settings["EXCHANGE"].lower() == 'koffeeswap':
                        transaction = routerContract.functions.swapExactKCSForTokens(
                            min_tokens,
                            [weth, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'value': amount,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })

                    elif settings["EXCHANGE"].lower() == 'pangolin' or settings["EXCHANGE"].lower() == 'traderjoe':
                        transaction = routerContract.functions.swapExactAVAXForTokens(
                            min_tokens,
                            [weth, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'value': amount,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })


                else:
                    # USECUSTOMBASEPAIR = false
                    # This section is for exchange with Modified = false --> uniswap / pancakeswap / apeswap, etc.

                    # Special condition on Uniswap, to implement EIP-1559
                    if settings["EXCHANGE"].lower() == 'uniswap':
                        transaction = routerContract.functions.swapExactETHForTokens(
                            min_tokens,
                            [weth, outToken],
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
                        # USECUSTOMBASEPAIR = false
                        # for all the rest of exchanges with Modified = false
                        transaction = routerContract.functions.swapExactETHForTokens(
                            min_tokens,
                            [weth, outToken],
                            Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            deadline
                        ).buildTransaction({
                            'gasPrice': Web3.toWei(gas, 'gwei'),
                            'gas': gaslimit,
                            'value': amount,
                            'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                            'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
                        })

        else:
            # USECUSTOMBASEPAIR = true
            if inToken == weth:
                # USECUSTOMBASEPAIR = true
                # but user chose to put WETH or WBNB contract as CUSTOMBASEPAIR address
                amount_out = routerContract.functions.getAmountsOut(amount, [weth, outToken]).call()[-1]
                if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                    min_tokens = 100
                else:
                    min_tokens = int(amount_out * (1 - (slippage / 100)))
                deadline = int(time() + + 60)

                if settings["EXCHANGE"].lower() == 'uniswap':
                    # Special condition on Uniswap, to implement EIP-1559
                    transaction = routerContract.functions.swapExactTokensForTokens(
                        min_tokens,
                        [weth, outToken],
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
                    transaction = routerContract.functions.swapExactTokensForTokens(
                        amount,
                        min_tokens,
                        [weth, outToken],
                        Web3.toChecksumAddress(settings['WALLETADDRESS']),
                        deadline
                    ).buildTransaction({
                        'gasPrice': Web3.toWei(gas, 'gwei'),
                        'gas': gaslimit,
                        'from': Web3.toChecksumAddress(settings['WALLETADDRESS']),
                        'nonce': client.eth.getTransactionCount(settings['WALLETADDRESS'])
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
                    inToken).lower() == '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48') and int(amount) > 2999:
                    printt_info("YOU ARE TRADING WITH VERY BIG AMOUNT, BE VERY CAREFUL YOU COULD LOSE MONEY!!! TEAM RECOMMEND NOT TO DO THAT")
                else:
                    pass

                if routing.lower() == 'true':
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth, outToken]).call()[
                        -1]
                    if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                        min_tokens = 100
                    else:
                        min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

                    if settings["EXCHANGE"].lower() == 'uniswap':
                        # USECUSTOMBASEPAIR = true
                        # Base Pair different from weth
                        # LIQUIDITYINNATIVETOKEN = true

                        # Special condition on Uniswap, to implement EIP-1559
                        transaction = routerContract.functions.swapExactTokensForTokens(
                            amount,
                            min_tokens,
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
                        # USECUSTOMBASEPAIR = true
                        # Base Pair different from weth
                        # LIQUIDITYINNATIVETOKEN = true
                        # Exchange different from Uniswap

                        transaction = routerContract.functions.swapExactTokensForTokens(
                            amount,
                            min_tokens,
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
                    # LIQUIDITYINNATIVETOKEN = false
                    # USECUSTOMBASEPAIR = true
                    # Base Pair different from weth

                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, outToken]).call()[-1]
                    if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                        min_tokens = 100
                    else:
                        min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

                    if settings["EXCHANGE"].lower() == 'uniswap':
                        # LIQUIDITYINNATIVETOKEN = false
                        # USECUSTOMBASEPAIR = true
                        # Base Pair different from weth
                        # Special condition on Uniswap, to implement EIP-1559

                        transaction = routerContract.functions.swapExactTokensForTokens(
                            amount,
                            min_tokens,
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
                        # LIQUIDITYINNATIVETOKEN = false
                        # USECUSTOMBASEPAIR = true
                        # Base Pair different from weth
                        # Exchange different from Uniswap

                        transaction = routerContract.functions.swapExactTokensForTokens(
                            amount,
                            min_tokens,
                            [inToken, outToken],
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
            print(timestamp(), "Transaction Hash = ", Web3.toHex(client.keccak(signed_txn.rawTransaction)))
            # LOG TX TO JSON
            with open('./transactions.json', 'r') as fp:
                data = json.load(fp)
            tx_hash = client.toHex(client.keccak(signed_txn.rawTransaction))
            tx_input = {"hash": tx_hash}
            data.append(tx_input)
            with open('./transactions.json', 'w') as fp:
                json.dump(data, fp, indent=2)
            fp.close()

            return tx_hash

def sell(token_dict, inToken, outToken):

    # Map variables until all code is cleaned up.
    amount = token_dict['SELLAMOUNTINTOKENS']
    moonbag = token_dict['MOONBAG']
    gas = token_dict['GAS']
    slippage = token_dict['SLIPPAGE']
    gaslimit = token_dict['GASLIMIT']
    boost = token_dict['BOOSTPERCENT']
    fees = token_dict["HASFEES"]
    custom = token_dict['USECUSTOMBASEPAIR']
    symbol = token_dict['SYMBOL']
    routing = token_dict['LIQUIDITYINNATIVETOKEN']
    gaspriority = token_dict['GASPRIORITY_FOR_ETH_ONLY']


    print(timestamp(), "Placing Sell Order " + symbol)
    balance = Web3.fromWei(check_balance(inToken, symbol), 'ether')

    # We ask the bot to check if your allowance is > to your balance. Use a 10000000000000000 multiplier for decimals.
    check_approval(token_dict, inToken, balance * 10000000000000000)

    if int(gaslimit) < 250000:
        gaslimit = 300000
        printt_info(
        "Your GASLIMIT parameter is too low : LimitSwap has forced it to 300000 otherwise your transaction would fail for sure. We advise you to raise it to 1000000.")

    if type(amount) == str:
        amount_check = balance
    else:
        amount_check = Decimal(amount)

    if balance >= Decimal(amount_check) and balance > 0.0000000000000001:

        if gas.lower() == 'boost':
            gas_check = client.eth.gasPrice
            gas_price = gas_check / 1000000000
            gas = (gas_price * ((int(boost) * 4) / 100)) + gas_price
        else:
            gas = int(gas)

        slippage = int(slippage)
        gaslimit = int(gaslimit)
        DECIMALS = decimals(inToken)

        if amount.lower() == 'all':
            balance = check_balance(inToken, symbol)
            moonbag = int(Decimal(moonbag) * DECIMALS)
            amount = int(Decimal(balance - moonbag))

        else:
            balance = check_balance(inToken, symbol)
            amount = Decimal(amount) * DECIMALS
            moonbag = int(Decimal(moonbag) * DECIMALS)

            if balance < amount:
                print(timestamp(), "Selling Remaining ", symbol)
                amount = int(Decimal(balance - moonbag))
            else:
                amount = int(Decimal(amount - moonbag))
                if amount > 0:
                    print(timestamp(), "Selling", amount / DECIMALS, symbol)
                else:
                    print("Not enough left to sell, would bust moonbag")
                    amount = 0

        if custom.lower() == 'false':
            # USECUSTOMBASEPAIR = false
            sync(inToken, weth)

            amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth]).call()[-1]
            min_tokens = int(amount_out * (1 - (slippage / 100)))
            deadline = int(time() + + 60)

            if fees.lower() == 'true':

                # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
                if modified == True:
                    # USECUSTOMBASEPAIR = false
                    # HASFEES = true

                    if settings["EXCHANGE"].lower() == 'koffeeswap':
                        transaction = routerContract.functions.swapExactTokensForKCSSupportingFeeOnTransferTokens(
                            amount,
                            min_tokens,
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
                        transaction = routerContract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
                            amount,
                            min_tokens,
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
                    transaction = routerContract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                        amount,
                        min_tokens,
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
                        transaction = routerContract.functions.swapExactTokensForKCS(
                            amount,
                            min_tokens,
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
                        transaction = routerContract.functions.swapExactTokensForAVAX(
                            amount,
                            min_tokens,
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

                    if settings["EXCHANGE"].lower() == 'uniswap':
                        # Special condition on Uniswap, to implement EIP-1559
                        transaction = routerContract.functions.swapExactTokensForETH(
                            amount,
                            min_tokens,
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
                        transaction = routerContract.functions.swapExactTokensForETH(
                            amount,
                            min_tokens,
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
                min_tokens = int(amount_out * (1 - (slippage / 100)))
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
                            transaction = routerContract.functions.swapExactTokensForKCSSupportingFeeOnTransferTokens(
                                amount,
                                min_tokens,
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
                            transaction = routerContract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
                                amount,
                                min_tokens,
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

                        transaction = routerContract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                            amount,
                            min_tokens,
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
                    transaction = routerContract.functions.swapExactTokensForTokens(
                        amount,
                        min_tokens,
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
                    min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

                    if fees.lower() == 'true':
                        # LIQUIDITYINNATIVETOKEN = false
                        # USECUSTOMBASEPAIR = true
                        # HASFEES = true
                        if settings["EXCHANGE"].lower() == 'uniswap':
                            # Special condition on Uniswap, to implement EIP-1559
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                min_tokens,
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
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                min_tokens,
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
                        if settings["EXCHANGE"].lower() == 'uniswap':
                            # Special condition on Uniswap, to implement EIP-1559
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                min_tokens,
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
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                min_tokens,
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
                    printt_err(
                        "ERROR IN YOUR TOKENS.JSON : YOU NEED TO CHOOSE THE PROPER BASE PAIR AS SYMBOL IF YOU ARE TRADING OUTSIDE OF NATIVE LIQUIDITY POOL")
                    logging.info("ERROR IN YOUR TOKENS.JSON : YOU NEED TO CHOOSE THE PROPER BASE PAIR AS SYMBOL IF YOU ARE TRADING OUTSIDE OF NATIVE LIQUIDITY POOL")

                else:
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth, outToken]).call()[-1]
                    min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

                    if fees.lower() == 'true':
                        # HASFEES = true
                        if settings["EXCHANGE"].lower() == 'uniswap':
                            # Special condition on Uniswap, to implement EIP-1559
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                min_tokens,
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
                            transaction = routerContract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                                amount,
                                min_tokens,
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
                        if settings["EXCHANGE"].lower() == 'uniswap':
                            # Special condition on Uniswap, to implement EIP-1559
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                min_tokens,
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
                            transaction = routerContract.functions.swapExactTokensForTokens(
                                amount,
                                min_tokens,
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
            print(timestamp(), "Transaction Hash = ", Web3.toHex(client.keccak(signed_txn.rawTransaction)))
            # LOG TX TO JSON
            with open('./transactions.json', 'r') as fp:
                data = json.load(fp)
            tx_hash = client.toHex(client.keccak(signed_txn.rawTransaction))
            tx_input = {"hash": tx_hash}
            data.append(tx_input)
            with open('./transactions.json', 'w') as fp:
                json.dump(data, fp, indent=2)
            fp.close()

            return tx_hash
    else:
        pass

def run():
    
    # Price Quote
    quote = 0

    try:
        tokens = load_tokens_file(command_line_args.tokens, True)

        eth_balance = Web3.fromWei(client.eth.getBalance(settings['WALLETADDRESS']), 'ether')

        if eth_balance < 0.05:
            printt_err("You have less than 0.05 ETH/BNB/FTM/MATIC/Etc. token in your wallet, bot needs at least 0.05 to cover fees : please add some more in your wallet")
            sleep(10)
            exit(1)

        # Display the number of token pairs we're attempting to trade
        token_list_report(tokens)


        # Check to see if the user wants to pre-approve token transactions. If they do, work through that approval process
        if settings['PREAPPROVE'] == 'true':
            preapprove(tokens)

        # For each token check to see if the user wants to run a rugdoc check against them.
        #   then run the rugdoctor check and prompt the user if they want to continue trading
        #   the token
        #
        # TODO PRUNE: Prune tokens if the user doesn't want to trade them. Exit only if we don't have any more tokens left
        # TODO ARG: Implement an argument that auto accepts or prunes tokens that are rejected/accepted by the rugdoc check
        for token in tokens:
            
            # Calculate contract decimals
            token['_CONTRACT_DECIMALS'] = int(decimals(token['ADDRESS']))
            # Check to see if we have any tokens in our wallet already
            token['_TOKEN_BALANCE'] = check_balance(token['ADDRESS'], token['SYMBOL']) / token['_CONTRACT_DECIMALS']
            if token['_TOKEN_BALANCE'] > 0 :
                printt_info(token['SYMBOL'], "started with", token['_TOKEN_BALANCE'], "tokens.")
                if token['_TOKEN_BALANCE'] > float(token['MAXTOKENS']): token['_REACHED_MAX_TOKENS'] = True 

            # Calculate how much gas we should use for this token
            calculate_gas(token)

            if token['RUGDOC_CHECK'] == 'true':

                rugresponse = requests.get('https://honeypot.api.rugdoc.io/api/honeypotStatus.js?address=' + token['ADDRESS'] + rugdocchain)
                # sending get request and saving the response as response object

                if rugresponse.status_code == 200:
                    d = json.loads(rugresponse.content)
                    print("debug 200")
                    for key, value in interpretations.items():
                        if d["status"] in key:
                            honeypot_status = value
                            honeypot_code = key
                            print(honeypot_status)

                else:
                    printt_warn("Sorry, Rugdoc's API does not work on this token (Rugdoc does not work on ETH chain for instance)")

                decision = ""
                while decision != "y" and decision != "n":
                    print ("\nWhat is your decision?")
                    decision = input("Would you like to snipe this token? (y/n): ")

                if decision == "y":
                    print ("\nOK let's go!!\n")
                else:
                    sys.exit()

                # Calculate how much gas we should use for this token
                
        
        load_token_file_increment = 0
        tokens_file_modified_time = os.path.getmtime(command_line_args.tokens)
        while True:

            # Check to see if the tokens file has changed every 10 iterations
            if load_token_file_increment > 10:
                modification_check = tokens_file_modified_time
                tokens_file_modified_time = os.path.getmtime(command_line_args.tokens)
                if (modification_check != tokens_file_modified_time):
                    raise Exception("tokens.json has been changed, reinitializing tokens.")
            else:
                load_token_file_increment = load_token_file_increment + 1

            for token in tokens:
            
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
                    # CHECK LIQUIDITY ... if we haven't already checked liquidity
                    #   Break out of the loop for this token if we haven't found liquidity yet
                    #
                    if token['_LIQUIDITY_READY'] == False:
                        try:
                                pool = check_pool(inToken, outToken, token['BASESYMBOL'])
                                token['_LIQUIDITY_READY'] = True
                                printt_info ("Found liquidity for",token['SYMBOL'])

                                #
                                #  CHECK FOR LIQUIDITY AMOUNT
                                #    If we've found liquidity and want to check for liquidity amount, do that here.
                                #    If this token doesn't have enough liquidity. Disable it and break out of this
                                #    loop for this token
                                #
                                if token["LIQUIDITYCHECK"] == 'true' and token['_LIQUIDITY_CHECKED'] == False:
                                    pool = check_pool(inToken, outToken, token['BASESYMBOL'])
                                    printt("You have set LIQUIDITYCHECK = true.")
                                    printt("Current", token['SYMBOL'], "Liquidity =", int(pool), "in token:",outToken)

                                    if float(token['LIQUIDITYAMOUNT']) <= float(pool):
                                        printt_ok("LIQUIDITYAMOUNT parameter =", int(token['LIQUIDITYAMOUNT']),
                                                    " --> Enough liquidity detected : Buy Signal Found!")
                                    
                                    # This position isn't looking good. Inform the user, disable the token and break out of this loop
                                    else:
                                        printt_warn("LIQUIDITYAMOUNT parameter =", int(token['LIQUIDITYAMOUNT']),
                                                " : not enough liquidity, bot will not buy. Disableing the trade of this token.")
                                        token['ENABLED'] = 'false'
                                        quote = 0
                                        break

                        except Exception:
                            printt_repeating (token, token['SYMBOL'] + " Not Listed For Trade Yet... waiting for liquidity to be added on exchange")
                            break



                    #
                    #  PRICE CHECK
                    #    Check the latest price on this token and record information on the price that we may
                    #    need to use later
                    #                    
                    token['_PREVIOUS_QUOTE'] = quote
                    quote = check_price(inToken, outToken, token['SYMBOL'], token['BASESYMBOL'],
                                       token['USECUSTOMBASEPAIR'], token['LIQUIDITYINNATIVETOKEN'],
                                       token['BUYPRICEINBASE'], token['SELLPRICEINBASE'], token['STOPLOSSPRICEINBASE'])
                    
                    if token['_ALL_TIME_HIGH'] == 0 and token['_ALL_TIME_LOW'] == 0:
                        token['_ALL_TIME_HIGH'] = quote
                        token['_ALL_TIME_LOW'] = quote

                    elif quote > token['_ALL_TIME_HIGH']:
                        token['_ALL_TIME_HIGH'] = quote
                    
                    elif quote < token['_ALL_TIME_LOW']:
                        token['_ALL_TIME_LOW'] = quote


                    # If we're still in the market to buy tokens, the print the buy message
                    if quote != 0 and token['_REACHED_MAX_TOKENS'] == False:
                        printt_buy_price(token, quote)

                    #
                    # BUY CHECK
                    #   If the liquidity check has returned a quote that is less than our BUYPRICEINBASE and we haven't informrmed
                    #   the user that we've reached the maximum number of tokens, check for other criteria to buy.
                    #
                    if quote != 0 and quote < Decimal(token['BUYPRICEINBASE']) and token['_REACHED_MAX_TOKENS'] == False:
                        #
                        # PURCHASE POSITION
                        #   If we've passed all checks, attempt to purchase the token
                        #
                        printt_debug ("===========================================")
                        printt_debug ("Quote:", quote)
                        printt_debug ("Buy Price:", Decimal(token['BUYPRICEINBASE']))
                        printt_debug ("_REACHED_MAX_TOKENS:", token['_REACHED_MAX_TOKENS'])
                        printt_debug ("===========================================")

                        log_price = "{:.18f}".format(quote)
                        logging.info("Buy Signal Found @" + str(log_price))
                        printt_ok("-----------------------------------------------------------")
                        printt_ok("Buy Signal Found =-= Buy Signal Found =-= Buy Signal Found ")
                        printt_ok("-----------------------------------------------------------")
                        if command_line_args.sim_buy:
                            tx = command_line_args.sim_buy
                        else:
                            tx = buy(token, outToken, inToken)

                        if tx != False:
                            tx = wait_for_tx(token, tx, token['ADDRESS'])

                            if tx != 1:
                                # transaction is a FAILURE
                                printt_err("---------------------------")
                                printt_err("ERROR TRANSACTION FAILURE !")
                                printt_err("---------------------------")
                                printt_err("Causes of failure can be :")
                                printt_err("- GASLIMIT too low")
                                printt_err("- SLIPPAGE too low")
                                printt_err("--------------------------")
                                token['_FAILED_TRANSACTIONS'] += 1
                                preapprove(tokens)
                            else:
                                # transaction is a SUCCESS
                                printt_ok("----------------------------------")
                                printt_ok("SUCCESS : your Tx is confirmed    ")
                                printt_ok("----------------------------------")

                            # Check the balance of our wallet
                            DECIMALS = decimals(inToken)
                            token['_TOKEN_BALANCE'] = check_balance(inToken, token['SYMBOL'], 60) / DECIMALS
                            if token['_TOKEN_BALANCE'] > Decimal(token['MAXTOKENS']):
                                token['_REACHED_MAX_TOKENS'] = True
                                printt_info ("You have reached the maximum number of tokens for this position.")

                            token['_COST_PER_TOKEN'] = float(token['BUYAMOUNTINBASE']) / float(token['_TOKEN_BALANCE'])
                            printt_debug (token['SYMBOL'], " cost per token was: ", token['_COST_PER_TOKEN'])

                    #
                    # SELL CHECK
                    #   If there are already more than MAX_TOKENS in the user's wallet, check to see if we should sell them.
                    #
                    elif token['_REACHED_MAX_TOKENS'] == True :
                        
                        price_conditions_met = False
                        
                        if token['_INFORMED_SELL'] == False:
                            printt_info("You own more tokens than your MAXTOKENS parameter for",token['SYMBOL'], " Looking to sell this position")
                            token['_INFORMED_SELL'] = True

                        # Looking to dump this token as soon as it drops <PUMP> percentage
                        if  isinstance(command_line_args.pump, int) and command_line_args.pump > 0 :
                            
                            if token['_COST_PER_TOKEN'] == 0 and token['_INFORMED_SELL'] == False:
                                printt_warn("WARNING: You are running a pump on an already purchased position.")
                                sleep(5)

                            printt_sell_price (token, quote)

                            minimum_price = token['_ALL_TIME_HIGH'] - (command_line_args.pump * 0.01 * token['_ALL_TIME_HIGH'])
                            if quote < minimum_price:
                                printt_err(token['SYMBOL'],"has dropped", command_line_args.pump,"% from it's ATH - SELLING POSITION")
                                price_conditions_met = True

                        elif quote > Decimal(token['SELLPRICEINBASE']) or quote < Decimal(token['STOPLOSSPRICEINBASE']):
                            price_conditions_met = True

                        if price_conditions_met == True :
                            log_price = "{:.18f}".format(quote)
                            logging.info("Sell Signal Found @" + str(log_price))
                            printt_ok("--------------------------------------------------------------")
                            printt_ok("Sell Signal Found =-= Sell Signal Found =-= Sell Signal Found ")
                            printt_ok("--------------------------------------------------------------")

                            tx = sell(token, inToken, outToken)
                            wait_for_tx(token, tx, token['ADDRESS'])
                            

                            # transaction is a SUCCESS
                            printt_ok("----------------------------------")
                            printt_ok("SUCCESS : your Tx is confirmed    ")
                            printt_ok("----------------------------------")
                                
                            # Assumeing we've bought and sold this position, disabling token
                            printt_info("We have sold our position in", token['SYMBOL'], "DISABLING this token.")
                            token['ENABLED'] = 'false'
                            check_balance(token['ADDRESS'], token['SYMBOL'])


            sleep(cooldown)

    except Exception as ee:
        print(timestamp(), "ERROR. Please go to /log folder and open your error logs : you will find more details.")
        logging.exception(ee)
        logger1.exception(ee)
        sleep(10)
        print("Restarting LimitSwap")
        logging.info("Restarting LimitSwap")
        # Cooldown Logic
        timeout = 10
        nonce = 0
        while True:
            print(".........Restart Cooldown left " + str(timeout - nonce) + " seconds.............")
            nonce += 1
            sleep(1)
            if nonce > timeout:
                run()
         
try:
    
    # Get the user password on first run
    userpassword = get_password()

    # Handle any proccessing that is necessary to load the private key for the wallet
    parse_wallet_settings(settings, userpassword)

    # The LIMIT balance of the user.
    true_balance = auth()

    version = 3.44
    logging.info("YOUR BOT IS CURRENTLY RUNNING VERSION " + str(version))
    print("YOUR BOT IS CURRENTLY RUNNING VERSION " + str(version))
    check_release()

    if true_balance >= 50:
        print(timestamp(), "Professional Subscriptions Active")
        cooldown = 0.01
        run()

    elif true_balance >= 25 and true_balance < 50:
        print(timestamp(), "Trader Subscriptions Active")
        cooldown = 3
        run()
    elif true_balance >= 10 and true_balance < 25:
        print(timestamp(), "Casual Subscriptions Active")
        cooldown = 6
        run()
    else:
        print(timestamp(),
              "10 - 50 LIMIT tokens needed to use this bot, please visit the LimitSwap.com for more info or buy more tokens on Uniswap to use!")
        logging.exception(
            "10 - 50 LIMIT tokens needed to use this bot, please visit the LimitSwap.com for more info or buy more tokens on Uniswap to use!")

except Exception as e:
    print(timestamp(), "ERROR. Please go to /log folder and open your error logs : you will find more details.")
    logging.exception(e)
    logger1.exception(e)
    print("Restarting LimitSwap")
    logging.info("Restarting LimitSwap")
    # Cooldown Logic
    timeout = 10
    nonce = 0
    while True:
        print(".........Restart Cooldown left " + str(timeout - nonce) + " seconds.............")
        nonce += 1
        sleep(1)
        if nonce > timeout:
            run()
