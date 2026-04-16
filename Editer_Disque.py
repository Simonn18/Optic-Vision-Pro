import cv2
import numpy as np

dragging = False
EndPos = (0, 0)
CurPos = [0, 0]

def mouse(event, px, py, flags, param):
    global dragging, EndPos, start, CurPos
    if event == cv2.EVENT_LBUTTONDOWN:
        dragging = True
        start = (px, py)

    elif event == cv2.EVENT_MOUSEMOVE and dragging:
        print(f"Déplacement vers {px}, {py}")

        dx = px - start[0]
        dy = py - start[1]

        EndPos = (CurPos[0] + dx, CurPos[1] + dy)

        print(f"end_x : {EndPos[0]} ; end_y : {EndPos[1]}")

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False

        CurPos[0] = EndPos[0]
        CurPos[1] = EndPos[1]

def disque(img):
    h, w = img.shape[:2]

    mask = np.any(img != [0, 0, 0], axis=-1).astype(np.uint8) * 255

    shape = cv2.bitwise_and(img, img, mask=mask)

    background = img.copy()
    background[mask > 0] = 0

    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse)

    while True :
        temp=background.copy()

        M = np.float32([[1, 0, EndPos[0]], [0, 1, EndPos[1]]])

        shifted_shape = cv2.warpAffine(shape, M, (w, h))
        shifted_mask = cv2.warpAffine(mask, M, (w, h))

        temp[shifted_mask > 0] = shifted_shape[shifted_mask > 0]
        cv2.imshow("Image", temp)
        if cv2.waitKey(1) == 13 : #13ENTER 27ESC
            cv2.imwrite("result.png", temp)
            break
        
    cv2.destroyAllWindows()