import os
import json

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