# Raspberry Pi 4 Smart Security Camera

An intelligent, real-time surveillance system built with a Raspberry Pi 4. It combines camera monitoring, PIR motion sensing, computer vision, face recognition, and Telegram messaging to help detect unexpected activity and notify the user remotely.

## Overview

The Raspberry Pi acts as the central controller. A camera provides the live video feed, while a PIR sensor detects movement in the monitored area. OpenCV locates faces in captured frames, and the face-recognition component compares them with a local collection of enrolled reference images.

When an unfamiliar face is detected, the system can send a Telegram alert along with visual evidence. Combining motion sensing with face-aware notifications makes the system useful for small-scale home, office, or laboratory monitoring.

## Features

- **Live camera monitoring** — capture and process frames from a Raspberry Pi camera.
- **Motion-triggered surveillance** — use a PIR sensor to detect activity in the monitored area.
- **Face detection** — locate faces in camera frames with OpenCV.
- **Known/unknown face matching** — compare detected faces with locally stored reference images.
- **Remote notifications** — send Telegram alerts when an unfamiliar face is detected.
- **Visual evidence** — capture and share images or short video clips with alerts.

## How It Works

1. The Raspberry Pi initializes the camera, PIR sensor, and face-recognition components.
2. The camera feed is processed to detect faces.
3. Detected faces are compared with the enrolled reference images.
4. The PIR sensor provides an additional motion trigger for recording.
5. When an unfamiliar face is detected, the system sends a Telegram notification and can attach a captured image or video.
6. The user receives the alert remotely and can review the evidence.

## Hardware

- Raspberry Pi 4
- Raspberry Pi Camera Module or compatible camera
- PIR motion sensor
- Jumper wires
- Suitable power supply

## Software

- Python 3
- OpenCV
- face_recognition
- Raspberry Pi camera interface
- RPi.GPIO
- Telegram Bot API client

The exact camera and GPIO packages may vary depending on the Raspberry Pi OS release and camera stack.

## Suggested Project Structure

```text
raspberry-pi-security-camera/
├── README.md
├── requirements.txt
├── .gitignore
├── security_camera.py
└── known_faces/
    └── .gitkeep
```

## Setup

1. Set up Raspberry Pi OS on the Raspberry Pi 4.
2. Connect the camera module and PIR sensor to the appropriate interfaces.
3. Install Python and the required libraries for your Raspberry Pi OS version.
4. Create a `known_faces/` directory and add reference images for people who have agreed to be enrolled. Use descriptive filenames so the application can associate an identity with each image.
5. Configure the Telegram bot securely without hardcoding credentials in source files.
6. Run the application on the Raspberry Pi and test motion detection, face matching, and notifications in a controlled environment.

## Privacy and Security

- Do not commit bot credentials, chat identifiers, private face images, or captured surveillance footage.
- Obtain consent before collecting or using face images.
- Keep access to the Raspberry Pi and Telegram bot restricted.
- Any bot credential previously included in an earlier code sample should be treated as exposed. Revoke it with the bot provider and generate a replacement.
- Deploy cameras only where monitoring is lawful and appropriately disclosed.

## Notes

This README describes the system's purpose and intended workflow. Hardware-specific setup and dependency versions may require adjustment for the Raspberry Pi OS release in use. Validate the system on the target hardware before relying on it for security monitoring.
