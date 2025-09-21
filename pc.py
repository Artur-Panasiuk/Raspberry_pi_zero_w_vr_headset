import socket
import struct
import cv2
import threading
import time
import win32api
import win32con

def move_mouse(dx, dy):
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

PI_IP = 'Pi Zero W addr'
PI_PORT = 5000

UDP_PORT = 6000
FPS = 15

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect((PI_IP, PI_PORT))

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 128)
cap.set(cv2.CAP_PROP_FPS, FPS)

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 30]

def head_tracking():
    import math
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('0.0.0.0', UDP_PORT))

    angle_x, angle_y = 0.0, 0.0
    last_time = time.time()
    alpha = 0.98

    smoothed_x, smoothed_y = 0.0, 0.0
    smooth_alpha = 0.7
    sensitivity = 100.0

    while True:
        data, addr = udp_sock.recvfrom(1024)
        if len(data) != 8:
            continue

        gx, gy = struct.unpack('ff', data)

        gyro_x = gx / 131.0
        gyro_y = gy / 131.0

        now = time.time()
        dt = now - last_time
        last_time = now

        angle_x += gyro_x * dt
        angle_y += gyro_y * dt

        angle_x = alpha * angle_x
        angle_y = alpha * angle_y

        smoothed_x = smooth_alpha * smoothed_x + (1 - smooth_alpha) * angle_x
        smoothed_y = smooth_alpha * smoothed_y + (1 - smooth_alpha) * angle_y

        move_mouse(smoothed_x * sensitivity, -smoothed_y * sensitivity)


threading.Thread(target=head_tracking, daemon=True).start()

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result, encimg = cv2.imencode('.jpg', frame_rgb, encode_param)
    data = encimg.tobytes()

    try:
        tcp_sock.sendall(struct.pack(">I", len(data)) + data)
    except Exception as e:
        print("err:", e)
        break

    time.sleep(1/FPS)
