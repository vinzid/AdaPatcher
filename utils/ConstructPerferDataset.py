import json
from codeTool.utlis.utils import save_data_to_json
from tqdm import tqdm
from collections import defaultdict
import argparse
def mergeJsonByTag(Json1Path, Json2Path, tag_list, SavePath):

    with open(Json1Path, 'r') as f1:
        data1 = json.load(f1)

    with open(Json2Path, 'r') as f2:
        data2 = json.load(f2)

    data1_dict = {item['submission1_id']: item for item in data1}
    data2_dict = {item['submission1_id']: item for item in data2}

    # Iterate over each record in file 2 and insert the corresponding tag_list
    data_list = []
    print(f"before merge {len(data_list)}")
    for record in data2:
        record_id = record['submission1_id']
        if record_id in data1_dict:
            record_item = data1_dict[record_id].copy()
            record_item["FL_content"] = record['crp_content']
            record_item["submission1_id"] = record_id + "-FL"
            record_item["added_lines"] = 0
            record_item["removed_lines"] = 0
            data_list.append(record_item)
    print(f"after merge {len(data_list)}")
    save_data_to_json(data_list, SavePath)


def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def update_code2_values(source_json, target_json):
    source_dict = {record['submission1_id']: record['code2'] for record in source_json}
    
    for record in tqdm(target_json, desc="Updating records"):
        submission_id = record['submission1_id']
        if submission_id in source_dict:
            record['code2'] = source_dict[submission_id]
    
    return target_json
    

def mergeJson(Json1Path, Json2Path, SavePath):

    with open(Json1Path, 'r') as f1:
        data1 = json.load(f1)
    print(len(data1))
    with open(Json2Path, 'r') as f2:
        data2 = json.load(f2)
    print(len(data2))
    for item in data2:
        data1.append(item)
    print(len(data1))
    save_data_to_json(data1, SavePath)
    print(f"Filtering is complete and the result is saved to the {SavePath} file.")


def FiltRepeatPreferDataByTag(crflp_path, SavePath, Tag='crp_content'):
    with open(crflp_path, 'r') as f1:
        dataset_list= json.load(f1)
    print(len(dataset_list))
    #dataset_dict = {item['submission1_id']: item for item in dataset_list}

    grouped_data = defaultdict(list)
    
    # Group by submission1_id
    for d in dataset_list:
        SId = d['submission1_id'].split('-')[0]
        grouped_data[SId].append(d)
    
    filtered_list = []
    ONE_count = 0
    count = 0
    for group in grouped_data.values():
        seen_scontent = set()
        Count = 0
        for d in group:
            scontent = d[Tag]
            if scontent not in seen_scontent:
                seen_scontent.add(scontent)
                Count += 1
        vis_scontent = set()
        if Count == 1: 
            ONE_count += 1
            continue
        else:
            count +=1

        for d in group:
            scontent = d[Tag]
            if scontent not in vis_scontent:
                vis_scontent.add(scontent)
                filtered_list.append(d)
                
    print(f"ONE_count = {ONE_count}")
    print(f"count = {count}")
    print(len(filtered_list))
    save_data_to_json(filtered_list, SavePath)

