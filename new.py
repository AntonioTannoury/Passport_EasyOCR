import easyocr
import cv2
reader = easyocr.Reader(["en"])
img = cv2.imread(r'C:\Users\AntonioTannoury\OneDrive - SirenAssociates\Desktop\Passport_EasyOCR\passport.jpg')
w = int(img.shape[1] * 0.5)
result = reader.readtext(img, min_size=w)