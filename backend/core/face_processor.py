import cv2
import face_recognition
import numpy as np
import os

from utils.logger_config import log


class FaceProcessor:
    DNN_CONFIDENCE_THRESHOLD = 0.6  # Aumentado um pouco para robustez
    FACE_REC_TOLERANCE = 0.55  # Ajustado para ser um pouco mais estrito
    MIN_SIMILARITY_AT_TOLERANCE = 60.0

    def __init__(self, model_dir="face_detector"):
        self.face_net = self._load_opencv_dnn_face_detector(model_dir)
        if not self.face_net:
            log.error("Falha crítica: Modelo de detecção de faces não pôde ser carregado.")
            # Em uma aplicação real, poderia levantar uma exceção aqui para parar a inicialização

    def _load_opencv_dnn_face_detector(self, model_dir: str):
        """Carrega o modelo de detecção de faces (OpenCV DNN Caffe)."""
        try:
            proto_path = os.path.join(model_dir, "deploy.prototxt")
            model_path = os.path.join(model_dir, "res10_300x300_ssd_iter_140000.caffemodel")

            if not (os.path.exists(proto_path) and os.path.exists(model_path)):
                log.error(f"Arquivos de modelo não encontrados. Verifique os caminhos: {proto_path}, {model_path}")
                return None

            log.info("Carregando modelo de detecção de faces (OpenCV DNN)...")
            face_net = cv2.dnn.readNet(proto_path, model_path)
            log.info("Modelo de detecção de faces carregado com sucesso.")
            return face_net
        except cv2.error as e:
            log.error(f"Erro ao carregar o modelo de detecção de faces OpenCV DNN: {e}")
            return None

    def get_face_encodings_from_image_bytes(self, image_bytes: bytes) -> list:
        """Extrai encodings faciais de uma imagem fornecida como bytes."""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                log.error("Não foi possível decodificar a imagem para extrair encodings.")
                return []

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            # Usar o detector DNN para encontrar as localizações das faces primeiro
            (h, w) = img_rgb.shape[:2]
            blob = cv2.dnn.blobFromImage(img_rgb, 1.0, (300, 300), (104.0, 177.0, 123.0))
            self.face_net.setInput(blob)
            detections = self.face_net.forward()

            face_locations_dnn = []
            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > self.DNN_CONFIDENCE_THRESHOLD:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    # face_recognition espera (top, right, bottom, left)
                    face_locations_dnn.append((startY, endX, endY, startX))

            if not face_locations_dnn:
                log.info("Nenhuma face detectada pelo DNN na imagem para encoding.")
                return []

            encodings = face_recognition.face_encodings(img_rgb, known_face_locations=face_locations_dnn)
            log.info(f"Extraídos {len(encodings)} encodings da imagem.")
            return encodings
        except Exception as e:
            log.error(f"Erro ao extrair encodings da imagem: {e}")
            return []

    def recognize_faces_in_frame(self, frame_bgr: np.ndarray, known_encodings: list, known_names: list) -> list:
        """Detecta e reconhece faces em um frame, retornando uma lista de resultados."""
        results = []
        if frame_bgr is None or self.face_net is None or not known_encodings:
            return results

        (h, w) = frame_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(frame_bgr, 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.face_net.setInput(blob)
        detections = self.face_net.forward()

        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.DNN_CONFIDENCE_THRESHOLD:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                face_roi_bgr = frame_bgr[startY:endY, startX:endX]
                if face_roi_bgr.size == 0:
                    continue

                face_roi_rgb = cv2.cvtColor(face_roi_bgr, cv2.COLOR_BGR2RGB)
                current_encodings = face_recognition.face_encodings(face_roi_rgb)

                if current_encodings:
                    current_encoding = current_encodings[0]
                    matches = face_recognition.compare_faces(
                        known_encodings, current_encoding, tolerance=self.FACE_REC_TOLERANCE
                    )
                    face_distances = face_recognition.face_distance(known_encodings, current_encoding)

                    if True in matches:  # Se houve algum match
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_names[best_match_index]
                            similarity = (1 - face_distances[best_match_index]) * 100  # Similaridade simples
                            results.append(
                                {"name": name, "box": [startX, startY, endX, endY], "similarity": similarity}
                            )
                            log.debug(f"Face reconhecida: {name} com similaridade {similarity:.2f}%")
        return results
