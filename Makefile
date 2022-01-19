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
	@echo "${y}$(bd)Commands:$(st)"
	@echo "    ${g}run${n}		Run the bot"
	@echo "    ${y}Usage:$(st)"
	@echo "    ${n}  make ${g}run${n} ${b}[settings]${n} ${b}[tokens]${n} ${b}[arguments]${n}"
	@echo "    ${b}    [settings] syntax${n}: ${g}${bd}make run s=bsc${n}${st} or ${g}${bd}make run settings=bsc${n}${st} means file ${bd}'settings-bsc.json'${st} will be used"
	@echo "    ${b}    [tokens] syntax${n}: ${g}${bd}make run t=moon${n}${st} or ${g}${bd}make run tokens=moon${n}${st} means file ${bd}'tokens-moon.json'${st} will be used"
	@echo "    ${b}    [arguments] syntax${n}: ${g}${bd}make run args='-v'${n}${st} means bot will be started in Verbose mode. All command line arguments of application supported"
	@echo "    ${g}benchmark${n}		Run benchmark mode"
	@echo "    ${g}clean${n}		Remove virtual environment, instances status and clear logs"
	@echo "    ${g}help${n}		Show this help output."
	@echo ""
	@echo "${y}$(bd)Instances configuration commands:$(st)"
	@echo "    ${g}init${n} ${b}[name]${n}		Initialization of configuration for the instance. Example:${g}${bd} make init test${n}${st}"
	@echo "    ${g}list${n}		List of instances configurations"
	@echo "    ${g}enable${n} ${b}[name]${n}	Enable instance configuration. Example:${g}${bd} make enable test${n}${st}"
	@echo "    ${g}disable${n} ${b}[name]${n}	Disable instance configuration. Example:${g}${bd} make enable test${n}${st}"

	@echo ""
	@echo "${y}$(bd)Docker commands:$(st)"
	@echo "    ${g}build${n} 		Build docker image. If image is not exist, it'll be built on 'make start'"
	@echo "    ${g}start${n} ${b}[name | all]${n}	Start docker container. Examples:${g}${bd} make start test${n}${st} or ${g}${bd} make start all${n}${st}"
	@echo "    ${g}stop${n}  ${b}[name | all]${n} 	Stop docker container. Examples:${g}${bd} make stop test${n}${st} or ${g}${bd} make stop all${n}${st}"
	@echo "    ${g}restart${n} ${b}[name | all]${n} 	Restart docker container. Examples:${g}${bd} make stop test${n}${st} or ${g}${bd} make stop all${n}${st}"
	@echo "    ${g}logs${n}  ${b}[name]${n}	Fetch the logs of the container. Example:${g}${bd} make logs test${n}${st}"
	@echo "    ${g}ssh${n}   ${b}[name]${n}	Run a shell in the  container. Example:${g}${bd} make ssh test${n}${st}"
	@echo "    ${g}status${n} 		Running docker instances status"
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
settings_str=$(shell ( test ${settings} || test ${s} ) &&  echo settings-${settings}${s}.json || echo settings.json)
tokens_str=$(shell ( test ${tokens} || test ${t} ) &&  echo tokens-${tokens}${t}.json || echo tokens.json)

prepare_args: prepare_args_str
	@test -f ${settings_str}  || (echo "${r}[!] Settings configuration file is not exist. Terminating...${n}" && exit 1)
	@test -f ${tokens_str}  || (echo "${r}[!] Tokens configuration file is not exist. Terminating...${n}" && exit 1)

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
	@echo "${g}[+] Virtual environment and logs cleaned successfully${n}"


#######################################################################################################################################
# Instances configuration																											  #
#######################################################################################################################################

init: hello
	@test -z ${INSTANCE} && ( echo "${r}[!] Please add instance name. Syntax: '${g}${bd}make init [name]'${n}${st}") || ( \
	echo "${b}[.] Creating instance ${g}${bd}'${INSTANCE}'${st}${n}"; test -d ${HOME}/instances/${INSTANCE} || mkdir -p ${HOME}/instances/${INSTANCE}/logs ;\
	( test -d ${HOME}/instances/${INSTANCE} && test ! -f ${HOME}/instances/${INSTANCE}/settings.json ) && \
	( cp ${HOME}/settings.json ${HOME}/instances/${INSTANCE}/settings.json && cp ${HOME}/tokens.json ${HOME}/instances/${INSTANCE}/tokens.json && \
	echo "${b}[.] Configuration files located in ${bd}${HOME}/instances/${INSTANCE}${st}${n}" && \
	echo "${b}[.] To enable instance use command: ${g}${bd}make enable ${INSTANCE}${n}" && \
	echo "${g}[+] Instance ${g}${bd}'${INSTANCE}'${st}${g} successfully initialized!${n}" ) || \
	echo "${r}[!] Instance ${g}${bd}'${INSTANCE}'${st}${r} already initialized!${n}"	)

