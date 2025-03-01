import os
import json
import hashlib
import re
def remove_comments(code):
    """
    Remove comments from code, including single-line comments and multi-line comments
    :param code: Code string containing comments
    :return: The code string after the comment is removed
    """
    single_line_comment_pattern = r'//.*?$|#.*?$'
    multi_line_comment_pattern = r'/\*.*?\*/|\'\'\'.*?\'\'\'|""".*?"""'
    
    pattern = re.compile(
        single_line_comment_pattern + '|' + multi_line_comment_pattern,
        re.DOTALL | re.MULTILINE
    )

    cleaned_code = re.sub(pattern, '', code)
    
    return cleaned_code

def calculate_md5(input_string):
    """
    Calculates and returns the MD5 hash of a string

    Parameters:
    input_string (str): The string for which the MD5 hash value is to be calculated

    Back:
    str: Enter the MD5 hash value of the string
    """
    # Creates an md5 hash object
    md5_hash = hashlib.md5()
    
    # Update the hash object and calculate the hash value
    md5_hash.update(input_string.encode('utf-8'))
    
    # Returns a hexadecimal hash value
    return md5_hash.hexdigest()

def check_catalogue_exists(filepath):
    """
    Check whether the file in the specified path exists.

    Parameters:
    filepath (str): The filepath to check.

    Back:
    bool: True if the file exists. Otherwise, return False.
    """
    return  os.path.exists(filepath)


def check_file_exists(filepath):
    """
    Check whether the file in the specified path exists.

    Parameters:
    filepath (str): The filepath to check.

    Back:
    bool: True if the file exists. Otherwise, return False.
    """
    return  os.path.isfile(filepath)

def read_python_file(file_path):
    """Reads the Python file in the specified path and returns its contents"""
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def write_file_content_to_json(content, json_path):
    """Writes the content to a JSON file in the specified path"""
    data = {'file_content': content}
    with open(json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def load_list_from_json(input_file_path):
        """Read the list from the JSON file"""
        with open(input_file_path, 'r') as json_file:
            data_list = json.load(json_file)
        return data_list
    
def save_list_to_json(lst, filepath):
    """
    Store the list in a JSON file in the specified path.

    Parameters:
    lst (list): list to be stored.
    filepath (str): specifies the path to save the JSON file.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as json_file:
            json.dump(lst, json_file, ensure_ascii=False, indent=4)
        #print(f"The list was successfully saved to {filepath}")
    except Exception as e:
        print(f"Error saving list: {e}")


class CustomJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        return self.encode_dict(obj)
        

    def encode_dict(self, obj):   
        items = []
        for key, value in obj.items():
            item = f'        "{key}": {json.dumps(value, ensure_ascii=False)}'
            items.append(item)
        return '    {\n' + ',\n'.join(items) + '\n    }'

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory {directory} was created.")
    else:
        print(f"Directory {directory} already exists.")

def save_data_to_json(data, filepath):
    """
    Store the data in a JSON file in the specified path, ensuring that certain list fields are not wrapped and other fields are wrapped.

    Parameters:
    data (list): List data to be stored.
    filepath (str): specifies the path to save the JSON file.
    """
    try:
        ensure_dir(filepath)
        with open(filepath, 'w', encoding='utf-8') as json_file:
            json_file.write('[\n')
            for i, element in enumerate(data):
                json_file.write(CustomJSONEncoder().encode(element))
                if i < len(data) - 1:
                    json_file.write(',\n')
            json_file.write('\n]')
        print(f"Data was successfully saved to {filepath}")
    except Exception as e:
        print(f"Error saving data: {e}")

def File2String(file_path, json_output_path):
    
    # Make sure the output directory exists, or create one if it does not
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)

    content = read_python_file(python_file_path)
    print(content)
    write_file_content_to_json(content, json_output_path)
    print("writing")
if __name__ == '__main__':
    print("here")
    # Specifies the Python file path
    python_file_path = '/home/develop/dzl/CodeFixProject/CodeTool/ConstructDataPair/test2.py'
    # Specifies the path to the output JSON file
    json_output_path = '/home/develop/dzl/CodeFixProject/CodeTool/utlis/out_file/CodeString.json'
    
    File2String(python_file_path ,json_output_path)
    
   

    