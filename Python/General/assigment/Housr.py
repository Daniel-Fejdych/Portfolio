import os, time #To allow the clearing of the console, To allow time delay
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql.connector"])
mydb = mysql.connector.connect(
  host="localhost",
  user="yourusername",
  password="yourpassword"
)

print(mydb)
class GameData():  #Includes all local Data
    def __init__(self):
        self._fArray = []
        with open("fData.txt") as readfile:
            line = readfile.readline().rstrip("\n")
            while line:
                fdata = line.split(", ")
                self._fArray.append([*fdata])
                line = readfile.readline().rstrip("\n")

    def fArray(self):
        return self._fArray


Data = GameData()
class GeneralFunctions(): #Includes general Functions
    def error(self, problem):
        os.system('cls')
        print("You have entered an incorrrect input, as", problem)
        time.sleep(5)

    def display(self, input):
        os.system('cls')
        print(input)

    def printGrid(self, array):  #To display array in grid
        os.system('cls')
        for i in range(len(array)):
            print(*array[i])
        time.sleep(5)



Func = GeneralFunctions()

class Login(): #Includes login/new account starter page
    def __init__(self):
        Func.display("Welcome to Housr, The dream house creation program. Are you an existing user?\n(yes)/(no)\n")
        if input("Input:\n") == "yes":
            self.login()
        else:
            self.createNewAccount()

    def login(self):
        
        if True == True:
            self.passed()
        else:
            Func.error("Incorrect details entered")
            self.login()

    def createNewAccount(self):
        pass
        if True == True:
            self.__init__()
        else:
            Func.error("Incorrect details entered")
            self.createNewAccount()

    def passed(self):
        pass #Allows the Menu object to start, in the next line



class HouseSelect():
    def __init__(self):
        Func.display("Do you want to load a house or create a new one? \n(load)/(create)\n")
        if input("Input:\n") == "load":
            self.load()
        else:
            self.create()

    def load(self):
      pass #RFD

    def create(self):
      global cRoomID, cHouse
      cRoomID = 0
      cHouse = House("H1")
      cHouse.addRoom(10, 10)  #Starts the next line, House create
class UserInput():  #This will Handle all user input for house creation
    def __init__(self):
        self._IN = ""
        self._cRoom = 0
        self.help()
        self.input()

    def help(self):
        Func.display("""Instructions
    To add new room, type: new {}
    To select room, type: sel {roomID}
    To add furniture, type: add {item xPos yPos}
    To delete furniture, type: del {item id}
    To display the current Room, type: dis
    To resize a Room in the House, type: res {width breadth}
    To rename House, type, ren {newName}
        """)

    def input(self):
        while self._IN not in ["exit", "quit"]:
            comm = self._IN.split(" ")

            if comm[0] == "sel":
                self._cRoom = int(comm[1])
            if comm[0] == "add":
                cHouse.getRoom(self._cRoom).addFurniture(*comm[1:])  #add it to correct room
            if comm[0] == "dis":
                cHouse.getRoom(self._cRoom).returnFurnitureArray()
            self.help()
            self._IN = input("Input: ").lower()
        exit()




class UserDatabase():  #USED TO STORE ALL USER DATA
    def __init__(self):
        self._UserArray = []  #!TBR to be read from DB


class User():  #Data Stored Per each User + !Login Details(Need At Least 2 DB tables)
    def __init__(self):
        self._username = ""  #!TBR to be read from DB
        self._password = ""  #!TBR to be read from DB
        self._HouseArray = []  #!TBR to read existing houses from DB

    def getUsername(self):
        return self._username

    def setUsername(self, newUsername):
        self._username = newUsername
        #Change data in DB

    def getPassword(self):
        return self._password

    def setPassword(self, newPassword):
        self._password = newPassword
        #!Change data in DB



class House():  # Data stored per each house
    def __init__(self, HouseName="", RoomArray=[]):
        self._houseName = HouseName
        self._houseCost = 0
        self._roomArray = RoomArray

    def addRoom(self, roomSizeX, roomSizeY):
        self._roomArray.append(Room(roomSizeX, roomSizeY))

    def deleteRoom(self, id):
        self._roomArray.pop(id)

    def getRoom(self, id):
        return self._roomArray[id]

    def recalcHouse(self):  #Recalculate house cost
        self._houseCost = 0
        for room in self._roomArray:
            self._houseCost += room.getRoomCost()



class Room():  # Data stored per each room
    def __init__(self, sizeX, sizeY):
        global cRoomID  #to set a diffrent id for each room
        self._roomCost = 0
        self._furnitureArray = []
        self._size = [sizeX, sizeY]
        self._doorPosition = [[]]  #?self._doorPosition[doorID][side, distFromMiddle]
        self._ID = cRoomID
        print("The new Room id is ", cRoomID)
        cRoomID += 1

    def addFurniture(
            self, type, posX,
            posY):  #appends a furniture object to the room object's array
        if type in [Data.fArray()[i][0] for i in range(len(Data.fArray()))]:
            for furniture in Data.fArray():
                if type == furniture[0]:
                    self._furnitureArray.append(
                        Furniture(furniture, posX, posY))
        else:
            Func.error("Furniture type non-exixtent.")

    def returnFurnitureArray(self):
        tempArray = [[None for a in range(self._size[0])]
                     for b in range(self._size[1])]
        for b in range(self._size[1]):
            for a in range(self._size[0]):
                tempArray[b][a] = self.checkFurniture(a, b)
        Func.printGrid(tempArray)

    def checkFurniture(
            self, x,
            y):  #Returns the item name if it is there, else returns None
        if [x, y] in [item.getPos() for item in self._furnitureArray
                      ]:  #!Possibly to be made more efficient
            for item in self._furnitureArray:
                if item.getPos() == [x, y]:
                    return item.getType()
        else:
            return None

    def getRoomSize(self):  #!Possibly Unneccessary
        return self._size

    def getRoomCost(self):
        self._roomCost = 0
        for item in self._furnitureArray:
            self._roomCost += item.getPrice()
        return self._roomCost



class Furniture():  #Info about specific furniture to be read from array of Furniture
    def __init__(self, furnitureData, X, Y):
        self._type = furnitureData[0]
        self._price = furnitureData[1]
        self._pos = [int(X), int(Y)]

    def getType(self):
        return self._type

    def getPrice(self):
        return self._price

    def getPos(self):  #Get position of this piece of Furnitute
        return self._pos



start = Login()
select = HouseSelect()
Input = UserInput()
