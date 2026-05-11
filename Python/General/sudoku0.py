numRows = 9;#set up size
numColls = 9;
sudokuArray = []
for i in range(0,numRows):#loop to get the sudo grid, 0 = unknown
    sudokuArray.append(list(map(int,input("Enter row {}: ".format(i+1)).split(","))));
#possSudoku = [] #temp
a = 0
b = 0
for depth in range(1,numRows):#loop for depth of search
    for repetition in range(0,depth):#loop to utilize the depth(10,20,21,30...)
        #print(str(depth) + str(repetition)) #test
        for row in range(0, numRows):
            if sudokuArray[row].count(0) == repetition:
                









for i in range(0,numRows):
    print(str(sudokuArray[i]));
