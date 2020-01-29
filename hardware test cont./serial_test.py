import serial

ser = serial.Serial("/dev/ttyS0", 9600)
encoding = "utf-8"

while True:
    receive = ""
    byte = ser.readline()
    receive += str(byte, encoding) # bytes to string
    names = receive.split(',') # create list of names

ser.close()

# ser = serial.Serial("/dev/ttyS0", 9600)
# encoding = 'utf-8'
# recieve = ""
# 
# try:
#     while True:
#         byte = ser.read()
#         letter = str(byte, encoding)
#         recieve += letter
# 
# except KeyboardInterrupt:
#     ser.close()
#      
# finally:
#     print(" ")
#     print(recieve)
#     print("finished")