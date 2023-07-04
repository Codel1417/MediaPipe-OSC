import ipaddress
import os
import shelve
import sys
import time
from os import path
from threading import Thread

import cv2
import mediapipe as mp
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QLineEdit, QApplication, QWidget, QComboBox, QFormLayout, QLabel, QCheckBox
from cv2 import VideoCapture
from mediapipe import Image
from mediapipe.tasks.python.vision import RunningMode
from mediapipe.tasks.python.vision.face_landmarker import FaceLandmarker, FaceLandmarkerOptions
from pygrabber.dshow_graph import FilterGraph
from pythonosc import udp_client
from pythonosc.udp_client import SimpleUDPClient

configPathAppData: str = path.join(path.expanduser('~'), 'AppData', 'Local', 'MediaPipeOSC')
configPath: str = path.join(configPathAppData, 'MediaPipeOSC.config')
model_path: str = path.abspath(path.join(path.dirname(__file__), 'face_landmarker.task'))
currentCamID: int = 0
currentCamName: str = ""
capture: VideoCapture | None = None
OSCip: str = "127.0.0.1"
OSCport: int = 8888
client: SimpleUDPClient = udp_client.SimpleUDPClient(OSCip, OSCport)
graph: FilterGraph = FilterGraph()
faceThread: Thread | None = None
enabled = False


def getCamFromStr(cam: str):
    global currentCamName
    try:
        cameras: list[str] = graph.get_input_devices()
        for i in range(len(cameras)):
            if cameras[i] == cam:
                currentCamName = cam
                return i
    except Exception as e:
        return 0


def createConfigFolder():
    if not path.exists(configPathAppData):
        print("Creating config folder")
        try:
            os.mkdir(configPathAppData)
        except Exception as e:
            print(e)
            return


def loadConfig():
    global OSCip
    global OSCport
    global currentCamID
    global enabled
    try:
        with shelve.open(filename=configPath, flag='c', protocol=None, writeback=False) as db:
            if "ip" in db:
                OSCip = db["ip"]
            if "port" in db:
                OSCport = db["port"]
            if "cam" in db:
                currentCamID = getCamFromStr(db["cam"])
            if "enabled" in db:
                startStop(db["enabled"])
    except Exception as e:
        print(e)
        return


def saveConfig():
    print("Saving config")
    with shelve.open(filename=configPath, flag='c', protocol=None, writeback=False) as db:
        db["ip"] = OSCip
        db["port"] = OSCport
        if currentCamName != "":
            db["cam"] = currentCamName
        db["enabled"] = enabled
        db.sync()


def getCameras():
    comboBox: QComboBox = QComboBox()
    cameras: list[str] = graph.get_input_devices()
    for camera in cameras:
        comboBox.addItem(camera)
    comboBox.currentIndexChanged.connect(lambda: changeCam(comboBox.currentIndex(), comboBox.currentText()))
    return comboBox


def connectOSC(address: str):
    global OSCip
    global OSCport
    oldIP = OSCip
    oldPort = OSCport
    try:
        OSCip, OSCport = address.split(":")
        OSCport = int(OSCport)
        if not ipaddress.ip_address(OSCip).is_private:
            raise Exception("Invalid IP address")
    except Exception as e:
        print("Invalid OSC address " + address)
        OSCip = oldIP
        OSCport = oldPort
        return
    saveConfig()


def startStop(checked: bool):
    print("startStop " + str(checked))
    global enabled
    global faceThread
    if (checked == enabled):
        return
    enabled = checked
    if faceThread is None:
        faceThread = Thread(target=loadFaceLandmark)
    if enabled and not faceThread.is_alive():
        faceThread.start()
    saveConfig()


def UI():
    try:
        app: QApplication = QApplication([])
        window: QWidget = QWidget()
        window.setWindowTitle("MediaPipe OSC")
        ipRegex = QRegularExpression('[0-9]+(?:\.[0-9]+){3}:[0-9]+')
        layout = QFormLayout()
        layout.addRow(QLabel("Camera:"), getCameras())
        oscAddress: QLineEdit = QLineEdit("127.0.0.1:8888")
        oscAddress.setValidator(QRegularExpressionValidator(ipRegex))
        oscAddress.textChanged.connect(lambda: connectOSC(oscAddress.text()))
        layout.addRow(QLabel("OSC Target"), oscAddress)
        enabledBox: QCheckBox = QCheckBox()
        enabledBox.setChecked(enabled)
        enabledBox.stateChanged.connect(lambda: startStop(enabledBox.isChecked()))
        layout.addRow("Enabled", enabledBox)
        window.setLayout(layout)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(e)
        return


def faceLandmarkResults(result: mp.tasks.vision.FaceLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    for category in result.face_blendshapes:
        for blendshape in category:
            client.send_message("/" + blendshape.category_name, blendshape.score)


options: FaceLandmarkerOptions = FaceLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
    running_mode=RunningMode.LIVE_STREAM,
    result_callback=faceLandmarkResults, num_faces=1, output_face_blendshapes=True)


def loadFaceLandmark():
    global capture
    global client
    print("Loading model")
    with FaceLandmarker.create_from_options(options) as landmarker:
        frameCount: int = 0
        print("Model loaded")
        if capture is None:
            changeCam(currentCamID)
        client = udp_client.SimpleUDPClient(OSCip, OSCport)
        print("Starting")
        while enabled:
            if capture is None:
                time.sleep(0.1)
                continue
            ret, frame = capture.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue
            mp_image: Image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            landmarker.detect_async(mp_image, frameCount)
            frameCount += 1
        else:
            print("stopping")
            if capture is not None:
                capture.release()


def changeCam(cameraId: int, cameraName: str = ""):
    global capture
    global currentCamID
    global currentCamName
    try:
        if not enabled:
            return
        if currentCamID is cameraId and capture is not None:
            return
        print("Changing camera to " + str(cameraId))
        if capture is not None:
            capture.release()
        capture = cv2.VideoCapture(cameraId, cv2.CAP_DSHOW)
        capture.read()  # read a frame to make sure it works
        currentCamID = cameraId
        currentCamName = cameraName
        saveConfig()
        print("Camera changed to " + str(cameraId))
    except Exception as e:
        print(e)
        currentCamID = -1
        return


if __name__ == "__main__":
    createConfigFolder()
    loadConfig()
    try:
        UI()
    finally:
        enabled = False
