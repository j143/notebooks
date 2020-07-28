# Databricks notebook source
# MAGIC %md # Ensuring Consistency with ACID Transactions with Delta Lake (Loan Risk Data)
# MAGIC 
# MAGIC <img src="https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-logo-whitebackground.png" width=200/>
# MAGIC 
# MAGIC This is a companion notebook to provide a Delta Lake example against the Lending Club data.
# MAGIC * This notebook has been tested with *DBR 5.4 ML Beta, Python 3*

# COMMAND ----------

# MAGIC %md ## The Data
# MAGIC 
# MAGIC The data used is public data from Lending Club. It includes all funded loans from 2012 to 2017. Each loan includes applicant information provided by the applicant as well as the current loan status (Current, Late, Fully Paid, etc.) and latest payment information. For a full view of the data please view the data dictionary available [here](https://resources.lendingclub.com/LCDataDictionary.xlsx).
# MAGIC 
# MAGIC 
# MAGIC ![Loan_Data](https://preview.ibb.co/d3tQ4R/Screen_Shot_2018_02_02_at_11_21_51_PM.png)
# MAGIC 
# MAGIC https://www.kaggle.com/wendykan/lending-club-loan-data

# COMMAND ----------

# MAGIC %md ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Delta Lake
# MAGIC 
# MAGIC Optimization Layer a top blob storage for Reliability (i.e. ACID compliance) and Low Latency of Streaming + Batch data pipelines.

# COMMAND ----------

# MAGIC %md ## Import Data and create pre-Delta Lake Table
# MAGIC * This will create a lot of small Parquet files emulating the typical small file problem that occurs with streaming or highly transactional data

# COMMAND ----------

# -----------------------------------------------
# Uncomment and run if this folder does not exist
# -----------------------------------------------
# Configure location of loanstats_2012_2017.parquet
lspq_path = "/databricks-datasets/samples/lending_club/parquet/"

# Read loanstats_2012_2017.parquet
data = spark.read.parquet(lspq_path)

# Reduce the amount of data (to run on DBCE)
(loan_stats, loan_stats_rest) = data.randomSplit([0.01, 0.99], seed=123)

# Select only the columns needed
loan_stats = loan_stats.select("addr_state", "loan_status")

# Create loan by state
loan_by_state = loan_stats.groupBy("addr_state").count()

# Create table
loan_by_state.createOrReplaceTempView("loan_by_state")

# Display loans by state
display(loan_by_state)

# COMMAND ----------

# MAGIC %md ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Easily Convert Parquet to Delta Lake format
# MAGIC With Delta Lake, you can easily transform your Parquet data into Delta Lake format.

# COMMAND ----------

# Configure Delta Lake Silver Path
DELTALAKE_SILVER_PATH = "/ml/j143/loan_by_state_delta"

# Remove folder if it exists
dbutils.fs.rm(DELTALAKE_SILVER_PATH, recurse=True)

# COMMAND ----------

# MAGIC %sql 
# MAGIC -- Current example is creating a new table instead of in-place import so will need to change this code
# MAGIC DROP TABLE IF EXISTS loan_by_state_delta;
# MAGIC 
# MAGIC CREATE TABLE loan_by_state_delta
# MAGIC USING delta
# MAGIC LOCATION '/ml/j143/loan_by_state_delta'
# MAGIC AS SELECT * FROM loan_by_state;
# MAGIC 
# MAGIC -- View Delta Lake table
# MAGIC SELECT * FROM loan_by_state_delta

# COMMAND ----------

# MAGIC %sql 
# MAGIC DESCRIBE DETAIL delta.`/ml/j143/loan_by_state_delta`

# COMMAND ----------

# MAGIC %md ## Stop the notebook before the streaming cell, in case of a "run all"

# COMMAND ----------

dbutils.notebook.exit("stop") 

# COMMAND ----------

# MAGIC %sh
# MAGIC ls -lt /dbfs/ml/j143/loan_by_state_delta/_delta_log/

# COMMAND ----------

# MAGIC %md ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Unified Batch and Streaming Source and Sink
# MAGIC 
# MAGIC These cells showcase streaming and batch concurrent queries (inserts and reads)
# MAGIC * This notebook will run an `INSERT` every 10s against our `loan_stats_delta` table
# MAGIC * We will run two streaming queries concurrently against this data
# MAGIC * Note, you can also use `writeStream` but this version is easier to run in DBCE

# COMMAND ----------

