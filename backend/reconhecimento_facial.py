import socket
import struct
import pickle
import cv2
import face_recognition
import numpy as np
import psycopg2
import os # Para verificar existência de arquivos de modelo
import logging # Adicionado para melhor logging

# from tensorflow.keras.models import load_model # Comentado, pois não é usado NESTE script.
                                                 # Mantenha tensorflow instalado para os scripts de máscara.

# --- Configurações ---
DB_HOST = os.getenv("DB_HOST_SCRIPT", "localhost")
DB_NAME = os.getenv("DB_NAME_SCRIPT", "reconhecimento_facial")
DB_USER = os.getenv("DB_USER_SCRIPT", "meu_usuario")
DB_PASS = os.getenv("DB_PASS_SCRIPT", "Innovate@V8")  # Carregar de variáveis de ambiente

STREAM_SERVER_HOST = os.getenv("STREAM_SERVER_HOST", 'localhost')
STREAM_SERVER_PORT = int(os.getenv("STREAM_SERVER_PORT", 8080))

# Parâmetros de detecção e reconhecimento
DNN_CONFIDENCE_THRESHOLD = 0.5  # Limiar de confiança para o detector de faces OpenCV DNN
FACE_REC_TOLERANCE = 0.6        # Tolerância para face_recognition.compare_faces
MIN_SIMILARITY_AT_TOLERANCE = 50.0 # Similaridade mínima em % quando a distância é igual à tolerância
MODEL_DIR = "face_detector"
DNN_PROTO_PATH = os.path.join(MODEL_DIR, "deploy.prototxt")
DNN_MODEL_PATH = os.path.join(MODEL_DIR, "res10_300x300_ssd_iter_140000.caffemodel")

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_db():
    """Estabelece conexão com o banco de dados PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        logging.info("Conexão com o banco de dados PostgreSQL estabelecida.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def load_known_faces_from_db(conn):
    """Carrega encodings e nomes de faces conhecidas do banco de dados."""
    if not conn:
        return [], []

    encodings_conhecidos = []
    nomes_conhecidos = []
    try:
        with conn.cursor() as cur:
            # Alterado para buscar da coluna correta 'face_encoding'
            cur.execute("SELECT nome_pessoa, face_encoding FROM pessoas WHERE face_encoding IS NOT NULL")
            pessoas = cur.fetchall()

            if not pessoas:
                logging.info("Nenhuma pessoa encontrada no banco de dados para carregar encodings.")
                return [], []

            logging.info(f"Carregando encodings para {len(pessoas)} pessoa(s) do banco de dados...")
            for nome_pessoa, face_encoding_bytes in pessoas:
                if face_encoding_bytes is None:
                    logging.warning(f"Encoding facial nulo para {nome_pessoa} no banco de dados.")
                    continue
                try:
                    # O encoding é armazenado como bytes de um array numpy.
                    # Precisamos reconstruir o array numpy.
                    # Assumindo que o encoding tem 128 dimensões e é float64.
                    encoding = np.frombuffer(face_encoding_bytes, dtype=np.float64)
                    if encoding.shape == (128,): # Validação básica da forma do encoding
                        encodings_conhecidos.append(encoding)
                        nomes_conhecidos.append(nome_pessoa)
                    else:
                        logging.warning(f"Encoding para {nome_pessoa} tem forma inesperada: {encoding.shape}. Pulando.")
                except Exception as e:
                    logging.warning(f"Não foi possível converter os bytes do encoding para {nome_pessoa}. Erro: {e}")
            
            if encodings_conhecidos:
                logging.info(f"Total de {len(encodings_conhecidos)} encodings conhecidos carregados com sucesso.")
    except psycopg2.Error as e:
        logging.error(f"Erro ao buscar dados de pessoas do banco: {e}")
    
    return encodings_conhecidos, nomes_conhecidos

def load_opencv_dnn_face_detector():
    """Carrega o modelo de detecção de faces (OpenCV DNN Caffe)."""
    try:
        logging.info("Carregando modelo de detecção de faces (OpenCV DNN)...")
        if not (os.path.exists(DNN_PROTO_PATH) and os.path.exists(DNN_MODEL_PATH)):
            logging.error(f"Arquivos de modelo não encontrados. Verifique os caminhos: {DNN_PROTO_PATH}, {DNN_MODEL_PATH}")
            return None
        face_net = cv2.dnn.readNet(DNN_PROTO_PATH, DNN_MODEL_PATH)
        logging.info("Modelo de detecção de faces carregado com sucesso.")
        return face_net
    except cv2.error as e:
        logging.error(f"Erro ao carregar o modelo de detecção de faces OpenCV DNN: {e}")
        return None

def detect_recognize_draw(frame, face_net, known_encodings, known_names):
    """Detecta faces, reconhece, e desenha informações no frame, incluindo similaridade."""
    if frame is None: return frame
    if face_net is None: return frame

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
    face_net.setInput(blob)
    detections = face_net.forward()

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > DNN_CONFIDENCE_THRESHOLD:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            startX = max(0, startX)
            startY = max(0, startY)
            endX = min(w - 1, endX)
            endY = min(h - 1, endY)

            if startX >= endX or startY >= endY:
                continue

            face_roi_bgr = frame[startY:endY, startX:endX]
            if face_roi_bgr.size == 0:
                continue
            
            face_roi_rgb = cv2.cvtColor(face_roi_bgr, cv2.COLOR_BGR2RGB)

            current_face_encodings = face_recognition.face_encodings(face_roi_rgb, 
                known_face_locations=[(0, face_roi_rgb.shape[1], face_roi_rgb.shape[0], 0)])
            current_face_landmarks_list = face_recognition.face_landmarks(face_roi_rgb)

            name = "Desconhecido"
            display_text = name # Texto padrão a ser exibido

            if current_face_encodings:
                current_face_encoding = current_face_encodings[0]
                
                if known_encodings: # Só compara se houver encodings conhecidos
                    matches = face_recognition.compare_faces(known_encodings, current_face_encoding, tolerance=FACE_REC_TOLERANCE)
                    face_distances = face_recognition.face_distance(known_encodings, current_face_encoding)
                    
                    if len(face_distances) > 0: # Deve ser sempre verdade se known_encodings não estiver vazio
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_names[best_match_index]
                            distance = face_distances[best_match_index]
                            
                            # 1. Similaridade Escalada (existente, baseada na tolerância e mínimo configurado)
                            # Mapeia distância [0.0, FACE_REC_TOLERANCE] para similaridade [100%, MIN_SIMILARITY_AT_TOLERANCE]
                            scaled_similarity_pct = MIN_SIMILARITY_AT_TOLERANCE + \
                                                    ((FACE_REC_TOLERANCE - distance) / FACE_REC_TOLERANCE) * \
                                                    (100.0 - MIN_SIMILARITY_AT_TOLERANCE)
                            # Garante que está visualmente entre 0-100, embora o natural seja [MIN_SIMILARITY_AT_TOLERANCE, 100]
                            scaled_similarity_pct = max(0.0, min(100.0, scaled_similarity_pct))

                            # 2. Similaridade Geral (nova, direta em relação à distância 0)
                            # Mapeia distância [0.0, FACE_REC_TOLERANCE] para similaridade [100%, 0%]
                            # Se distance > FACE_REC_TOLERANCE, será 0% após o clamp.
                            overall_match_pct = (1.0 - (distance / FACE_REC_TOLERANCE)) * 100.0
                            overall_match_pct = max(0.0, min(100.0, overall_match_pct)) # Clamp para 0-100%

                            # Simplificando a exibição para apenas uma métrica de similaridade
                            display_text = f"{name} ({scaled_similarity_pct:.1f}%)"
                        # Se não houver match (matches[best_match_index] é False), 'name' continua "Desconhecido"
                        # e 'display_text' também.
            # Desenho
            color = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)
            cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
            
            # Ajusta o posicionamento do texto para evitar sair da tela e sobreposição
            text_size, _ = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            text_y = startY - 10 
            if text_y < text_size[1]: # Se for sair por cima
                 text_y = startY + text_size[1] + 10 # Coloca abaixo da caixa, dentro dela
                 if text_y + text_size[1] > endY: # Se ainda assim for sair por baixo da caixa
                     text_y = endY - 5 # Coloca um pouco acima da borda inferior da caixa


            cv2.putText(frame, display_text, (startX + 5, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2) # Tamanho da fonte 0.5, adicionado um pequeno offset em X

            # Opcional: Desenhar landmarks (pode ser visualmente ruidoso)
            # if current_face_landmarks_list:
            #     landmarks = current_face_landmarks_list[0] 
            #     for landmark_type in landmarks.keys():
            #         for (lx, ly) in landmarks[landmark_type]:
            #             cv2.circle(frame, (startX + lx, startY + ly), 1, (255, 0, 0), -1)
    return frame

def main():
    db_connection = connect_db()
    if not db_connection:
        logging.error("Encerrando: Falha na conexão com o banco de dados.")
        return

    known_encodings, known_names = load_known_faces_from_db(db_connection)
    
    face_detector_net = load_opencv_dnn_face_detector()
    if not face_detector_net:
        logging.error("Encerrando: Falha ao carregar o modelo de detecção de faces.")
        if db_connection: db_connection.close()
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        logging.info(f"Tentando conectar ao servidor de stream em {STREAM_SERVER_HOST}:{STREAM_SERVER_PORT}...")
        client_socket.connect((STREAM_SERVER_HOST, STREAM_SERVER_PORT))
        logging.info("Conectado ao servidor de stream com sucesso.")
    except socket.error as e:
        logging.error(f"Erro ao conectar ao servidor de stream: {e}")
        logging.error("Verifique se o 'video_stream_server.py' está rodando e acessível.")
        if db_connection: db_connection.close()
        return

    data_buffer = b""
    # "!I" é para unsigned int (4 bytes) em network byte order (big-endian).
    payload_size = struct.calcsize("!I") 

    logging.info("Aguardando e processando frames do servidor...")
    window_title = "Reconhecimento Facial (Cliente Stream - Linux Mint)"
    try:
        while True:
            while len(data_buffer) < payload_size:
                packet = client_socket.recv(4096)
                if not packet:
                    raise ConnectionAbortedError("Servidor fechou a conexão (tamanho do payload).")
                data_buffer += packet
            
            packed_msg_size = data_buffer[:payload_size]
            data_buffer = data_buffer[payload_size:]
            msg_size = struct.unpack("!I", packed_msg_size)[0]

            while len(data_buffer) < msg_size:
                packet = client_socket.recv(4096) # Adicionado `packet =` aqui
                if not packet: 
                    raise ConnectionAbortedError("Servidor fechou a conexão (dados do frame).")
                data_buffer += packet

            frame_data = data_buffer[:msg_size]
            data_buffer = data_buffer[msg_size:]

            try:
                frame = pickle.loads(frame_data)
            except pickle.UnpicklingError as e:
                logging.error(f"Erro ao desserializar frame (pickle): {e}. Pulando este frame.")
                continue
            except Exception as e: 
                logging.error(f"Erro inesperado ao processar frame_data (pickle): {e}")
                continue
            
            if frame is None:
                logging.warning("Frame recebido é None. Pulando.")
                continue

            processed_frame = detect_recognize_draw(frame, face_detector_net, known_encodings, known_names)
            
            cv2.imshow(window_title, processed_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logging.info("Tecla 'q' pressionada. Encerrando cliente...")
                break
    
    except ConnectionAbortedError as e:
        logging.warning(f"Conexão com o servidor perdida: {e}")
    except socket.error as e:
        logging.error(f"Erro de socket: {e}")
    except KeyboardInterrupt:
        logging.info("Interrupção pelo usuário (Ctrl+C). Encerrando cliente...")
    except Exception as e:
        logging.exception(f"Erro inesperado no loop principal do cliente:") # logging.exception inclui traceback
    finally:
        logging.info("Fechando recursos do cliente...")
        client_socket.close()
        cv2.destroyAllWindows()
        if db_connection:
            db_connection.close()
            logging.info("Conexão com o banco de dados fechada.")
        logging.info("Cliente de reconhecimento facial encerrado.")

if __name__ == "__main__":
    main()