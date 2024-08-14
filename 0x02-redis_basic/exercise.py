#!/usr/bin/env python3
"""Using the Redis NoSQL data storage.
"""
import uuid
import redis
from functools import wraps
from typing import Any, Union, Callable, Optional


def count_calls(method: Callable) -> Callable:
    '''Tracks the number of calls made to a method in a Cache class.

    Args:
        method (Callable): The method to track the number of calls.

    Returns:
        Callable: The wrapped method.
    '''
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        '''Invokes the given method after incrementing its call counter.

        Args:
            self: The instance of the class.
            *args: Positional arguments passed to the method.
            **kwargs: Keyword arguments passed to the method.

        Returns:
            Any: The result of the method call.
        '''
        if isinstance(self._redis, redis.Redis):
            self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return invoker


def call_history(method: Callable) -> Callable:
    """Tracks the call details of a method in a Cache class.
    """
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        """Returns the method's output after storing its inputs and output.
        """
        # Creates keys for input and output storage
        key_inp = '{}:inputs'.format(method.__qualname__)
        key_outp = '{}:outputs'.format(method.__qualname__)

        # Store input in redis
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(key_inp, str(args))

        # Calls the method and stores its output
        output = method(self, *args, **kwargs)

        # Stores output in Redis
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(key_outp, output)

        return output
    return invoker


class Cache:
    """
    A class that stores and retrieves data from Redis using UUIDs as keys.

    Attributes:
        self._redis (redis.Redis): A Redis client instance.

    Methods:
        __init__(): Initializes a Redis client instance and clear database.
        store(data): Store the data in Redis with a UUID key and
        return the key.
    """

    def __init__(self):
        """
        Initializes a Redis client instance and clear the database.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Stores data in Redis with a UUID key and return the unique key.

        Args:
            data: Data to be stored. Can be a string, bytes, int, or float.

        Returns:
            str: The UUID/unique key used to store the data.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(
        self,
        key: str,
        fn: Optional[Callable[[Any], Union[str, bytes, int, float]]] = None
            ) -> Optional[Union[str, bytes, int, float]]:
        """
        Retrieves a value from a Redis data storage.

        Args:
            key: The key of the data to be retrieved.
            fn: An optional function to apply to the retrieved data.

        Returns:
            The retrieved data, optionally transformed by the function.
        """
        # Retrieve the data from Redis
        data = self._redis.get(key)

        # Apply the function to the data (if provided)
        return fn(data) if fn is not None else data

    def get_str(self, key: str) -> Optional[str]:
        """Retrieve a string value from Redis based on the given key.

            Args:
                key: The key to retrieve the string value from Redis.

            Returns:
                The retrieved string value.
        """
        # Retrievee  data using get() method
        data = self.get(key)

        # checks if data is None
        if data is None:
            return None

        # Converts data to sring and returns it
        return str(data)


def get_int(self, key: str) -> Optional[int]:
    """
    Retrieves an int value from a Redis data base.

    Args:
        key: The unique key of the data to be retrieved.

    Returns:
        The retrieved value of type int.
    """
    # Retrieves  data using the get() method.
    data = self.get(key)

    # Checks if data is None.
    if data is None:
        return None

    # Converts to int and return
    return int(data)


def replay(fn: Callable) -> None:
    """display the history of calls of a particular function.
    """
    if fn is None or not hasattr(fn, '__self__'):
        return
    r_storage = getattr(fn.__self__, '_redis', None)
    if not isinstance(r_storage, redis.Redis):
        return
    func_name = fn.__qualname__
    in_key = '{}:inputs'.format(func_name)
    out_key = '{}:outputs'.format(func_name)
    func_call_count = 0
    if r_storage.exists(func_name) != 0:
        func_call_count = int(r_storage.get(func_name) or 0)
    print('{} was called {} times:'.format(func_name, func_call_count))
    func_inputs = r_storage.lrange(in_key, 0, -1)
    func_outputs = r_storage.lrange(out_key, 0, -1)
    for func_input, func_output in zip(func_inputs, func_outputs):
        print('{}(*{}) -> {}'.format(
            func_name,
            func_input.decode("utf-8"),
            func_output.decode(
                "utf-8") if isinstance(func_output, bytes) else func_output,
        ))
