import tensorflow as tf
import cv2
import numpy as np

modelo_mascara = tf.keras.models.load_model('model/modelo_detector_mascara.h5')

def detectar_mascara(imagem_caminho):
    imagem = cv2.imread(imagem_caminho)
    if imagem is None:
        print(f"Erro: Não foi possível carregar a imagem em {imagem_caminho}.")
        return None

    imagem_redimensionada = cv2.resize(imagem, (128, 128))
    imagem_preprocessada = np.expand_dims(imagem_redimensionada / 255.0, axis=0)

    predicoes = modelo_mascara.predict(imagem_preprocessada)
    classe_prevista = np.argmax(predicoes)

    # 0: com máscara, 1: sem máscara
    return classe_prevista
