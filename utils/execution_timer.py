import time
from functools import wraps


def timeit(func):
    """
    A decorator that measures and prints the execution time of the decorated function.

    This decorator wraps the given function and measures the time it takes to execute,
    then prints the execution time in seconds.

    Parameters:
        func (callable): The function to be wrapped and timed.

    Returns:
        callable: The wrapped function with timing functionality.

    Example:
        @timeit
        def example_function():
            # Function code here
            pass

        # When example_function() is called, it will print the execution time:
        example_function()

        Output:
        Function example_function executed in 0.1234 seconds.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function {func.__name__} executed in {execution_time:.4f} seconds.")
        return result
    return wrapper

