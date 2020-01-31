import serial
# ser = serial.Serial('/dev/ttyS0',9600)  # open serial port

# check which port was really used
# string = "anna meurer"
# string_encode = string.encode()
# 
# ser.write(string_encode)
# ser.close()             # close port

names = ["anna meurer", "emily scherer"]
for name in names:
    ser = serial.Serial('/dev/ttyS0',9600)
    string_encode = str(name).encode()
    ser.write(string_encode)
    ser.close()
    

