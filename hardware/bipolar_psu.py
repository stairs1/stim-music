# https://hackaday.com/2012/11/07/building-a-bipolar-supply-from-a-boost-converter/

#these are what I have on hand in through hole, so they are what I can test in a breadboard right now
common_r_values = [1, 2, 2.2, 3.3, 4.7, 5.1, 6.8, 10, 20, 47, 51, 68, 100, 220, 330, 470, 680, 1000] #*1000

#bipolar psu voltage set
v_out = 9 #we want +- v_out Volts

def get_voltage(R_one, R_two):
    v_out = ((R_one / R_two) + 1) * 1.255
    return v_out

for val in common_r_values:
    R_two = val * 1000
    R_one = R_two * ((v_out / 1.255) - 1)
    print("R1: {}k ohms, R2: {}k ohms".format(R_one/1000, R_two/1000))
print("REMEMBER: higher pair is better, as this is a voltage divider, so run as little current as possible.")

# best setup
#R_one = 2k
#R_two = 322ohm = 300ohm + 22ohm
