from web3 import Web3
from time import sleep, time
import json
from decimal import Decimal
import os
from web3.exceptions import ABIFunctionNotFound, TransactionNotFound, BadFunctionCallOutput
import logging
from datetime import datetime
import sys
import requests
import cryptocode, re, pwinput

# global used to track if any settings need to be written to file
settings_changed = False

def timestamp():
    timestamp = time()
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object

"""""""""""""""""""""""""""
//PRELOAD
"""""""""""""""""""""""""""
print(timestamp(), "Preloading Data")
f = open('./settings.json', )
settings = json.load(f)[0]
f.close()

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


if settings['EXCHANGE'].lower() == 'pancakeswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://bsc-dataseed4.defibit.io"

    client = Web3(Web3.HTTPProvider(my_provider))
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
    modified = False

if settings['EXCHANGE'].lower() == 'traderjoe':

    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = True

elif settings['EXCHANGE'].lower() == 'apeswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = False

elif settings["EXCHANGE"].lower() == 'uniswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = False

elif settings["EXCHANGE"].lower() == 'kuswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = False

elif settings["EXCHANGE"].lower() == 'koffeeswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = True

elif settings["EXCHANGE"].lower() == 'spookyswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = False

elif settings["EXCHANGE"].lower() == 'spiritswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = False

elif settings["EXCHANGE"].lower() == 'quickswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
        my_provider = settings['CUSTOMNODE']
    else:
        my_provider = "https://rpc-mainnet.matic.network"

    client = Web3(Web3.HTTPProvider(my_provider))
    print(timestamp(), "Matic Chain Connected =", client.isConnected())
    print(timestamp(), "Loading Smart Contracts...")
    routerAddress = Web3.toChecksumAddress("0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")
    factoryAddress = Web3.toChecksumAddress("0x5757371414417b8c6caad45baef941abc7d3ab32")
    routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
    factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
    weth = Web3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
    base_symbol = "MATIC"
    modified = False

elif settings["EXCHANGE"].lower() == 'waultswap':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = False

elif settings["EXCHANGE"].lower() == 'pangolin':
    if settings['USECUSTOMNODE'].lower() == 'true':
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
    modified = True

def get_password():
    
    global settings_changed
    setnewpassword = False

    # Check to see if the user has a version of the settings file before private key encryption existed
    if 'ENCRYPTPRIVATEKEYS' not in settings:
        response = ""
        settings_changed = True
        while response != "y" and response != "n":
            print ("\nWould you like to use a password to encrypt your private keys?")
            response = input ("You will need to input this password each time LimitSwap is executed (y/n): ")
    
        if response == "y":
            settings['ENCRYPTPRIVATEKEYS'] = "true"
            setnewpassword = True
        else:
            settings['ENCRYPTPRIVATEKEYS'] = "false"  

    # If the user wants to encrypt their private keys, but we don't have an encrypted private key recorded, we need to ask for a password
    elif settings['ENCRYPTPRIVATEKEYS'] == "true" and not settings['PRIVATEKEY'].startswith('aes:'):
        print ("\nPlease create a password to encrypt your private keys.")
        setnewpassword = True

    # Set a new password when necessary
    if setnewpassword == True:
        settings_changed = True
        passwords_differ = True
        while passwords_differ:
            pwd = pwinput.pwinput(prompt="\nType your new password: ")
            pwd2 = pwinput.pwinput(prompt="\nType your new password again: ")
            
            if pwd != pwd2:
                print ("Error, password mismatch. Try again.")
            else:
                passwords_differ = False
    
    # The user already has encrypted private keys. Accept a password so we can unencrypt them
    elif settings['ENCRYPTPRIVATEKEYS'] == "true":

        pwd = pwinput.pwinput(prompt="\nPlease specify the password to decrypt your keys: ")

    else:
        pwd = ""

    if not pwd.strip():
        print ()
        print ("X WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING=-= WARNING X")
        print ("X       You are running LimitSwap without encrypting your private keys.          X")
        print ("X     Private keys are stored on disk unencrypted and can be accessed by         X")
        print ("X anyone with access to the file system, including the Systems/VPS administrator X")
        print ("X       and anyone with physical access to the machine or hard drives.           X")
        print ("X WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING =-= WARNING=-= WARNING X")
        print ()

    return pwd

