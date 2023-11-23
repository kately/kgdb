### Set-up the Dev Env

These are the technologies used in the solution.
* Graph Database: Neo4J
* Message Queue: Kafka/Zookeeper
* Computing Engine: PySpark

The env is set-up in docker containers. Each service runs in separate container and set-up to communicate through 'host' network.

<img width="500" alt="Screenshot 2023-11-23 at 5 10 32 AM" src="https://github.com/kately/kgdb/assets/9557623/7d9d30f1-9d93-4530-b261-849993779d04">

## Requirements
* Docker
* Makefile (this is use for running the docker build)

## Repo
```
git clone git@github.com:kately/kgdb.git
```
## Bringing up the containers
1) Run docker build for Kafka/Zookeeper, Neo4J, PySpark
   ```
   ./bin/build-all.sh
   docker images
   ```
2) Start-up Kafka/Zookeeper. Running this target will bring up both Zookeeper and Kafka.
   ```
   # Launch Kafka
   PARAM=kafka make kafka-up
   ```
3) Start-up graph database Neo4j
   ```
   # Launch graph database
   PARAM=neo4j make neo4j-db-up
   ```
Start-up 2 separate Python clients.
One will be used for managing Kafka updates while the other could be use to query the updates to Neo4J.
The docker image is build to run PySpark.

4) This client uses for kafka topics set-up and producing updates. 
   ```
   # Launch client for managing update to Kafka
   PARAM=python make run-pyclient

   # Create Kafka topics
   ./bin/kafka-topics.sh --create Y
   
   # Run message updates
   ./bin/kafka-producer.sh  
   ```
5) This client uses for querying Neo4J
   ```
   # Launch Cypher shell to query the KG/Neo4J.
   make neo4j-shell

   # Querying Neo4J - return the nodes
   MATCH(n) RETURN n;
   ```
