table = []
num = int(input("number of rows:"))
for i in range(0,num):
    a = []
    a=input("row no. {}:".format(i + 1)).split(",")
    table.append(a)
for row in table:
    print(row)
