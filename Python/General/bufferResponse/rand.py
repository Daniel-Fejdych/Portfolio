import random
for g in range(4950, 5051):
    f = 0
    fm = 0
    for i in range(0,1000000):
        if random.randrange(1,10001) > g:
            f += 1
        else:
            f -= 1
        if f > fm:
            fm = f
    print(str(g) + ", " + str(f) + ", " + str(fm))
