### Set-up the Dev Env

These are the technologies used in the solution.
* Graph Database: Neo4J
* Message Queue: Kafka/Zookeeper
* Computing Engine: PySpark

The dev env is set-up for docker containerization. Each service runs in separate container and set-up to communicate through 'host' network.

| Design HL | Process |
| ------- | ------- |
| <img width="500" alt="Screenshot 2023-11-24 at 5 33 44 AM" src="https://github.com/kately/kgdb/assets/9557623/5b988c0a-7ac5-482d-bc24-eeeb6f9801b0"> | <img width="500" alt="Screenshot 2023-11-24 at 9 20 37 AM" src="https://github.com/kately/kgdb/assets/9557623/57b46ae8-c5e9-4044-93fd-2f32084efb1e"> |

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
   # Launch Kafka server
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

4) This client uses for kafka topics set-up and producing updates, Spark load and graph db/Neo4j initialize and seed sample data. 
   ```
   # Launch client for managing update to Kafka, Spark load, graph db update
   PARAM=python make run-pyclient

   # Build and seed db with sample data
   ./bin/neo4j-build-graph.sh

   # Create Kafka topics
   ./bin/kafka-topics.sh --create Y
   
   # Generate and run message updates
   ./bin/kafka-producer.sh

   # Run spark load
   ./bin/pyspark-loader.sh 
   ```
5) This client uses for querying Neo4J.
   Use this link to Neo4J interactive browser. `http://localhost:7474/browser/`
   ```
   # Launch Cypher shell to query the KG/Neo4J.
   make neo4j-shell

   # Querying Neo4J - return the nodes
   MATCH(n) RETURN n;
   ```
