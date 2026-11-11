"""Raspberry Pi 4 smart security camera.

Reconstructed and formatted from the project source. Configure hardware and
install the legacy PiCamera stack before running on a compatible Raspberry Pi OS.
Telegram credentials are requested interactively and are never stored in code.
"""

import getpass
import os
import threading
import time
from pathlib import Path

import cv2
import face_recognition
import RPi.GPIO as GPIO
import telepot
from picamera import PiCamera
from picamera.array import PiRGBArray

# Hardware configuration
PIR_PIN = 4  # BCM numbering
FRAME_SIZE = (640, 480)
FRAME_RATE = 30
RECORD_SECONDS = 5
KNOWN_FACES_DIR = Path("known_faces")
CASCADE_PATH = "haarcascade_frontalface_default.xml"
OUTPUT_DIR = Path("/tmp")

chat_id = None
chat_lock = threading.Lock()
stop_event = threading.Event()


def load_known_faces():
    """Load face encodings from known_faces; filenames become display names."""
    encodings = []
    names = []

    KNOWN_FACES_DIR.mkdir(exist_ok=True)
    for image_path in sorted(KNOWN_FACES_DIR.iterdir()):
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        image = face_recognition.load_image_file(str(image_path))
        face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            encodings.append(face_encodings[0])
            names.append(image_path.stem)
        else:
            print(f"No face found in reference image: {image_path.name}")

    return encodings, names


def handle_telegram_message(message):
    """Remember the chat that starts the bot and confirm activation."""
    global chat_id

    message_text = message.get("text", "")
    message_chat_id = message.get("chat", {}).get("id")
    if not message_chat_id:
        return

    if message_text == "/start":
        with chat_lock:
            chat_id = message_chat_id
        bot.sendMessage(message_chat_id, "Security camera with face recognition is activated.")
        print(f"Telegram chat registered: {message_chat_id}")


def send_message(text):
    with chat_lock:
        destination = chat_id
    if destination is None:
        print("Telegram chat is not registered. Send /start to the bot first.")
        return

    try:
        bot.sendMessage(destination, text)
    except Exception as error:
        print(f"Telegram message error: {error}")


def send_photo(image_path, caption):
    with chat_lock:
        destination = chat_id
    if destination is None:
        print("Telegram chat is not registered. Send /start to the bot first.")
        return

    try:
        with open(image_path, "rb") as photo:
            bot.sendPhoto(destination, photo, caption=caption)
    except Exception as error:
        print(f"Telegram photo error: {error}")


def send_video(video_path, caption):
    with chat_lock:
        destination = chat_id
    if destination is None:
        print("Telegram chat is not registered. Send /start to the bot first.")
        return

    try:
        with open(video_path, "rb") as video:
            bot.sendVideo(destination, video, caption=caption)
    except Exception as error:
        print(f"Telegram video error: {error}")


def check_unknown_faces(video_path, known_face_encodings):
    """Return True if any face in the recorded video is not enrolled."""
    capture = cv2.VideoCapture(str(video_path))
    unknown_detected = False

    try:
        while capture.isOpened():
            success, frame = capture.read()
            if not success:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_frame)
            encodings = face_recognition.face_encodings(rgb_frame, locations)

            for encoding in encodings:
                matches = face_recognition.compare_faces(
                    known_face_encodings, encoding
                )
                if not any(matches):
                    unknown_detected = True
                    return True
    finally:
        capture.release()

    return unknown_detected


def record_motion_event(camera, known_face_encodings):
    """Record a short clip after PIR motion and alert if it contains an unknown face."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    h264_path = OUTPUT_DIR / f"security_event_{timestamp}.h264"
    mp4_path = OUTPUT_DIR / f"security_event_{timestamp}.mp4"

    print("Motion detected — recording video...")
    try:
        camera.start_recording(str(h264_path))
        time.sleep(RECORD_SECONDS)
        camera.stop_recording()
    except Exception as error:
        print(f"Camera recording error: {error}")
        try:
            camera.stop_recording()
        except Exception:
            pass
        return

    # MP4Box is used by the original project to convert H.264 to MP4.
    conversion_status = os.system(
        f'MP4Box -add "{h264_path}" "{mp4_path}"'
    )
    if conversion_status != 0 or not mp4_path.exists():
        print("Video conversion failed. Check that MP4Box is installed.")
        return

    if check_unknown_faces(mp4_path, known_face_encodings):
        print("Unknown face detected in recorded video.")
        send_video(str(mp4_path), "Unknown face detected!")
    else:
        print("No unknown faces detected in the recorded video.")


def show_live_feed(camera, raw_capture, face_cascade,
                   known_face_encodings, known_face_names):
    """Display camera frames, draw face boxes, and alert on unknown faces."""
    print("Starting live camera feed...")

    try:
        for frame in camera.capture_continuous(
            raw_capture, format="bgr", use_video_port=True
        ):
            if stop_event.is_set():
                break

            image = frame.array.copy()
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            detected_faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            for (x, y, width, height) in detected_faces:
                cv2.rectangle(
                    image, (x, y), (x + width, y + height), (0, 255, 0), 2
                )

            rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations
            )

            for (top, right, bottom, left), encoding in zip(
                face_locations, face_encodings
            ):
                matches = face_recognition.compare_faces(
                    known_face_encodings, encoding
                )
                name = "Unknown"

                if True in matches:
                    match_index = matches.index(True)
                    name = known_face_names[match_index]
                else:
                    print("Unknown face detected in live feed.")
                    send_message("Unknown face detected!")
                    photo_path = OUTPUT_DIR / "unknown_face.jpg"
                    cv2.imwrite(str(photo_path), image)
                    send_photo(str(photo_path), "Unknown face detected!")

                cv2.rectangle(
                    image, (left, top), (right, bottom), (255, 0, 0), 2
                )
                cv2.putText(
                    image, name, (left, bottom + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2
                )

            cv2.imshow("Raspberry Pi Security Camera", image)

            if cv2.waitKey(10) & 0xFF == ord("q"):
                stop_event.set()
                break

            raw_capture.truncate(0)
    finally:
        cv2.destroyAllWindows()


def main():
    global bot

    token = getpass.getpass("Enter your Telegram bot token (input hidden): ").strip()
    if not token:
        raise ValueError("A Telegram bot token is required to send alerts.")

    known_face_encodings, known_face_names = load_known_faces()
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if face_cascade.empty():
        raise FileNotFoundError(
            f"Could not load Haar cascade file: {CASCADE_PATH}"
        )

    bot = telepot.Bot(token)
    bot.message_loop(handle_telegram_message)
    print("Telegram bot started. Open the bot and send /start to register your chat.")

    camera = PiCamera()
    camera.resolution = FRAME_SIZE
    camera.framerate = FRAME_RATE
    raw_capture = PiRGBArray(camera, size=FRAME_SIZE)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)

    live_feed_thread = threading.Thread(
        target=show_live_feed,
        args=(
            camera, raw_capture, face_cascade,
            known_face_encodings, known_face_names,
        ),
        daemon=True,
    )
    live_feed_thread.start()

    try:
        while not stop_event.is_set():
            if GPIO.input(PIR_PIN) == GPIO.HIGH:
                record_motion_event(camera, known_face_encodings)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping security camera...")
    finally:
        stop_event.set()
        live_feed_thread.join(timeout=3)
        GPIO.cleanup()
        camera.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
