# Raspberry pi VR headset
## Introduction
This project explores usage of low power raspberry pi zero w in VR displaying applications.
## Setup
For this project I prepared following hardware:
- Raspberry pi zero w
- 2x LCD displays (128 x 160 p waveshare ST7735S) -> SPI
- MPU-6500 gryoscope accelerometer -> I2C

Due to limited hardware, displays share same MOSI and SCLK lines.

## Software
### Raspberry pi
Script collects data from gyro and sends them over wifi to PC. Recieved, rendered frame is then splitted from 320x128 to two seperate images and displayed appropriately.
### PC
PC recieves gyro data and moves mouse coordinates, while sending locked amount of scaled frames, streamed from OBS virtual camera.

## Conclusion
Result of this experiment showed that raspberry pi zero is technically capable of running as VR headset for debugging/development. But even with locked frames, low resolution and compressed image, the result of ~10-15 FPS and 3~4 seconds of latency is not ideal.
