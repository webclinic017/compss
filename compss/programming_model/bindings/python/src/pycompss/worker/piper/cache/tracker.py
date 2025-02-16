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

"""
PyCOMPSs Cache tracker
======================
    This file contains the cache object tracker.
    IMPORTANT: Only used with python >= 3.8.
"""

import os
from collections import OrderedDict
from pycompss.util.exceptions import PyCOMPSsException
from pycompss.util.objects.sizer import total_sizeof
from pycompss.util.tracing.helpers import emit_event
from pycompss.worker.commons.constants import RETRIEVE_OBJECT_FROM_CACHE_EVENT
from pycompss.worker.commons.constants import INSERT_OBJECT_INTO_CACHE_EVENT
from pycompss.worker.commons.constants import REMOVE_OBJECT_FROM_CACHE_EVENT
try:
    from multiprocessing.shared_memory import SharedMemory    # noqa
    from multiprocessing.shared_memory import ShareableList   # noqa
    from multiprocessing.managers import SharedMemoryManager  # noqa
except ImportError:
    # Unsupported in python < 3.8
    SharedMemory = None
    ShareableList = None
    SharedMemoryManager = None
try:
    import numpy as np
except ImportError:
    np = None
from pycompss.worker.commons.constants import TASK_EVENTS_SERIALIZE_SIZE_CACHE
from pycompss.worker.commons.constants import TASK_EVENTS_DESERIALIZE_SIZE_CACHE
from pycompss.util.tracing.helpers import emit_manual_event_explicit


HEADER = "[PYTHON CACHE] "
SHARED_MEMORY_MANAGER = None

# Supported shared objects (remind that nested lists are not supported).
SHARED_MEMORY_TAG = "SharedMemory"
SHAREABLE_LIST_TAG = "ShareableList"
SHAREABLE_TUPLE_TAG = "ShareableTuple"
# Currently dicts are unsupported since conversion requires nesting of lists.
# SHAREABLE_DICT_TAG = "ShareableTuple"

AUTH_KEY = b"compss_cache"
IP = "127.0.0.1"
PORT = 50000


class CacheTrackerConf(object):
    """
    Cache tracker configuration
    """

    __slots__ = ['logger', 'size', 'policy', 'cache_ids']

    def __init__(self, logger, size, policy, cache_ids):
        """
        Constructs a new cache tracker configuration.

        :param logger: Main logger.
        :param size: Total cache size supported.
        :param policy: Eviction policy.
        :param cache_ids: Shared dictionary proxy where the ids and
                          (size, hits) as its value are.
        """
        self.logger = logger
        self.size = size
        self.policy = policy        # currently no policies defined.
        self.cache_ids = cache_ids  # key - (id, shape, dtype, size, hits, shared_type)


def cache_tracker(queue, process_name, conf):
    # type: (..., str, CacheTrackerConf) -> None
    """ Process main body

    :param queue: Queue where to put exception messages.
    :param process_name: Process name.
    :param conf: configuration of the cache tracker.
    :return: None
    """
    # Process properties
    alive = True
    logger = conf.logger
    cache_ids = conf.cache_ids
    max_size = conf.size

    if __debug__:
        logger.debug(HEADER + "[%s] Starting Cache Tracker" %
                     str(process_name))

    # MAIN CACHE TRACKER LOOP
    used_size = 0
    while alive:
        msg = queue.get()
        if msg == "QUIT":
            if __debug__:
                logger.debug(HEADER + "[%s] Stopping Cache Tracker: %s" %
                             (str(process_name), str(msg)))
            alive = False
        else:
            try:
                action, message = msg
                if action == "PUT":
                    f_name, cache_id, shape, dtype, obj_size, shared_type = message  # noqa: E501
                    if f_name in cache_ids:
                        # Any executor has already put the id
                        if __debug__:
                            logger.debug(HEADER + "[%s] Cache hit" %
                                         str(process_name))
                        # Increment hits
                        cache_ids[f_name][4] += 1
                    else:
                        # Add new entry request
                        if __debug__:
                            logger.debug(HEADER + "[%s] Cache add entry: %s" %
                                         (str(process_name), str(msg)))
                        # Check if it is going to fit and remove if necessary
                        obj_size = int(obj_size)
                        if used_size + obj_size > max_size:
                            # Cache is full, need to evict
                            used_size = check_cache_status(conf,
                                                           used_size,
                                                           obj_size)
                        # Add without problems
                        used_size = used_size + obj_size
                        cache_ids[f_name] = [cache_id,
                                             shape,
                                             dtype,
                                             obj_size,
                                             0,
                                             shared_type]
                elif action == "REMOVE":
                    f_name = __get_file_name__(message)
                    logger.debug(HEADER + "[%s] Removing: %s" %
                                 (str(process_name), str(f_name)))
                    cache_ids.pop(f_name)
            except Exception as e:
                logger.exception("%s - Exception %s" % (str(process_name),
                                                        str(e)))
                alive = False