# Read the insertion of data
spark.sql("set spark.sql.shuffle.partitions = 1")
spark.sql("set spark.databricks.delta.snapshotPartitions = 1")
loan_by_state_readStream = spark.readStream.format("delta").load(DELTALAKE_SILVER_PATH)
loan_by_state_readStream.createOrReplaceTempView("loan_by_state_readStream")

# COMMAND ----------

# MAGIC %sql
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_readStream group by addr_state

# COMMAND ----------

# Read the insertion of data
loan_by_state_readStream = spark.readStream.format("delta").load(DELTALAKE_SILVER_PATH)
loan_by_state_readStream.createOrReplaceTempView("loan_by_state_readStream")
display(spark.sql("select sum(count) from loan_by_state_readStream where addr_state = 'IA'"))

# COMMAND ----------

# MAGIC %md **Wait** until the stream is up and running before executing the code below

# COMMAND ----------

import time
i = 1
while i <= 6:
  # Execute Insert statement
  insert_sql = "INSERT INTO loan_by_state_delta VALUES ('IA', 450)"
  spark.sql(insert_sql)
  print('loan_by_state_delta: inserted new row of data, loop: [%s]' % i)
    
  # Loop through
  i = i + 1
  time.sleep(5)

# COMMAND ----------

# MAGIC %md **Note**: Once the previous cell is finished and the state of Iowa is fully populated in the map (in cell 14), click *Cancel* in Cell 14 to stop the `readStream`.

# COMMAND ----------

# MAGIC %sh
# MAGIC ls -lt /dbfs/ml/j143/loan_by_state_delta/_delta_log/

# COMMAND ----------

# MAGIC %md Let's review our current set of loans using our map visualization.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md Observe that the Iowa (middle state) has the largest number of loans due to the recent stream of data.  Note that the original `loan_by_state_delta` table is updated as we're reading `loan_by_state_readStream`.

# COMMAND ----------

# MAGIC %md ##![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Full DML Support
# MAGIC 
# MAGIC **Note**: Full DML Support is a feature that will be coming soon to Delta Lake; the preview is currently available in Databricks.
# MAGIC 
# MAGIC Delta Lake supports standard DML including UPDATE, DELETE and MERGE INTO providing developers more controls to manage their big datasets.

# COMMAND ----------

# MAGIC %md Let's start by creating a traditional Parquet table

# COMMAND ----------

# Load new DataFrame based on current Delta table
lbs_df = sql("select * from loan_by_state_delta")

# Save DataFrame to Parquet
lbs_df.write.mode("overwrite").parquet("loan_by_state.parquet")

# Reload Parquet Data
lbs_pq = spark.read.parquet("loan_by_state.parquet")

# Create new table on this parquet data
lbs_pq.createOrReplaceTempView("loan_by_state_pq")

# Review data
display(sql("select * from loan_by_state_pq"))

# COMMAND ----------

# MAGIC %md ###![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) DELETE Support
# MAGIC 
# MAGIC The data was originally supposed to be assigned to `WA` state, so let's `DELETE` those values assigned to `IA`

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Attempting to run `DELETE` on the Parquet table
# MAGIC DELETE FROM loan_by_state_pq WHERE addr_state = 'IA'

# COMMAND ----------

# MAGIC %md **Note**: This command fails because the `DELETE` statements are not supported in Parquet, but are supported in Delta Lake.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Running `DELETE` on the Delta Lake table
# MAGIC DELETE FROM loan_by_state_delta WHERE addr_state = 'IA'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md ###![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) UPDATE Support
# MAGIC The data was originally supposed to be assigned to `WA` state, so let's `UPDATE` those values

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Attempting to run `UPDATE` on the Parquet table
# MAGIC UPDATE loan_by_state_pq SET `count` = 2700 WHERE addr_state = 'WA'

# COMMAND ----------

# MAGIC %md **Note**: This command fails because the `UPDATE` statements are not supported in Parquet, but are supported in Delta Lake.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Running `UPDATE` on the Delta Lake table
# MAGIC UPDATE loan_by_state_delta SET `count` = 2700 WHERE addr_state = 'WA'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md ###![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) MERGE INTO Support
# MAGIC 
# MAGIC #### INSERT or UPDATE parquet: 7-step process
# MAGIC 
# MAGIC With a legacy data pipeline, to insert or update a table, you must:
# MAGIC 1. Identify the new rows to be inserted
# MAGIC 2. Identify the rows that will be replaced (i.e. updated)
# MAGIC 3. Identify all of the rows that are not impacted by the insert or update
# MAGIC 4. Create a new temp based on all three insert statements
# MAGIC 5. Delete the original table (and all of those associated files)
# MAGIC 6. "Rename" the temp table back to the original table name
# MAGIC 7. Drop the temp table
# MAGIC 
# MAGIC ![](https://pages.databricks.com/rs/094-YMS-629/images/merge-into-legacy.gif)
# MAGIC 
# MAGIC 
# MAGIC #### INSERT or UPDATE with Delta Lake
# MAGIC 
# MAGIC 2-step process: 
# MAGIC 1. Identify rows to insert or update
# MAGIC 2. Use `MERGE`

