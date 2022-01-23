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
	@echo "${g}${bd}LimitSwap command line interface${n}${st}"
	@echo ""

help: hello
	@echo ""
	@echo "${y}$(bd)Instances configuration commands:$(st)"
	@echo "    ${g}init${n} ${b}[name]${n}		Initialization of configuration for the instance. Example:${g}${bd} make init test${n}${st}"
	@echo "    ${g}list${n}		List of instances configurations"
	@echo "    ${g}edit${n} ${b}[name]${n}		Edit instance tokens.json. Example:${g}${bd} make edit test${n}${st}"
	@echo "    ${g}setup${n} ${b}[name]${n}	Edit instance settings.json. Example:${g}${bd} make setup test${n}${st}"
	@echo "    ${g}enable${n} ${b}[name]${n}	Enable instance configuration. Example:${g}${bd} make enable test${n}${st}"
	@echo "    ${g}disable${n} ${b}[name]${n}	Disable instance configuration. Example:${g}${bd} make disable test${n}${st}"
	@echo "    ${g}update${n} ${b}[version]${n}	Update with 'git' to current or specific version. "
	@echo "			Example:${g}${bd} make update${n}${st} or ${g}${bd} make update 4.2.1.2${n}${st}"


	@echo ""
	@echo "${y}$(bd)Local environment commands:$(st)"
	@echo "    ${g}run${n}	${b}[name]${n}		Run the bot from local. "
	@echo "			Examples:${g}${bd} make run test${n}${st} - run bot with 'test' configuration or ${g}${bd}make run${n}${st} - run bot with default configuration"
	@echo "    ${b}    [arguments]${n} 	${g}${bd}make run args='-v'${n}${st} means bot will be started in Verbose mode. "
	@echo " 			All command line arguments of application supported. Use command ${g}${bd}make args${n}${st} to view all of them."
	@echo "    ${g}benchmark${n}		Run benchmark mode"
	@echo "    ${g}clean${n}		Remove virtual environment, instances status and clear logs"
	@echo "    ${g}help${n}		Show this help output."

	@echo ""
	@echo "${y}$(bd)Docker environment commands:$(st)"
	@echo "    ${g}build${n} 		Build docker image. If image is not exist, it'll be built on 'make start'"
	@echo "    ${g}start${n} ${b}[name | all]${n}	Start docker container. Examples:${g}${bd} make start test${n}${st} or ${g}${bd} make start all${n}${st}"
	@echo "    ${g}stop${n}  ${b}[name | all]${n} 	Stop docker container. Examples:${g}${bd} make stop test${n}${st} or ${g}${bd} make stop all${n}${st}"
	@echo "    ${g}restart${n} ${b}[name | all]${n} 	Restart docker container. Examples:${g}${bd} make stop test${n}${st} or ${g}${bd} make stop all${n}${st}"
	@echo "    ${g}logs${n}  ${b}[name]${n}	Fetch the logs of the container. Example:${g}${bd} make logs test${n}${st}"
	@echo "    ${g}ssh${n}   ${b}[name]${n}	Run a shell in the  container. Example:${g}${bd} make ssh test${n}${st}"
	@echo "    ${g}status${n} 		Running docker instances status"
	@echo "    ${g}prune${n} 		Remove docker image"


#######################################################################################################################################
# Instances configuration																											  #
#######################################################################################################################################

init: hello
	@test -z ${INSTANCE} && ( echo "${r}[!] Please add instance name. Syntax: '${g}${bd}make init [name]'${n}${st}") || ( \
	echo "${b}[.] Creating instance ${g}${bd}'${INSTANCE}'${st}${n}"; test -d ${HOME}/instances/${INSTANCE} || mkdir -p ${HOME}/instances/${INSTANCE}/logs ;\
	( test -d ${HOME}/instances/${INSTANCE} && test ! -f ${HOME}/instances/${INSTANCE}/settings.json ) && \
	( cp ${HOME}/settings.json ${HOME}/instances/${INSTANCE}/settings.json && cp ${HOME}/tokens.json ${HOME}/instances/${INSTANCE}/tokens.json && \
	echo "${b}[.] Configuration files located in ${bd}${HOME}/instances/${INSTANCE}${st}${n}" && \
	echo "${b}[.] To enable instance use command: ${g}${bd}make enable ${INSTANCE}${st}${n}" && \
	echo "${b}[.] To list all instances use command: ${g}${bd}make list${st}${n}" && \
	echo "${g}[+] Instance ${g}${bd}'${INSTANCE}'${st}${g} successfully initialized!${n}" ) || \
	echo "${r}[!] Instance ${g}${bd}'${INSTANCE}'${st}${r} already initialized!${n}"	)

list: hello print_state

edit: hello
	@test -z ${INSTANCE} && ( echo "${r}[!] Please add instance name. Syntax: '${g}${bd}make edit [name]'${n}${st}") || \
	(nano ${HOME}/instances/${INSTANCE}/tokens.json)

