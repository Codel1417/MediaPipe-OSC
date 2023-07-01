import os
import sys
from os import path
import cv2
import mediapipe as mp
from pythonosc import udp_client

model_path = path.abspath(path.join(path.dirname(__file__), 'face_landmarker.task'))
print(model_path)

print('Starting OSC')
OSCip = "127.0.0.1"
OSCport = 8888  # VR Chat OSC port
client = udp_client.SimpleUDPClient(OSCip, OSCport)

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult


# Create a face landmarker instance with the live stream mode:
def print_result(result: FaceLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    for category in result.face_blendshapes:
        for blendshape in category:
            client.send_message("/" + blendshape.category_name, blendshape.score)


options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result, num_faces=1, output_face_blendshapes=True)

print('starting camera')
cap = cv2.VideoCapture(0)
print('loading model')
frameCount = 0
with FaceLandmarker.create_from_options(options) as landmarker:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        landmarker.detect_async(mp_image, frameCount)
        frameCount += 1
