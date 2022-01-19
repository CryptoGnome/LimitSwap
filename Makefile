#######################################################################################################################################
# Variables																															  #
#######################################################################################################################################

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
.PHONY: help run benchmark clean build start stop restart logs ssh enable
.PHONY: hello prepare_venv prepare_args prepare_args_vars install_dependencies start_container

INSTANCE := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(INSTANCE):;@:)

#######################################################################################################################################
# Common targets																													  #
#######################################################################################################################################

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
	@echo "    ${g}clean${n}		Remove virtual environment, instances status and clear logs"
	@echo "    ${g}help${n}		Show this help output."
	@echo ""
	@echo "${y}$(bd)Instances commands:$(st)"
	@echo "    ${g}init${n} NAME		Initialization of configuration for the instance"
	@echo "    ${g}list${n}		List of instances configurations"
	@echo "    ${g}enable${n} NAME		Enable instance configuration"
	@echo "    ${g}disable${n} NAME	Disable instance configuration"

	@echo ""
	@echo "${y}$(bd)Docker commands:$(st)"
	@echo "    ${g}build${n} 		Build docker image. If image is not exist, it'll be built on 'make start'"
	@echo "    ${g}start${n} NAME|all		Start docker container."
	@echo "    ${g}stop${n} NAME|all 	Stop docker container"
	@echo "    ${g}logs${n} NAME		Fetch the logs of the container"
	@echo "    ${g}ssh${n} NAME			Run a shell in the  container"
	@echo "    ${g}status${n} 		Instances status"
	@echo "    ${g}prune${n} 		Remove docker image"



#######################################################################################################################################
# Local environment																													  #
#######################################################################################################################################

install_dependencies:
	@test -d $(VENV_NAME) || echo "${b}[.] Installing dependencies${n}"; sudo apt-get update -qq >/dev/null && sudo apt-get install python3-dev build-essential python3-pip python3-venv virtualenv -y -qq >/dev/null

prepare_venv: install_dependencies $(VENV_NAME)/bin/activate
	@echo "${g}[+] Virtual environment is ready${n}"

$(VENV_NAME)/bin/activate: requirements.txt
	@echo "${b}[.] Preparing virtual environment${n}"
	test -d ${VENV_NAME} || virtualenv -p python3 ${VENV_NAME}
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -r requirements.txt
	touch $(VENV_NAME)/bin/activate	

prepare_args_vars: 
settings_arg=$(shell ( test ${settings} || test ${s} ) &&  echo ${settings}${s})
tokens_arg=$(shell ( test ${tokens} || test ${t} ) &&  echo ${tokens}${t})

prepare_args_str: prepare_args_vars
settings_str=$(shell ( test ${settings} || test ${s} ) &&  echo settings/settings-${settings}${s}.json || echo settings.json)
tokens_str=$(shell ( test ${tokens} || test ${t} ) &&  echo tokens/tokens-${tokens}${t}.json || echo tokens.json)

prepare_args: prepare_args_str
	@echo ${settings_arg} ${tokens_arg}
	@echo ${settings_str} ${tokens_str}

#echo ${settings_arg} | grep -q "," && echo "Found it with grep"; \


	@test -f ${settings_str}  || (echo "[!] Settings configuration file is not exist. Terminating..." && exit 1)
	@test -f ${tokens_str}  || (echo "[!] Tokens configuration file is not exist. Terminating..." && exit 1)

run: hello prepare_venv prepare_args
	@echo "${b}[.] Running bot${n}"
	${PYTHON} LimitSwap.py -s $(settings_str) -t ${tokens_str} ${args}

benchmark: prepare_venv
	@echo "${b}[.] Running benchmark${n}"
	${PYTHON} LimitSwap.py --benchmark

