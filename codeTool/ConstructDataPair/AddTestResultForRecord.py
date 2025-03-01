#from ExecutiveProgram.ExecRestRequest import APIManager
from ExecutiveProgram.FileIO import FileHandlerSingleton 
from ExecutiveProgram.Worker import Checker, Worker, Program_Submission, Quesion_Test_Point_objectList
from utlis.utils import load_list_from_json, save_list_to_json, save_data_to_json
from tqdm import tqdm
class RecordProcess:
    def __init__(self, Available_Record_PId_path = "/home/develop/dzl/CodeFixProject/CodeFixDatasets/CodeFixPairData/PythonStatistics/Available_PId.json",\
        Read_prefix_url = "/home/develop/dzl/CodeFixProject/CodeFixDatasets/CodeFixPairData/PythonData/",\
        test_directory_prefix_url = '/home/develop/dzl/CodeFixProject/CodeDatasets/merged_test_cases/',\
        Write_prefix_url = "/home/develop/dzl/CodeFixDatasets/CodeFixPairData/PythonResultData/",\
        language = "Python"):
        self.Available_Record_PId_path = Available_Record_PId_path
        self.Read_prefix_url = Read_prefix_url
        self.Write_prefix_url = Write_prefix_url
        self.test_directory_prefix_url = test_directory_prefix_url
        self.language = language
        self.worker = Worker()
        self.checker = Checker()
        self.Available_PId_List = load_list_from_json(self.Available_Record_PId_path)
        FileHandlerSingleton.initialize()     # Example Initialize a file sharing object
    def JudgeWrongResultStatus(self, Psubmit, item):

        if Psubmit.ResultStatus == item["status1"]:
            TotalScore = len(Psubmit.CheckRunResultList)
            # Define the mapping of results to scores
            result_mapping = {
                'Accepted': 1,
                'Time Limit Exceeded': -1,
                'Wrong Answer': 0
            }
            
            # Transform using maps
            CheckRunResultList = [result_mapping[result] for result in Psubmit.CheckRunResultList]
            # Calculating the Score
            Score = CheckRunResultList.count(1)
            item["code1_test_status"] = CheckRunResultList
            item["code1_test_score"] = Score
            item["TotalScore"] = TotalScore
            return True
        else:
            return False
    
    def JudgeACResultStatus(self, Psubmit):
        if Psubmit.ResultStatus == "Accepted":
            return True
        else:
            return False
    
    def Process_For_Single_RecordJson(self, Pid):

        #Read and write json positions
        Read_prefix_path = self.Read_prefix_url + f"p{Pid}.json"
        Write_prefix_path = self.Write_prefix_url + f"p{Pid}.json"
        #reading P{PId}.json object 
        ProcessDataList = load_list_from_json(Read_prefix_path)
        #reading test case file
        test_directory_path = self.test_directory_prefix_url + f"p{Pid}"
        #instance_info = FileHandlerSingleton(test_directory_path)
        Test_List = Quesion_Test_Point_objectList()
        Test_List.inint_Tlist_by_FileHandlerSingleton(FileDirectory=test_directory_path)
        # print(instance_info['input_files'])
        # print("Output Files:")
        # print(instance_info['output_files'])
        
        ResultDataList = []
        Wrong2AC_data_count = 0
        AC2Wrong_data_count = 0

        for item in ProcessDataList:
            #Each record is evaluated to get the returned object
            #Puts the returned object selection element into the result  
            #"code1_test_status": [],
            #"code1_test_score": 0
            if item["status1"] == "Time Limit Exceeded": continue
            
            #Run Code1 to fill in the result
            submission1_id = item["submission1_id"]
            Compile_File_name = f"{submission1_id}.py"
            CodeContent =  item["code1"]
            Psubmit = Program_Submission(Compile_File_name, CodeContent, self.language)
            self.worker.Run_Program_By_One_All_Point(Psubmit, Test_List, deBug = False)
            self.checker.Check_Run_Result(Psubmit, Test_List)
            flag = self.JudgeWrongResultStatus(Psubmit, item)
            if flag == False:
                Wrong2AC_data_count += 1
                continue
            #Verify the correctness of data
            submission2_id = item["submission2_id"]
            Compile_File_name = f"{submission2_id}.py"
            CodeContent =  item["code2"]
            Psubmit = Program_Submission(Compile_File_name, CodeContent, self.language)
            self.worker.Run_Program_By_One_All_Point(Psubmit, Test_List, deBug = False)
            self.checker.Check_Run_Result(Psubmit, Test_List)
            flag = self.JudgeACResultStatus(Psubmit)

            if flag == False:
                AC2Wrong_data_count += 1
                continue
            # print(Psubmit)
            # print(item["problem_id"])
            # print(len(Psubmit.CheckRunResultList))
            # Put data
            
            ResultDataList.append(item)

            
        save_data_to_json(ResultDataList, Write_prefix_path)
        
    def ProcessAllData(self):
        for Pid in tqdm(self.Available_PId_List, desc="Processing elements"):
            self.Process_For_Single_RecordJson(Pid)


if __name__ == "__main__":

    EXECUTION_ALL = True
    
    if EXECUTION_ALL == True:
        process = RecordProcess()
        process.ProcessAllData()