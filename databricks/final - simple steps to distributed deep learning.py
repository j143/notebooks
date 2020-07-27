# Databricks notebook source
# MAGIC %md
# MAGIC ##### This notebook has the following requirements:
# MAGIC * Use a DBR 5.2 ML cluster.
# MAGIC * Install pyarrow v0.12 on the cluster. Pyarrow is available as a pypi package which can be installed using [workspace libraries](https://docs.databricks.com/user-guide/libraries.html#pypi-libraries).
# MAGIC * Use an init-script to mount persistent-storage to your cluster. See instructions for setting up the init script with [Azure Blob Store](https://docs.azuredatabricks.net/applications/deep-learning/distributed-deep-learning/ddl-storage.html#ddl-fuse) or [S3](https://docs.databricks.com/applications/deep-learning/distributed-deep-learning/ddl-storage.html#ddl-fuse).

# COMMAND ----------

from tensorflow import keras

def get_keras_dataset():
  (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()
  
  # Add channel dimension so it works with keras.layers.Conv2D
  x_train = x_train.reshape(-1, 28, 28, 1)
  x_test = x_test.reshape(-1, 28, 28, 1)
  
  return (x_train, y_train), (x_test, y_test)

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC <img src="https://www.tensorflow.org/images/MNIST.png">

# COMMAND ----------

import random

from scipy import ndimage

from pyspark.sql.types import IntegerType, StructField, StructType
from pyspark.ml.image import ImageSchema

uint8_one_channel = ImageSchema.ocvTypes['CV_8UC1']

def spark_image(numpy_image):
  height, width, num_chan = numpy_image.shape
  data = bytearray(numpy_image.tobytes())
  return ['', height, width, num_chan, uint8_one_channel, data]

enhancment_factor = 5

def add_rotation(example):
  """Make rotated images from the orginal example"""
  image, label = example
  for i in range(enhancment_factor):
    angle = random.randint(-45, 45)
    rotatedImage = ndimage.rotate(image, angle, reshape=False).astype('uint8')
    yield [spark_image(rotatedImage), label]

schema = (StructType()
  .add(StructField("image", ImageSchema.columnSchema))
  .add(StructField("label", IntegerType())))

(x_train, y_train), (x_test, y_test) = get_keras_dataset()
enhanced_data = (sc.parallelize(zip(x_train, y_train.tolist()), 8)
  .flatMap(add_rotation)
  .toDF(schema))
  
display(enhanced_data)

# COMMAND ----------

# MAGIC %md
# MAGIC We need to set up our working directory using the fuse mounted persistent storage. We'll use this directory to stage data, store checkpoints and to save anything else we don't want to lose.

# COMMAND ----------

import os
from time import time

working_dir = "/mnt/persistent-storage/simple-steps-to-distributed-deep-learning"
if not os.path.exists(working_dir):
  os.mkdir(working_dir)

current_time = int(time())
checkpoint_dir = f"{working_dir}/checkpoints-{current_time}"
data_dir = f"{working_dir}/tfrecords-{current_time}"
log_dir = f"{working_dir}/logs-{current_time}"

# COMMAND ----------

enhanced_data.select(enhanced_data.image["data"].alias("image_raw"), enhanced_data.label) \
  .write.format("tfrecords") \
  .option("recordType", "Example") \
  .mode("overwrite") \
  .save("file:"+data_dir)

# COMMAND ----------

import tensorflow as tf

def build_dataset(files, batch_size, steps_per_epoch):
  files = tf.data.Dataset.list_files(files)
  # Horovod: shard input data across workers
  dataset = tf.data.TFRecordDataset(files) \
    .shard(hvd.size(), hvd.rank()) \
    .repeat() \
    .shuffle(batch_size * steps_per_epoch) \
    .map(decode) \
    .map(normalize) \
    .prefetch(batch_size * 10) \
    .batch(batch_size)
  return dataset

def decode(serialized_example):
  features = tf.parse_single_example(serialized_example,
      features={
          'image_raw': tf.FixedLenFeature([], tf.string),
          'label': tf.FixedLenFeature([], tf.int64),
      })
  image = tf.decode_raw(features['image_raw'], tf.uint8)
  image.set_shape(28 * 28)
  image = tf.reshape(image, (28, 28, 1))
  label = tf.cast(features['label'], tf.int32)
  label = tf.one_hot(label, 10)
  return image, label

def normalize(image, label):
  image = tf.cast(image, tf.float32) / 255.
  return image, label

# COMMAND ----------

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D, MaxPooling2D

def get_model():
  model = Sequential()
  model.add(Conv2D(32, kernel_size=(3, 3),
                   activation='relu',
                   input_shape=(28, 28, 1)))
  model.add(Conv2D(64, (3, 3), activation='relu'))
  model.add(MaxPooling2D(pool_size=(2, 2)))
  model.add(Dropout(0.25))
  model.add(Flatten())
  model.add(Dense(128, activation='relu'))
  model.add(Dropout(0.5))
  model.add(Dense(10, activation='softmax'))
  return model

# COMMAND ----------

# Horovod: Import the relevant submodule
import horovod.tensorflow.keras as hvd

def train_hvd(learning_rate, epochs, batch_size, steps_per_epoch):
  
    tf.reset_default_graph()
    with tf.Session() as sess:

      # Horovod: initialize Horovod.
      hvd.init()
      
      dataset = build_dataset(data_dir + "/part-*", batch_size, steps_per_epoch)
      model = get_model()

      # Horovod: adjust learning rate based on number of GPUs.
      optimizer = keras.optimizers.Adadelta(lr=learning_rate * hvd.size())

      # Horovod: add Horovod Distributed Optimizer.
      optimizer = hvd.DistributedOptimizer(optimizer)

      model.compile(optimizer=optimizer,
                    loss='categorical_crossentropy',
                    metrics=['accuracy'])

      callbacks = [
          # Horovod: broadcast initial variable states from rank 0 to all other processes.
          # This is necessary to ensure consistent initialization of all workers when
          # training is started with random weights or restored from a checkpoint.
          hvd.callbacks.BroadcastGlobalVariablesCallback(0),
      ]

      # Horovod: save checkpoints only on worker 0 to prevent other workers from corrupting them.
      if hvd.rank() == 0:
          callbacks.append(keras.callbacks.ModelCheckpoint(checkpoint_dir + '/checkpoint-{epoch}', 
                                                           save_weights_only=True))
          callbacks.append(keras.callbacks.TensorBoard(log_dir))

      model.fit(dataset,
                callbacks=callbacks,
                epochs=epochs,
                verbose=2,
                steps_per_epoch=steps_per_epoch)


# COMMAND ----------

dbutils.tensorboard.start(log_dir)

# COMMAND ----------

from sparkdl import HorovodRunner

hr = HorovodRunner(np=0)
hr.run(train_hvd, learning_rate=1.0, epochs=5, batch_size=64, steps_per_epoch=200)

# COMMAND ----------

import numpy as np
import pandas as pd

from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.types import IntegerType

spark.conf.set("spark.sql.execution.arrow.enabled", "true")
spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "1000")

