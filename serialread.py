import serial
ser = serial.Serial(' /dev/tty0')
x = ser.read(10)
print(x)
ser.close()