def save_settings(pwd):
    
    global settings_changed

    if len(pwd) > 0:
        encrypted_settings = settings.copy()
        encrypted_settings['LIMITWALLETPRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['LIMITWALLETPRIVATEKEY'], pwd)
        encrypted_settings['PRIVATEKEY'] = 'aes:' + cryptocode.encrypt(settings['PRIVATEKEY'], pwd)
    
    # MASSAGE OUTPUT - LimitSwap currently loads settings.json as a [0] element, so we need to massage our
    #                  settings.json output so that it's reasable. This should probably be fixed by us importing
    #                  the entire json file, instead of just the [0] element.
    if settings_changed == True:
        print (timestamp(), "Writing settings to file.")

        if settings['ENCRYPTPRIVATEKEYS'] == "true":
            output_settings = encrypted_settings
        else:
            output_settings = settings

        with open('settings.json', 'w') as f:
            f.write("[\n")                 
            f.write(json.dumps(output_settings, indent=4))
            f.write("\n]\n")

def load_wallet_settings(pwd):

    global settings
    global settings_changed

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
        print (timestamp(), "Decrypting limit wallet private key.")
        settings['LIMITWALLETPRIVATEKEY'] = settings['LIMITWALLETPRIVATEKEY'].replace('aes:', "", 1)
        settings['LIMITWALLETPRIVATEKEY'] = cryptocode.decrypt(settings['LIMITWALLETPRIVATEKEY'], pwd)

        if settings['LIMITWALLETPRIVATEKEY'] == False:
            print("ERROR: Your private key decryption password is incorrect")
            exit(1)


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
        print (timestamp(), "Decrypting limit wallet private key.")
        settings['PRIVATEKEY'] = settings['PRIVATEKEY'].replace('aes:', "", 1)
        settings['PRIVATEKEY'] = cryptocode.decrypt(settings['PRIVATEKEY'], pwd)


def decimals(address):
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

    #Exception for incorrect Key Input
    try:
        decode = decode_key()
    except Exception:
        print("There is a problem with your private key : please check if it's correct. Don't enter seed phrase !")
        logging.info("There is a problem with your private key : please check if it's correct. Don't enter seed phrase !")

    wallet_address = Web3.toChecksumAddress(decode)
    balance = balanceContract.functions.balanceOf(wallet_address).call()
    true_balance = balance / DECIMALS
    print(timestamp(), "Current Tokens Staked =", true_balance)
    logging.info("Current Tokens Staked = " + str(true_balance))
    return true_balance

def approve(address, amount):
    print(timestamp(), "Approving", address)

    eth_balance = Web3.fromWei(client.eth.getBalance(settings['WALLETADDRESS']), 'ether')

    if eth_balance > 0.01:
        print("Estimating Gas Cost Using Web3")
        if settings['EXCHANGE'].lower() == 'uniswap':
            print("Estimating Gas Cost Using Web3")
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price =", gas)

        elif settings['EXCHANGE'].lower() == 'pancakeswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'].lower() == 'spiritswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'].lower() == 'spookyswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'].lower() == 'pangolin':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'].lower() == 'quickswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        elif settings['EXCHANGE'].lower() == 'kuswap' or 'koffeeswap':
            gas = (((client.eth.gasPrice) / 1000000000)) + ((client.eth.gasPrice) / 1000000000) * (int(20) / 100)
            print("Current Gas Price = ", gas)
        else:
            print("EXCHANGE NAME IN SETTINGS IS SPELLED INCORRECTLY OR NOT SUPPORTED YET CHECK WIKI!")
            logging.info("EXCHANGE NAME IN SETTINGS IS SPELLED INCORRECTLY OR NOT SUPPORTED YET CHECK WIKI!")
            exit()


        contract = client.eth.contract(address=Web3.toChecksumAddress(address), abi=standardAbi)
        transaction = contract.functions.approve(routerAddress, amount
        ).buildTransaction({
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
        print(timestamp(), "you have less than 0.01 ETH/BNB/FTM/MATIC or network gas token in your wallet, please make sure you have enough to cover fees!!")
        logging.info("you have less than 0.01 ETH/BNB/FTM/MATIC or network gas token in your wallet, please make sure you have enough to cover fees!!")
        exit()

def check_approval(address, balance):
    print(timestamp(), "Checking Approval Status", address)
    contract = client.eth.contract(address=Web3.toChecksumAddress(address), abi=standardAbi)
    allowance = contract.functions.allowance(Web3.toChecksumAddress(settings['WALLETADDRESS']), routerAddress).call()


    if allowance < balance:

        if settings["EXCHANGE"].lower() == 'quickswap':
            print("Revert to Zero To change approval")
            tx = approve(address, 0)
            wait_for_tx(tx, address, False)
            tx = approve(address, balance)
            wait_for_tx(tx, address, False)
        else:
            tx = approve(address, balance)
            wait_for_tx(tx, address, False)


        return

    else:
        pass

def check_bnb_balance():
    balance = client.eth.getBalance(settings['WALLETADDRESS'])
    print(timestamp(), "Current Wallet Balance is :", Web3.fromWei(balance, 'ether'), base_symbol)
    return balance

def check_balance(address, symbol):
    address = Web3.toChecksumAddress(address)
    DECIMALS = decimals(address)
    balanceContract = client.eth.contract(address=address, abi=standardAbi)
    balance = balanceContract.functions.balanceOf(settings['WALLETADDRESS']).call()
    print(timestamp(), "Current Wallet Balance is: " + str(balance/DECIMALS) + " " + symbol)

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

    pair_address = factoryContract.functions.getPair(inToken, outToken).call()
    DECIMALS = decimals(outToken)
    pair_contract = client.eth.contract(address=pair_address, abi=lpAbi)
    reserves = pair_contract.functions.getReserves().call()
    pooled = reserves[-1] / DECIMALS
    print(timestamp(), "Current Liquidity Reserves:", pooled, symbol)

    return pooled

def check_price(inToken, outToken, symbol, base, custom, routing):
    # CHECK GET RATE OF THE TOKEn

    DECIMALS = decimals(inToken)
    stamp = timestamp()

    if custom.lower() == 'false':
        base = base_symbol
    else:
        pass

    if routing == 'true':
        if outToken != weth:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, weth, outToken]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            print(stamp, symbol, " Price ", tokenPrice,  base)
        else:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, weth]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            price_output = "{:.18f}".format(tokenPrice)
            print(stamp, symbol, "Price =", price_output,  base)

    else:
        if outToken != weth:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, outToken]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            print(stamp, symbol, " Price ", tokenPrice,  base)
        else:
            price_check = routerContract.functions.getAmountsOut(1 * DECIMALS, [inToken, weth]).call()[-1]
            DECIMALS = decimals(outToken)
            tokenPrice = price_check / DECIMALS
            price_output = "{:.18f}".format(tokenPrice)
            print(stamp, symbol, "Price =", price_output,  base)


    return tokenPrice

