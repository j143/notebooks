function Install-SystemDS([string]$systemdsHome){
  
  # start http://google.com
  # Installing dependencies
  # 0. Install Java OpenJDK
  
  # 1. Install Apache Spark (with Hadoop)
  Install-Spark("F:\Repo\P005\sml")
  
  # 2. Install Apache Maven
  Install-Maven()
  
  # 3. Install Hadoop utilities
  
}

function Install-OpenJDK8() {
  # 1. Download OpenJDK
  # 2. Set OpenJDK to path
}

function Install-Spark([string]$installDir) {
  # 1. Download spark
  # 1a. Verify spark artifacts
  # 2. Unzip spark
  # 3. Set `SPARK_HOME` variable
  # 4. Set `SPARK_HOME\bin` to path
  # 5. Test that `spark-shell` command works
}

function Install-Maven() {
  # 1. Download maven
  # 1a. verify maven artifacts
  # 2. Unzip maven
  # 3. Set `MAVEN_HOME` variable
  # 4. Set `MAVEN_HOME\bin` to path
  # 5. Test the `mvn -v` command works
}

function Install-HadoopUtils() {
  # 1. Download winutils.exe file 
  # corresponding to hadoop version from
  # https://github.com/cdarlint/winutils
  # 1a. Verify the artifacts with committer(should be of apache) key
  # 
  # Directory structure:
  # $\winutils\bin\winutils.exe
  # HADOOP_HOME = .\winutils
  # 2. set `HADOOP_HOME` variable
  
}

Install-SystemDS("F:\Repo\systemds")
