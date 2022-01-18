.DEFAULT_GOAL = help
g  =\033[32m
r  =\033[31m
y  =\033[33m
b  =\033[34m
n  =\033[0m
bd =$(shell tput bold)
st =$(shell tput sgr0)

VENV_NAME?=env
PYTHON=${VENV_NAME}/bin/python
HOME=$(shell pwd)
.PHONY: help run  benchmark clean build start stop restart logs ssh
.PHONY: hello prepare_venv prepare_args prepare_args_vars install_dependencies start_container

hello:
	@echo ""
	@echo "${g}LimitSwap command line interface${n}"
	@echo ""

help: hello
	@echo ""
	@echo "${y}$(bd)Commands:$(st)"
	@echo "    ${g}run${n}		Run the bot"
	@echo "    ${y}Usage:$(st)"
	@echo "    ${n}  make ${g}run${n} ${b}[settings]${n} ${b}[tokens]${n} ${b}[arguments]${n}"
	@echo "    ${b}    [settings] syntax${n}: 'make run s=bsc' or 'make run settings=bsc' means file 'settings/settings-bsc.json' will be used"
	@echo "    ${b}    [tokens] syntax${n}: 'make run t=moon' or 'make run tokens=moon' means file 'tokens/tokens-moon.json' will be used"
	@echo "    ${b}    [arguments] syntax${n}: 'make run args='-v'' means bot will be started in Verbose mode. All command line arguments of application supported"
	@echo "    ${g}benchmark${n}		Run benchmark mode"
	@echo "    ${g}clean${n}		Remove virtual environment and clear logs"
	@echo "    ${g}help${n}		Show this help output."
	@echo ""
	@echo "${y}$(bd)Docker commands:$(st)"
	@echo "    ${g}build${n}		Build docker image"
	@echo "    ${g}start${n}		Start docker container. Arguments from 'make run' supported"
	@echo "    ${g}stop${n}		Stop docker container"
	@echo "    ${g}restart${n}		Restart docker container"
	@echo "    ${g}logs${n}		Fetch the logs of the container"
	@echo "    ${g}ssh${n}			Run a shell in the  container"

install_dependencies:
	@test -d $(VENV_NAME) || echo "${b}[.] Installing dependencies${n}"; sudo apt-get update -qq >/dev/null && sudo apt-get install python3-dev build-essential python3-pip python3-venv virtualenv -y -qq >/dev/null

prepare_venv: install-dependencies $(VENV_NAME)/bin/activate
	@echo "${g}[+] Virtual environment is ready${n}"

$(VENV_NAME)/bin/activate: requirements.txt
	@echo "${b}[.] Preparing virtual environment${n}"
	test -d ${VENV_NAME} || virtualenv -p python3 ${VENV_NAME}
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -r requirements.txt
	touch $(VENV_NAME)/bin/activate	

prepare_args_vars: 
settings_arg=$(shell ( test ${settings} || test ${s} ) &&  echo settings/settings-${settings}${s}.json || echo settings.json)
tokens_arg=$(shell ( test ${tokens} || test ${t} ) &&  echo tokens/tokens-${tokens}${t}.json || echo tokens.json)

prepare_args: prepare_args_vars
	echo ${settings_arg} ${tokens_arg}
	@test -f ${settings_arg}  || (echo "[!] Settings configuration file is not exist. Terminating..." && exit 1)
	@test -f ${tokens_arg}  || (echo "[!] Tokens configuration file is not exist. Terminating..." && exit 1)

run: hello prepare_venv prepare_args
	@echo "${b}[.] Running bot${n}"
	${PYTHON} LimitSwap.py -s $(settings_arg) -t ${tokens_arg} ${args}

benchmark: prepare_venv
	@echo "${b}[.] Running benchmark${n}"
	${PYTHON} LimitSwap.py --benchmark

clean:
	@echo "${b}[.] Cleaning virtual environment and logs${n}"
	@rm -rf env
	@rm -rf logs/*.log
	@echo "${b}[+] Virtual environment and logs cleaned successfully${n}"

build: hello
	@echo "${b}[.] Building docker image${n}"
	@docker build -t limit_swap_v4 .
	@echo "${b}[+] Docker image successfully built${n}"

start_container: prepare_args
	@echo "${b}[.] Running the bot in container${n}"
	docker run -d --rm --name limit_swap_v4 -v $(HOME)/${settings_arg}:/app/settings.json -v $(HOME)/${tokens_arg}:/app/tokens.json -v $(HOME)/logs:/app/logs limit_swap_v4
	@echo "${b}[+] The bot in container successfully started${n}"

logs:
	@echo "${b}[.] Fetching the logs of a container${n}"
	@docker logs -f limit_swap_v4

ssh: hello
	@echo "${b}[.] Entering shell to the container${n}"
	@docker exec -it limit_swap_v4 bash

stop: hello
	@echo "${b}[.] Stopping the bot in  container${n}"
	@docker stop limit_swap_v4
	@echo "${b}[+] The bot in container successfully stopped${n}"

start: hello start_container logs

restart: stop start