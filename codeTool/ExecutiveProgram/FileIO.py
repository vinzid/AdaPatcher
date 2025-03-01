import os
import re
import multiprocessing
from multiprocessing import Manager, Lock
# `Manager().dict()` provides a shared dictionary that allows safe storage and access to a singleton instance across multiple processes.
# The `Lock` ensures that only one process can modify the shared dictionary at a time, thus preventing race conditions.
# When using `multiprocessing.Manager` and `Lock` to implement the singleton pattern in a multi-process environment, `_instances` and `_lock` need to be initialized in the main process.
# The reason is that shared objects created by `multiprocessing.Manager` (such as `Manager().dict()`) and `multiprocessing.Lock` must be created in the main process so they can be shared between child processes.
# If these objects are not initialized in the main process, it may lead to issues where child processes cannot correctly share them.
# However, you can provide an initialization method in the class definition to initialize these shared objects, and then call this method in the main program to perform the initialization.
# This approach can make the code clearer and ensure that `_instances` and `_lock` are properly initialized in the main process.
class FileHandlerSingleton:
    # The singleton instance filename used to store each filename corresponds to a class entity （P0010)
    _instances = None  # Used to store singleton instances for each file name
    _lock = None  # Lock object, used for interprocess synchronization

    @classmethod
    def initialize(cls):
        if cls._instances is None or cls._lock is None:
            manager = Manager()
            cls._instances = manager.dict()
            cls._lock = Lock()

    def __new__(cls, directory):
        abs_directory = os.path.abspath(directory)  # Gets the absolute path to the directory
        with cls._lock:
            if abs_directory not in cls._instances:
                instance = super(FileHandlerSingleton, cls).__new__(cls)
                instance.directory = abs_directory
                instance.input_files, instance.output_files = cls.read_text_files(abs_directory)
                # Store simple data structures instead of entire instances
                cls._instances[abs_directory] = {
                    'directory': abs_directory,
                    'input_files': instance.input_files,
                    'output_files': instance.output_files
                }
        return cls._instances[abs_directory]

    def __init__(self, directory):
        with self._lock:
            if not hasattr(self, 'initialized'):
                self.directory = os.path.abspath(directory)  # Gets the absolute path to the directory
                self.input_files, self.output_files = self.read_text_files(self.directory)
                self.initialized = True

    @staticmethod
    def read_text_files(directory):
        input_files = {}
        output_files = {}
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory {directory} does not exist")

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            match = re.match(r'(input|output)\.(\d+)\.txt', filename)
            if match:
                file_type, index = match.groups()
                with open(file_path, 'r') as file:
                    if file_type == 'input':
                        input_files[int(index)] = file.read()
                    elif file_type == 'output':
                        output_files[int(index)] = file.read()

        # Keystrokes sort and convert to an ordered dictionary
        input_files = dict(sorted(input_files.items()))
        output_files = dict(sorted(output_files.items()))

        return input_files, output_files

    def get_input_files(self):
        return self.input_files

    def get_output_files(self):
        return self.output_files

def process_function(directory):
    instance_info = FileHandlerSingleton(directory)
    print("Input Files:")
    print(instance_info['input_files'])
    print("Output Files:")
    print(instance_info['output_files'])

if __name__ == '__main__':
    # Example Initialize the shared object
    FileHandlerSingleton.initialize()

    # Confirm the working directory and path
    test_directory = '/home/develop/dzl/CodeFixProject/CodeDatasets/merged_test_cases/p03391'
    if not os.path.exists(test_directory):
        raise FileNotFoundError(f"Directory {test_directory} does not exist")

    # Create multiple processes
    processes = []
    for i in range(2):  # Test with 2 processes
        p = multiprocessing.Process(target=process_function, args=(test_directory,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

