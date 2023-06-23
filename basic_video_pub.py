import base64
import cv2
import numpy as np
import zmq

context = zmq.Context()

footage_socket = context.socket(zmq.PUB)
footage_socket.bind(f"tcp://*:8080")

# init the camera
camera = cv2.VideoCapture(0)

while True:

    wasGrabbed, frame = camera.read()            # grab the current frame

    if not wasGrabbed:
        print("Can't receive frame (stream end?). Exiting...")
        break
    
    is_encoded, buffer = cv2.imencode('.jpg', frame)

    if not is_encoded:
        break

    buffer = np.array(buffer)
    footage_socket.send(buffer.tobytes())