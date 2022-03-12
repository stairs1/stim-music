import threading
from getch import _Getch
import sys

class KeyboardThread(threading.Thread):
    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        self.getch = _Getch()
        self.kill_self = False
        super(KeyboardThread, self).__init__(name=name)
        self.start()

    def kill(self):
        self.kill_self = True

    def run(self):
        while not self.kill_self:
            raw_getch = self.getch()
            key_code = ord(raw_getch)
            if key_code == 3: #if ctrl-c
                sys.exit()

            #getch sends three values to buffer when an arrow key is pressed, we do this here to deal with arrow key presses
            #https://stackoverflow.com/questions/10463201/getch-and-arrow-codes
            if (raw_getch == '\033'): #if the first value is esc
                self.getch(); #skip the [ #if we want to be able to use escape key, we would exit here and return escape key ord
                #get the next keycode, which is A,B,C,or D, that corresponds to arrow keys
                raw_getch = self.getch()
                key_code = ord(raw_getch)
                #below, we make up our own codes for arrow keys so all key messages sent are integers
                if raw_getch == 'A':
                    key_code = 200 
                elif raw_getch == 'B':
                    key_code = 201 
                elif raw_getch == 'C':
                    key_code = 202 
                elif raw_getch == 'D':
                    key_code = 203 

            #send keycode to callback
            self.input_cbk(key_code)

showcounter = 0 #something to demonstrate the change

def my_callback(inp):
    #evaluate the keyboard input
    print('You Entered:', inp, ' Counter is at:', showcounter)

if __name__ == "__main__":
    #start the Keyboard thread
    kthread = KeyboardThread(my_callback)

    while True:
        #the normal program executes without blocking. here just counting up
        showcounter += 1
