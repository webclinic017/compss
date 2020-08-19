#!/usr/bin/python
#
#  Copyright 2002-2019 Barcelona Supercomputing Center (www.bsc.es)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
PyCOMPSs Worker for Containers
=======================
    This file contains the code of a fake worker to execute Python tasks inside containers.
"""

import sys
import logging

from pycompss.worker.commons.worker import execute_task

# Define static logger
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
LOGGER = logging.getLogger()


#
# Main method for Python task execution inside a Container
#
def main():
    # type: (...) -> int
    """ Main method to process the task execution.

    :return: Exit value
    """

    # Log initialisation
    if __debug__:
        LOGGER.debug("Initialising Python worker inside the container...")

    # Parse arguments
    if __debug__:
        LOGGER.debug("Parsing Python function and arguments...")

    # TODO: Enhance the received parameters from ContainerInvoker.java
    func_file_path = sys.argv[2]
    func_name = sys.argv[3]
    num_slaves = 0
    timeout = 0
    cus = 1
    has_target = False
    return_type = "null"
    return_length = 0
    num_params = sys.argv[4]
    func_params = sys.argv[5:]

    execute_task_params = [func_file_path, func_name, num_slaves, timeout, cus, has_target, return_type, return_length,
                           num_params, func_params]

    if __debug__:
        LOGGER.debug("- File: " + str(func_file_path))
        LOGGER.debug("- Function: " + str(func_name))
        LOGGER.debug("- Num Parameters: " + str(num_params))
        LOGGER.debug("- Parameters: " + str(func_params))
        LOGGER.debug("DONE Parsing Python function and arguments")

    # Process task
    if __debug__:
        LOGGER.debug("Processing task...")

    process_name = "ContainerInvoker"
    storage_conf = "null"
    tracing = False
    log_files = None
    python_mpi = False
    collections_layouts = None
    result = execute_task(process_name,
                          storage_conf,
                          execute_task_params,
                          tracing,
                          LOGGER,
                          log_files,
                          python_mpi,
                          collections_layouts
                          )
    exit_value, new_types, new_values, timed_out, except_msg = result

    if __debug__:
        LOGGER.debug("DONE Processing task")

    # Process results
    # TODO: Enhance the result treatment for ContainerInvoker.java
    if __debug__:
        print ("Processing results...")

    if exit_value != 0:
        LOGGER.debug("ERROR: Task execution finished with non-zero exit value (" + str(exit_value) + " != 0")
    else:
        LOGGER.debug("Task execution finished SUCCESSFULLY!")
    return exit_value


#
# Entry point
#
if __name__ == "__main__":
    main()