# COMMAND ----------

# Let's create a simple table to merge
items = [('IA', 10), ('CA', 2500), ('OR', None)]
cols = ['addr_state', 'count']
merge_table = spark.createDataFrame(items, cols)
merge_table.createOrReplaceTempView("merge_table")
display(merge_table)

# COMMAND ----------

# MAGIC %md Instead of writing separate `INSERT` and `UPDATE` statements, we can use a `MERGE` statement.

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO loan_by_state_delta as d
# MAGIC USING merge_table as m
# MAGIC on d.addr_state = m.addr_state
# MAGIC WHEN MATCHED THEN 
# MAGIC   UPDATE SET *
# MAGIC WHEN NOT MATCHED 
# MAGIC   THEN INSERT *

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`count`) as loans from loan_by_state_delta group by addr_state

# COMMAND ----------

# MAGIC %md ##![Delta Lake Logo Tiny](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Schema Evolution
# MAGIC With the `mergeSchema` option, you can evolve your Delta Lake table schema

# COMMAND ----------

# Generate new loans with dollar amounts 
loans = sql("select addr_state, cast(rand(10)*count as bigint) as count, cast(rand(10) * 10000 * count as double) as amount from loan_by_state_delta")
display(loans)

# COMMAND ----------

# Let's write this data out to our Delta table
loans.write.format("delta").mode("append").save(DELTALAKE_SILVER_PATH)

# COMMAND ----------

# MAGIC %md **Note**: This command fails because the schema of our new data does not match the schema of our original data

# COMMAND ----------

# Add the mergeSchema option
loans.write.option("mergeSchema","true").format("delta").mode("append").save(DELTALAKE_SILVER_PATH)

# COMMAND ----------

# MAGIC %md **Note**: With the `mergeSchema` option, we can merge these different schemas together.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Review current loans within the `loan_by_state_delta` Delta Lake table
# MAGIC select addr_state, sum(`amount`) as amount from loan_by_state_delta group by addr_state order by sum(`amount`) desc limit 10

# COMMAND ----------

# MAGIC %md ## ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Let's Travel back in Time!
# MAGIC Databricks Delta’s time travel capabilities simplify building data pipelines for the following use cases. 
# MAGIC 
# MAGIC * Audit Data Changes
# MAGIC * Reproduce experiments & reports
# MAGIC * Rollbacks
# MAGIC 
# MAGIC As you write into a Delta table or directory, every operation is automatically versioned.
# MAGIC 
# MAGIC You can query by:
# MAGIC 1. Using a timestamp
# MAGIC 1. Using a version number
# MAGIC 
# MAGIC using Python, Scala, and/or Scala syntax; for these examples we will use the SQL syntax.  
# MAGIC 
# MAGIC For more information, refer to [Introducing Delta Time Travel for Large Scale Data Lakes](https://databricks.com/blog/2019/02/04/introducing-delta-time-travel-for-large-scale-data-lakes.html)

# COMMAND ----------

# MAGIC %md ### ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Review Delta Lake Table History
# MAGIC All the transactions for this table are stored within this table including the initial set of insertions, update, delete, merge, and inserts with schema modification

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY loan_by_state_delta

# COMMAND ----------

# MAGIC %md ### ![Delta Lake Tiny Logo](https://pages.databricks.com/rs/094-YMS-629/images/delta-lake-tiny-logo.png) Time Travel via Version Number
# MAGIC Below are SQL syntax examples of Delta Time Travel by using a Version Number

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM loan_by_state_delta VERSION AS OF 0

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM loan_by_state_delta VERSION AS OF 9

# COMMAND ----------

# MAGIC %md ## Run Our Model
# MAGIC Let's run a simple linear regression model to predict the number of loans based on the population of the state

# COMMAND ----------

# MAGIC %sh mkdir -p /dbfs/tmp/sais_eu_19_demo/census/ && wget -O /dbfs/tmp/sais_eu_19_demo/census/us_census_2010.csv https://pages.databricks.com/rs/094-YMS-629/images/us_census_2010.csv && ls -al /dbfs/tmp/sais_eu_19_demo/census/

# COMMAND ----------

