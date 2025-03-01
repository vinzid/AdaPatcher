import requests
import json
import copy
# Destination URL prefix
url_prefix = 'http://127.0.0.1:5050/'
class APIManager: #Reentrant function
    def __init__(self, url_prefix):
        self.url_prefix = url_prefix
        # JSON data for POST requests
        self.CompileData = {
            "cmd": [{
                "args": ["python3", "-m", "py_compile" ,"pytest.py"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [{
                    "content": ""
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": 10000000000,
                "memoryLimit": 1048576000,
                "procLimit": 50,
                "copyIn": {
                    # "pytest.py": {
                    #     "content": "for i in range(int(input())):\n    x1, y1, x2, y2, x3, y3 = map(float, input().split())\n    c = (x1-x2)**2 + (y1-y2)**2\n    a = (x2-x3)**2 + (y2-y3)**2\n    b = (x3-x1)**2 + (y3-y1)**2\n    # 16s^2\n    s = 2*(a*b + b*c + c*a) - (a*a + b*b + c*c)\n\n    px = (a*(b+c-a)*x1 + b*(c+a-b)*x2 + c*(a+b-c)*x3) / s\n    py = (a*(b+c-a)*y1 + b*(c+a-b)*y2 + c*(a+b-c)*y3) / s\n\n    ar = a**0.5\n    br = b**0.5\n    cr = c**0.5\n\n    r = ar*br*cr / ((ar+br+cr)*(-ar+br+cr)*(ar-br+cr)*(ar+br-cr))**0.5\n\n    print(\"{:>.3f}\".format(px),\"{:>.3f}\".format(py),\"{:>.3f}\".format(r))"
                    # }
                },
                "copyOut": ["stdout", "stderr"],
                "copyOutCached": ["__pycache__/pytest.cpython-311.pyc"]
            }]
        }
        self.ExecutiveData = {
            "cmd": [{
                "args": ["/usr/bin/python3", "__pycache__/pytest.cpython-311.pyc"],
                "env": ["PATH=/usr/bin:/bin"],
                "files": [{
                    "content": "1\n0.0 0.0 2.0 0.5127281311709682 2.0 2.0"
                }, {
                    "name": "stdout",
                    "max": 10240
                }, {
                    "name": "stderr",
                    "max": 10240
                }],
                "cpuLimit": 1000000000,
                "memoryLimit": 104857600,
                "procLimit": 50,
                "copyIn": {
                    "__pycache__/pytest.cpython-311.pyc": {
                        "fileId": "BWO4DDB5"
                    }
                }
            }]
        }
        self.CopyIn_FileId_Dict = self.GET_File_Id_Dict()
        
    # Send a GET request to get the file ID SET
    def GET_File_Id_Dict(self, deBug = False):
        
        request_rul = self.url_prefix + f"file"
        response = requests.get(request_rul)
        data_dict = json.loads(response.text)
        if deBug == True:
            print('>>> GET Request Response:')
            print('>>> Status Code:', response.status_code) #200
            print('>>> Response Body:', response.text)
        return data_dict
    
    # Sends a DELETE request to delete the file with the specified FileId
    def Delete_File_By_Fileid(self, FileId):
        
        #print('\n>>> DELETE Request Response:')
        request_rul = self.url_prefix + f"file/{FileId}"
        response = requests.delete(request_rul)
        #print('>>> Status Code:', response.status_code) #200
    
    # Send a POST request for Post_Json_Text
    def send_post_request(self, Post_Json_Data, deBug = False):
        
        request_rul = self.url_prefix + f"run"
        response = requests.post(request_rul, json= Post_Json_Data)
        if deBug == True:
            print('\nPOST Request Response:')
            print('Status Code:', response.status_code)
            print('Response Body:', response.text)
        return response.text
    
    def Modify_Command_For_Compile_Program(self, new_args, code_content, language = "Python"):
        data_copy = copy.deepcopy(self.CompileData)
        
        if language == "Python":
            Execute_File_name = new_args[-1]
            # Modify args
            data_copy["cmd"][0]["args"] = new_args
            # Modify the contents of the copyIn file
            # If there is no "Execute_File_name" key, it is created
            data_copy["cmd"][0]["copyIn"][Execute_File_name] = {"content": code_content}
            Execute_File_name_without_type = Execute_File_name.split(".")[0]
            #print(Execute_File_name_without_type)
            data_copy["cmd"][0]["copyOutCached"] = [f"__pycache__/{Execute_File_name_without_type}.cpython-311.pyc"]
        else:
            Execute_File_name = "" # None
        return data_copy    
    
    def Modify_Command_For_Execute_Program(self, new_args, CopyIn_fileId, Execute_File_name, TestPoint_Content, language = "Python"):
        data_copy = copy.deepcopy(self.ExecutiveData)
        
        if language == "Python":
            Execute_File_name = new_args[-1]
            # Modify args
            data_copy["cmd"][0]["args"] = new_args
            # Modify the contents of the copyIn file
            # If there is no "Execute_File_name" key, it is created
            data_copy["cmd"][0]["files"][0]["content"] = TestPoint_Content
            data_copy["cmd"][0]["copyIn"] = {Execute_File_name:{"fileId": CopyIn_fileId}}
        else:
            Execute_File_name = "" # None
        return data_copy
    
    # Delete all cached files using Fileid
    def Delete_All_File(self, deBug = False):
        
        #Get Fileid
        Fileid_dict = self.GET_file_id_dict()
        #The call requests the deletion of the file corresponding to the Fileid.
        for k, v in Fileid_dict.items():
            if "pyc" not in v:
                self.Delete_file_by_fileid(k)   
        print(">>> Delete Success")
        
    # Deletes the specified cache file using Fileid
    def Delete_All_File_by_FileId(self, FileId, deBug = False): 
        self.Delete_file_by_fileid(FileId)   
        print(f">>> Delete FileId:{FileId} Success")
    
    # Compile the corresponding language CodeString
    # Return Result Jons(include status/fileIds)
    def Compile_Program(self, Execute_File_name, CodeContent, language = "Python"):
        #Construct the REST json data
        if language == "Python":
            new_args = ["python3", "-m", "py_compile" , f"{Execute_File_name}"]
            Post_Json_Data = self.Modify_Command_For_Compile_Program(new_args, CodeContent)
            Json_Text_response = self.send_post_request(Post_Json_Data)
        else:
            raise ValueError(">>> language value is wrong")
        
        return Json_Text_response
    
    
    # Execution program (compiled successfully by default)
    def Execute_Program_After_Compile(self, CopyIn_fileId, Execute_File_name, TestPoint_Content, language = "Python") :
        
        if language == "Python":
            # Construct the REST json data
            new_args = ["/usr/bin/python3", Execute_File_name]
            #Requests are sent based on Post_Json_Data
            Post_Json_Data = self.Modify_Command_For_Execute_Program(new_args, CopyIn_fileId, Execute_File_name, TestPoint_Content)
            #Request execution
            Json_Text_response = self.send_post_request(Post_Json_Data)
            #After all test points are executed, delete the corresponding cache file
            #self.Delete_All_File_by_FileId(CopyIn_fileId)    
        else:
            raise ValueError(">>> language value is wrong")
            
        return Json_Text_response


if __name__ == '__main__':
    TEST_COMPILE = True
    TEST_GET_FILE_ID = False
    TEST_EXCUTE_FILE = False
    TEST_COMPILE_AND_EXCUTE = True
    api_manager = APIManager(url_prefix)

    #Test compilation function
    if TEST_COMPILE == True:
        Compile_File_name = "s001.py"
        CodeContent = "for i in range(int(input())):\n    x1, y1, x2, y2, x3, y3 = map(float, input().split())\n    c = (x1-x2)**2 + (y1-y2)**2\n    a = (x2-x3)**2 + (y2-y3)**2\n    b = (x3-x1)**2 + (y3-y1)**2\n    # 16s^2\n    s = 2*(a*b + b*c + c*a) - (a*a + b*b + c*c)\n\n    px = (a*(b+c-a)*x1 + b*(c+a-b)*x2 + c*(a+b-c)*x3) / s\n    py = (a*(b+c-a)*y1 + b*(c+a-b)*y2 + c*(a+b-c)*y3) / s\n\n    ar = a**0.5\n    br = b**0.5\n    cr = c**0.5\n\n    r = ar*br*cr / ((ar+br+cr)*(-ar+br+cr)*(ar-br+cr)*(ar+br-cr))**0.5\n\n    print(\"{:>.3f}\".format(px),\"{:>.3f}\".format(py),\"{:>.3f}\".format(r))"
        api_manager.GET_File_Id_Dict(deBug = True)
        
        result = api_manager.Compile_Program(Compile_File_name, CodeContent)
        print(result)
        api_manager.GET_File_Id_Dict(deBug = True)
    #Test to get the compiled file
    if TEST_GET_FILE_ID == True:
        api_manager.GET_File_Id_Dict(deBug = True)
    #Test execution of compiled files
    if TEST_EXCUTE_FILE == True:
        # Execution program (compiled by default)
        CopyIn_fileId = "MFM7PJOD"
        Execute_File_name = "__pycache__/s001.cpython-311.pyc"
        TestPoint_Content = "1\n0.0 0.0 2.0 0.5127281311709682 2.0 2.0"
        Json_Text_response = api_manager.Execute_Program_After_Compile(CopyIn_fileId, Execute_File_name, TestPoint_Content)
        print(Json_Text_response)

