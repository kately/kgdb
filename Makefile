# Makefile

JAVA_VERSION = 11
SPARK_VERSION = 3.4.2
PYTHON_VERSION = 3.9
NEO4J_VERSION = 5.13.0
KAFKA_VERSION = 3.3
ZOOKEEPER_VERSION = 3.8

NEO4J_DATABASE_USER = $(shell echo $${NEO4J_DATABASE_USERNAME-neo4j})
NEO4J_DATABASE_PASS = $(shell echo $${NEO4J_DATABASE_PASSWORD-test@!123})

build-all: build-zookeeper build-kafka build-python build-neo4j-db

# ================
# Graph DB: Neo4j
# ================

.PHONY: build-neo4j-db
build-neo4j-db: clean-images
	IMAGE_TAG=neo4j-${NEO4J_VERSION} \
        docker-compose --file docker/docker-compose-neo4j.yml build \
                       --build-arg NEO4J_VERSION=${NEO4J_VERSION} \
                       --no-cache neo4j
.PHONY: neo4j-db-up
neo4j-db-up:
	@echo NEO4J_DATABASE_USERNAME=$(NEO4J_DATABASE_USER); \
	IMAGE_TAG=neo4j-${NEO4J_VERSION} \
        NEO4J_DATABASE_USERNAME=$(NEO4J_DATABASE_USER) \
        NEO4J_DATABASE_PASSWORD=$(NEO4J_DATABASE_PASS) \
        docker-compose --file docker/docker-compose-neo4j.yml up neo4j-db

.PHONY: neo4j-db-down 
neo4j-db-down:
	IMAGE_TAG=neo4j-${NEO4J_VERSION} \
	docker-compose --file docker/docker-compose-neo4j.yml down neo4j-db

.PHONY: neo4j-shell
neo4j-shell:
	NEO4J_DATABASE_USERNAME=$(NEO4J_DATABASE_USER) \
	NEO4J_DATABASE_PASSWORD=$(NEO4J_DATABASE_PASS) \
	docker exec -it Neo4j-db cypher-shell -u $(NEO4J_DATABASE_USER) -p $(NEO4J_DATABASE_PASS)

# ================
# Python Dev
# ================

.PHONY: build-python
build-python: clean-images
	IMAGE_TAG=python-bin-${PYTHON_VERSION} \
        docker-compose --file docker/docker-compose-python.yml build \
                       --build-arg PYTHON_VERSION=${PYTHON_VERSION} \
                       --build-arg JAVA_VERSION=${JAVA_VERSION} \
                       --build-arg SPARK_VERSION=${SPARK_VERSION} \
                       --no-cache python-bin

.PHONY: run-pyclient
run-pyclient:
	IMAGE_TAG=python-bin-${PYTHON_VERSION} \
        docker-compose --file docker/docker-compose-python.yml run \
                       --rm -it --entrypoint /bin/bash python-dev

# ================
# Msg Q: Kafka
# ================

.PHONY: build-zookeeper
build-zookeeper: clean-images
	ZK_IMAGE_TAG=kafka-zk-${ZOOKEEPER_VERSION} \
	KF_IMAGE_TAG=kafka-kf-${KAFKA_VERSION} \
        docker-compose --file docker/docker-compose-kafka.yml build \
                       --build-arg ZOOKEEPER_VERSION=${ZOOKEEPER_VERSION} \
                       --no-cache zookeeper-bin

.PHONY: build-kafka
build-kafka: clean-images
	ZK_IMAGE_TAG=kafka-zk-${ZOOKEEPER_VERSION} \
	KF_IMAGE_TAG=kafka-kf-${KAFKA_VERSION} \
        docker-compose --file docker/docker-compose-kafka.yml build \
                       --build-arg KAFKA_VERSION=${KAFKA_VERSION} \
                       --no-cache kafka-bin

.PHONY: kafka-up
kafka-up: build-zookeeper build-kafka
	ZK_IMAGE_TAG=kafka-zk-${ZOOKEEPER_VERSION} \
	KF_IMAGE_TAG=kafka-kf-${KAFKA_VERSION} \
        docker-compose --file docker/docker-compose-kafka.yml up kafka

.PHONY: kafka-down
kafka-down: build-zookeeper build-kafka
	ZK_IMAGE_TAG=kafka-zk-${ZOOKEEPER_VERSION} \
	KF_IMAGE_TAG=kafka-kf-${KAFKA_VERSION} \
        docker-compose --file docker/docker-compose-kafka.yml down kafka

# ================
# Helpers
# ================

.PHONY: clear-dangling-imgs
clear-dangling-imgs:
	IMG=$(shell docker images | grep none | awk '{print $$3}'); echo "$$IMG"; \
        [ -z "$$IMG" -a "$$IMG" != "IMAGE" ] || (docker image rmi $$IMG) && echo "Removed img '$$IMG'"

.PHONY: clean-images
clean-images: clear-dangling-imgs
	CID=$(shell docker ps -a | grep $(PARAM) | awk '{print $$1}'); \
        [ -z "$$CID" -a "$$CID" != "CONTAINER" ] || (docker stop $$CID) && echo "Stopped container '$$CID'"; \
        [ -z "$$CID" -a "$$CID" != "CONTAINER" ] || (docker rm $$CID) && echo "Removed container '$$CID'"
	IMG=$(shell docker images | grep $(PARAM) | awk '{print $$3}'); \
        [ -z "$$IMG" -a "$$IMG" != "IMAGE" ] || (docker image rmi $$IMG) && echo "Removed img '$$IMG'"

.PHONY: clean
clean: clean-images
	echo "Done"

# PARAM=value make clean
