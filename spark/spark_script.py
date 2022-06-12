'''
Aggiungo la colonna di prediction e invio a elasticsearch sull'indice "spotify-spark-output"
'''
import os
from numpy import true_divide
from pyspark.sql import SparkSession
from pyspark import SparkConf, SparkContext
import pyspark.sql.types as tp
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.functions import from_json
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql.functions import *
from elasticsearch import Elasticsearch


sparkConf = SparkConf().set("es.nodes", "elasticsearch").set("es.port", "9200")
sc = SparkContext(appName="spotify_app", conf=sparkConf)
spark = SparkSession(sc)
sc.setLogLevel("ERROR")

# Costruisco il primo training set
train1 = spark.read.csv("/opt/tap/top_songs.csv", header=True, inferSchema=True)
train1 = train1.drop("name", "track_id").withColumn("mainstreamness", lit(1)) #Imposto il valore a 1 (massimo)

# Costruisco il secondo training set
train_inverse = train1.select(*[(1-train1[c]).alias(c) for c in train1.columns])
train_inverse = train_inverse.withColumn("mainstreamness", lit(0)) #Imposto il valore a 0 (minimo)

# Unisco i due train sets
train = train1.union(train_inverse)

# Costruisco la pipeline
stage1 = VectorAssembler(inputCols=["acousticness", "danceability", "instrumentalness", "liveness", "speechiness", "valence", "energy"], outputCol="features").setHandleInvalid("keep")
stage2 = LinearRegression(featuresCol="features", labelCol="mainstreamness", maxIter=10, regParam=0.001)
pipeline = Pipeline(stages=[stage1, stage2])

# Modello pronto
model = pipeline.fit(train)
# Per vedere l'attendibilità (non con LinearRegression)
# print("Model accuracy: ")
# print(model.stages[-1].summary.accuracy)


# prendo i dati da kafka come structured streaming
df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafkaserver:9092")
    .option("subscribe", "topic_1")
    .load()
)


# I campi dei dati json che arrivano da logstash
structure = tp.StructType([
    # tp.StructField(name= 'id', dataType=tp.StringType(), nullable=True),
    tp.StructField(name= 'playlist', dataType= tp.StringType(),  nullable= True),
    tp.StructField(name= 'name', dataType= tp.StringType(),  nullable= True),
    tp.StructField(name= '@timestamp', dataType= tp.StringType(),  nullable= True),
    tp.StructField(name= 'acousticness', dataType= tp.FloatType(),  nullable= True),
    tp.StructField(name= 'danceability', dataType= tp.FloatType(),  nullable= True),
    tp.StructField(name= 'instrumentalness', dataType= tp.FloatType(),  nullable= True),
    tp.StructField(name= 'liveness', dataType= tp.FloatType(),  nullable= True),
    tp.StructField(name= 'speechiness', dataType= tp.FloatType(),  nullable= True),
    tp.StructField(name= 'valence', dataType= tp.FloatType(),  nullable= True),
    tp.StructField(name= 'energy', dataType= tp.FloatType(),  nullable= True),
])
    
# Se faccio modifiche ai mapping devo cancellare l'indice (possibile farlo anche da kibana)
es_mapping = {
    "properties": {
        "playlist": {"type": "keyword"},
        "name": {"type": "keyword"},
        "@timestamp": {"type": "date"},
        "acousticness": {"type": "double"},
        "danceability": {"type": "double"},
        "instrumentalness": {"type": "double"},
        "liveness": {"type": "double"},
        "speechiness": {"type": "double"},
        "valence": {"type": "double"},
        "energy": {"type": "double"},
        "prediction": {"type": "double"}
    }
}

es_index = "spotify-spark-output"
es = Elasticsearch("http://elasticsearch:9200", request_timeout=60, retry_on_timeout=True, max_retries=10).options(ignore_status=400)
if not es.ping():
    print("Elasticsearch not available")
    exit(-1)
resp = es.indices.create(
    index=es_index, 
    mappings=es_mapping,
)


if 'acknowledged' in resp:
    if resp['acknowledged'] == True:
        print("Successfully created index:", resp['index'])


print("READy")

# Fa un cast dei dati in input come stringa (altrimenti sono esadecimali), formatta i campi json in base alla struttura data (structure), dà un nome (alias) alla colonna (altrimenti la colonna si chiama "from_json(..)"), e trasforma i campi e valori dentro l'unica colonna "value" in colonne multiple (select("value.*"))
df = (
    df.selectExpr("CAST(value AS STRING)")
    .select(from_json("value", structure).alias("value")).select("value.*")
)

df = model.transform(df).drop("features")

(
    df
    .writeStream
    .option("checkpointLocation", "/temp/tmp/checkpoints")
    .format("es")
    .start(es_index)
    .awaitTermination()
)
