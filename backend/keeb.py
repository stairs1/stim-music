from ble_client import DualStimClient
from readchar import readkey

stimclient = DualStimClient()
stimclient.connect()


while True:
    data = readkey()
    match data:
        case 's':
            stimclient.pos_1()
        case 'd':
            stimclient.off_1()
        case 'f':
            stimclient.neg_1()
        case 'j':
            stimclient.pos_2()
        case 'k':
            stimclient.off_2()
        case 'l':
            stimclient.neg_2()
        case 'o':
            stimclient.off()
        case 'b':
            stimclient.seizure()
        case '\x03':  # ctrl-c
            break
        
