import os
import json
import time
import logging
import pyspark.sql.types as T
import pyspark.sql.functions as F
from typing import Dict, List
from common.utils import load_file
from pyspark.sql import SparkSession


def decode_json_column(value: str) -> List:
    try:
        value = json.loads(value, strict=False)
        # print(f"=====> decode_column(value) 1: {value}")
        list_of_dict = value
        # print(f"=====> list_of_dict 2: {json.dumps(list_of_dict)}")
        value_as_dict = [json.dumps(x) for x in list_of_dict]
        return ("\|").join(value_as_dict)     # noqa
    except Exception as e:
        logging.error("ERROR:", e)
        return None


# TODO: register UDF
decode_json_column_udf = F.udf(decode_json_column)
decode_record_schema_udf = (lambda x, schema: F.from_json(x, schema))
expand_json_to_array_udf = (lambda x: F.split(decode_json_column_udf(x), "\|"))   # noqa
expand_jsonarray_to_rows_udf = (lambda x: F.explode(expand_json_to_array_udf(x))) # noqa
flatten_jsondict_to_columns_udf = (lambda x, schema:
        F.explode(F.array(decode_record_schema_udf(x, schema))))   # noqa

# create a new DataFrame of the transformed DF to graph db
# deserialized the message
org_schema = T.StructType([
    T.StructField("company_id", T.LongType(), True),
    T.StructField("company_name", T.StringType(), True),
    T.StructField("headcount", T.LongType(), True),
])
# T.StructField("timestamp", T.TimestampType(), True), \


class KafkaToNeo4jTransformer:
    def __init__(self, config: str, topic_to_node_map: Dict):
        self.__config = load_file(config)
        self.__kf_cfg = self.__config.get("kafka")
        self.__db_cfg = self.__config.get("neo4j")
        self.__topic_to_node_map = topic_to_node_map

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
            .option("subscribe", ",".join(list(self.__topic_to_node_map.keys()))) \
            .option("startingOffsets", "earliest") \
            .load()

        # Extract encoded 'value' column of a batch of json string
        # A batch could consist of one or more json kafka records.
        # Decode batch and explode the batch of multiple records into rows.
        rows = expand_jsonarray_to_rows_udf(F.col("value"))
        grdf = kafka_df.select(rows.alias("cols")) \
                       .select(F.col("cols"),
                               flatten_jsondict_to_columns_udf(
                                   F.col("cols"), org_schema).alias("attrs")) \
                       .select(F.col("attrs"))

        for field in grdf.schema.fields:
            if field.name.startswith("attrs"):
                grdf = grdf.withColumnRenamed(
                        field.name, field.name.replace("attrs.", ""))
        grdf.printSchema()

        # TODO: identify the label to use for the given batch
        # for now:
        #     assume each micro-batch consists of records from the same topic.
        topic_name = "companies"

        # Write extracted streamed micro batch to the graph db.
        query = grdf.writeStream.format("org.neo4j.spark.DataSource") \
            .option("url", db_uri) \
            .option("save.mode", "Overwrite") \
            .option("authentication.type", "basic") \
            .option("authentication.basic.username",
                    self.__db_cfg.get("user"))  \
            .option("authentication.basic.password",
                    self.__db_cfg.get("password")) \
            .option("checkpointLocation", "/tmp/checkpoint/myCheckPoint") \
            .option("labels", self.get_node_label(topic_name)) \
            .option("node.keys", "attrs.company_id") \
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

    def get_node_label(self, topic_name: str) -> str:
        assert topic_name is not None, "get_node_label: topic_name is empty or None"
        if topic_name not in self.__topic_to_node_map.keys():
            raise Exception(
                    f"Cannot find node_label for the given topic_name '{topic_name}'")
        return self.__topic_to_node_map.get(topic_name)


if __name__ == "__main__":
    cwd = os.getcwd()
    conf_path = f"{cwd}/conf"

    # topic to node mapping
    topic_to_node_map = {
              "companies": "Organization",
              "acq_companies": "Subsidiary",
              "persons": "Person"
            }

    # read from kafka, transform and load into graph db
    loader = KafkaToNeo4jTransformer(
            config=f"{conf_path}/test_config.json",
            topic_to_node_map=topic_to_node_map)
    loader.start_stream_query()
