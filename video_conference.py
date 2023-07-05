import cv2
import numpy as np
import pyaudio
import threading
import zmq

class VideoConference:
    def __init__(self, nick='Nome Sobrenome', my_ip = '*', ip_list='localhost'):
        self.context = zmq.Context()
        self.max_nodes = 8
        self.nick = nick
        self.my_ip = my_ip
        self.ip_list = ip_list.split()        
        self.publisher = dict()
        self.subscriber = dict()
        self.pub_permissions = {'TEXT': True, 'VIDEO': True, 'AUDIO': True}
        self.sub_permissions = {'TEXT': True, 'VIDEO': True, 'AUDIO': True}

        # Configura os sockets de publish e subscribe
        self.set_pub()
        self.set_sub()

        # Inicializa o que necessario para enviar video e audio
        self.set_video()
        self.set_audio()

        # Inicializa as threads de publisher e subscriber
        self.start_pub_threads()
        self.start_sub_threads()
    
    def set_pub(self):
        # self.pub_socket = zmq.socket(zmq.PUB)
        self.publisher['TEXT']  = self.context.socket(zmq.PUB)
        self.publisher['VIDEO'] = self.context.socket(zmq.PUB)
        self.publisher['AUDIO'] = self.context.socket(zmq.PUB)

        self.publisher['TEXT'].bind(f'tcp://{self.my_ip}:5555')
        self.publisher['VIDEO'].bind(f'tcp://{self.my_ip}:6666')
        self.publisher['AUDIO'].bind(f'tcp://{self.my_ip}:7777')
    
    def set_sub(self):
        # self.sub_socket = zmq.socket(zmq.SUB)
        self.subscriber['TEXT']  = []
        self.subscriber['VIDEO'] = []
        self.subscriber['AUDIO'] = []

        for ip in self.ip_list:
            sock_text = self.context.socket(zmq.SUB)
            sock_video = self.context.socket(zmq.SUB)
            sock_audio = self.context.socket(zmq.SUB)

            sock_text.connect(f'tcp://{ip}:5555')
            sock_video.connect(f'tcp://{ip}:6666')
            sock_audio.connect(f'tcp://{ip}:7777')

            # sock_text.setsockopt_string(zmq.SUBSCRIBE, '')
            # sock_video.setsockopt_string(zmq.SUBSCRIBE, '')
            # sock_audio.setsockopt_string(zmq.SUBSCRIBE, '')
            sock_text.subscribe('')
            sock_video.subscribe('')
            sock_audio.subscribe('')

            self.subscriber['TEXT'].append(sock_text)
            self.subscriber['VIDEO'].append(sock_video)
            self.subscriber['AUDIO'].append(sock_audio)
    
    def set_video(self):
        # Liga a camera
        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    def set_audio(self):
        # Liga o microfone
        self.CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        audio = pyaudio.PyAudio()
        self.stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=self.CHUNK)
    
    def start_pub_threads(self):
        # Configura e inicia os threads de publish
        pub_text_thread = threading.Thread(target=self.pub_text, args=())
        pub_video_thread = threading.Thread(target=self.pub_video, args=())
        pub_audio_thread = threading.Thread(target=self.pub_audio, args=())
        pub_text_thread.start()
        pub_video_thread.start()
        pub_audio_thread.start()
    
    def pub_text(self):
        while self.pub_permissions['TEXT']:
            try:
                # Aguarda o usuário informar uma mensagem
                message = input("")
                # self.publisher['TEXT'].send(bytes(f'[{self.nick}]: {message}', 'utf-8'))
                self.publisher['TEXT'].send_multipart([self.nick.encode(), message.encode()])
            except (KeyboardInterrupt, Exception) as error:
                print(f'Aconteceu um erro inesperado no pub_text -> {error.__class__.__name__}')
                self.pub_permissions['TEXT'] = False
                break
    
    def pub_video(self):
        while self.pub_permissions['VIDEO']:
            try:
                ret, frame = self.camera.read()

                if not ret:
                    break
                
                # Converta o quadro em bytes
                frame_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
                
                # Envie o quadro pelo socket
                # self.publisher['VIDEO'].send(bytes(self.nick, 'utf-8'), zmq.SNDMORE)
                # self.publisher['VIDEO'].send(frame_bytes)
                self.publisher['VIDEO'].send_multipart([self.nick.encode(), frame_bytes])
            except (KeyboardInterrupt, Exception) as error:
                print(f'Aconteceu um erro inesperado no pub_video -> {error}')
                self.pub_permissions['VIDEO'] = False
                break
    
    def pub_audio(self):
        while self.pub_permissions['AUDIO']:
            try:
                data = self.stream.read(self.CHUNK)
                # self.publisher['AUDIO'].send(data)
                self.publisher['AUDIO'].send_multipart([self.nick.encode(), data])
            except (KeyboardInterrupt, Exception) as error:
                print(f'Aconteceu um erro inesperado pub_audio -> {error}')
                self.pub_permissions['AUDIO'] = False
                break
    
    def start_sub_threads(self):
        for sock in self.subscriber['TEXT']:
            sub_text_thread = threading.Thread(target=self.sub_text, args=(sock,))
            sub_text_thread.start()
        
        for sock in self.subscriber['VIDEO']:
            sub_video_thread = threading.Thread(target=self.sub_video, args=(sock,))
            sub_video_thread.start()
        
        for sock in self.subscriber['AUDIO']:
            sub_audio_thread = threading.Thread(target=self.sub_audio, args=(sock,))
            sub_audio_thread.start()
    
    def sub_text(self, socket):
        while self.sub_permissions['TEXT']:
            try:
                # nick = socket.recv()
                # message = socket.recv()
                nick, message = socket.recv_multipart()
                print(f'\033[33m[{nick.decode("utf-8")}]: {message.decode("utf-8")}\033[0m')
            except (KeyboardInterrupt, Exception) as error:
                print(f'Aconteceu um erro inesperado sub_text -> {error}')
                self.sub_permissions['TEXT'] = False
                break
    
    def sub_video(self, socket):
        while self.sub_permissions['VIDEO']:
            try:
                # nick = socket.recv().decode('utf-8')
                # frame_bytes = socket.recv()
                nick, frame_bytes = socket.recv_multipart()
                nick = nick.decode()
                if(frame_bytes):
                    # Converta os bytes recebidos em um quadro de imagem
                    frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    # Mostrar o quadro
                    cv2.imshow(nick, frame)
                    
                    # Pressione 'q' para sair do loop
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            except (KeyboardInterrupt, Exception) as error:
                print(f'Aconteceu um erro inesperado sub_video -> {error}')
                self.sub_permissions['VIDEO'] = False
                break
    
    def sub_audio(self, socket):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)
        while self.sub_permissions['AUDIO']:
            try:
                # data = socket.recv()
                nick, data = socket.recv_multipart()
                nick = nick.decode()
                
                # Reproduza os dados de áudio
                stream.write(data)
            except (KeyboardInterrupt, Exception) as error:
                print(f'Aconteceu um erro inesperado sub_audio -> {error}')
                self.sub_permissions['AUDIO'] = False
                break
    
    def __del__(self):
        self.camera.release()
        cv2.destroyAllWindows()

        self.publisher['TEXT'].close()
        self.publisher['VIDEO'].close()
        self.publisher['AUDIO'].close()

        for sock in self.subscriber['TEXT']:
            sock.close()

        for sock in self.subscriber['VIDEO']:
            sock.close()

        for sock in self.subscriber['AUDIO']:
            sock.close()

        self.context.term()

def main():
    nick = input('Digite seu nome: ')
    my_ip = input('Digite seu endereço IP: ')
    ip_list = input('Digite os endereços IPs que deseja se conectar: ')

    try:
        video_conference = VideoConference(nick, my_ip, ip_list)
    except (KeyboardInterrupt, Exception) as error:
        print(f'Aconteceu um erro inesperado -> {error}')
        del video_conference

if __name__ == '__main__':
    main()