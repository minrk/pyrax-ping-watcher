NAME=pyrax-ping-watcher

all: build run

run:
	- docker rm -f ${NAME}
	docker run -d --restart=always --env-file env --name ${NAME} -t ${NAME}

test: build
	docker run --rm --env-file env -it ${NAME} --interval 60 --threads 1

build:
	docker build -t ${NAME} .