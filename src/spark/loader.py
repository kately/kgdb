import os
import time
import logging
from common.utils import load_file
from pyspark.sql.functions import col, explode, regexp_replace, split
from pyspark.sql import SparkSession


class KafkaToNeo4jTransformer:
    def __init__(self, config: str):
        self.__config = load_file(config)
        self.__kf_cfg = self.__config.get("kafka")
        self.__db_cfg = self.__config.get("neo4j")

        # spark session
        self.spark = SparkSession \
            .builder \
            .master('local[*]') \
            .appName("Kafka-to-Neo4j-Loader") \
            .getOrCreate()
        logging.basicConfig(level=logging.INFO)

    def start_stream_query(self):
        kf_uri = f"{self.__kf_cfg.get('broker_host')}:{self.__kf_cfg.get('broker_port')}"  # noqa
        db_uri = f"bolt://{self.__db_cfg.get('host')}:{self.__db_cfg.get('port')}"   # noqa

        # reading messages from kafka
        kafka_df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kf_uri) \
            .option("subscribe", "companies,acq_companies,persons") \
            .option("startingOffsets", "earliest") \
            .load()

        # create a new DataFrame of the transformed DF to graph db
        # deserialized the message
        grdf = kafka_df.withColumn("value",
                explode(split(
                    regexp_replace
                    (regexp_replace(col("value"),
                        "(^\[)|(\]$)", ""), "\}, \{",  "\}\|\{"), "\|"))) \
            .select(col("value"))

        query = grdf.writeStream.format("org.neo4j.spark.DataSource") \
            .option("url", db_uri) \
            .option("save.mode", "ErrorIfExists") \
            .option("authentication.type", "basic") \
            .option("authentication.basic.username",
                    self.__db_cfg.get("user"))  \
            .option("authentication.basic.password",
                    self.__db_cfg.get("password")) \
            .option("checkpointLocation", "/tmp/checkpoint/myCheckPoint") \
            .option("labels", "Organization") \
            .option("node.keys", "value") \
            .start()

        query.awaitTermination()

        # TODO: fault-tolerance with checkpointLocation
        # For fault-tolerance, use option checkpointLocation
        #    for each output stream separately.

    def stop_stream_query(self, query, wait_time):
        """Stop a running streaming query"""
        while query.isActive:
            msg = query.status['message']
            data_avail = query.status['isDataAvailable']
            trigger_active = query.status['isTriggerActive']
            if not data_avail and not trigger_active \
                    and msg != "Initializing sources":
                logging.info('Stopping query...')
                query.stop()
            time.sleep(0.5)

            # Wait for the termination to happen
            logging.info('Awaiting termination...')
            query.awaitTermination(wait_time)

    def stop(self):
        # TODO: shutdown hook, monitoring stream progress
        self.spark.stop()


if __name__ == "__main__":
    cwd = os.getcwd()
    conf_path = f"{cwd}/conf"
    loader = KafkaToNeo4jTransformer(config=f"{conf_path}/test_config.json")
    loader.start_stream_query()
