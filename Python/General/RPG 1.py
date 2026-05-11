import math as m
import time as t
from tkinter import *
from random import * #importatation of needed modules
global Pl_name, Char_name, cst, opt, o #intialisation of variables
cst = """Story
In a world full of magic there is an adventurer wanting to get a lot gold
"""
actions = ""
Pl_name = input("Please Enter Your Name to Start:\n")
Char_name = input("Greetings {}, Please Input Your Character's Name:\n".format(Pl_name)) #Puts the player name and character name to their respective variables
print("Starting Game...")

def rollDice(nos): #Function for randomisation and dice rolls
    randomNum = randint(0, nos)
    return randomNum #Returns a number between 1 and nos(Number of Sides)

def drawMenu(): #Draw the main Menu
    o = Tk()
    Label(o, o.title("RPG 1"), text = "Welcome {},\n {} is ready to start".format(Pl_name, Char_name)).grid(row=0, sticky=N)
    Button(o, text = "Start Game", command = startGame).grid(row=3, sticky=W, pady=1) #when pressed, do start game
    Button(o, text = "Exit", command = o.destroy).grid(row=3, sticky=E, pady=1) #when pressed, destroy this menu
    mainloop()
def startGame():
    print("Game has Started!")
    r = Tk() #Main Game Window
    Label(r, r.title("RPG 1"), text = cst+actions).grid(row=0, sticky=N) #cst-Current Story Text
    Button(r, text = "1", command = option1).grid(row=3, sticky=W, pady=1)
    Button(r, text = "3", command = option3).grid(row=3, sticky=E, pady=1)
    Button(r, text = "2", command = option2).grid(row=3, sticky=S, pady=1)
    mainloop()
def option1():
    opt=1;
def option2():
    opt=2;
def option3():
    opt=3;
drawMenu()
