import base64
import cv2
import numpy as np
import pyaudio
import sys
import threading
import time
import zmq

class VideoConference:

	def __init__(self, nickname = "Somebody"):

		self.context = zmq.Context()
		self.camera = cv2.VideoCapture(0)
		self.pub_port = np.array([-1, -1, -1], dtype=[('CHAT', 'int8'), ('VIDEO', 'int8'), ('AUDIO', 'int8')])
		self.sub_ports = np.array([-1, -1, -1], dtype=[('CHAT', 'int8'), ('VIDEO', 'int8'), ('AUDIO', 'int8')])
		self.nick = nickname
	
	def set_pub_chat(self, port_pub):

		self.chat_socket_pub = self.context.socket(zmq.PUB)
		self.chat_socket_pub.bind(f"tcp://*:{port_pub}")

	def set_sub_chat(self, port_sub):

		self.chat_socket_sub = self.context.socket(zmq.SUB)
		self.chat_socket_sub.connect(f"tcp://localhost:{port_sub}")
		self.chat_socket_sub.setsockopt_string(zmq.SUBSCRIBE, "")
	
	def set_pub_video(self, port_pub):

		self.footage_socket_pub = self.context.socket(zmq.PUB)
		self.footage_socket_pub.bind(f"tcp://*:{port_pub}")
	
	def sub_video(self, port_sub):

		self.footage_socket_sub = self.context.socket(zmq.SUB)
		self.footage_socket_sub.connect(f"tcp://192.168.0.41:{port_sub}")
		self.footage_socket_sub.setsockopt_string(zmq.SUBSCRIBE, "")
	
	def finish_conference(self):

		# self.chat_socket_pub.close()
		# self.chat_socket_sub.close()
		# self.footage_socket_pub.close()
		# self.footage_socket_sub.close()
		cv2.destroyAllWindows()
		self.context.term()

def sub_side(port_sub: str,
			 context: zmq.Context = None):
	
	context = context or zmq.Context.instance()

	subscriber = context.socket(zmq.SUB)
	subscriber.connect(f"tcp://localhost:{port_sub}")
	subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

	while True:

		try:

			message = subscriber.recv_string()
			print(message)

		except KeyboardInterrupt:

			subscriber.close()

def pub_side(nick: str,
			 port_pub: str,
			 context: zmq.Context = None):

	context = context or zmq.Context.instance()

	publisher = context.socket(zmq.PUB)
	publisher.bind(f"tcp://*:{port_pub}")

	while True:

		try:

			message = input()
			message = f"[{nick}] : {message}"
			# publisher.send_multipart([b"msg", bytes(url_pub, "ascii"), bytes(message, "ascii")])
			publisher.send_string(message)

		except KeyboardInterrupt:

			publisher.close()

def pub_video(nick: str,
			  port_pub: str,
			  camera = None,
			  context: zmq.Context = None):

	context = zmq.Context().instance()

	footage_socket = context.socket(zmq.PUB)
	footage_socket.bind(f"tcp://*:{port_pub}")

	# init the camera

	while True:

		wasGrabbed, frame = camera.read()

		if not wasGrabbed:
			print("Can't receive frame (stream end?). Exiting...")
			break
		
		is_encoded, buffer = cv2.imencode('.jpg', frame)

		if not is_encoded:
			break
		
		buffer = np.array(buffer)
		footage_socket.send(buffer.tobytes())
	
	footage_socket.close()
	print("\n\nBye bye\n")

def sub_video(port_sub: str,
			  context: zmq.Context = None):

	context = zmq.Context.instance()
	footage_socket = context.socket(zmq.SUB)
	footage_socket.connect(f"tcp://192.168.0.41:{port_sub}")
	footage_socket.setsockopt_string(zmq.SUBSCRIBE, "")

	# camera = cv2.VideoCapture("output.avi")

	while True:

		frame_byte = footage_socket.recv()
		frame = np.asarray(bytearray(frame_byte))
		source = cv2.imdecode(frame, cv2.IMREAD_COLOR)

		cv2.imshow("Frame", source)
		
		if cv2.waitKey(10) and ord("x") == 0xFF:				
			break
	
	cv2.destroyAllWindows()
	footage_socket.close()
	print("\n\nBye bye\n")

def pub_audio():

	print()

def main():

	# print("-> Login")
	# print()
	# user = input("Username: ")
	# password = input("Password: ")

	nick = input("Enter your nickname: ")
	pub_port = input("Enter publisher's port: ")
	sub_port = input("Enter subscriber's ports: ")
	first_port = 8080

	context = zmq.Context.instance()
	camera = cv2.VideoCapture(0)

	# while True:

	try:

		# pub = threading.Thread(target=pub_side, args=(nick, pub_port,))
		# sub = threading.Thread(target=sub_side, args=(sub_port,))		
		
		# pub.daemon = True
		# sub.daemon = True		
		
		# pub.start()
		# sub.start()		
		
		# pub.join()
		# sub.join()		

		# pub2 = threading.Thread(target=pub_video, args=(nick, pub_port, camera,))
		# sub2 = threading.Thread(target=sub_video, args=(sub_port,))

		# pub2.daemon = True
		# sub2.daemon = True

		# pub2.start()
		# sub2.start()

		# pub2.join()
		# sub2.join()

		FS = 11025  # Hz
		CHUNKSZ = 256  # samples
		
		p = pyaudio.PyAudio()
		stream = p.open(format=pyaudio.paInt16,
						channels=1,
						rate=FS,
						input=True,
						frames_per_buffer=CHUNKSZ)


		data = stream.read(CHUNKSZ)

		stream.stop_stream()
		stream.close()
		p.terminate()
		
		camera.release()
		context.term()

	except KeyboardInterrupt:

		context.term()

def main2():

	nick = input("Enter your nickname: ")
	video_conference = VideoConference(nick)
	time.sleep(5)
	video_conference.finish_conference()

if __name__ == "__main__":
	main()