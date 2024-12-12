import sys
import os
from codeTool.ExecutiveProgram.FileIO import FileHandlerSingleton
from codeTool.ExecutiveProgram.Worker import Worker, Program_Submission, Checker, Quesion_Test_Point_objectList,Quesion_Test_Point_object


if __name__ == '__main__':
    EXECUTION_ONE = False
    EXECUTION_ALL = True
    CHECK_TEST1 = False
    # Confirm the test directory
    test_directory = './merged_test_cases/p03479'
    checker = Checker()
    if CHECK_TEST1 == True:
        str1 = "  Hello, world! \nThis is a test.   \n  "
        str2 = "Hello, world!\nThis is a test.\n"
        result = checker.Check_consistency(str1, str2)
        print(result)  # output: True

    w = Worker()
    Compile_File_name = "s001.py"
    CodeContent = """
    x, y = map(int, input().split())

    ans = 0

    while x < y:
        x *= 2
        ans += 1
    print(ans)

    """
    Psubmit = Program_Submission(Compile_File_name, CodeContent)
    if EXECUTION_ONE == True:    
        Test_Point_Input = "1\n0.0 0.0 2.0 0.5127281311709682 2.0 2.0"
        w.Run_Program_By_One_Test_Point(Psubmit, Test_Point_Input)
        print(Psubmit)
        print(type(Psubmit))
    if EXECUTION_ALL == True:
        FileHandlerSingleton.initialize()
        if not os.path.exists(test_directory):
            raise FileNotFoundError(f"Directory {test_directory} does not exist")
        
        Test_List = Quesion_Test_Point_objectList()
        Test_List.inint_Tlist_by_FileHandlerSingleton(FileDirectory=test_directory, deBug= False)
        
        # Q1 = Quesion_Test_Point_object("1\n0.0 0.0 2.0 0.5127281311709682 2.0 2.0", "0.744 1.256 1.460\n\n")
        # Q2 = Quesion_Test_Point_object("1\n0.0 0.0 2.4487612247110815 0.5127281311709682 2.0 2.0", "1.087 0.913 1.420\n\n")
        # Q3 = Quesion_Test_Point_object("1\n0.0 0.0 2.4487612247110815 0.5127281311709682 2.0 2.033916337250816", "1.082 0.936 1.431\n\n")
        # Test_List.Insert_Test_Point(Q1)
        # Test_List.Insert_Test_Point(Q2)
        # Test_List.Insert_Test_Point(Q3)
        
        w.Run_Program_By_One_All_Point(Psubmit, Test_List)
        checker.Check_Run_Result(Psubmit, Test_List)
        print(Psubmit)




