t = 1
while t == 1: #Loop until the user wants to quit
    a = int(input("Enter start number:\n"))#User Inputs
    b = int(input("Enter end number:\n"))
    aPrimePrinted = int(input("Do you want prime check printed out? 0 for no / 1 for yes:\n"))
    notaPrimePrinted = int(input("Do you want not prime check printed out? 0 for no / 1 for yes:\n"))
    c = int(input("Comments? 0 for no / 1 for yes:\n")) # Used in 1a
    nums = list(range(a,b+1)) #Puts all your numbers in an array
    for i in range(a,b+1): #Loops to check every number
        notPrime = 0 #Assumes a number is prime (Not Not Prime)
        primeCheck = i #i is the number being checked
        for ii in range(2,i):#Loops for every number between 2 and i
            if primeCheck % ii != 0: #checks if the remainder in not equal to zero (If there is a remainder)
                if c == 1: #1a
                    print("{} is undivisible by {}".format(i,ii))#comment 1
            else:
                if c == 1:#1a as well
                    print("{} is divisible by {}".format(i,ii)) #comment 2 (if used, then the current i is not Prime)
                notPrime = 1 #Thus the variable is set aprioprietly
        #Once it loops through every possible divider for i, it prints whether i is prime if you selected at the begining
        if notPrime != 1: #if i is a prime (never had a remainder of zero in the aformentioned stage)
            if aPrimePrinted == 1: #if the user wants to,
                print("{} is a prime number".format(i)) #Say i is a prime
        else:
            if notaPrimePrinted == 1:
                print("{} is not a prime number".format(i))
            nums.remove(i)#Remove it for step 2a

    q = int(input("Do you want every prime number printed out? 0 for no / 1 for yes:\n"))#2a - If the user wants to, they can have the list (with only the prime numbers left) printed out
    if q == 1: #A very simple way for y/n user input
        print(nums)
    t = int(input("Do you want to try again? 0 for no / 1 for yes:\n")) #User can decide to try again
