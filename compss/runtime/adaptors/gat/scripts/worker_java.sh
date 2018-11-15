#!/bin/bash

  # Get worker common functions
  SCRIPT_DIR=$(dirname "$0")
  # shellcheck source=./worker_commons.sh
  source "${SCRIPT_DIR}"/worker_commons.sh

  #-------------------------------------
  # Retrieve host configuration
  #-------------------------------------
  get_host_parameters "$@"

  implType=${invocation[0]}
  case "${implType}" in
    "METHOD")
      lang=${invocation[1]}
      cp=${invocation[2]}
      echo "[WORKER_JAVA.SH]    - classpath                          = $cp"
      className=${invocation[3]}
      echo "[WORKER_JAVA.SH]    - class name                         = $className"
      methodName=${invocation[4]}
      echo "[WORKER_JAVA.SH]    - method name                        = $methodName"
      implDescription=( "${implType}" "${className}" "${methodName}" )
      arguments=(${invocation[@]:5})
      ;;
    "MPI")
      mpi_runner=${invocation[1]}
      echo "[WORKER_JAVA.SH]    - mpi                                = ${mpi_runner}"
      mpi_binary=${invocation[2]}
      echo "[WORKER_JAVA.SH]    - mpi binary                         = ${mpi_binary}"
      mpi_sandbox=${invocation[3]}
      echo "[WORKER_JAVA.SH]    - sandbox                            = ${mpi_sandbox}"
      implDescription=( "${implType}" "${mpi_runner}" "${mpi_binary}" "${mpi_sandbox}")
      arguments=(${invocation[@]:4})
      ;;
    "DECAF")
      decaf_dfScript=${invocation[1]}
      echo "[WORKER_JAVA.SH]    - Decaf dfScript                      = ${decaf_dfScript}"
      decaf_dfExecutor=${invocation[2]}
      echo "[WORKER_JAVA.SH]    - Decaf dfExecutor                    = ${decaf_dfExecutor}"
      decaf_dfLib=${invocation[3]}
      echo "[WORKER_JAVA.SH]    - Decaf dfLib                         = ${decaf_dfLib}"
      mpi_runner=${invocation[4]}
      echo "[WORKER_JAVA.SH]    - mpi runner                          = ${mpi_runner}"
      decaf_sandbox=${invocation[5]}
      echo "[WORKER_JAVA.SH]    - sandbox                             = ${decaf_sandbox}"
      implDescription=( "${implType}" "${decaf_dfScript}" "${decaf_dfExecutor}" "${decaf_dfLib}" "${mpi_runner}" "${decaf_sandbox}")
      arguments=(${invocation[@]:6})
      ;;
    "OMPSS")
      ompss_binary=${invocation[1]}
      echo "[WORKER_JAVA.SH]    - ompss binary                        = ${ompss_binary}"
      ompss_sandbox=${invocation[2]}
      echo "[WORKER_JAVA.SH]    - sandbox                             = ${ompss_sandbox}"
      implDescription=( "${implType}" "${ompss_binary}" "${ompss_sandbox}")
      arguments=(${invocation[@]:3})
      ;;
    "OPENCL")
      opencl_kernel=${invocation[1]}
      echo "[WORKER_JAVA.SH]    - opencl kernel                       = ${opencl_kernel}"
      opencl_sandbox=${invocation[2]}
      echo "[WORKER_JAVA.SH]    - sandbox                             = ${opencl_sandbox}"
      implDescription=( "${implType}" "${opencl_kernel}" "${opencl_sandbox}")
      arguments=(${invocation[@]:3})
      ;;
    "BINARY")
      binary=${invocation[1]}
      echo "[WORKER_JAVA.SH]    - binary                              = ${binary}"
      binary_sandbox=${invocation[2]}
      echo "[WORKER_JAVA.SH]    - sandbox                             = ${binary_sandbox}"
      implDescription=( "${implType}" "${binary}" "${binary_sandbox}")
      arguments=(${invocation[@]:3})
      ;;
    *)
      echo 1>&2 "Unsupported implementation Type "${implType}""
      exit 7
      ;;
  esac

  echo "ARGUMENTS  = ${arguments[*]}"
  get_invocation_params ${arguments[@]}

  # Pre-execution
  set_env
  
  # Execution: launch the JVM to run the task
  java \
    -Xms128m -Xmx2048m \
    -classpath "$CLASSPATH" \
    es.bsc.compss.gat.worker.GATWorker ${hostFlags[@]} ${implDescription[@]} ${invocationParams[@]}
  ev=$?
 echo "Exit value=$ev"
  # Exit  
  if [ $ev -eq 0 ]; then
    exit 0
  else
    echo 1>&2 "Task execution failed"
    exit 7
  fi

