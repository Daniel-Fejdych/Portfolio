from random import *
amo = []
def rollDice(nos):
    out = randint(0,nos)
    return out
nm = input("Hello Player\nPlease Enter Your Name and your Character name below it\n:")
cnm = input()
for i in range(0,5):
    stat = ["Strength","Health","Combat Rating","Luck","Magic Amplitude"]
    input("Now, please roll a dice for {}'s {}".format(cnm, stat[i]))
    amo.insert(i,rollDice(32 - i ** 2))
    print("Your {} stat rolled {}".format(stat[i],amo[i]))
input("In a cold, northernly part of Quarltocia sits the city of Icia.\nThere, lives a human wanting to be rich named {}\nHe finds himself up against a spider(10STR and 14HEA).\n".format(cnm))
