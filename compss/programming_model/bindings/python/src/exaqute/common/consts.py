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
INOUT = "inout"
FILE_IN = "filein"
FILE_OUT = "fileout"
FILE_INOUT = "fileinout"

COLLECTION_IN = "collection_in" 
COLLECTION_INOUT = "collection_inout"
COLLECTION_OUT = "collection_out"

# Aliases for parameter definition as dictionary
Type = 'type'  # parameter type

# available at PyCOMPSs but not used in XMC ( specfic
#Direction = 'direction'  # parameter type
#StdIOStream = 'stream'  # parameter stream
#Prefix = 'prefix'  # parameter prefix

Depth = 'depth'  # collection recursive depth

# data layout for Collections in MPI
block_count = 'block_count'
block_length = 'block_length'
stride = 'stride'

