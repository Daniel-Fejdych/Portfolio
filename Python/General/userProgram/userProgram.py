import time
users = {} #Create a new dictionary
usrs = open("Users.txt") #Open the file with users
for lines in usrs:
    x=lines.split(" ")
    users[x[0]] = x[1] #put the file into the dictionary
status = ""

def displayMenu(): #The menu at the start
    global status
    status = input("Do you have a Login Account, y/n? q to quit.\n")
    if status == "y":
        oldUser()
    elif status == "n":
        newUser()
    elif status == "q":
        quit()
def newUser(): #When a new person creates an account
    createLogin = input("Create a login: ")
    if createLogin in users:
        print("\nLogin name already exists!\n") #For no usename duplicates
    else:
        createPassw = input("Create Password: ") #Add a password
        users[createLogin] = createPassw #Add the password into the dictionary
        usrs = open("Users.txt", "a") #Open the file on a(Add text) setting
        usrs.write("\n" + createLogin + " " + createPassw) #Add this user as an entry
        usrs.close()
        print("\nUser created!\n")
def oldUser(): #When they already have an account
    login = input("Enter your Username:\n")
    passw = input("Enter your Password:\n")
    if login in users and users[login] == passw:#Check if password matches to username
        print("\nLogin Succesfull!\n")
        print("User: {} acessed the system on: {}".format(login,time.asctime())) #Print the time they logged on
    else: #If user doesn't exist
        print("\nUser doesn't exist or wrong password!\n")
while status != "q":
    status = displayMenu() #Loop until they quit