def check_cache_status(conf, used_size, requested_size):
    # type: (CacheTrackerConf, int, int) -> int
    """ Checks the cache status looking into the shared dictionary.

    :param conf: configuration of the cache tracker.
    :param used_size: Current used size of the cache.
    :param requested_size: Size needed to fit the new object.
    :return: new used size
    """
    logger = conf.logger  # noqa
    max_size = conf.size
    cache_ids = conf.cache_ids

    if __debug__:
        logger.debug(HEADER + "Checking cache status: Requested %s" %
                     str(requested_size))

    # Sort by number of hits (from lower to higher)
    sorted_cache_ids = OrderedDict(sorted(cache_ids.items(),
                                          key=lambda item: item[1][4]))

    size_to_recover = used_size + requested_size - max_size
    # Select how many to evict
    to_evict = list()
    position = 0
    recovered_size = 0
    keys = list(sorted_cache_ids.keys())
    while size_to_recover > 0:
        key = keys[position]
        value = sorted_cache_ids[key]
        to_evict.append(key)
        size_to_recover = size_to_recover - value[3]
        recovered_size = recovered_size + value[3]
        position = position + 1

    if __debug__:
        logger.debug(HEADER + "Evicting %d entries" % (len(to_evict)))
    # Evict
    for entry in to_evict:
        cache_ids.pop(entry)
    return used_size - recovered_size


def load_shared_memory_manager():
    # type: () -> None
    """ Connects to the main shared memory manager initiated in piper_worker.py.

    :return: None
    """
    global SHARED_MEMORY_MANAGER
    SHARED_MEMORY_MANAGER = SharedMemoryManager(address=(IP, PORT),
                                                authkey=AUTH_KEY)
    SHARED_MEMORY_MANAGER.connect()


def start_shared_memory_manager():
    # type: () -> SharedMemoryManager
    """ Starts the shared memory manager.

    :return: Shared memory manager instance.
    """
    smm = SharedMemoryManager(address=('', PORT), authkey=AUTH_KEY)
    smm.start()
    return smm


def stop_shared_memory_manager(smm):
    # type: (SharedMemoryManager) -> None
    """ Stops the given shared memory manager, releasing automatically the
    objects contained in it.

    Only needed to be stopped from the main worker process. It is not
    necessary to disconnect each executor.

    :param smm: Shared memory manager.
    :return: None
    """
    smm.shutdown()


