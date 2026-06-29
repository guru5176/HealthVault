from paddleocr import PaddleOCR
import numpy as np
import cv2

ocr = PaddleOCR(enable_mkldnn=False, use_angle_cls=True)

# create a dummy crop
img = np.zeros((50, 200, 3), dtype=np.uint8)
cv2.putText(img, "TEST", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

print("Trying ocr.ocr()...")
res_ocr = ocr.ocr(img, det=False, cls=True)
print(res_ocr)

try:
    print("Trying ocr.predict()...")
    res_predict = ocr.predict(img)
    print(res_predict)
except Exception as e:
    print("Error with ocr.predict:", type(e), str(e))
