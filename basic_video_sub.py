import cv2
import numpy as np
import zmq

context = zmq.Context()
footage_socket = context.socket(zmq.SUB)
footage_socket.connect(f"tcp://localhost:8080")
footage_socket.setsockopt(zmq.SUBSCRIBE, b"")

nick = "Cultura Livre por Bala Desejo"

while True:

    frame_byte = footage_socket.recv()
    frame = np.asarray(bytearray(frame_byte))
    source = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    
    cv2.imshow(nick, source)
    
    if cv2.waitKey(1) and ord("x") == 0xFF:				
        break

cv2.destroyAllWindows()
footage_socket.close()
print("\n\nBye bye\n")