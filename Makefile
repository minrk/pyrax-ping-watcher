NAME=pyrax-ping-watcher

all: build run

run:
	docker run --rm --restart=always --env-file env --name ${NAME} -t ${NAME}
testrun: build
	docker run --rm --env-file env -it ${NAME} --interval 60

build:
	docker build -t ${NAME} .