setup: hello
	@test -z ${INSTANCE} && ( echo "${r}[!] Please add instance name. Syntax: '${g}${bd}make setup [name]'${n}${st}") || \
	(nano ${HOME}/instances/${INSTANCE}/settings.json)

enable: hello 
	@test -d ${HOME}/env/enabled || mkdir -p ${HOME}/env/enabled
	@test ! -f $(HOME)/env/enabled/${INSTANCE} && ( \
	echo "${b}[.] Enabling ${bd}${INSTANCE}${st}${n}" && touch $(HOME)/env/enabled/$(INSTANCE) ) || ( \
	echo "${r}[!] ${bd}${INSTANCE}${st} ${r}instance already enabled${n}" )
	@make print_state  --no-print-directory 2> /dev/null

disable: hello
	@test -f $(HOME)/env/enabled/${INSTANCE} && ( \
	echo "${b}[.] Disabling ${bd}${INSTANCE}${st}${n}" && unlink $(HOME)/env/enabled/$(INSTANCE) ) || \
	echo "${r}[!] ${bd}${INSTANCE}${st} ${r}instance already disabled${n}"
	@make print_state  --no-print-directory 2> /dev/null

update: hello
	@test -d ${HOME}/.git1 && (test -z ${INSTANCE} && git pull || ( git fetch --all --tags && git checkout tags/v${INSTANCE} -b master) ) || \
	( echo "${r}[!] You are not using version control system (git). We recommend to use git. LimitSwap.py will be updated and backed up.${n}" && \
	while [ -z "$$CONTINUE" ]; do \
		read -r -p "Are you sure you wish to continue? [y/N] " CONTINUE; \
	done ; \
	( test $$CONTINUE = "y" || test $$CONTINUE = "Y" ) && \
	( mv LimitSwap.py LimitSwap.py.backup && wget https://raw.githubusercontent.com/tsarbuig/LimitSwap/master/LimitSwap.py -O LimitSwap.py && wget https://raw.githubusercontent.com/tsarbuig/LimitSwap/master/requirements.txt -O requirements.txt ) || \
	echo "${r}[!] Terminating...${n}" && exit 1 )

check: check_exists check_enabled

check_enabled:
	@(test -f ${HOME}/env/enabled/${INSTANCE}) || ( \
	echo "${g}To enable instance please use command: ${bd}make enable ${INSTANCE}${st}${n}" && \
	make print_state  --no-print-directory 2> /dev/null && \
	echo "${r}[!] Instance is not enabled. Terminating...${n}" && exit 1 )

check_exists:
	@(test -d ${HOME}/instances/${INSTANCE} && test -f ${HOME}/instances/${INSTANCE}/settings.json ) || ( echo "${r}[!] Instance configuration is not exist. Terminating...${n}" && exit 0 )

check_instances:
	@(test -d ${HOME}/instances || echo "${r}[!] Instances configuration directory is not exist. Terminating...${n}" && exit 1 )

get_instances: 
instances_available = $(shell ls $(HOME)/instances)
instances_enabled = $(shell ls $(HOME)/env/enabled)

print_state: get_instances
	@echo "${y}$(bd)Availabled instances:$(st)"
	@for dir in $(instances_available); do \
        echo $$dir; \
    done

	@echo "${y}$(bd)Enabled instances:$(st)"
	@for dir in $(instances_enabled); do \
        echo $$dir; \
    done


#######################################################################################################################################
# Local environment																													  #
#######################################################################################################################################

install_dependencies: 
	@test $(shell uname -s) = "Darwin" && \
	make install_dependencies_mac  --no-print-directory 2> /dev/null || \
	make install_dependencies_linux  --no-print-directory 2> /dev/null

install_dependencies_linux:
	@test -d $(VENV_NAME) || echo "${b}[.] Installing dependencies${n}"; sudo apt-get update -qq >/dev/null && sudo apt-get install python3-dev build-essential python3-pip python3-venv virtualenv nano -y -qq >/dev/null

install_dependencies_mac:
	@test -d $(VENV_NAME) || echo "${b}[.] Installing dependencies${n}"; sudo pip3 install virtualenv

prepare_venv: install_dependencies $(VENV_NAME)/bin/activate
	@echo "${g}[+] Virtual environment is ready${n}"

$(VENV_NAME)/bin/activate: requirements.txt
	@echo "${b}[.] Preparing virtual environment${n}"
	test -d ${VENV_NAME} || virtualenv -p python3 ${VENV_NAME}
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -r requirements.txt
	touch $(VENV_NAME)/bin/activate	

prepare_args_str: 
settings=$(shell ( test ${INSTANCE} && echo "$(HOME)/instances/${INSTANCE}/settings.json " || echo "settings.json"))
tokens=$(shell ( test ${INSTANCE} && echo "$(HOME)/instances/${INSTANCE}/tokens.json" || echo "tokens.json "))

prepare_args: prepare_args_str
	@test -f ${settings} || (echo "${r}[!] Settings configuration file is not exist. Terminating...${n}" && exit 1)
	@test -f ${settings} || (echo "${r}[!] Tokens configuration file is not exist. Terminating...${n}" && exit 1)

run: hello prepare_venv check prepare_args 
	@echo "${b}[.] Running bot for instance: ${bd}${INSTANCE}${st}${n}"
	@${PYTHON} LimitSwap.py -s $(settings) -t $(tokens) ${args}

args: hello prepare_venv
	@echo "${b}[.] Available arguments${n}"
	@echo "Instance: ${INSTANCE}"
	@${PYTHON} LimitSwap.py -h

benchmark: prepare_venv
	@echo "${b}[.] Running benchmark${n}"
	${PYTHON} LimitSwap.py --benchmark

clean:
	@echo "${b}[.] Cleaning virtual environment and logs${n}"
	@rm -rf env
	@rm -rf logs/*.log
	@echo "${g}[+] Virtual environment and logs cleaned successfully${n}"


#######################################################################################################################################
# Instances docker operations																										  #
#######################################################################################################################################

build: hello
	@echo "${b}[.] Check if docker image exists${n}"
	@test ! -z "$(shell docker images -q limit_swap 2> /dev/null)"  && \
	echo "${b}[+] Image ${g}${bd}limit_swap${st} ${b}exists${n}" || ( \
	echo "${b}[.] Building docker image${n}" && docker build -t limit_swap . && \
	echo "${b}[+] Docker image successfully built${n}")

prune: hello
	@echo "${b}[.] Check if docker image exists${n}"
	@test -z "$(shell docker images -q limit_swap 2> /dev/null)"  && \
	echo "${b}[+] Image ${bd}limit_swap${st} ${b}does not exist${n}" || ( \
	docker rmi limit_swap && echo "${b}[+] Docker image successfully deleted${n}")

start: hello build
	@test -z ${INSTANCE} && ( make print_state  --no-print-directory 2> /dev/null && \
	echo "${r}[!] Enter Instance name ${g}${bd}make start [name]${st} ${r}OR use ${g}${bd}make start all${st}${r} to start all${n}" )  || ( \
	test "${INSTANCE}" = "all"  && ( \
	make start_all --no-print-directory 2> /dev/null && make status --no-print-directory 2> /dev/null ) || ( \
	make ${INSTANCE}_start --no-print-directory 2> /dev/null && make status --no-print-directory 2> /dev/null ) )

start_all:
	@for dir in $(instances_enabled); do \
		str=_start; make $$dir$$str  --no-print-directory 2> /dev/null; \
	done

%_start: 
	@echo ""
	@echo "${b}[.] Running the instance ${bd}$*${st} ${n}"
	@test "$(shell docker container inspect -f '{{.State.Status}}' limit_swap_$*)" = "running" && \
	echo "${r}[!] Container ${g}${bd}$*${st}${r} is already running. Skipping...${n}" || ( \
	docker run -d --rm --name limit_swap_$* \
	-v $(HOME)/instances/$*/settings.json:/app/settings.json -v $(HOME)/instances/$*/tokens.json:/app/tokens.json \
	-v $(HOME)/LimitSwap.py:/app/LimitSwap.py -v $(HOME)/instances/$*/logs/:/app/logs/ \
	--entrypoint '/bin/bash' limit_swap -c 'python LimitSwap.py ${args}')

	@echo "${g}[+] Finished starting the bot in container for $*${n}"
	@echo ""


