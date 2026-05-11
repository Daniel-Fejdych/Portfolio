#Country Expander
import turtle as t #Only needed for visual interpretetion!
import random as r #This one is actually needed!
pixelSize = 10 #defines how big the pixels are.
t.ht() #Invisiblises the turtle
t.speed(0) #speeds up the process
t.resizemode("noresize") 
#Puts the pen in the right place
t.pu()
t.goto(t.window_width() * -0.5, t.window_height() * 0.5)
t.pd()
print(t.window_height())
def drawPixel():
    t.begin_fill()
    for i in range(0,4):
        t.forward(pixelSize)
        t.right(90)
    t.end_fill()
    t.forward(pixelSize)
countries = [['POL', "pink"],['GER', "gray"], ['FRA', "blue"], ['ENG', "red"]] # Each country's tags and its color    \/the database of placements
tilePlacement = [[r.randrange(0, 4, 1) for i in range(96)] for i in range(41)] # A 2d array of province owner ids {no. in the contries array}
for i in range(0, len(tilePlacement)): #code for drawing
    for tileId in tilePlacement[i]:
        t.color(countries[tileId][1])
        drawPixel()
    t.penup()
    t.back(pixelSize * len(tilePlacement[i]))
    t.left(90)
    t.back(pixelSize)
    t.right(90)
    t.pendown()