# MAGIC %md ### Notes
# MAGIC If you forgot to install `mlflow` and `yellowbrick` on your cluster, instead of re-running everything all over again:
# MAGIC * Note that the Delta Lake table is stored in `DELTALAKE_SILVERPATH` or `/ml/loan_by_state_delta`
# MAGIC * You can add the libraries, restart the cluster and then start reading the data from the following cells (instead of rerunning everything all over again)
# MAGIC * Just uncomment the cell below to reconnect to your Delta Table

# COMMAND ----------

## Recreate loan_by_state_delta view
# spark.read.format("delta").load("/ml/loan_by_state_delta").createOrReplaceTempView("loan_by_state_delta")
## Check data
# display(spark.sql("select count(1) from loan_by_state_delta"))

# COMMAND ----------

# Include census data
census = spark.read.csv('/tmp/sais_eu_19_demo/census/us_census_2010.csv', sep=',', inferSchema=True, header=True)
census.createOrReplaceTempView("census")

# Data versions (0, 6, 9)
dfv0 = spark.sql("select c.Population, l.count as label from (select addr_state as State, count from loan_by_state_delta  version as of 0) l left outer join census c on c.State = l.State")
dfv6 = spark.sql("select c.Population, l.count as label from (select addr_state as State, count from loan_by_state_delta  version as of 6) l left outer join census c on c.State = l.State")
dfv9 = spark.sql("select c.Population, l.count as label from (select addr_state as State, count from loan_by_state_delta  version as of 9 where count is not null) l left outer join census c on c.State = l.State")

# COMMAND ----------

!pip install mlflow

# COMMAND ----------

!pip install yellowbrick

# COMMAND ----------

# Import MLflow
import mlflow
import mlflow.spark
print("MLflow Version: %s" % mlflow.__version__)

# Display Residuals (yellowbrick)
def displayResiduals(train, test):
  from sklearn.linear_model import Ridge
  from yellowbrick.regressor import ResidualsPlot

  # define feature columns
  featureColumns = ['Population']

  # Create pandas DataFrames
  pdf_train = train.toPandas()
  pdf_test = test.toPandas()

  # Convert to X, y train and test values
  X_train = pdf_train[['Population']].to_numpy()
  y_train = pdf_train[['label']].to_numpy().flatten()
  X_test = pdf_test[['Population']].to_numpy()
  y_test = pdf_test[['label']].to_numpy().flatten()  
  
  # Instantiate the linear model and visualizer
  ridge = Ridge()
  visualizer = ResidualsPlot(ridge)

  # Visualize
  visualizer.fit(X_train, y_train)  # Fit the training data to the model
  visualizer.score(X_test, y_test)  # Evaluate the model on the test data
  visualizer.show(outpath="ridge-model-residuals.png")
  #fig=visualizer.poof()             # Draw/show/poof the data
  
# Predict Loan Count (based on state population)
def predictLoanCount(df, data_version):
  from pyspark.ml.linalg import Vectors
  from pyspark.ml.feature import VectorAssembler
  from pyspark.ml.regression import LinearRegression
  from pyspark.ml.evaluation import RegressionEvaluator
  
  # assemble vector
  assembler = VectorAssembler(
    inputCols=["Population"],
    outputCol="features")
  output = assembler.transform(df)

  # Log mlflow
  with mlflow.start_run() as run:  
    # Define LinearRegression algorithm
    lr = LinearRegression(maxIter=10, regParam=0.0, elasticNetParam=0.8)
    model = lr.fit(output)  

    # Calculate predictions
    predictions = model.transform(output)

    # calculate RMSE
    evaluator = RegressionEvaluator(metricName="rmse")
    RMSE = evaluator.evaluate(predictions)

    # Log Parameters
    mlflow.log_param("data version", data_version)
    mlflow.log_metric("RMSE", RMSE)

    # Log Model
    mlflow.spark.log_model(model, "model") 
    
    # Save if not data_version is "v0"
    if (data_version != 'v0'):
      # Log artifacts (output files)
      mlflow.log_artifact("ridge-model-residuals.png")
  
  # return predictions DataFrame
  #return predictions

# COMMAND ----------

# Calculate predictions
# Initial version of data (v0)
predictLoanCount(dfv0, 'v0')

# Version 6 (after streaming of Iowa data)
displayResiduals(dfv0, dfv6)
predictLoanCount(dfv6, 'v6')

# Version 9 (after correction of data: update, delete, merge)
displayResiduals(dfv0, dfv9)
predictLoanCount(dfv9, 'v9')

# COMMAND ----------

# MAGIC %md #### Review RMSE and Residuals
# MAGIC * Review the RMSE values via the MLflow Sidebar
