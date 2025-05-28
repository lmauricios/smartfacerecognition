import cv2
import socket
import struct
import pickle
import time # Para adicionar um pequeno delay em caso de erro na captura

# --- Configurações ---
HOST = '0.0.0.0'  # Escuta em todas as interfaces disponíveis
PORT = 8080       # Porta para o servidor de stream
CAMERA_INDEX = 0  # Índice da câmera (0 geralmente é a padrão)

def main():
    # Configura a câmera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Erro: Não foi possível abrir a câmera no índice {CAMERA_INDEX}.")
        print("Verifique se a câmera está conectada e não está sendo usada por outro aplicativo.")
        print("Você pode precisar instalar drivers ou pacotes adicionais para sua câmera no Linux Mint.")
        print("Tente listar câmeras com: v4l2-ctl --list-devices (instale v4l-utils se necessário)")
        return

    print(f"Câmera {CAMERA_INDEX} aberta com sucesso.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) # Opcional: definir resolução
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # Opcional: definir resolução

    # Configura o socket do servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permite reutilizar o endereço para evitar erro "Address already in use"
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1) # Aceita apenas uma conexão por vez
        print(f"Servidor de stream aguardando conexão em {HOST}:{PORT}...")
        
        # Aceita a conexão do cliente
        conn, addr = server_socket.accept()
        print(f"Conexão estabelecida com {addr}")

        with conn: # Usar 'with' garante que o socket do cliente seja fechado
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    print("Erro ao capturar frame da câmera. Tentando novamente...")
                    time.sleep(0.1) # Pequena pausa antes de tentar novamente
                    # Poderia adicionar um contador aqui para sair após X falhas consecutivas
                    continue
                
                # Serializa o frame
                try:
                    data = pickle.dumps(frame, protocol=pickle.HIGHEST_PROTOCOL) # Usar o protocolo mais alto
                except pickle.PicklingError as e:
                    print(f"Erro ao serializar frame (pickle): {e}. Pulando este frame.")
                    continue
                except Exception as e:
                    print(f"Erro inesperado ao serializar frame (pickle): {e}")
                    continue

                # Empacota o tamanho da mensagem (usando 'I' para unsigned int, consistente com o cliente)
                try:
                    message_size = struct.pack("!I", len(data)) # '!' para big-endian (network byte order)
                                                              # 'I' para unsigned int
                except struct.error as e:
                    print(f"Erro ao empacotar o tamanho da mensagem (struct): {e}. Pulando este frame.")
                    continue

                # Envia o tamanho da mensagem e depois os dados do frame
                try:
                    conn.sendall(message_size + data)
                except socket.error as e:
                    print(f"Erro de socket ao enviar dados para {addr}: {e}")
                    print("Cliente pode ter desconectado.")
                    break # Sai do loop se não puder enviar (cliente desconectou)
                except Exception as e:
                    print(f"Erro inesperado ao enviar dados para o cliente: {e}")
                    break


    except socket.error as e:
        print(f"Erro de socket do servidor: {e}")
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuário (Ctrl+C).")
    except Exception as e:
        print(f"Erro inesperado no servidor: {e}")
    finally:
        print("Encerrando servidor de stream...")
        if 'cap' in locals() and cap.isOpened():
            cap.release()
            print("Câmera liberada.")
        if 'server_socket' in locals():
            server_socket.close()
            print("Socket do servidor fechado.")
        print("Servidor de stream encerrado.")

if __name__ == "__main__":
    main()