list: hello print_state
 
enable: hello check_enabled 
	@echo ""
	@test -d ${HOME}/env/enabled || mkdir -p ${HOME}/env/enabled
	@test ! -f $(HOME)/env/enabled/${INSTANCE} && ( echo "${b}[.] Enabling ${bd}${INSTANCE}${st}${n}" && touch $(HOME)/env/enabled/$(INSTANCE) ) || echo "${r}[!] ${bd}${INSTANCE}${st} ${r}instance already enabled${n}"
	@make print_state

disable: hello check_enabled 
	@echo ""
	@test -f $(HOME)/env/enabled/${INSTANCE} && ( echo "${b}[.] Disabling ${bd}${INSTANCE}${st}${n}" && unlink $(HOME)/env/enabled/$(INSTANCE) ) || echo "${r}[!] ${bd}${INSTANCE}${st} ${r}instance already disabled${n}"
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
	@test ! -z "$(shell docker images -q limit_swap 2> /dev/null)"  && \
	echo "${b}[+] Image ${g}${bd}limit_swap${st} ${b}exists${n}" || ( \
	echo "${b}[.] Building docker image${n}" && docker build -t limit_swap . && \
	echo "${b}[+] Docker image successfully built${n}")

prune: hello
	@echo "${b}[.] Check if docker image exists${n}"
	@test -z "$(shell docker images -q limit_swap 2> /dev/null)"  && \
	echo "${b}[+] Image ${bd}limit_swap${st} ${b}does not exist${n}" || ( \
	docker rmi limit_swap  && echo "${b}[+] Docker image successfully deleted${n}")

start: hello build
	@test -z ${INSTANCE} && echo "${r}[!] Enter Instance name ${g}${bd}make start [name]${st} ${r}OR use ${g}${bd}make start all${st}${r} to start all${n}"  || ( \
	test "${INSTANCE}" = "all"  && ( \
	make start_all && make status ) || ( \
	make ${INSTANCE}_start && make status ) )

start_all:
	@for dir in $(instances_enabled); do \
		str=_start; make $$dir$$str; \
	done

%_start: 
	@echo ""
	@echo "${b}[.] Running the instance ${bd}$*${st} ${n}"
	@test "$(shell docker container inspect -f '{{.State.Status}}' limit_swap_$*)" = "running" && \
	echo "${r}[!] Container ${g}${bd}$*${st}${r} is already running. Skipping...${n}" || ( \
	docker run -d --rm --name limit_swap_$* -v $(HOME)/instances/$*/settings.json:/app/settings.json -v $(HOME)/instances/$*/tokens.json:/app/tokens.json -v $(HOME)/instances/$*/logs/:/app/logs/ limit_swap )
	@echo "${g}[+] Finished starting the bot in container for $*${n}"
	@echo ""


stop: hello
	@test -z ${INSTANCE} && echo "${b}[!] Input Instance name ${g}${bd}make stop [name]${st}${n} OR use ${g}${bd}make stop all${st}${n} to stop all${n}" || ( \
	test "${INSTANCE}" = "all" && make stop_all || make ${INSTANCE}_stop  )
	@make status

stop_all: 
	@for dir in $(instances_enabled); do \
        str=_stop; make $$dir$$str; \
    done

%_stop: 
	@echo ""
	@echo "${b}[.] Stopping the instance ${bd}$*${st} ${n}"
	@test "$(shell docker container inspect -f '{{.State.Status}}' limit_swap_$* )" = "running" && docker stop limit_swap_$* || ( echo "[!] Container $* is not running. Skipping..." )
	@echo "${b}[+] The instance ${bd}$*${st}${b} successfully stopped${n}"
	@echo ""


restart: stop start

status:
	@echo ""
	@echo "${y}$(bd)Running docker instances:$(st)"
	@docker ps --no-trunc
	@echo ""

logs: hello
	@echo "${b}[.] Fetching the logs of a container for $(INSTANCE)${n}"
	@docker logs -f limit_swap_$(INSTANCE)

ssh: hello
	@echo "${b}[.] Entering shell to the container${n}"
	@docker exec -it limit_swap_$(INSTANCE) bash