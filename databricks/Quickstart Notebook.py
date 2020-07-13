# Databricks notebook source
# MAGIC %md
# MAGIC # Apache SystemDS on Databricks in 5 minutes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create a quickstart cluster
# MAGIC 
# MAGIC 1. In the sidebar, right-click the **Clusters** button and open the link in a new window.
# MAGIC 1. On the Clusters page, click **Create Cluster**.
# MAGIC 1. Name the cluster **Quickstart**.
# MAGIC 1. In the Databricks Runtime Version drop-down, select **6.3 (Scala 2.11, Spark 2.4.4)**.
# MAGIC 1. Click **Create Cluster**.
# MAGIC 1. Attach `SystemDS.jar` file to the libraries

# COMMAND ----------

# MAGIC %md
# MAGIC ## Attach the notebook to the cluster and run all commands in the notebook
# MAGIC 
# MAGIC 1. Return to this notebook. 
# MAGIC 1. In the notebook menu bar, select **<img src="http://docs.databricks.com/_static/images/notebooks/detached.png"/></a> > Quickstart**.
# MAGIC 1. When the cluster changes from <img src="http://docs.databricks.com/_static/images/clusters/cluster-starting.png"/></a> to <img src="http://docs.databricks.com/_static/images/clusters/cluster-running.png"/></a>, click **<img src="http://docs.databricks.com/_static/images/notebooks/run-all.png"/></a> Run All**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load SystemDS MLContext API

# COMMAND ----------

# MAGIC %scala
# MAGIC import org.apache.sysds.api.mlcontext._
# MAGIC import org.apache.sysds.api.mlcontext.ScriptFactory._
# MAGIC val ml = new MLContext(spark)

# COMMAND ----------

# MAGIC %scala
# MAGIC val habermanUrl = "http://archive.ics.uci.edu/ml/machine-learning-databases/haberman/haberman.data"
# MAGIC val habermanList = scala.io.Source.fromURL(habermanUrl).mkString.split("\n")
# MAGIC val habermanRDD = sc.parallelize(habermanList)
# MAGIC val habermanMetadata = new MatrixMetadata(306, 4)
# MAGIC val typesRDD = sc.parallelize(Array("1.0,1.0,1.0,2.0"))
# MAGIC val typesMetadata = new MatrixMetadata(1, 4)
# MAGIC val scriptUrl = "https://raw.githubusercontent.com/apache/systemds/master/scripts/algorithms/Univar-Stats.dml"
# MAGIC val uni = dmlFromUrl(scriptUrl).in("A", habermanRDD, habermanMetadata).in("K", typesRDD, typesMetadata).in("$CONSOLE_OUTPUT", true)
# MAGIC ml.execute(uni)
