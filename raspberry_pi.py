import socket
import struct
from PIL import Image
import io
from luma.core.interface.serial import spi
from luma.lcd.device import st7735
import smbus2
import threading
import queue
import time

serial_left = spi(port=0, device=0, gpio_DC=25, gpio_RST=23, bus_speed_hz=40000000)
left = st7735(serial_left, width=160, height=128, rotate=0)

serial_right = spi(port=0, device=1, gpio_DC=24, gpio_RST=22, bus_speed_hz=40000000)
right = st7735(serial_right, width=160, height=128, rotate=0)

bus = smbus2.SMBus(1)
MPU_ADDR = 0x68
bus.write_byte_data(MPU_ADDR, 0x6B, 0)

mpu_data = {'gx':0,'gy':0}
lock = threading.Lock()

def read_word(reg):
    high = bus.read_byte_data(MPU_ADDR, reg)
    low = bus.read_byte_data(MPU_ADDR, reg+1)
    val = (high << 8) + low
    if val >= 0x8000:
        val = -((65535 - val) + 1)
    return val

def mpu_thread():
    gx_offset = read_word(0x43)
    gy_offset = read_word(0x45)
    while True:
        gx = read_word(0x43) - gx_offset
        gy = read_word(0x45) - gy_offset
        with lock:
            mpu_data.update({'gx': gx, 'gy': gy})
        time.sleep(0.01)

threading.Thread(target=mpu_thread, daemon=True).start()

UDP_HOST = 'PC IP'
UDP_PORT = 6000
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def udp_thread():
    while True:
        with lock:
            dx = mpu_data['gx'] * 0.02
            dy = mpu_data['gy'] * 0.02
        udp_sock.sendto(struct.pack('ff', dx, dy), (UDP_HOST, UDP_PORT))
        time.sleep(0.01)

threading.Thread(target=udp_thread, daemon=True).start()

frame_queue = queue.Queue(maxsize=2)

def recv_thread(conn):
    while True:
        raw_len = conn.recv(4)
        if not raw_len:
            break
        msg_len = struct.unpack(">I", raw_len)[0]
        data = b''
        while len(data) < msg_len:
            packet = conn.recv(msg_len - len(data))
            if not packet:
                break
            data += packet
        try:
            frame = Image.open(io.BytesIO(data)).convert('RGB')
            if frame_queue.full():
                try: frame_queue.get_nowait()
                except queue.Empty: pass
            frame_queue.put(frame)
        except:
            continue

TCP_HOST = ''
TCP_PORT = 5000
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.bind((TCP_HOST, TCP_PORT))
tcp_sock.listen(1)
conn, addr = tcp_sock.accept()

threading.Thread(target=recv_thread, args=(conn,), daemon=True).start()

try:
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            with lock:
                x_offset = int(mpu_data['gx']*0.05)
                y_offset = int(mpu_data['gy']*0.05)
                x_offset = max(0, min(x_offset, 160))
                y_offset = max(0, min(y_offset, 0))

            left_img = frame.crop((x_offset, y_offset, x_offset+160, y_offset+128))
            right_img = frame.crop((x_offset+160, y_offset, x_offset+320, y_offset+128))

            left.display(left_img)
            right.display(right_img)

except KeyboardInterrupt:
    left.cleanup()
    right.cleanup()
