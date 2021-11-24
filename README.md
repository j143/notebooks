# notebooks
Jupyter notebooks for data science applications with [`Apache SystemDS`](https://github.com/apache/systemds).

#### JIRA
https://issues.apache.org/jira/browse/SYSTEMDS-1783


##### Contribution
Accepting contributions for adding **documentation** and **notebooks** or ask in the `issues` about how you can contribute.


### How to run

#### Run dml

```sh
java -Xmx110g -Xms110g -Xmn11g \
    -cp /home/user/systemds/target/lib/*:/home/aphani/systemds/target/SystemDS.jar \
    -Dlog4j.configuration=file:/home/aphani/systemds/log4j-silent.properties \
    org.apache.sysds.api.DMLScript \
    -exec singlenode \
    -debug \
    -config /home/user/systemds/SystemDS-config.xml \
    "$@"
```

#### For testing

```sh
mvn -ntp test -DenableGPU=true -Dmaven.test.skip=false -Dtest-parallel=suites -Dtest-threadCount=1 -Dtest-forkCount=1 -D automatedtestbase.tputbuffering=false -Dtest=org.apache.sysds.test.gpu.codegen.CellwiseTmplTest.java

```
