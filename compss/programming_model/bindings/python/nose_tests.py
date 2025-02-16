#!/usr/bin/python
#
#  Copyright 2002-2021 Barcelona Supercomputing Center (www.bsc.es)
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

# -*- coding: utf-8 -*-

# Imports
import nose
import sys
from nose.plugins.base import Plugin

if sys.version_info >= (3, 0):
    IS_PYTHON3 = True
else:
    # autoparallel is not compatible with python3
    IS_PYTHON3 = False


DIRECTORIES_WHITE_LIST = [
    'src',
    'pycompss',
    'pycompss/tests',
    'pycompss/tests/api',
    'pycompss/tests/api/dummy',
    'pycompss/tests/api/commons',
    'pycompss/tests/dds',
    'pycompss/tests/functions',
    'pycompss/tests/integration',
    'pycompss/tests/main',
    'pycompss/tests/runtime',
    'pycompss/tests/streams',
    'pycompss/tests/util',
    'pycompss/tests/worker',
    'pycompss/api',
    'pycompss/util'
]

FILES_WHITE_LIST = [
    # Include all tests that check only the sources.
    # (Do not include tests that use the installed runtime. Use
    # INTEGRATION_WHITE_LIST instead of this)
    'pycompss/tests/main/test_main.py',
    'pycompss/tests/api/test_api.py',
    'pycompss/tests/api/test_binary.py',
    'pycompss/tests/api/test_compss.py',
    'pycompss/tests/api/test_constraint.py',
    'pycompss/tests/api/test_container.py',
    'pycompss/tests/api/test_decaf.py',
    'pycompss/tests/api/test_decorator.py',
    'pycompss/tests/api/test_err_msgs.py',
    'pycompss/tests/api/test_exaqute_api.py',
    'pycompss/tests/api/test_exceptions.py',
    'pycompss/tests/api/test_implement.py',
    'pycompss/tests/api/test_io.py',
    'pycompss/tests/api/test_local.py',
    'pycompss/tests/api/test_mpi.py',
    'pycompss/tests/api/test_multinode.py',
    'pycompss/tests/api/test_ompss.py',
    'pycompss/tests/api/test_on_failure.py',
    'pycompss/tests/api/test_opencl.py',
    'pycompss/tests/api/test_information.py',
    'pycompss/tests/api/test_reduction.py',
    'pycompss/tests/api/dummy/test_dummy_binary.py',
    'pycompss/tests/api/dummy/test_dummy_task.py',
    'pycompss/tests/api/dummy/test_dummy_container.py',
    'pycompss/tests/api/dummy/test_dummy_reduction.py',
    'pycompss/tests/api/dummy/test_dummy_on_failure.py',
    'pycompss/tests/dds/test_heapq.py',
    'pycompss/tests/dds/test_dds_class.py',
    'pycompss/tests/dds/dds_examples.py',
    'pycompss/tests/functions/test_data.py',
    'pycompss/tests/functions/test_elapsed_time.py',
    'pycompss/tests/functions/test_reduce.py',
    'pycompss/tests/functions/test_profile.py',
    'pycompss/tests/runtime/test_object_tracker.py',
    'pycompss/tests/runtime/test_core_element.py',
    'pycompss/tests/runtime/test_management_direction.py',
    'pycompss/tests/runtime/test_link.py',
    'pycompss/tests/runtime/test_COMPSs.py',
    'pycompss/tests/streams/test_distro_stream_client.py',
    'pycompss/tests/util/test_arguments.py',
    'pycompss/tests/util/test_context.py',
    'pycompss/tests/util/test_exceptions.py',
    'pycompss/tests/util/test_jvm_parser.py',
    'pycompss/tests/util/test_mpi_helper.py',
    'pycompss/tests/util/test_objects.py',
    'pycompss/tests/util/test_object_replace.py',
    'pycompss/tests/util/test_object_sizer.py',
    'pycompss/tests/util/test_serializer.py',
    'pycompss/tests/util/test_supercomputer.py',
    'pycompss/tests/util/test_warning_modules.py',
    'pycompss/tests/worker/test_container_worker.py',
    'pycompss/tests/worker/test_gat.py',
    'pycompss/tests/worker/test_piper.py',
    'pycompss/tests/worker/test_mpi_piper.py',
    'pycompss/tests/worker/test_external_mpi.py',
    'pycompss/tests/worker/test_piper_worker_cache.py'
]
FILES_BLACK_LIST = [
]
INTEGRATION_WHITE_LIST = [
    # Include here all tests that require the runtime installed
    'pycompss/tests/dds/test_dds_examples.py',
    'pycompss/tests/integration/test_launch_application.py',
    'pycompss/tests/integration/test_launch_application_collection.py',
    'pycompss/tests/integration/test_launch_application_tracing.py',
    'pycompss/tests/integration/test_launch_application_storage.py',
    'pycompss/tests/integration/test_launch_synthetic_application.py',
    'pycompss/tests/integration/test_launch_functions.py',
    'pycompss/tests/integration/test_launch_0_basic1.py',
    'pycompss/tests/integration/test_launch_stream_objects.py',
    'pycompss/tests/integration/test_runcompss_application.py',
    'pycompss/tests/main/test_notebook.py',
]


