from tkinter import *

# Creating root widget (=window)
master = Tk()

# Conf display
Label(master, text="Local").grid(row=0, column=1)
Label(master, text="RPi").grid(row=0, column=2)
Label(master, text="TPB site").grid(row=1, column=0, sticky=W)
Label(master, text="DB path").grid(row=2, column=0, sticky=W)
Label(master, text="Working Directory").grid(row=3, column=0, sticky=W)
Label(master, text="Number of links").grid(row=4, column=0, sticky=W)
Button(master, text="Save configuration").grid(row=5, column=0, columnspan=3)

for r in range(1, 5):
    for c in [1, 2]:
        Entry(master).grid(row=r, column=c)

master.mainloop()