@emit_event(RETRIEVE_OBJECT_FROM_CACHE_EVENT, master=False, inside=True)
def retrieve_object_from_cache(logger, cache_ids, identifier):  # noqa
    # type: (..., ..., str) -> ...
    """ Retrieve an object from the given cache proxy dict.

    :param logger: Logger where to push messages.
    :param cache_ids: Cache proxy dictionary.
    :param identifier: Object identifier.
    :return: The object from cache.
    """
    emit_manual_event_explicit(TASK_EVENTS_DESERIALIZE_SIZE_CACHE, 0)
    identifier = __get_file_name__(identifier)
    if __debug__:
        logger.debug(HEADER + "Retrieving: " + str(identifier))
    obj_id, obj_shape, obj_d_type, _, obj_hits, shared_type = cache_ids[identifier]  # noqa: E501
    size = 0
    if shared_type == SHARED_MEMORY_TAG:
        existing_shm = SharedMemory(name=obj_id)
        size = len(existing_shm.buf)
        output = np.ndarray(obj_shape, dtype=obj_d_type, buffer=existing_shm.buf)    # noqa: E501
    elif shared_type == SHAREABLE_LIST_TAG:
        existing_shm = ShareableList(name=obj_id)
        size = len(existing_shm.shm.buf)
        output = list(existing_shm)
    elif shared_type == SHAREABLE_TUPLE_TAG:
        existing_shm = ShareableList(name=obj_id)
        size = len(existing_shm.shm.buf)
        output = tuple(existing_shm)
    # Currently unsupported since conversion requires lists of lists.
    # elif shared_type == SHAREABLE_DICT_TAG:
    #     existing_shm = ShareableList(name=obj_id)
    #     output = dict(existing_shm)
    else:
        raise PyCOMPSsException("Unknown cacheable type.")
    if __debug__:
        logger.debug(HEADER + "Retrieved: " + str(identifier))
    emit_manual_event_explicit(TASK_EVENTS_DESERIALIZE_SIZE_CACHE, size)
    cache_ids[identifier][4] = obj_hits + 1
    return output, existing_shm


def insert_object_into_cache_wrapper(logger, cache_queue, obj, f_name):  # noqa
    # type: (..., ..., ..., ...) -> None
    """ Put an object into cache filter to avoid event emission when not
    supported.

    :param logger: Logger where to push messages.
    :param cache_queue: Cache notification queue.
    :param obj: Object to store.
    :param f_name: File name that corresponds to the object (used as id).
    :return: None
    """
    if np and cache_queue is not None and ((isinstance(obj, np.ndarray)
                                            and not obj.dtype == object)
                                           or isinstance(obj, list)
                                           or isinstance(obj, tuple)
                                           or isinstance(obj, dict)):
        insert_object_into_cache(logger, cache_queue, obj, f_name)


