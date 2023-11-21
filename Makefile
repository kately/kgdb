# Makefile

JAVA_VERSION = 11
SPARK_VERSION = 3.4.1
PYTHON_VERSION = 3.9
NEO4J_VERSION = 5.13.0

.PHONY: clear-dangling-imgs
clear-dangling-imgs:
        IMG=$(shell docker images | grep none | awk '{print $$3}'); echo "$$IMG"; \
        [ -z "$$IMG" ] || (docker image rmi $$IMG)

.PHONY: unset-neo4j-db
unset-neo4j-db: clear-dangling-imgs
	CID=$(shell docker ps -a | grep neo4j | awk '{print $$1}'); echo $$CID; \
	[ -z "$$CID" ] || (docker stop $$CID && docker rm $$CID)
	IMG=$(shell docker images | grep neo4j | awk '{print $$3}'); echo "$$IMG"; \
	[ -z "$$IMG" ] || (docker image rmi $$IMG)

.PHONY: set-neo4j-db
set-neo4j-db: unset-neo4j-db
	IMAGE_TAG=neo4j-${NEO4J_VERSION} \
	docker-compose --file docker/docker-compose-neo4j.yml build \
                       --build-arg NEO4J_VERSION=${NEO4J_VERSION} \
                       --no-cache neo4j
.PHONY: neo4j-db-up
neo4j-db-up: set-neo4j-db
	IMAGE_TAG=neo4j-${NEO4J_VERSION} \
	docker-compose --file docker/docker-compose-neo4j.yml up neo4j-db

.PHONY: neo4j-db-down 
neo4j-db-down:
	IMAGE_TAG=neo4j-${NEO4J_VERSION} \
	docker-compose --file docker/docker-compose-neo4j.yml down neo4j-db

.PHONY: neo4j-shell
neo4j-shell:
	docker exec -it Neo4j-db cypher-shell -u neo4j -p N3xt@sti987

.PHONY: run-pyclient
run-pyclient:
	IMAGE_TAG=neo4j-${NEO4J_VERSION} \
	CLIENT_IMAGE_TAG=python-bin-${PYTHON_VERSION} \
        docker-compose --file docker/docker-compose-neo4j.yml run \
                       --rm -it --entrypoint /bin/bash python-dev-client

.PHONY: clean
clean:
	echo "Done"