def wait_for_tx(tx_hash, address, check):
    print(timestamp(), "Waiting for TX to Confirm....")
    timeout = time() + 60
    while True:
        print(timestamp(), ".........waiting............")
        try:
            txn_receipt = client.eth.getTransactionReceipt(tx_hash)
            return txn_receipt['status']
        except Exception as e:
            txn_receipt = None


        if txn_receipt is not None and txn_receipt['blockHash'] is not None:
            return txn_receipt['status']

        elif time() > timeout:
            print(timestamp(), "Transaction Timed Out, Breaking Check Cycle....")
            logging.info("Transaction Timed Out, Breaking Check Cycle....")
            break


    #loop to check for balance after purchase
    if check == True:
        timeout = time() + 30
        while True:
            print(timestamp(), ".........Balance Check After Purchase............")

            balance = check_balance(address, address)

            if balance > 0:
                break
            elif time() > timeout:
                print(timestamp(), "NO BUY FOUND, WE WILL CHECK A FEW TIMES TO SEE IF THERE IS BLOCKCHAIN DELAY, IF NOT WE WILL ASSUME THE TX HAS FAILED")
                logging.info("NO BUY FOUND, WE WILL CHECK A FEW TIMES TO SEE IF THERE IS BLOCKCHAIN DELAY, IF NOT WE WILL ASSUME THE TX HAS FAILED")
                break

