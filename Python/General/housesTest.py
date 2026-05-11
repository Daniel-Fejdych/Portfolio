a = [1,1,1,1,2,5,2,1,1,1,1]
b = [1,2,3,4,5,6,7,8,9,10,11]
d = [11,10,9,8,7,6,5,4,3,2,1]
def OPT(i,r):
    if i < 4:
        return max(r[0:i])
    else:
        print(c)
        return max(r[i-1] + OPT(i - 3,r), OPT(i - 1,r))
#for ii in range(1, len(d)+1):
#   print(OPT(ii,d))
print(OPT(11,d))
