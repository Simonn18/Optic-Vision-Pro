import cv2
import numpy as np

dragging = False
EndPos = [0, 0]
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