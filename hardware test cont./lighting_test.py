from PIL import Image

im = Image.open('cropped-image.png')
pixels = im.getdata()   # get the pixels as a flattened sequence
black_thresh = 50 # darker the pixel, lower the value
tot_pixels = 0

for pixel in pixels:
    tot_pixels += pixel
n = len(pixels)
if av_pixels/n < black_thresh: # get average value of pixels
    print("lights off")
else:
    print("light")
