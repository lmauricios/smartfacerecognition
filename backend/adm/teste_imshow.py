import cv2
import socket
import struct
import pickle

# Configuração do cliente para se conectar ao servidor de vídeo no Windows
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("192.168.101.73", 8080))  # Substitua pelo IP do Windows

data = b""
payload_size = struct.calcsize("L")

print("Conectado ao servidor de vídeo.")

while True:
    # Receber o tamanho da mensagem
    while len(data) < payload_size:
        data += client_socket.recv(4096)
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]

    # Receber o quadro da câmera
    while len(data) < msg_size:
        data += client_socket.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Deserializar o quadro e mostrar
    frame = pickle.loads(frame_data)
    cv2.imshow("Stream de Vídeo", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

client_socket.close()
cv2.destroyAllWindows()