def preapprove(tokens):

    for token in tokens:
        check_approval(token['ADDRESS'], 115792089237316195423570985008687907853269984665640564039457584007913129639934)

        if token['USECUSTOMBASEPAIR'].lower() == 'false':
            check_approval(weth, 115792089237316195423570985008687907853269984665640564039457584007913129639934)
        else:
            check_approval(token['BASEADDRESS'], 115792089237316195423570985008687907853269984665640564039457584007913129639934)

def buy(amount, inToken, outToken, gas, slippage, gaslimit, boost, fees, custom, symbol, base, routing):
    print(timestamp(), "Placing New Buy Order for " + symbol)

    if int(gaslimit) < 250000:
        gaslimit = 300000

    if custom.lower() == 'false':
        balance = Web3.fromWei(check_bnb_balance(), 'ether')
        base = base_symbol
    else:
        address = Web3.toChecksumAddress(inToken)
        DECIMALS = decimals(address)
        balance_check = check_balance(inToken, base)
        balance = balance_check/DECIMALS

    if balance > Decimal(amount):
        if gas.lower() == 'boost':
            gas_check = client.eth.gasPrice
            gas_price = gas_check / 1000000000
            gas = (gas_price * ((int(boost)*4)/100)) + gas_price
        else:
            gas = int(gas)

        gaslimit = int(gaslimit)
        slippage = int(slippage)
        DECIMALS = decimals(inToken)
        amount = int(float(amount) * DECIMALS)


        if custom.lower() == 'false':
            amount_out = routerContract.functions.getAmountsOut(amount, [weth, outToken]).call()[-1]
            if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                min_tokens = 100
            else:
                min_tokens = int(amount_out * (1 - (slippage / 100)))

            deadline = int(time() + + 60)


            # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
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
                # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
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

            if inToken == weth:
                amount_out = routerContract.functions.getAmountsOut(amount, [weth, outToken]).call()[-1]
                if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                    min_tokens = 100
                else:
                    min_tokens = int(amount_out * (1 - (slippage / 100)))
                deadline = int(time() + + 60)

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

                if routing.lower() == 'true':
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth, outToken]).call()[-1]
                    if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                        min_tokens = 100
                    else:
                        min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

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
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, outToken]).call()[-1]
                    if settings['UNLIMITEDSLIPPAGE'].lower() == 'true':
                        min_tokens = 100
                    else:
                        min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

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

    else:
        print(timestamp(), "Not Enough " + base + " Balance to make buys")
        logging.info("Not Enough " + base + " Balance to make buys")
        return False

