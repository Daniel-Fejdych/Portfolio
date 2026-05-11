def create_Table(noc,nor): #noc - No. of columns, nor - no. of rows
    table = [] # start to create the 2d Array
    for i in range(0,noc):
        a = []
        for ii in range(0,nor):
            a.append((input("row no. {}, column no. {}:".format(i + 1, ii + 1))))
        table.append(a)
    for row in table:
        print(row)