stop: hello
	@test -z ${INSTANCE} && echo "${b}[!] Input Instance name ${g}${bd}make stop [name]${st}${n} OR use ${g}${bd}make stop all${st}${n} to stop all${n}" || ( \
	test "${INSTANCE}" = "all" && make stop_all --no-print-directory 2> /dev/null || make ${INSTANCE}_stop --no-print-directory 2> /dev/null ) 
	@make status --no-print-directory 2> /dev/null

stop_all: 
	@for dir in $(instances_enabled); do \
        str=_stop; make $$dir$$str --no-print-directory 2> /dev/null; \
    done

%_stop: 
	@echo "${b}[.] Stopping the instance ${bd}$*${st} ${n}"
	@test "$(shell docker container inspect -f '{{.State.Status}}' limit_swap_$* )" = "running" && docker stop limit_swap_$* || ( echo "[!] Container $* is not running. Skipping..." )
	@echo "${b}[+] The instance ${bd}$*${st}${b} successfully stopped${n}"
	@echo ""


restart: stop start

status:
	@echo "${y}$(bd)Running docker instances:$(st)"
	@docker ps --format="table {{.Names}}\t{{.State}}\t{{.Status}}\t{{.Command}}" --no-trunc
	@echo ""

logs: hello
	@echo "${b}[.] Fetching the logs of a container for $(INSTANCE)${n}"
	@docker logs -f limit_swap_$(INSTANCE)

ssh: hello
	@echo "${b}[.] Entering shell to the container${n}"
	@docker exec -it limit_swap_$(INSTANCE) bash