def sell(amount, moonbag, inToken, outToken, gas, slippage, gaslimit, boost, fees, custom, symbol, routing):
    print(timestamp(), "Placing Sell Order " + symbol)
    balance = Web3.fromWei(check_balance(inToken, symbol), 'ether')
    check_approval(inToken, balance)

    if int(gaslimit) < 250000:
        gaslimit = 300000

    if type(amount) == str:
        amount_check = balance
    else:
        amount_check = Decimal(amount)


    if balance >= Decimal(amount_check) and balance > 0.0000000000000001:

        if gas.lower() == 'boost':
            gas_check = client.eth.gasPrice
            gas_price = gas_check / 1000000000
            gas = (gas_price * ((int(boost)*4)/100)) + gas_price
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
                amount = int(Decimal(balance - moonbag))
                if amount > 0:
                    print(timestamp(), "Selling", amount / DECIMALS, symbol)
                else:
                    print("Not enough left to sell, would bust moonbag")
                    amount = 0




        if custom.lower() == 'false':
            sync(inToken, weth)

            amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth]).call()[-1]
            min_tokens = int(amount_out * (1 - (slippage / 100)))
            deadline = int(time() + + 60)

            if fees.lower() == 'true':

                # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
                if modified == True:

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

                # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
                if modified == True:

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

            if outToken == weth:
                sync(inToken, outToken)
                amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth]).call()[-1]
                min_tokens = int(amount_out * (1 - (slippage / 100)))
                deadline = int(time() + + 60)

                if fees.lower() == 'true':

                    if int(gaslimit) < 950000:
                        gaslimit = 950000

                    # THIS SECTION IS FOR MODIFIED CONTRACTS AND EACH EXCHANGE IS SPECIFIED
                    if modified == True:

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
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, outToken]).call()[-1]
                    min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

                    if fees.lower() == 'true':
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
                    print("ERROR IN SETTINGS.... YOU NEED TO CHOOSE THE PROPER BASE PAIR AS SYMBOL IN YOUR TOKENS.JSON IF YOU ARE TRADING OUTSIDE OF NATIVE LIQUIDITY POOL")

                else:
                    amount_out = routerContract.functions.getAmountsOut(amount, [inToken, weth, outToken]).call()[-1]
                    min_tokens = int(amount_out * (1 - (slippage / 100)))
                    deadline = int(time() + + 60)

                    if fees.lower() == 'true':
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
    try:
        s = open('./tokens.json', )
        tokens = json.load(s)
        s.close()
        if settings['PREAPPROVE'].lower() == 'true':
            preapprove(tokens)
        else:
            pass

        while True:
            s = open('./tokens.json', )
            tokens = json.load(s)
            s.close()

            for token in tokens:

                if token['ENABLED'].lower() == 'true':
                    inToken = Web3.toChecksumAddress(token['ADDRESS'])


                    if token['USECUSTOMBASEPAIR'].lower() == 'true':
                        outToken = Web3.toChecksumAddress(token['BASEADDRESS'])
                    else:
                        outToken = weth

                    try:
                        quote = check_price(inToken, outToken, token['SYMBOL'], token['BASESYMBOL'], token['USECUSTOMBASEPAIR'], token['LIQUIDITYINNATIVETOKEN'])

                    except Exception:
                        print(timestamp(), token['SYMBOL'], " Not Listed For Trade Yet... waiting for liquidity to be added on exchange")
                        quote = 0

                    if quote < Decimal(token['BUYPRICEINBASE']) and quote != 0:
                        balance = check_balance(inToken, token['SYMBOL'])
                        DECIMALS = decimals(inToken)
                        if Decimal(balance/DECIMALS) < Decimal(token['MAXTOKENS']):

                            if token["LIQUIDITYCHECK"].lower() == 'true':
                                pool = check_pool(inToken, outToken, token['BASESYMBOL'])
                                if float(token['LIQUIDITYAMOUNT']) <= float(pool):
                                    print(timestamp(), "Buy Signal Found!")
                                    log_price = "{:.18f}".format(quote)
                                    logging.info("BuySignal Found @" + str(log_price))
                                    tx = buy(token['BUYAMOUNTINBASE'], outToken, inToken, token['GAS'], token['SLIPPAGE'], token['GASLIMIT'], token['BOOSTPERCENT'], token["HASFEES"], token['USECUSTOMBASEPAIR'], token['SYMBOL'], token['BASESYMBOL'], token['LIQUIDITYINNATIVETOKEN'])

                                    if tx != False:
                                        tx = wait_for_tx(tx, token['ADDRESS'], True)
                                        if tx != 1:
                                            preapprove(tokens)
                                        else:
                                            pass

                                    else:
                                        pass
                                else:
                                    print(timestamp(), "Not enough Liquidity for", token['SYMBOL'])

                            else:
                                print(timestamp(), "Buy Signal Found!")
                                log_price = "{:.18f}".format(quote)
                                logging.info("BuySignal Found @" + str(log_price))
                                tx = buy(token['BUYAMOUNTINBASE'], outToken, inToken, token['GAS'], token['SLIPPAGE'], token['GASLIMIT'], token['BOOSTPERCENT'], token["HASFEES"], token['USECUSTOMBASEPAIR'], token['SYMBOL'], token['BASESYMBOL'], token['LIQUIDITYINNATIVETOKEN'])

                                if tx != False:
                                    tx = wait_for_tx(tx, token['ADDRESS'], True)
                                    if tx != 1:
                                        preapprove(tokens)
                                    else:
                                        pass
                                else:
                                    pass


                        else:
                            print(timestamp(), "Max Position Size Reached for ", token['SYMBOL'])

                            if quote > Decimal(token['SELLPRICEINBASE']):
                                DECIMALS = decimals(inToken)
                                balance = check_balance(inToken, token['SYMBOL'])
                                moonbag = int(Decimal(token['MOONBAG']) * DECIMALS)
                                balance = int(Decimal(balance - moonbag))

                                if balance > 0:
                                    print(timestamp(), "Sell Signal Found " + token['SYMBOL'])
                                    log_price = "{:.18f}".format(quote)
                                    logging.info("Sell Signal Found @" + str(log_price))
                                    tx = sell(token['SELLAMOUNTINTOKENS'], token['MOONBAG'], inToken, outToken,
                                              token['GAS'], token['SLIPPAGE'], token['GASLIMIT'], token['BOOSTPERCENT'],
                                              token["HASFEES"], token['USECUSTOMBASEPAIR'], token['SYMBOL'], token['LIQUIDITYINNATIVETOKEN'])
                                    wait_for_tx(tx, token['ADDRESS'], False)
                                else:
                                    pass


                    elif quote > Decimal(token['SELLPRICEINBASE']) and quote != 0:
                        DECIMALS = decimals(inToken)
                        balance = check_balance(inToken, token['SYMBOL'])
                        moonbag = int(Decimal(token['MOONBAG']) * DECIMALS)
                        balance = int(Decimal(balance - moonbag))

                        if balance > 0:
                            print(timestamp(), "Sell Signal Found " + token['SYMBOL'])
                            log_price = "{:.18f}".format(quote)
                            logging.info("Sell Signal Found @" + str(log_price))
                            tx = sell(token['SELLAMOUNTINTOKENS'], token['MOONBAG'], inToken, outToken, token['GAS'], token['SLIPPAGE'], token['GASLIMIT'], token['BOOSTPERCENT'], token["HASFEES"], token['USECUSTOMBASEPAIR'], token['SYMBOL'], token['LIQUIDITYINNATIVETOKEN'])
                            wait_for_tx(tx, token['ADDRESS'], False)
                        else:
                            #Double Check For Buy if Sell Signal Triggers
                            if quote < Decimal(token['BUYPRICEINBASE']):
                                balance = check_balance(inToken, token['SYMBOL'])
                                if Web3.fromWei(balance, 'ether') < Decimal(token['MAXTOKENS']):
                                    print(timestamp(), "Buy Signal Found!")
                                    log_price = "{:.18f}".format(quote)
                                    logging.info("Sell Signal Found @" + str(log_price))
                                    tx = buy(token['BUYAMOUNTINBASE'], outToken, inToken, token['GAS'], token['SLIPPAGE'], token['GASLIMIT'], token['BOOSTPERCENT'], token["HASFEES"], token['USECUSTOMBASEPAIR'], token['SYMBOL'], token['LIQUIDITYINNATIVETOKEN'])
                                    wait_for_tx(tx, token['ADDRESS'], False)
                                else:
                                    print(timestamp(), "Max Position Size Reached for ", token['SYMBOL'])
                                    pass
                else:
                    pass

            sleep(cooldown)

    except Exception as ee:
        print(timestamp(), "ERROR: Please Check Your Error & Exception Logs for more info...")
        logging.exception(ee)
        logger1.exception(ee)
        sleep(10)
        print("Restarting LimitSwap")
        logging.info("Restarting LimitSwap")
        #Cooldown Logic
        timeout = 10
        nonce = 0
        while True:
            print(".........Restart Cooldown left " + str(timeout - nonce) + " seconds.............")
            nonce += 1
            sleep(1)
            if nonce > timeout:
                run()


try:

    check_logs()
    userpassword = get_password()
    load_wallet_settings(userpassword)
    true_balance = auth()
    save_settings(userpassword)

    version = 3.36
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
        print(timestamp(), "10 - 50 $LIMIT tokens needed to use this bot, please visit the LimitSwap.com for more info or buy more tokens on Uniswap to use!")
        logging.exception("10 - 50 $LIMIT tokens needed to use this bot, please visit the LimitSwap.com for more info or buy more tokens on Uniswap to use!")



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