if not IS_PYTHON3:
    # If is python2, add autoparallel code
    DIRECTORIES_WHITE_LIST += [
        'pycompss/util/translators',
        'pycompss/util/translators/code_loader',
        'pycompss/util/translators/code_replacer',
        'pycompss/util/translators/py2pycompss',
        'pycompss/util/translators/py2scop',
        'pycompss/util/translators/scop2pscop2py',
        'pycompss/util/translators/scop_types',
        'pycompss/util/translators/scop_types/scop',
        'pycompss/util/translators/scop_types/scop/extensions',
        'pycompss/util/translators/scop_types/scop/globl',
        'pycompss/util/translators/scop_types/scop/globl/parameters',
        'pycompss/util/translators/scop_types/scop/statement'
    ]
    FILES_WHITE_LIST += [
        'pycompss/api/parallel.py',
        'pycompss/util/translators/code_loader/code_loader.py',
        'pycompss/util/translators/code_replacer/code_replacer.py',
        'pycompss/util/translators/py2pycompss/translator_py2pycompss.py',
        'pycompss/util/translators/py2scop/translator_py2scop.py',
        'pycompss/util/translators/scop2pscop2py/translator_scop2pscop2py.py',
        'pycompss/util/translators/scop_types/scop_class.py',
        'pycompss/util/translators/scop_types/scop/statement_class.py',
        'pycompss/util/translators/scop_types/scop/extensions/coordinates_class.py',
        'pycompss/util/translators/scop_types/scop/extensions/scatnames_class.py',
        'pycompss/util/translators/scop_types/scop/extensions/arrays_class.py',
        'pycompss/util/translators/scop_types/scop/global_class.py',
        'pycompss/util/translators/scop_types/scop/globl/parameters/parameter_class.py',
        'pycompss/util/translators/scop_types/scop/globl/parameters_class.py',
        'pycompss/util/translators/scop_types/scop/globl/context_class.py',
        'pycompss/util/translators/scop_types/scop/statement/statement_extension_class.py',
        'pycompss/util/translators/scop_types/scop/statement/relation_class.py',
        'pycompss/util/translators/scop_types/scop/extensions_class.py'
    ]
else:
    FILES_BLACK_LIST += [
        'pycompss/api/parallel.py',
    ]


class ExtensionPlugin(Plugin):

    name = "ExtensionPlugin"

    def __init__(self, integration=False):
        super(ExtensionPlugin, self).__init__()
        if integration:
            self.files_white_list = INTEGRATION_WHITE_LIST
        else:
            self.files_white_list = FILES_WHITE_LIST
        self.directories_white_list = DIRECTORIES_WHITE_LIST
        self.files_black_list = FILES_BLACK_LIST

    def options(self, parser, env):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.enabled = True

    def wantFile(self, file):  # noqa
        print("FILE: " + str(file))
        # Check that is a python file
        if file.endswith('.py'):
            # Check that is white-listed
            for white_file in self.files_white_list:
                if white_file not in self.files_black_list and file.endswith(white_file):
                    print("Testing File: " + str(file))
                    return True
        # Does not match any pattern
        return False

    def wantDirectory(self, directory):  # noqa
        # Check that the directory is white-listed
        for white_dir in self.directories_white_list:
            if directory.endswith(white_dir):
                return True
        # Does not match any pattern
        return False

    def wantModule(self, file):  # noqa
        print("MODULE: " + str(file))
        return True


if __name__ == '__main__':
    do_integration_tests = sys.argv.pop() == "True"
    includeDirs = ["-w", "."]
    nose.main(addplugins=[ExtensionPlugin(integration=do_integration_tests)],
              argv=sys.argv.extend(includeDirs))
