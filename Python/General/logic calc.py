class Op:
    def __init__(self, n1, v1, o, n2, v2):
        self.var1 = [n1, v1]
        self.var2 = [n2, v2]
        self.op = o
    def calc(self):
        if self.op = "O":
            return 
        


IN = input("Type A-and, O-or, N-not with space in between.")
na = [" ", "Not"]
aa = ["Or", "And"]
#In format: p A N q O r (read left to right)
for i in range(len(IN)):
    if IN[i] in ["A", "O"] and IN[i-2] not in ["A", "O", "N", " "]:
        if IN[i] == "A":
            ADD = 1
        else:
            ADD = 0
            
        if IN[i-4] == "N":
            NOT1 = 1
        else:
            NOT1 = 0
            
        tempVar1 = IN[i-2]
        
        if IN[i+2] == "N":
            NOT2 = 1
            if IN[i+4] not in ["A", "O", "N", " "]:
                tempVar2 = IN[i+4]
        elif IN[i+2] != " ":
            tempVar2 = IN[i+2]
            NOT2 = 0
        print(na[NOT1],tempVar1, aa[ADD], na[NOT2], tempVar2)
        
        
            
