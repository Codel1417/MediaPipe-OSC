# MediaPipe OSC

This wraps Google MediaPipe Face Landmark API for real time webcam based face and eye tracking. This is designed to be used with [VRCFT-MediaPipe](https://github.com/Codel1417/VRCFT-MediaPipe).


## Build
Building an EXE

```shell
pyinstaller --noconfirm --onefile --add-data './face_landmarker.task;.'  .\mediaPipeFaceTracking.py
```