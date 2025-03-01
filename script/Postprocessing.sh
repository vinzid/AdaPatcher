DATA_dir="Claude"
File_name="Exec_woSDLccl_repair.json" 
Pattern="test"
predict_path="./predict_evalResult_dir/$DATA_dir/retention_rate_dir/$File_name"
python -m Eval.Code_Lines_compute \
    --code1 "./repairDataset/RepairData-PythonLevel/CRFLPDataset/$Pattern.json"\
    --code2 "./predict_evalResult_dir/$DATA_dir/$File_name"\
    --output_file "$predict_path"\
    --compare_file "./comparebaseline"

python -m Eval.Statistical_Execution_Results\
    --file_path "$predict_path"\
    --eval_pattern "$Pattern"\
    --second_eval_pattern "dev_3"