import argparse
import cv2
import math
import tkinter as tk
import copy
from traffic_counter.database_client import DatabaseClient  # your class from earlier

# ---------------- Command-line arguments ----------------
parser = argparse.ArgumentParser(description="Traffic camera line editor")
parser.add_argument("--video", type=str, required=True, help="Path to the video file")
parser.add_argument("--camera", type=str, required=True, help="Camera ID to save lines")
args = parser.parse_args()

VIDEO_PATH = args.video
CAM_ID = args.camera

# ---------------- Config ----------------
WINDOW_NAME = "Line Editor"

BTN_SAVE_TL = (10, 10)
BTN_SAVE_BR = (160, 50)

BTN_CLEAR_TL = (180, 10)
BTN_CLEAR_BR = (330, 50)

BTN_UNDO_TL = (350, 10)
BTN_UNDO_BR = (470, 50)

BTN_REDO_TL = (490, 10)
BTN_REDO_BR = (610, 50)

HANDLE_RADIUS = 6
HANDLE_COLOR = (0, 0, 255)
LINE_COLOR = (0, 255, 0)
SELECT_RADIUS = 10

MARGIN = 100

db = DatabaseClient()  # initialize your database client
# ---------------------------------------

lines = []
undo_stack = []
redo_stack = []

drawing = False
start_point = None

dragging = False
drag_info = None
fullscreen = False

# ---------------- Functions ----------------

def push_undo():
    undo_stack.append(copy.deepcopy(lines))
    redo_stack.clear()

def undo():
    if not undo_stack:
        return
    redo_stack.append(copy.deepcopy(lines))
    lines.clear()
    lines.extend(undo_stack.pop())

def redo():
    if not redo_stack:
        return
    undo_stack.append(copy.deepcopy(lines))
    lines.clear()
    lines.extend(redo_stack.pop())

def get_screen_size():
    root = tk.Tk()
    root.withdraw()
    return root.winfo_screenwidth(), root.winfo_screenheight()

def draw_button(img, tl, br, text):
    cv2.rectangle(img, tl, br, (50, 50, 50), -1)
    cv2.rectangle(img, tl, br, (255, 255, 255), 1)
    cv2.putText(
        img,
        text,
        (tl[0] + 10, tl[1] + 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

def inside_rect(x, y, tl, br):
    return tl[0] <= x <= br[0] and tl[1] <= y <= br[1]

def dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def find_handle(x, y):
    for i, (x1, y1, x2, y2) in enumerate(lines):
        if dist((x, y), (x1, y1)) < SELECT_RADIUS:
            return i, 0
        if dist((x, y), (x2, y2)) < SELECT_RADIUS:
            return i, 1
    return None

def mouse_callback(event, x, y, flags, param):
    global drawing, start_point, dragging, drag_info

    ix = int(x / scale)
    iy = int(y / scale)

    # Save button
    if event == cv2.EVENT_LBUTTONDOWN:
        if inside_rect(ix, iy, BTN_SAVE_TL, BTN_SAVE_BR):
            db.save_camera(
                cam_id=CAM_ID,
                video_path=VIDEO_PATH,
                frame_width=base.shape[1],
                frame_height=base.shape[0],
                lines=lines
            )
            print(f"Camera {CAM_ID} saved with {len(lines)} lines")
            return

        if inside_rect(ix, iy, BTN_CLEAR_TL, BTN_CLEAR_BR):
            push_undo()
            lines.clear()
            return

        if inside_rect(ix, iy, BTN_UNDO_TL, BTN_UNDO_BR):
            undo()
            return

        if inside_rect(ix, iy, BTN_REDO_TL, BTN_REDO_BR):
            redo()
            return

        handle = find_handle(ix, iy)
        if handle is not None:
            push_undo()
            dragging = True
            drag_info = handle
            return

        push_undo()
        drawing = True
        start_point = (ix, iy)

    elif event == cv2.EVENT_MOUSEMOVE and dragging:
        idx, pt = drag_info
        x1, y1, x2, y2 = lines[idx]
        if pt == 0:
            lines[idx] = (ix, iy, x2, y2)
        else:
            lines[idx] = (x1, y1, ix, iy)

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False
        drag_info = None

        if drawing:
            lines.append((*start_point, ix, iy))
            drawing = False
            start_point = None

# ---------------- Load video ----------------

cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
cap.release()

if not ret:
    raise RuntimeError(f"Could not read video: {VIDEO_PATH}")

base = frame.copy()
h, w = base.shape[:2]

screen_w, screen_h = get_screen_size()
scale = min(
    (screen_w - MARGIN) / w,
    (screen_h - MARGIN) / h,
    1.0,
)

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, int(w * scale), int(h * scale))
cv2.setMouseCallback(WINDOW_NAME, mouse_callback)

# ---------------- Main loop ----------------

while True:
    display = base.copy()

    for x1, y1, x2, y2 in lines:
        cv2.line(display, (x1, y1), (x2, y2), LINE_COLOR, 2)
        cv2.circle(display, (x1, y1), HANDLE_RADIUS, HANDLE_COLOR, -1)
        cv2.circle(display, (x2, y2), HANDLE_RADIUS, HANDLE_COLOR, -1)

    draw_button(display, BTN_SAVE_TL, BTN_SAVE_BR, "Save")
    draw_button(display, BTN_CLEAR_TL, BTN_CLEAR_BR, "Clear")
    draw_button(display, BTN_UNDO_TL, BTN_UNDO_BR, "Undo")
    draw_button(display, BTN_REDO_TL, BTN_REDO_BR, "Redo")

    resized = cv2.resize(display, None, fx=scale, fy=scale)
    cv2.imshow(WINDOW_NAME, resized)

    key = cv2.waitKey(16) & 0xFF

    if key == 27:
        break

    # Ctrl+Z
    if key == 26:
        undo()

    # Ctrl+Shift+Z (usually same as Ctrl+Z but uppercase)
    if key == ord("Z"):
        redo()

    if key == ord("f"):
        fullscreen = not fullscreen
        mode = cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, mode)

db.close()
cv2.destroyAllWindows()
