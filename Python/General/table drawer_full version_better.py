table = []#future
num = int(input("number of columns:\n"))
rows = int(input("number of rows:\n"))
#ents =int(input("number of entries:\n"))
x=0
for i in range(0,rows):
    a = []
    for ii in range(0,num):
        a.append(input("Row no. {}, column no. {}:".format(i + 1, ii + 1)))
    table.append(a)
for row in table:
    x+=1
    print("row {} - {}".format(x,", ".join(row)))
