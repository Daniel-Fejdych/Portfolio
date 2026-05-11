table = []
num = int(input("number of columns:"))
rws = int(input("number of rows:"))
for i in range(0,rws):
    a = []
    for ii in range(0,num):
        a.append(float(input("Row no. {}, column no. {}:".format(i + 1, ii + 1))))
    table.append(a)
for row in table:
    print(row)