def predict(epoch):
  """Create udf to make predictions using model saved after `epoch`"""
  @pandas_udf(IntegerType(), PandasUDFType.SCALAR)
  def predict_for_epoch(pandas_series):
    image_batch = np.frombuffer(b"".join(pandas_series), 'uint8')
    image_batch = image_batch.reshape(-1, 28, 28, 1)

    model = get_model()
    keras.backend.set_learning_phase(0)
    model.load_weights(checkpoint_dir + "/checkpoint-%s" % epoch)
    
    predictions = model.predict_on_batch(image_batch)
    return pd.Series(predictions.argmax(1))
  
  return predict_for_epoch

# COMMAND ----------

testData = sc.parallelize(zip(x_test, y_test.tolist()), 8) \
  .flatMap(add_rotation).toDF(schema)

# COMMAND ----------

from pyspark.sql.functions import sum, when

test_cases = len(x_test) * enhancment_factor

predictions = testData \
  .withColumn("predicted_label_epoch_1", predict(epoch=1)(testData.image.data)) \
  .withColumn("predicted_label_epoch_5", predict(epoch=5)(testData.image.data)) \
  .cache()

accuracy = predictions.agg(
  (sum(when(predictions.predicted_label_epoch_1 == predictions.label, 1)) / test_cases).alias("epoch_1_accuracy"),
  (sum(when(predictions.predicted_label_epoch_5 == predictions.label, 1)) / test_cases).alias("epoch_5_accuracy"))
display(accuracy)

# COMMAND ----------

bad_predictions = predictions.filter(predictions.label != predictions.predicted_label_epoch_1)

display(bad_predictions)
