set -u

abort() {
  echo $@
  exit 1
}

echo "Collecting system info..."

OUTPUT_FILE=systemds_env.txt
python_bin_path=$(which python || which python3 || abort "couldn't find Python binary")

{
echo
echo '==== check python ===='
} >> ${OUTPUT_FILE}

cat <<EOF > /tmp/check_python.py
import platform

print("""python version: %s
python branch: %s
python build version: %s
python compiler version: %s
python implementation: %s
""" %(
platform.python_version(),
platform.python_branch(),
platform.python_build(),
platform.python_compiler(),
platform.python_implementation(),
))
EOF
${python_bin_path} /tmp/check_python.py 2>&1 >> ${OUTPUT_FILE}

{
echo
echo '==== check os platform =='
} >> ${OUTPUT_FILE}

cat <<DOF > /tmp/check_os.py
import platform

print("""os: %s
os kernel version: %s
os release version: %s
""" % (
platform.system(),
platform.version(),
))
EOF
${python_bin_path} /tmp/check_os.py 2>&1 >> ${OUTPUT_FILE}

{
  echo '=== c++ compiler ==='
  c++ --version 2>&1

  echo
  echo '=== maven version ==='

} >> ${OUTPUT_FILE}