def ConstructPreferDataset(dataset_path, FirstCRP_path, Exc_PerferDate_path, save_path):
    '''
    {
        "user_id": "u089142196",
        "problem_id": "p02607",
        "submission1_id": "s086035817",
        "input": "001 000\n",
        "actual_output": "Yes\n",
        "expected_output": "No\n\n",
        "anno_code": ["\na,b = map(int,input().split()) # (0): a=1, b=0\nx = a*len(str(b))+b # (1): x=1\nans = 'No' # (2): ans=No\nfor y in range(1000): # (3): y=0 (5): y=1\n    if x==y*y: # (4): NO CHANGE (6): NO CHANGE\n        ans = 'Yes' # (7): ans=Yes\n        break # (8): NO CHANGE\nprint(ans)"],
        "anno_status": [true],
        "crp_content": "\n \n \n N=int(input())\n a=list(map(int,input().split()))\n \n ans=0\n for i in range(N):\n-    if a[i]%2==1 and i%2==1:\n         ans +=1\n print(ans)\n",
        "crp_content2": "\n \n \n N=int(input())\n a=list(map(int,input().split()))\n \n ans=0\n for i in range(N):\n-    if a[i]%2==1 and i%2==1:\n         ans +=1\n print(ans)\n",
        "origin_generated_text": "\n```\n \n \n N=int(input())\n a=list(map(int,input().split()))\n \n ans=0\n for i in range(N):\n-    if a[i]%2==1 and i%2==1:\n         ans +=1\n print(ans)\n```\n "
    }
    '''
    with open(dataset_path, 'r') as f1:
        dataset_list= json.load(f1)
    
    with open(FirstCRP_path, 'r') as f1:
        FirstCRPData_list= json.load(f1)

    with open(Exc_PerferDate_path, 'r') as f1:
        PerferData_list= json.load(f1)
    dataset_dict = {item['submission1_id']: item for item in dataset_list}
    FirstCRPData_dict = {item['submission1_id']: item for item in FirstCRPData_list}

    print(len(dataset_list))

    grouped_data = defaultdict(list)
    
    #submission1_id 
    for d in PerferData_list:
        SId = d['submission1_id'].split('-')[0]
        grouped_data[SId].append(d)
    
    filtered_list = []
    count = 0

    for Sid, group in grouped_data.items():
  
        data = dataset_dict[Sid]

        code1_test_score = data['code1_test_score']
        max_score1 = -1
        min_score2 = 999
        max_idx = -1
        min_idx = -1
        for d in group:

            score = d['code_test_score']
            if score > max_score1:
                max_score1 = score
                max_idx = d['submission1_id']
            elif score <min_score2:
                min_score2 = score
                min_idx = d['submission1_id']
        if max_idx == min_idx or max_score1 == min_score2 or max_idx == -1 or min_score2 == 999: continue
        elif max_score1 < code1_test_score: continue
        else:
            data['crp_content'] = FirstCRPData_dict[max_idx]['crp_content']
            data['crp_content2'] = FirstCRPData_dict[min_idx]['crp_content']
            data['Chosen_score'] = max_score1
            data['Reject_score'] = min_score2
            count+=1
            filtered_list.append(data)

    save_data_to_json(filtered_list, save_path)

       
def splitDataset(input_path, trian_path, dev_path):
    with open(input_path, 'r') as f1:
        dataset_list= json.load(f1)
    train_data = dataset_list[:7000]
    dev_data = dataset_list[7000:-1]
    save_data_to_json(train_data, trian_path)
    save_data_to_json(dev_data, dev_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation Statistical Script")
    parser.add_argument('--data_path', type=str, default='./repairDataset/RepairData-PythonLevel/CRFLPDataset/train.json', required=False, help='eval data path')
    parser.add_argument('--PerferCRP_path', type=str, default='./predict_dir/loraWeight/trace_CRFLP_PerferData/checkpoint-14000_train-prefer-Filt.json', required=False, help='Input data ')
    parser.add_argument('--file_path', type=str, default='./predict_evalResult_dir/trace_CRFLP_PerferData/Exec_Prefer2SecondFixResult-Filt.json', required=False, help='Input data ')
    parser.add_argument('--save_path', type=str, default='./repairDataset/RepairData-PythonLevel/PreferDataset/train.json', required=False, help='Output data for evaluation')
    parser.add_argument('--train_path', type=str, default='./repairDataset/RepairData-PythonLevel/PreferDataset/train.json', required=False, help='Input data ')
    parser.add_argument('--dev_path', type=str, default='./repairDataset/RepairData-PythonLevel/PreferDataset/dev.json', required=False, help='Input data ')
    args = parser.parse_args()
    #FiltRepeatPreferData(args.file_path, args.save_path)
    #FiltRepeatPreferDataByTag(args.file_path, args.save_path,Tag='code_content')

    #ConstructPreferDataset(args.data_path, args.PerferCRP_path, args.file_path, args.save_path)

    #splitDataset(args.save_path, args.train_path, args.dev_path)