clean:
	@echo "${b}[.] Cleaning virtual environment and logs${n}"
	@rm -rf env
	@rm -rf logs/*.log
	@echo "${b}[+] Virtual environment and logs cleaned successfully${n}"


#######################################################################################################################################
# Instances configuration																											  #
#######################################################################################################################################

init: hello
	@echo "[.] Creating instance '${INSTANCE}'"
	@test -d ${HOME}/instances/${INSTANCE} || mkdir -p ${HOME}/instances/${INSTANCE}
	@( test -d ${HOME}/instances/${INSTANCE} && test ! -f ${HOME}/instances/${INSTANCE}/settings.json ) && \
	( cp ${HOME}/settings.json ${HOME}/instances/${INSTANCE}/settings.json && cp ${HOME}/tokens.json ${HOME}/instances/${INSTANCE}/tokens.json && \
	echo [.] Configuration files located in ${HOME}/instances/${INSTANCE}/ && \
	echo [.] To enable instance use command: make enable ${INSTANCE} && \
	echo [+] Instance '${INSTANCE}' successfully initialized! ) || \
	echo [!] Instance '${INSTANCE}' already initialized!

list: hello print_state
 
enable: hello check_enabled print_state
	@echo ""
	@test -d ${HOME}/env/enabled || mkdir -p ${HOME}/env/enabled
	@test ! -f $(HOME)/env/enabled/${INSTANCE} && ( echo [.] Enabling ${INSTANCE} && touch $(HOME)/env/enabled/$(INSTANCE) ) || echo ${INSTANCE} instance already enabled 

disable: hello check_enabled 
	@echo ""
	test -f $(HOME)/env/enabled/${INSTANCE} && ( echo [.] Disabling ${INSTANCE} && unlink $(HOME)/env/enabled/$(INSTANCE) ) || echo ${INSTANCE} instance already disabled
	@make print_state

check_enabled:
instances_available = $(shell ls $(HOME)/instances)
instances_enabled = $(shell ls $(HOME)/env/enabled)

print_state: check_enabled
	@echo "${y}$(bd)Availabled instances:$(st)"
	@for dir in $(instances_available); do \
        echo $$dir; \
    done

	@echo "${y}$(bd)Enabled instances:$(st)"
	@for dir in $(instances_enabled); do \
        echo $$dir; \
    done


#######################################################################################################################################
# Instances docker operations																										  #
#######################################################################################################################################

build: hello
	@echo "${b}[.] Check if docker image exists${n}"
	@test ! -z "$(shell docker images -q limit_swap 2> /dev/null)"  && echo "${b}[+] Image ${bd}limit_swap${st} ${b}exists${n}" || (echo "${b}[.] Building docker image${n}" && docker build -t limit_swap . && echo "${b}[+] Docker image successfully built${n}")

prune: hello
	@echo "${b}[.] Check if docker image exists${n}"
	@test -z "$(shell docker images -q limit_swap 2> /dev/null)"  && echo "${b}[+] Image ${bd}limit_swap${st} ${b}does not exist${n}" || (docker rmi limit_swap  && echo "${b}[+] Docker image successfully deleted${n}")

start: hello build
	@test -z ${INSTANCE} && echo "[!] Enter Instance name 'make start NAME' OR use 'make start all' to start all"  || ( test "${INSTANCE}" = "all"  && ( make start_all && make status ) || ( make ${INSTANCE}_start && make status ) )

start_all:
	@for dir in $(instances_enabled); do \
		str=_start; make $$dir$$str; \
	done

%_start: 
	@echo ""
	@echo "${b}[.] Running the bot in container for $*${n}"
	@test "$(shell docker container inspect -f '{{.State.Status}}' limit_swap_$*)" = "running" && echo "[!] Container $* is already running. Skipping..." || ( echo "Container is not running" && docker run -d --rm --name limit_swap_$* -v $(HOME)/instances/$*/settings.json:/app/settings.json -v $(HOME)/instances/$*/tokens.json:/app/tokens.json -v $(HOME)/logs:/app/logs limit_swap )
	@echo "${b}[+] Finished starting the bot in container for $*${n}"
	@echo ""

stop: hello
	@test -z ${INSTANCE} && echo "[!] Enter Instance name 'make stop NAME' OR use 'make stop all' to stop all" || ( test "${INSTANCE}" = "all" && make stop_all || make ${INSTANCE}_stop  )
	make status

stop_all: 
	@for dir in $(instances_enabled); do \
        str=_stop; make $$dir$$str; \
    done

%_stop: 
	@echo ""
	@echo "${b}[.] Stopping the bot in container $* ${n}"
	@test "$(shell docker container inspect -f '{{.State.Status}}' limit_swap_$* )" = "running" && docker stop limit_swap_$* || ( echo "[!] Container $* is not running. Skipping..." )
	@echo "${b}[+] The bot in container successfully stopped${n}"
	@echo ""

status:
	@echo ""
	@echo "${y}$(bd)Working instances:$(st)"
	@docker ps
	@echo ""

logs: hello
	@echo "${b}[.] Fetching the logs of a container for $(INSTANCE)${n}"
	@docker logs -f limit_swap_$(INSTANCE)

ssh: hello
	@echo "${b}[.] Entering shell to the container${n}"
	@docker exec -it limit_swap_$(INSTANCE) bash