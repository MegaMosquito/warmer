
all: build run

build:
	docker build -t warmer .

# Maybe use this instead of `--privileged`:  `--device /dev/gpiomem`
dev: build
	-docker rm -f warmer 2> /dev/null || :
	docker run -it --privileged --name warmer --publish=80:5000 --volume `pwd`:/outside warmer /bin/sh

run:
	-docker rm -f warmer 2> /dev/null || :
	docker run -d --privileged --name warmer --publish=80:5000 --volume `pwd`:/outside warmer

exec:
	docker exec -it warmer /bin/sh

stop:
	-docker rm -f warmer 2> /dev/null || :

clean: stop
	-docker rmi warmer 2> /dev/null || :

tar:
	cd ..; rm -f ./warmer.tar; tar -cvf ./warmer.tar Warmer

.PHONY: all build dev run exec stop clean tar
