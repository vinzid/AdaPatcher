import os
import json
import subprocess
import re
import argparse
from tqdm import tqdm

from codeTool.utlis.utils import save_data_to_json


def read_json(json_name):
    with open(json_name, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# data2 should be a dictionary, each dictionary holds the code snippet
def save_temp_file(data1,data2,id,compare_file):

    submission1_id=data1["submission1_id"]
    code1 = data1["code1"].strip()
    if 'code_content' in data2:
        code2 = data2['code_content'].strip()
    else:
        print("Key 'code_content' not found in data2")
        code2 = None  
    #A file is generated under the current directory to store code1 and code2 for easy comparison
    base_dir=compare_file
    #Name of the saved file
    submission_dir = os.path.join(base_dir, f'{id}_{submission1_id}')
    os.makedirs(submission_dir, exist_ok=True)

    # Create file name
    code1_filename = os.path.join(submission_dir, f'{id}_{submission1_id}_code1.py')
    code2_filename = os.path.join(submission_dir, f'{id}_{submission1_id}_code2.py')
    # Write code1 to a file
    with open(code1_filename, 'w') as code1_file:
        code1_file.write(code1)
        # In order to solve the problem of "\ No newline at end of file" when diff
        code1_file.write('\n')
    
    # Write code2 to a file
    with open(code2_filename, 'w') as code2_file:
        code2_file.write(code2)
        # In order to solve the problem of "\ No newline at end of file" when diff
        code2_file.write('\n')
    
    return code1_filename, code2_filename

def process_diff_file(input_file, output_file, new_indicator="+", old_indicator="-"):
    # Open input and output files
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        added_line_written = False

        """
        The first four lines are the header information of the git diff and do not need to be processed.
        """
        for _ in range(4):
            next(infile)

        for line in infile:
            #  If the line begins with "+++", it is written directly to the output file
            if line.startswith("+++"):
                outfile.write(line)
                continue
            
            # If the line starts with @@, it is skipped
            if line.startswith("@@"):
                continue
            
            # Process the new rows
            if line.startswith(new_indicator):
                if not added_line_written:
                    # outfile.write(new_indicator + '\n')
                    outfile.write('<+>' + '\n')
                    added_line_written = True

            # Process deleted rows
            elif line.startswith(old_indicator):
                continue
            # The rest of the rows remain the same
            else:
                outfile.write(line)
                added_line_written = False



# Gets the number of rows added and deleted
def add_empty_line_to_file(filename):
    with open(filename, 'a') as file:
        file.write('\n')

def remove_last_empty_line(file_path):
    """
    Open the file and delete the last blank line (if it exists)
    :param file_path: indicates the file path
    """
    try:
        with open(file_path, 'r+', encoding='utf-8') as file:
            lines = file.readlines()
            if not lines:
                print("The file is empty.")
                return
            
            # Check whether the last line is empty
            if lines[-1].strip() == '':
                lines = lines[:-1]
            
            file.seek(0)
            file.truncate()
            file.writelines(lines)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except IOError as e:
        print(f"Error reading/writing file '{file_path}': {e}")
       
def get_diff_stats(code1_filename, code2_filename):
    code1_filename = os.path.abspath(code1_filename)
    code2_filename = os.path.abspath(code2_filename)

    add_empty_line_to_file(code1_filename)
    add_empty_line_to_file(code2_filename)

    result = subprocess.run(
        ['git', 'diff', '--no-index', '--shortstat', code1_filename, code2_filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output = result.stdout.strip()
    
    # Use regular expressions to parse the number of rows added and deleted
    insertions = re.search(r'(\d+) insertions?\(\+\)', output)
    deletions = re.search(r'(\d+) deletions?\(-\)', output)
    
    # If the match is successful, the number is extracted, otherwise it is set to 0
    added_lines = int(insertions.group(1)) if insertions else 0
    removed_lines = int(deletions.group(1)) if deletions else 0
    
    remove_last_empty_line(code1_filename)
    remove_last_empty_line(code2_filename)

    return added_lines, removed_lines

def get_file_line_count(file_path):
    """
    Counts the number of rows in a file
    :param file_path: indicates the file path
    :return: indicates the number of lines in the file. If the file does not exist or fails to be read, 0 is returned.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            return len(lines)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return 0
    except IOError as e:
        print(f"Error reading file '{file_path}': {e}")
        return 0


def compute_code_lines(data1,data2,output_file,compare_file):
    result=[]
    i = 0
    for entry in tqdm(data1):
        submission1_id=entry["submission1_id"]
        data3= next((item for item in data2 if item["submission1_id"] == submission1_id),None)
        code1_filename, code2_filename = save_temp_file(data1=entry, data2=data3,id=i+1,compare_file=compare_file)
        added_lines,removed_lines= get_diff_stats(code1_filename, code2_filename)
        data={}
        data["now_id"]=i+1
        data["user_id"]=data3["user_id"]
        data["problem_id"]=data3["problem_id"]
        data["submission1_id"]=data3["submission1_id"]
        data["code_content"]=data3["code_content"]
        data["origin_generated_text"]=data3["origin_generated_text"]
        data["code_test_status"]=data3["code_test_status"]
        data["code_test_score"]=data3["code_test_score"]
        data["TotalScore"]=data3["TotalScore"]
        if "flag" in data3:
            data["flag"]=data3["flag"]
        data["removed_lines"]=removed_lines
        data["added_lines"]=added_lines
        code1_lines = get_file_line_count(code1_filename)
        data["code1_lines"]=code1_lines
        result.append(data)
        i += 1
    save_data_to_json(result, output_file)
    return 0

if __name__ == '__main__':
    
    parser=argparse.ArgumentParser(description="Compute the retention rate of code1 to another code.")
    parser.add_argument('--code1',type=str,required=False,default="./repairDataset/CRFLPDataset/test.json",help="the filename of source code(list)")
    parser.add_argument('--code2',type=str,required=False,default="./predict_evalResult_dir/baseline/baseline/Exec_baseline_result.json",help="the filename of new code(list)")
    parser.add_argument('--output_file',type=str,required=False,default="./predict_evalResult_dir/baseline/baseline/Exec_code1_baseline_result.json",help="the filename of result code1->code2")
    parser.add_argument('--compare_file',type=str,required=False,default="./compare_code1",help="the file of comparing code1 and code2")
    parser.add_argument('--add_flag',type=bool,required=False,default=False,help="the file of comparing code1 and code2")
    
    
    args=parser.parse_args()
    json_name1 = args.code1
    data1 = read_json(json_name1)
    
    json_name2 = args.code2
    data2 = read_json(json_name2)

    compute_code_lines(data1,data2,args.output_file,args.compare_file)

    
    

