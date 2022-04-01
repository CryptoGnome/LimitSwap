from web3.middleware import geth_poa_middleware
from datetime import datetime
import os
import json


"""""""""""""""""""""""""""
// ABI DEFINITION
"""""""""""""""""""""""""""

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
filename = "Swapper.json"
file_path = os.path.join(directory, filename)
with open(file_path) as json_file:
    swapperAbi = json.load(json_file)

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
// NETWORKS SELECT
"""""""""""""""""""""""""""

def getRouters(settings, Web3):
    if settings['EXCHANGE'] == 'pancakeswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://bsc-dataseed4.defibit.io"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        
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
        swapper_address = Web3.toChecksumAddress("0x18be7f977Ec1217B71D0C134FBCFF36Ea4366fCD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier': 0},
                                     'BUSD': {'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier': 0},
                                     'USDC': {'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier': 0}}

    elif settings['EXCHANGE'] == 'sushiswapbsc':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://bsc-dataseed4.defibit.io"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading SushiSwap Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")
        factoryAddress = Web3.toChecksumAddress("0xc35DADB65012eC5796536bD9864eD8773aBc74C4")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        base_symbol = "BNB "
        rugdocchain = '&chain=bsc'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x18be7f977Ec1217B71D0C134FBCFF36Ea4366fCD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier': 0},
                                     'BUSD': {'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier': 0},
                                     'USDC': {'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier': 0}}
    
    if settings['EXCHANGE'].lower() == 'pancakeswaptestnet':
        
        if settings['USECUSTOMNODE'].lower() == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://data-seed-prebsc-2-s2.binance.org:8545"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain testnet Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        
        if settings['EXCHANGEVERSION'] == "1":
            routerAddress = Web3.toChecksumAddress("0x05fF2B0DB69458A0750badebc4f9e13aDd608C7F")
            factoryAddress = Web3.toChecksumAddress("0xbcfccbde45ce874adcb698cc183debcf17952812")
        elif settings['EXCHANGEVERSION'] == "2":
            routerAddress = Web3.toChecksumAddress("0x9ac64cc6e4415144c455bd8e4837fea55603e5c3")
            factoryAddress = Web3.toChecksumAddress("0xb7926c0430afb07aa7defde6da862ae0bde767bc")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xae13d989dac2f0debff460ac112a837c89baa7cd")
        base_symbol = "BNBt"
        rugdocchain = '&chain=bsc'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNBt'
        settings['_STABLE_BASES'] = {'BUSD': {'address': '0x8301f2213c0eed49a7e28ae4c3e91722919b8b47', 'multiplier': 0},
                                     'DAI ': {'address': '0x8a9424745056eb399fd19a0ec26a14316684e274', 'multiplier': 0}}
    
    if settings['EXCHANGE'].lower() == 'traderjoe':
        
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://api.avax.network/ext/bc/C/rpc"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "AVAX Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading TraderJoe Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x60aE616a2155Ee3d9A68541Ba4544862310933d4")
        factoryAddress = Web3.toChecksumAddress("0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10")
        
        routerContract = client.eth.contract(address=routerAddress, abi=joeRouter)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7")
        base_symbol = "AVAX"
        rugdocchain = '&chain=avax'
        modified = True
        swapper_address = Web3.toChecksumAddress("0x052a50b4b8309Fc2dF49E2ec78470E29DD9fA459")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'AVAX'
        settings['_STABLE_BASES'] = {'MIM ': {'address': '0x130966628846bfd36ff31a822705796e8cb8c18d', 'multiplier': 0},
                                     'USDC': {'address': '0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664', 'multiplier': 0},
                                     'USDC': {'address': '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e', 'multiplier': 0},
                                     'USDT': {'address': '0xc7198437980c041c805a1edcba50c1ce5db95118', 'multiplier': 0}}
    
    if settings['EXCHANGE'].lower() == 'sushiswapavax':
        
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://api.avax.network/ext/bc/C/rpc"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "AVAX Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading SushiSwap Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")
        factoryAddress = Web3.toChecksumAddress("0xc35DADB65012eC5796536bD9864eD8773aBc74C4")
        
        routerContract = client.eth.contract(address=routerAddress, abi=pangolinAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7")
        base_symbol = "AVAX"
        rugdocchain = '&chain=avax'
        modified = True
        swapper_address = Web3.toChecksumAddress("0x052a50b4b8309Fc2dF49E2ec78470E29DD9fA459")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'AVAX'
        settings['_STABLE_BASES'] = {'MIM ': {'address': '0x130966628846bfd36ff31a822705796e8cb8c18d', 'multiplier': 0},
                                     'USDC': {'address': '0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664', 'multiplier': 0},
                                     'USDC': {'address': '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e', 'multiplier': 0},
                                     'USDT': {'address': '0xc7198437980c041c805a1edcba50c1ce5db95118', 'multiplier': 0}}
    
    if settings["EXCHANGE"] == 'pangolin':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://api.avax.network/ext/bc/C/rpc"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "AVAX Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106")
        factoryAddress = Web3.toChecksumAddress("0xefa94DE7a4656D787667C749f7E1223D71E9FD88")
        routerContract = client.eth.contract(address=routerAddress, abi=pangolinAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7")
        base_symbol = "AVAX"
        rugdocchain = '&chain=avax'
        modified = True
        swapper_address = Web3.toChecksumAddress("0x052a50b4b8309Fc2dF49E2ec78470E29DD9fA459")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        
        settings['_EXCHANGE_BASE_SYMBOL'] = 'AVAX'
        settings['_STABLE_BASES'] = {'MIM ': {'address': '0x130966628846bfd36ff31a822705796e8cb8c18d', 'multiplier': 0},
                                     'USDC': {'address': '0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664', 'multiplier': 0},
                                     'USDC': {'address': '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e', 'multiplier': 0},
                                     'USDT': {'address': '0xc7198437980c041c805a1edcba50c1ce5db95118', 'multiplier': 0}}
    
    if settings['EXCHANGE'] == 'pinkswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://bsc-dataseed4.defibit.io"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading PinkSwap Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x319EF69a98c8E8aAB36Aea561Daba0Bf3D0fa3ac")
        factoryAddress = Web3.toChecksumAddress("0x7d2ce25c28334e40f37b2a068ec8d5a59f11ea54")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        
        weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        base_symbol = "BNB "
        rugdocchain = '&chain=bsc'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x18be7f977Ec1217B71D0C134FBCFF36Ea4366fCD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier': 0},
                                     'BUSD': {'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier': 0},
                                     'USDC': {'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier': 0}}
    
    if settings['EXCHANGE'] == 'biswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://bsc-dataseed4.defibit.io"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading BiSwap Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8")
        factoryAddress = Web3.toChecksumAddress("0x858E3312ed3A876947EA49d572A7C42DE08af7EE")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        
        weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        base_symbol = "BNB "
        rugdocchain = '&chain=bsc'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x18be7f977Ec1217B71D0C134FBCFF36Ea4366fCD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier': 0},
                                     'BUSD': {'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier': 0},
                                     'USDC': {'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier': 0}}
    
    elif settings['EXCHANGE'].lower() == 'babyswap':
        if settings['USECUSTOMNODE'].lower() == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://bsc-dataseed4.defibit.io"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading BabySwap Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x325E343f1dE602396E256B67eFd1F61C3A6B38Bd")
        factoryAddress = Web3.toChecksumAddress("0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        
        weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        base_symbol = "BNB "
        rugdocchain = '&chain=bsc'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x18be7f977Ec1217B71D0C134FBCFF36Ea4366fCD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier': 0},
                                     'BUSD': {'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier': 0},
                                     'USDC': {'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier': 0}}
    
    elif settings['EXCHANGE'].lower() == 'tethys':
        if settings['USECUSTOMNODE'].lower() == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://andromeda.metis.io/?owner=1088"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Metis Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Tethys Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x81b9FA50D5f5155Ee17817C21702C3AE4780AD09")
        factoryAddress = Web3.toChecksumAddress("0x2CdFB20205701FF01689461610C9F321D1d00F80")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        
        weth = Web3.toChecksumAddress("0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000")
        base_symbol = "METIS"
        rugdocchain = '&chain=metis'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'METIS'
        settings['_STABLE_BASES'] = {'mUSDC': {'address': '0xEA32A96608495e54156Ae48931A7c20f0dcc1a21', 'multiplier': 0}}
    
    if settings['EXCHANGE'] == 'bakeryswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using custom node.')
        else:
            my_provider = "https://bsc-dataseed4.defibit.io"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading BakerySwap Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0xCDe540d7eAFE93aC5fE6233Bee57E1270D3E330F")
        factoryAddress = Web3.toChecksumAddress("0x01bF7C66c6BD861915CdaaE475042d3c4BaE16A7")
        
        routerContract = client.eth.contract(address=routerAddress, abi=bakeryRouter)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        
        weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        base_symbol = "BNB "
        rugdocchain = '&chain=bsc'
        modified = True
        swapper_address = Web3.toChecksumAddress("0x18be7f977Ec1217B71D0C134FBCFF36Ea4366fCD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier': 0},
                                     'BUSD': {'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier': 0},
                                     'USDC': {'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier': 0}}
    
    if settings['EXCHANGE'] == 'apeswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://bsc-dataseed4.defibit.io"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Binance Smart Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading ApeSwap Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7")
        factoryAddress = Web3.toChecksumAddress("0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        
        weth = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        busd = Web3.toChecksumAddress("0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56")
        base_symbol = "BNB "
        rugdocchain = '&chain=bsc'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x18be7f977Ec1217B71D0C134FBCFF36Ea4366fCD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'BNB '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x55d398326f99059ff775485246999027b3197955', 'multiplier': 0},
                                     'BUSD': {'address': '0xe9e7cea3dedca5984780bafc599bd69add087d56', 'multiplier': 0},
                                     'USDC': {'address': '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'uniswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Uniswap Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
        factoryAddress = Web3.toChecksumAddress("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        base_symbol = "ETH "
        rugdocchain = '&chain=eth'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'ETH '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0xdac17f958d2ee523a2206206994597c13d831ec7', 'multiplier': 0},
                                     'USDC': {'address': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'sushiswapeth':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Uniswap Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading SushiSwap Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")
        factoryAddress = Web3.toChecksumAddress("0xc35DADB65012eC5796536bD9864eD8773aBc74C4")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        base_symbol = "ETH "
        rugdocchain = '&chain=eth'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'ETH '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0xdac17f958d2ee523a2206206994597c13d831ec7', 'multiplier': 0},
                                     'USDC': {'address': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'degenswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Degenswap Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x4bf3E2287D4CeD7796bFaB364C0401DFcE4a4f7F")
        factoryAddress = Web3.toChecksumAddress("0x5c515455EFB90308689579993C11A84fC41229C0")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        base_symbol = "ETH "
        rugdocchain = '&chain=eth'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'ETH '
        settings['_STABLE_BASES'] = {'USDT': {'address': '0xdac17f958d2ee523a2206206994597c13d831ec7', 'multiplier': 0},
                                     'USDC': {'address': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'uniswaptestnet':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rinkeby-light.eth.linkpool.io/"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Uniswap Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
        factoryAddress = Web3.toChecksumAddress("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xc778417e063141139fce010982780140aa0cd5ab")
        base_symbol = "ETHt"
        rugdocchain = '&chain=eth'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'ETHt'
        settings['_STABLE_BASES'] = {'USDT': {'address': '0x3b00ef435fa4fcff5c209a37d1f3dcff37c705ad', 'multiplier': 0},
                                     'USDC': {'address': '0x4dbcdf9b62e891a7cec5a2568c3f4faf9e8abe2b', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'kuswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc-mainnet.kcc.network"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Kucoin Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading KuSwap Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xa58350d6dee8441aa42754346860e3545cc83cda")
        factoryAddress = Web3.toChecksumAddress("0xAE46cBBCDFBa3bE0F02F463Ec5486eBB4e2e65Ae")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x4446Fc4eb47f2f6586f9fAAb68B3498F86C07521")
        base_symbol = "KCS"
        rugdocchain = '&chain=kcc'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'KCS'
        settings['_STABLE_BASES'] = {'USD ': {'address': '0x0039f574ee5cc39bdd162e9a88e3eb1f111baf48', 'multiplier': 0}}
    
    
    elif settings["EXCHANGE"] == 'koffeeswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc-mainnet.kcc.network"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Kucoin Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading KoffeeSwap Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xc0fFee0000C824D24E0F280f1e4D21152625742b")
        factoryAddress = Web3.toChecksumAddress("0xC0fFeE00000e1439651C6aD025ea2A71ED7F3Eab")
        routerContract = client.eth.contract(address=routerAddress, abi=koffeeAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x4446Fc4eb47f2f6586f9fAAb68B3498F86C07521")
        base_symbol = "KCS"
        rugdocchain = '&chain=kcc'
        modified = True
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'KCS'
        settings['_STABLE_BASES'] = {'USD ': {'address': '0x0039f574ee5cc39bdd162e9a88e3eb1f111baf48', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'spookyswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc.ftm.tools/"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "FANTOM Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xF491e7B69E4244ad4002BC14e878a34207E38c29")
        factoryAddress = Web3.toChecksumAddress("0x152eE697f2E276fA89E96742e9bB9aB1F2E61bE3")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83")
        base_symbol = "FTM "
        rugdocchain = '&chain=ftm'
        modified = False
        swapper_address = Web3.toChecksumAddress("0xdA19096CCecFEEE1da30021c17a33819dE6E11F1")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'FTM '
        settings['_STABLE_BASES'] = {'USDC': {'address': '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 'multiplier': 0},
                                     'USDT': {'address': '0x049d68029688eabf473097a2fc38ef61633a3c7a', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'sushiswapftm':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc.ftm.tools/"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "FANTOM Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading SushiSwap Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")
        factoryAddress = Web3.toChecksumAddress("0xc35DADB65012eC5796536bD9864eD8773aBc74C4")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83")
        base_symbol = "FTM "
        rugdocchain = '&chain=ftm'
        modified = False
        swapper_address = Web3.toChecksumAddress("0xdA19096CCecFEEE1da30021c17a33819dE6E11F1")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'FTM '
        settings['_STABLE_BASES'] = {'USDC': {'address': '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 'multiplier': 0},
                                     'USDT': {'address': '0x049d68029688eabf473097a2fc38ef61633a3c7a', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'protofi':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc.ftm.tools/"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "FANTOM Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xF4C587a0972Ac2039BFF67Bc44574bB403eF5235")
        factoryAddress = Web3.toChecksumAddress("0x39720E5Fe53BEEeb9De4759cb91d8E7d42c17b76")
        routerContract = client.eth.contract(address=routerAddress, abi=protofirouter)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83")
        base_symbol = "FTM "
        rugdocchain = '&chain=ftm'
        modified = False
        swapper_address = Web3.toChecksumAddress("0xdA19096CCecFEEE1da30021c17a33819dE6E11F1")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'FTM '
        settings['_STABLE_BASES'] = {'USDC': {'address': '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 'multiplier': 0},
                                     'USDT': {'address': '0x049d68029688eabf473097a2fc38ef61633a3c7a', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'spiritswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc.ftm.tools/"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "FANTOM Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52")
        factoryAddress = Web3.toChecksumAddress("0xEF45d134b73241eDa7703fa787148D9C9F4950b0")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83")
        base_symbol = "FTM "
        rugdocchain = '&chain=ftm'
        modified = False
        swapper_address = Web3.toChecksumAddress("0xdA19096CCecFEEE1da30021c17a33819dE6E11F1")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'FTM '
        settings['_STABLE_BASES'] = {'USDC': {'address': '0x04068da6c83afcfa0e13ba15a6696662335d5b75', 'multiplier': 0},
                                     'USDT': {'address': '0x049d68029688eabf473097a2fc38ef61633a3c7a', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'quickswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://polygon-rpc.com"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Matic Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")
        factoryAddress = Web3.toChecksumAddress("0x5757371414417b8c6caad45baef941abc7d3ab32")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
        base_symbol = "MATIC"
        rugdocchain = '&chain=poly'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'MATIC'
        settings['_STABLE_BASES'] = {'USDT ': {'address': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', 'multiplier': 0},
                                     'USDC ': {'address': '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'sushiswapmatic':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://polygon-rpc.com"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Matic Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading SushiSwap Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")
        factoryAddress = Web3.toChecksumAddress("0xc35DADB65012eC5796536bD9864eD8773aBc74C4")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
        base_symbol = "MATIC"
        rugdocchain = '&chain=poly'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'MATIC'
        settings['_STABLE_BASES'] = {'USDT ': {'address': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', 'multiplier': 0},
                                     'USDC ': {'address': '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'polygon-apeswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://polygon-rpc.com"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Matic Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xC0788A3aD43d79aa53B09c2EaCc313A787d1d607")
        factoryAddress = Web3.toChecksumAddress("0xCf083Be4164828f00cAE704EC15a36D711491284")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
        base_symbol = "MATIC"
        rugdocchain = '&chain=poly'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'MATIC'
        settings['_STABLE_BASES'] = {'USDT ': {'address': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', 'multiplier': 0},
                                     'USDC ': {'address': '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'waultswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc-waultfinance-mainnet.maticvigil.com/v1/0bc1bb1691429f1eeee66b2a4b919c279d83d6b0"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Matic Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x3a1D87f206D12415f5b0A33E786967680AAb4f6d")
        factoryAddress = Web3.toChecksumAddress("0xa98ea6356A316b44Bf710D5f9b6b4eA0081409Ef")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")
        base_symbol = "MATIC"
        rugdocchain = '&chain=poly'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'MATIC'
        settings['_STABLE_BASES'] = {'USDT ': {'address': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', 'multiplier': 0},
                                     'USDC ': {'address': '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'cronos-vvs':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://evm-cronos.crypto.org"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Cronos Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x145863Eb42Cf62847A6Ca784e6416C1682b1b2Ae")
        factoryAddress = Web3.toChecksumAddress("0x3b44b2a187a7b3824131f8db5a74194d0a42fc15")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x5C7F8A570d578ED84E63fdFA7b1eE72dEae1AE23")
        base_symbol = "CRO"
        rugdocchain = '&chain=cronos'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'CRO'
        settings['_STABLE_BASES'] = {'USDC': {'address': '0xc21223249ca28397b4b6541dffaecc539bff0c59', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'cronos-meerkat':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://evm-cronos.crypto.org"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Cronos Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0x145677FC4d9b8F19B5D56d1820c48e0443049a30")
        factoryAddress = Web3.toChecksumAddress("0xd590cC180601AEcD6eeADD9B7f2B7611519544f4")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x5c7f8a570d578ed84e63fdfa7b1ee72deae1ae23")
        base_symbol = "CRO"
        rugdocchain = '&chain=cronos'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'CRO'
        settings['_STABLE_BASES'] = {'USDC': {'address': '0xc21223249ca28397b4b6541dffaecc539bff0c59', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'cronos-crona':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://evm-cronos.crypto.org"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Cronos Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading Smart Contracts...")
        routerAddress = Web3.toChecksumAddress("0xcd7d16fB918511BF7269eC4f48d61D79Fb26f918")
        factoryAddress = Web3.toChecksumAddress("0x73A48f8f521EB31c55c0e1274dB0898dE599Cb11")
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0x5c7f8a570d578ed84e63fdfa7b1ee72deae1ae23")
        base_symbol = "CRO"
        rugdocchain = '&chain=cronos'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)
        settings['_EXCHANGE_BASE_SYMBOL'] = 'CRO'
        settings['_STABLE_BASES'] = {'USDC': {'address': '0xc21223249ca28397b4b6541dffaecc539bff0c59', 'multiplier': 0}}
    
    elif settings["EXCHANGE"] == 'viperswap':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://api.harmony.one/"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "HARMONY Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading WONE Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0xf012702a5f0e54015362cbca26a26fc90aa832a3")
        factoryAddress = Web3.toChecksumAddress("0x7D02c116b98d0965ba7B642ace0183ad8b8D2196")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xcf664087a5bb0237a0bad6742852ec6c8d69a27a")
        base_symbol = "WONE"
        rugdocchain = '&chain=one'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'WONE'
        settings['_STABLE_BASES'] = {'BUSD': {'address': '0xe176ebe47d621b984a73036b9da5d834411ef734', 'multiplier': 0},
                                     'USDT': {'address': '0x3c2b8be99c50593081eaa2a724f0b8285f5aba8f', 'multiplier': 0}}

    elif settings["EXCHANGE"] == 'milkomeda':
        if settings['USECUSTOMNODE'] == 'true':
            my_provider = settings['CUSTOMNODE']
        else:
            my_provider = "https://rpc-mainnet-cardano-evm.c1.milkomeda.com"
        
        if not my_provider:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Custom node empty. Exiting')
            exit(1)
        
        if my_provider[0].lower() == 'h':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using HTTPProvider')
            client = Web3(Web3.HTTPProvider(my_provider))
        elif my_provider[0].lower() == 'w':
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using WebsocketProvider')
            client = Web3(Web3.WebsocketProvider(my_provider))
        else:
            print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), 'Using IPCProvider')
            client = Web3(Web3.IPCProvider(my_provider))
        
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "MILKOMEDA Chain Connected =", client.isConnected())
        print(datetime.now().strftime('%m-%d %H:%M:%S.%f'), "Loading WADA Smart Contracts...")
        
        routerAddress = Web3.toChecksumAddress("0x9D2E30C2FB648BeE307EDBaFDb461b09DF79516C")
        factoryAddress = Web3.toChecksumAddress("0xD6Ab33Ad975b39A8cc981bBc4Aaf61F957A5aD29")
        
        routerContract = client.eth.contract(address=routerAddress, abi=routerAbi)
        factoryContract = client.eth.contract(address=factoryAddress, abi=factoryAbi)
        weth = Web3.toChecksumAddress("0xAE83571000aF4499798d1e3b0fA0070EB3A3E3F9")
        base_symbol = "ADA"
        rugdocchain = '&chain=ada'
        modified = False
        swapper_address = Web3.toChecksumAddress("0x000000000000000000000000000000000000dEaD")
        swapper = client.eth.contract(address=swapper_address, abi=swapperAbi)

        settings['_EXCHANGE_BASE_SYMBOL'] = 'ADA'
        settings['_STABLE_BASES'] = {'USDC': {'address': '0x6a2d262D56735DbA19Dd70682B39F6bE9a931D98', 'multiplier': 0},
                                     'USDT': {'address': '0x3795C36e7D12A8c252A20C5a7B455f7c57b60283', 'multiplier': 0}}


    # Necessary to scan mempool
    client.middleware_onion.inject(geth_poa_middleware, layer=0)

    return client, routerAddress, factoryAddress, routerContract, factoryContract, weth, base_symbol, modified, my_provider, rugdocchain, swapper


