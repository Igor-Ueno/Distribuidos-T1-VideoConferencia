import time
import zmq
import threading
import cv2
import pyaudio
import numpy as np

def subthread(socket, n): #Funcao que roda em cada thread subscriber (que vai ouvir os outros)
    while True:
        socket.subscribe("")
        message = socket.recv()
        print("\033[3" + str(n+2) + "m" + str(message) + "\033[0m")

def pubthread(socket, nome): #Funcao que roda na thread publisher (que manda msg pros outros)
    while True:
        try:
            message = input("")
            socket.send_string(nome + ": " + message)
        except zmq.ZMQError as e:
            print(e)

def pubthreadvideo(socket, cap):
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Converta o quadro em bytes
        frame_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
        
        # Envie o quadro pelo socket
        socket.send(frame_bytes)

def subthreadvideo(socket):
    socket.subscribe("")
    while True:
        frame_bytes = socket.recv()
        if(frame_bytes):
            # Converta os bytes recebidos em um quadro de imagem
            frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            # Mostrar o quadro
            cv2.imshow("Video", frame)
            
            # Pressione 'q' para sair do loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def pubthreadaudio(socket, stream, CHUNK):
    while True:
        data = stream.read(CHUNK)
        
        # Envie os dados de áudio pelo socket
        socket.send(data)

def subthreadaudio(socket):
    socket.subscribe("")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)
    while True:
        data = socket.recv()
        
        # Reproduza os dados de áudio
        stream.write(data)

#MAIN
nickname = input("Digite seu nome: ")
maxclientes = 8
context = zmq.Context()
socketpub = context.socket(zmq.PUB)
socketsub = [] # Precisa de um socket para dar subscribe em cada cliente que vc for ouvir
bindado = False #Flag que identifica se vc ja deu bind em uma porta (pra vc nao dar em mais portas)
socketpubvideo = context.socket(zmq.PUB)
socketsubvideo = []
video_capture = cv2.VideoCapture(0)
socketpubaudio = context.socket(zmq.PUB)
socketsubaudio = []
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
ips = []
ipsvideo = []
ipsaudio = []
meuip = input("escreva seu endereço de ip")
socketpub.bind("tcp://" + str(meuip) + ":5555") #bind chat
socketpubvideo.bind("tcp://" + str(meuip) + ":6666")
socketpubaudio.bind("tcp://" + str(meuip) + ":7777")
nips = input("digite o numero de ips que deseja se conectar")

threadsub = [] #para cada socket que vc der subscribe, vai ter uma thread separada
threadsubvideo = [] 
threadsubaudio = []

for i in range(0, int(nips)):
    ip = input("digite o endereço que deseja se conectar")
    ips.append(ip)

    socket = context.socket(zmq.SUB)
    socket.connect("tcp://" + str(ip) + ":5555")
    socketsub.append(socket)

    socket2 = context.socket(zmq.SUB)
    socket2.connect("tcp://" + str(ip) + ":6666")
    socketsubvideo.append(socket2)

    socket3 = context.socket(zmq.SUB)
    socket3.connect("tcp://" + str(ip) + ":7777")
    socketsubaudio.append(socket3)

    t = threading.Thread(target = subthread, args = (socketsub[i], i, )) #thread que vai receber msgs de texto de cada usuario
    t.start()
    threadsub.append(t)

    t2 = threading.Thread(target = subthreadvideo, args = (socketsubvideo[i], )) #thread que vai receber video de cada usuario
    t2.start()
    threadsubvideo.append(t2)

    t3 = threading.Thread(target = subthreadaudio, args = (socketsubaudio[i], )) #thread que vai receber audio de cada usuario
    t3.start()
    threadsubaudio.append(t3)

'''for i in range(5, 5 + maxclientes): #A porta padrao é a 5555 mas se ja tiver alguem bindado nela, vc binda na 5556-55512
    try: #tenta dar bind na porta 555 + i
        if(bindado):
            raise #raise cria um erro (joga o codigo pro except)
        #print("tentando bindar na 555" + str(i))
        socketpub.bind("tcp://*:555" + str(i)) #bind chat

        socketpubvideo.bind("tcp://*:666" + str(i))#bind video

        socketpubaudio.bind("tcp://*:777" + str(i))#bind audio

        #print("bindado a 555" + str(i))
        bindado = True
    except: #caso vc nao de bind em uma porta, voce quer se conectar a ela para poder ouvir quem der bind nela.
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:555" + str(i))
        socketsub.append(socket)

        socket2 = context.socket(zmq.SUB)
        socket2.connect("tcp://localhost:666" + str(i))
        socketsubvideo.append(socket2)

        socket3 = context.socket(zmq.SUB)
        socket3.connect("tcp://localhost:777" + str(i))
        socketsubaudio.append(socket3)

        #print("conectado na 555" + str(i))'''

'''for i in range(0, maxclientes - 1):
    t = threading.Thread(target = subthread, args = (socketsub[i], i, )) #thread que vai receber msgs de texto de cada usuario
    t.start()
    threadsub.append(t)

    t2 = threading.Thread(target = subthreadvideo, args = (socketsubvideo[i], )) #thread que vai receber video de cada usuario
    t2.start()
    threadsubvideo.append(t2)

    t3 = threading.Thread(target = subthreadaudio, args = (socketsubaudio[i], )) #thread que vai receber audio de cada usuario
    t3.start()
    threadsubaudio.append(t3)'''



threadpub = threading.Thread(target=pubthread, args= (socketpub, nickname, ))#thread que vai enviar msgs de texto 
threadpubvideo = threading.Thread(target=pubthreadvideo, args= (socketpubvideo, video_capture, ))#thread que vai enviar video
threadpubaudio = threading.Thread(target=pubthreadaudio, args= (socketpubaudio, stream, CHUNK, ))#thread que vai enviar audio
threadpub.start()
threadpubvideo.start()
threadpubaudio.start()
print("conectado")

#while True:
    #ret, frame = video_capture.read()
#time.sleep(25)