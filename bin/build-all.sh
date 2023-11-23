
# pull ubuntu_base_20.04 (focal) from dockerhub public cloud (free to use)
UBUNTU_VERSION=20.04 && \
docker pull ubuntu:${UBUNTU_VERSION} && \
docker tag ubuntu:${UBUNTU_VERSION} ubuntu:ubuntu_base_${UBUNTU_VERSION} && \
docker rmi ubuntu:${UBUNTU_VERSION}

# pre-build the images (zookeeper, kafka, pyspark, neo4j-db)
make build-all
