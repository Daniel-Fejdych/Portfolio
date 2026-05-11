e=m=f=1
ea=ma=fa=2
while e > 0:
    inp = 0
    while inp != 1 or inp != 2 or inp != 3:
        try:
            inp=int(input("Options\n1. 1 Energy -> {} Money\n2. 1 Money -> {} Food\n3. 1 Food -> {} Energy\nUpgrades\n4. 10 Energy -> 0.2 Money per Trade\n5. 10 Money -> 0.2 Food per Trade\n6. 10 Food -> 0,2 Energy per Trade\nCurrent:\nEnergy: {}\nMoney: {}\nFood: {}\n:".format(ea,ma,fa,round(e,2),round(m,2),round(f,2))))
        except ValueError:
            print("Error!"+"\n"*20)
        if inp == 1:
            if e >= 1:
                e -= 1
                m += ea
            else:
                print("Not enough Energy!"+"\n"*20)
        elif inp == 2:
            if m >= 1:
                m -= 1
                f += ma
            else:
                print("Not enough Money!"+"\n"*20)
        elif inp == 3:
            if f >= 1:
                f -= 1
                e += fa
            else:
                print("Not enough Food!"+"\n"*20)
        elif inp == 4:
            if e >= 10:
                e -= 10
                ea += 0.2
            else:
                print("Not enough Money!"+"\n"*20)
        elif inp == 5:
            if m >= 10:
                m -= 10
                ma += 0.2
            else:
                print("Not enough Money!"+"\n"*20)
        elif inp == 6:
            if f >= 10:
                f -= 10
                fa += 0.2
            else:
                print("Not enough Energy!"+"\n"*20)
        else:
            print("Error!"+"\n"*20)