@emit_event(INSERT_OBJECT_INTO_CACHE_EVENT, master=False, inside=True)
def insert_object_into_cache(logger, cache_queue, obj, f_name):  # noqa
    # type: (..., ..., ..., ...) -> None
    """ Put an object into cache.

    :param logger: Logger where to push messages.
    :param cache_queue: Cache notification queue.
    :param obj: Object to store.
    :param f_name: File name that corresponds to the object (used as id).
    :return: None
    """
    f_name = __get_file_name__(f_name)
    if __debug__:
        logger.debug(HEADER + "Inserting into cache (%s): %s" %
                     (str(type(obj)), str(f_name)))
    try:
        inserted = True
        if isinstance(obj, np.ndarray):
            emit_manual_event_explicit(TASK_EVENTS_SERIALIZE_SIZE_CACHE, 0)
            shape = obj.shape
            d_type = obj.dtype
            size = obj.nbytes
            shm = SHARED_MEMORY_MANAGER.SharedMemory(size=size)  # noqa
            within_cache = np.ndarray(shape, dtype=d_type, buffer=shm.buf)
            within_cache[:] = obj[:]  # Copy contents
            new_cache_id = shm.name
            cache_queue.put(("PUT", (f_name, new_cache_id, shape, d_type, size, SHARED_MEMORY_TAG)))  # noqa: E501
        elif isinstance(obj, list):
            emit_manual_event_explicit(TASK_EVENTS_SERIALIZE_SIZE_CACHE, 0)
            sl = SHARED_MEMORY_MANAGER.ShareableList(obj)  # noqa
            new_cache_id = sl.shm.name
            size = total_sizeof(obj)
            cache_queue.put(("PUT", (f_name, new_cache_id, 0, 0, size, SHAREABLE_LIST_TAG)))  # noqa: E501
        elif isinstance(obj, tuple):
            emit_manual_event_explicit(TASK_EVENTS_SERIALIZE_SIZE_CACHE, 0)
            sl = SHARED_MEMORY_MANAGER.ShareableList(obj)  # noqa
            new_cache_id = sl.shm.name
            size = total_sizeof(obj)
            cache_queue.put(("PUT", (f_name, new_cache_id, 0, 0, size, SHAREABLE_TUPLE_TAG)))  # noqa: E501
        # Unsupported dicts since they are lists of lists when converted.
        # elif isinstance(obj, dict):
        #     # Convert dict to list of tuples
        #     list_tuples = list(zip(obj.keys(), obj.values()))
        #     sl = SHARED_MEMORY_MANAGER.ShareableList(list_tuples)  # noqa
        #     new_cache_id = sl.shm.name
        #     size = total_sizeof(obj)
        #     cache_queue.put(("PUT", (f_name, new_cache_id, 0, 0, size, SHAREABLE_DICT_TAG)))  # noqa: E501
        else:
            inserted = False
            if __debug__:
                logger.debug(HEADER + "Can not put into cache: Not a [np.ndarray | list | tuple ] object")  # noqa: E501
        if inserted:
            emit_manual_event_explicit(TASK_EVENTS_SERIALIZE_SIZE_CACHE, size)
        if __debug__ and inserted:
            logger.debug(HEADER + "Inserted into cache: " + str(f_name) + " as " + str(new_cache_id))  # noqa: E501
    except KeyError as e:  # noqa
        if __debug__:
            logger.debug(HEADER + "Can not put into cache. It may be a [np.ndarray | list | tuple ] object containing an unsupported type")  # noqa: E501
            logger.debug(str(e))


@emit_event(REMOVE_OBJECT_FROM_CACHE_EVENT, master=False, inside=True)
def remove_object_from_cache(logger, cache_queue, f_name):  # noqa
    # type: (..., ..., ...) -> None
    """ Removes an object from cache.

    :param logger: Logger where to push messages.
    :param cache_queue: Cache notification queue.
    :param f_name: File name that corresponds to the object (used as id).
    :return: None
    """
    f_name = __get_file_name__(f_name)
    if __debug__:
        logger.debug(HEADER + "Removing from cache: " + str(f_name))
    cache_queue.put(("REMOVE", f_name))
    if __debug__:
        logger.debug(HEADER + "Removed from cache: " + str(f_name))


def replace_object_into_cache(logger, cache_queue, obj, f_name):  # noqa
    # type: (..., ..., ..., ...) -> None
    """ Put an object into cache.

    :param logger: Logger where to push messages.
    :param cache_queue: Cache notification queue.
    :param obj: Object to store.
    :param f_name: File name that corresponds to the object (used as id).
    :return: None
    """
    f_name = __get_file_name__(f_name)
    if __debug__:
        logger.debug(HEADER + "Replacing from cache: " + str(f_name))
    remove_object_from_cache(logger, cache_queue, f_name)
    insert_object_into_cache(logger, cache_queue, obj, f_name)
    if __debug__:
        logger.debug(HEADER + "Replaced from cache: " + str(f_name))


def in_cache(f_name, cache):
    # type: (str, dict) -> bool
    """ Checks if the given file name is in the cache

    :param f_name: Absolute file name.
    :param cache: Proxy dictionary cache.
    :return: True if in. False otherwise.
    """
    if cache:
        f_name = __get_file_name__(f_name)
        return f_name in cache
    else:
        return False


def __get_file_name__(f_name):
    # type: (str) -> str
    """ Convert a full path with file name to the file name (removes the path).
    Example: /a/b/c.py -> c.py

    :param f_name: Absolute file name path
    :return: File name
    """
    return os.path.basename(f_name)
