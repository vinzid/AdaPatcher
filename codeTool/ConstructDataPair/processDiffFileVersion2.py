import os
import json
import subprocess
import re

# Check whether the specified path is a git repository
def check_git_repo(path):
    try:
        result = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0 and result.stdout.strip() == 'true'
    except Exception as e:
        return False

def read_json(json_name):
    # Read the JSON data of the user code
    with open(json_name, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# It is used to process two commits of code from a user, saved to a temporary python file
def save_temp_file(entry, output='output'):
    user_id = entry['user_id']
    problem_id = entry['problem_id']
    
    code1 = entry['code1']
    code2 = entry['code2']

    os.makedirs(f"{output}/{problem_id}", exist_ok=True)
    
    # Create file name
    code1_filename = os.path.join(f"{output}/{problem_id}", f'{user_id}_{problem_id}_code1.py')
    code2_filename = os.path.join(f"{output}/{problem_id}", f'{user_id}_{problem_id}_code2.py')
    
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
    
    print(f'************Saved {user_id} code1 to {code1_filename}************')
    print(f'************Saved {user_id} code2 to {code2_filename}************')

    return code1_filename, code2_filename

# Used to compare two files
def git_diff_file(code1_filename, code2_filename, output='output_txt', output_indicator_new='+', output_indicator_old='-'):
    # Make sure the output folder exists
    os.makedirs(output, exist_ok=True)
    
    # Ensure that all directory names in the path are relative or full paths
    code1_filename = os.path.abspath(code1_filename)
    code2_filename = os.path.abspath(code2_filename)
    output = os.path.abspath(output)
    
    # Add two files to the git repository
    subprocess.run(['git', 'add', code1_filename], cwd=output)
    subprocess.run(['git', 'add', code2_filename], cwd=output)
    subprocess.run(['git', 'commit', '-m', f'Add {code1_filename} and {code2_filename}'], cwd=output, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Clear the staging area
    # subprocess.run(['git', 'restore', '--staged', '.'], cwd=output)

    # Create the problem ID folder
    user_id = code1_filename.split('/')[-1].split('_')[0]
    problem_id = code1_filename.split('/')[-1].split('_')[1]
    problem_output_dir = os.path.join(output, problem_id)
    os.makedirs(problem_output_dir, exist_ok=True)
    
    # Output file path
    output_filename = os.path.join(problem_output_dir, f'{user_id}_{problem_id}.txt')
    
    # Construct the git diff command
    git_diff_command = [
        'git', 'diff', '--unified=1024', '--no-index', code1_filename, code2_filename,
        f'--output-indicator-new={output_indicator_new}',
        f'--output-indicator-old={output_indicator_old}'
    ]
    
    # Execute git diff commands and process the output through sed
    sed_command = "sed 's/^\(@@.*@@\) /\\1\\n/'"
    
    # Execute the command chain and write the results to a file
    with open(output_filename, 'w') as output_file:
        process1 = subprocess.Popen(git_diff_command, stdout=subprocess.PIPE, cwd=output)
        process2 = subprocess.Popen(sed_command, stdin=process1.stdout, stdout=output_file, shell=True)
        process1.stdout.close()  # Allows process1 to receive SIGPIPE signals
        process2.communicate()
    
    return output_filename    

def process_diff_file(input_file, output_file, new_indicator="+", old_indicator="-"):
    # Open input and output files
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        added_line_written = False

        # Skip the first four lines
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

# Processing file
def dispose_file(data, output='output', output_indicator_new='+', output_indicator_old='-'):
    # Gets the absolute path to the output directory
    output = os.path.abspath(output)
    os.makedirs(output, exist_ok=True)

    # Check whether the output directory is a git repository
    if not check_git_repo(output):
        subprocess.run(['git', 'init'], cwd=output)
        current_file_path = __file__
        current_file_name = os.path.basename(current_file_path)
        destination_path = os.path.join(output, current_file_name)
        with open(current_file_path, 'r') as source_file:
            with open(destination_path, 'w') as dest_file:
                dest_file.write(source_file.read())
        subprocess.run(['git', 'add', current_file_name], cwd=output)
        subprocess.run(['git', 'commit', '-m', 'Initialize repository'], cwd=output)

    # Process each file, comparing code1 and code2
    for i, entry in enumerate(data):
        # Convert to a python file first
        code1_filename, code2_filename = save_temp_file(entry=entry, output=output)
        problem_id = entry["problem_id"]
        # Get the file after diff
        output_filename = git_diff_file(code1_filename=code1_filename, code2_filename=code2_filename, output=f"{output}/output_txt", output_indicator_new=output_indicator_new, output_indicator_old=output_indicator_old)
        # Process files after diff
        final_output_filename = os.path.join(output, problem_id, f'{output_filename.split("/")[-1].split(".")[0]}_processed.txt')
        process_diff_file(input_file=output_filename, output_file=final_output_filename, new_indicator=output_indicator_new, old_indicator=output_indicator_old)
        subprocess.run(['git', 'rm', code1_filename], cwd=output)
        subprocess.run(['git', 'rm', code2_filename], cwd=output)
        subprocess.run(['git', 'commit', '-m', f'Remove {code1_filename} and {code2_filename}'], cwd=output)

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
    :return: indicates the number of lines in the file. If the file does not exist or fails to be read, 0 is returned
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

if __name__ == '__main__':
    # Read json file
    json_name = 'test.json'
    data = read_json(json_name)
    # Processing file
    dispose_file(data, output='output', output_indicator_old='-', output_indicator_new='+')
    # Test get_diff_stats() to see how many rows are added and deleted
    added_lines,removed_lines= get_diff_stats('test1.py', 'test2.py')
    print(f'Added lines: {added_lines}')
    print(f'Removed lines: {removed_lines}')
    # Test get_file_line_count() to see how many lines the file has
    line = get_file_line_count('test1.py')
    print(line)


