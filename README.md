# MediaPipe OSC

This wraps Google [MediaPipe Face Landmark API](https://developers.google.com/mediapipe/solutions/vision/face_landmarker) for real time webcam based face and eye tracking. This is designed to be used with [VRCFT-MediaPipe](https://github.com/Codel1417/VRCFT-MediaPipe). This is only tested and supported on Windows 11, but the code itself should be compatible with linux and mac with minimal editing.

## How to use

1. Download the [latest EXE](https://github.com/Codel1417/MediaPipe-OSC/releases)
2. Start it
<img width="221" alt="image" src="https://github.com/Codel1417/MediaPipe-OSC/assets/13484789/6992e38d-ee15-46bb-976d-7a0db81cd907">

3. Select the camera to use
4. Check the enabled box
5. If [VRCFaceTracking](https://github.com/benaclejames/VRCFaceTracking) is set up with the [VRCFT-MediaPipe](https://github.com/Codel1417/VRCFT-MediaPipe) plugin, Face tracking should be ready to go.

### Notes

- Requires a webcam.
- The OSC port is editable, but the VRCFT plugin only supports port 8888.

## Build
Building an EXE
- setup Python3 on windows
- Install dependencies `pip -r requirements.txt`
- build the EXE `pyinstaller --noconfirm .\mediaPipeFaceTracking.spec`
