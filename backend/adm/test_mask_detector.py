import tensorflow as tf
import cv2
import numpy as np

modelo = tf.keras.models.load_model("model/modelo_detector_mascara.h5")


def detectar_mascara(imagem_caminho):
    imagem = cv2.imread(imagem_caminho)

    if imagem is None:
        print(f"Erro: Não foi possível carregar a imagem em {imagem_caminho}. Verifique o caminho.")
        return

    imagem_redimensionada = cv2.resize(imagem, (128, 128))

    imagem_preprocessada = np.expand_dims(imagem_redimensionada / 255.0, axis=0)

    predicoes = modelo.predict(imagem_preprocessada)

    # Resultado: 0 para "com máscara", 1 para "sem máscara"
    classe_prevista = np.argmax(predicoes)
    return classe_prevista


caminho_imagem = "imagens/Screenshot_5.jpg"
resultado = detectar_mascara(caminho_imagem)

if resultado == 0:
    print("A pessoa está usando máscara.")
elif resultado == 1:
    print("A pessoa não está usando máscara.")
else:
    print("Erro na predição.")
