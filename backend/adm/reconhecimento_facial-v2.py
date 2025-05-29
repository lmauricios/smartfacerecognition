import psycopg2
import face_recognition
import cv2
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import numpy as np
from datetime import datetime
from detect_mask import detectar_mascara

conn = psycopg2.connect(host="localhost", database="reconhecimento_facial", user="meu_usuario", password="Innovate@V8")
cur = conn.cursor()


# Função para salvar logs
def salvar_log(diretorio_log, conteudo_log):
    with open(f"{diretorio_log}/log.txt", "a") as log_file:
        log_file.write(conteudo_log + "\n")


# Ajusta os pontos faciais para focar apenas nas áreas dos olhos e testa
def ajustar_areas_com_mascara(face_landmarks_list):
    ajustados = []
    for face_landmarks in face_landmarks_list:
        eyes_and_forehead = {
            key: face_landmarks[key] for key in ["left_eye", "right_eye", "left_eyebrow", "right_eyebrow"]
        }
        ajustados.append(eyes_and_forehead)
    return ajustados


# Reconhecimento facial com logs e armazenamento de imagem processada
def reconhecimento_facial():
    print("Abrindo diálogo para selecionar a imagem...")
    caminho_foto = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])

    if not caminho_foto:
        print("Nenhuma imagem selecionada.")
        messagebox.showerror("Erro", "Nenhuma imagem foi selecionada!")
        return

    # Criar diretório de log baseado no timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    diretorio_log = f"log_reconhecimento_{timestamp}"
    os.makedirs(diretorio_log, exist_ok=True)

    # Carregar a imagem antes de detectar a máscara
    log_content = f"Carregando imagem desconhecida: {caminho_foto}"
    print(log_content)
    salvar_log(diretorio_log, log_content)

    imagem_desconhecida = face_recognition.load_image_file(caminho_foto)

    # Detectar se a pessoa está usando máscara
    log_content = f"Verificando se a pessoa está usando máscara na imagem: {caminho_foto}"
    print(log_content)
    salvar_log(diretorio_log, log_content)

    tem_mascara = detectar_mascara(caminho_foto)

    if tem_mascara == 0:
        log_content = "Máscara detectada. Adaptando o reconhecimento facial."
        print(log_content)
        salvar_log(diretorio_log, log_content)
        messagebox.showinfo("Detecção de Máscara", "Máscara detectada. Adaptando o reconhecimento facial...")

        # Adapte as áreas de reconhecimento facial para focar nos olhos e testa
        face_landmarks_list = face_recognition.face_landmarks(imagem_desconhecida)
        face_landmarks_list = ajustar_areas_com_mascara(face_landmarks_list)  # Ajusta os pontos faciais

    elif tem_mascara == 1:
        log_content = "Nenhuma máscara detectada."
        print(log_content)
        salvar_log(diretorio_log, log_content)
    else:
        log_content = "Erro ao detectar máscara."
        print(log_content)
        salvar_log(diretorio_log, log_content)
        messagebox.showerror("Erro", "Erro ao detectar máscara.")
        return

    tempo_inicio = time.time()

    try:
        encodings_desconhecidos = face_recognition.face_encodings(imagem_desconhecida)[0]
    except IndexError:
        log_content = f"Imagem com poucos pontos de verificação facial: {caminho_foto}."
        print(log_content)
        salvar_log(diretorio_log, log_content)
        messagebox.showerror("Erro", "Imagem com poucos pontos de verificação facial!")
        return

    # Salvar a imagem de entrada "limpa" sem as informações
    imagem_entrada_limpa = cv2.imread(caminho_foto)
    nome_arquivo_entrada_limpa = f"{diretorio_log}/entrada_limpa.jpg"
    cv2.imwrite(nome_arquivo_entrada_limpa, imagem_entrada_limpa)
    log_content = f"Imagem de entrada 'limpa' salva como: {nome_arquivo_entrada_limpa}"
    print(log_content)
    salvar_log(diretorio_log, log_content)

    # Detectar as faces e obter as coordenadas
    face_locations_desconhecidos = face_recognition.face_locations(imagem_desconhecida)
    log_content = f"Coordenadas da face detectada na imagem desconhecida: {face_locations_desconhecidos}"
    print(log_content)
    salvar_log(diretorio_log, log_content)

    # Desenhar retângulo verde na imagem de entrada
    for top, right, bottom, left in face_locations_desconhecidos:
        cv2.rectangle(imagem_entrada_limpa, (left, top), (right, bottom), (0, 255, 0), 2)

    # Detectar os pontos faciais na imagem de entrada
    face_landmarks_list = face_recognition.face_landmarks(imagem_desconhecida)

    for face_landmarks in face_landmarks_list:
        for landmark_name, points in face_landmarks.items():
            for point in points:
                # Pontos azuis
                cv2.circle(imagem_entrada_limpa, point, 2, (255, 0, 0), -1)

    # Salvar a imagem de entrada com as informações
    nome_arquivo_entrada_info = f"{diretorio_log}/entrada_com_info.jpg"
    cv2.imwrite(nome_arquivo_entrada_info, imagem_entrada_limpa)
    log_content = f"Imagem de entrada com informações salva como: {nome_arquivo_entrada_info}"
    print(log_content)
    salvar_log(diretorio_log, log_content)

    print("Comparando com os rostos armazenados no banco de dados...")
    cur.execute("SELECT nome_pessoa, foto FROM pessoas")
    pessoas = cur.fetchall()

    for nome_pessoa, foto in pessoas:
        # Salvar a foto temporariamente para processar com face_recognition
        temp_image_path = "temp_image.jpg"
        with open(temp_image_path, "wb") as f:
            f.write(foto)

        # Carregar a imagem da pessoa no banco de dados
        imagem_conhecida = face_recognition.load_image_file(temp_image_path)
        encodings_conhecidos = face_recognition.face_encodings(imagem_conhecida)[0]

        # Calcular a distância entre os vetores de codificação facial
        distancia = face_recognition.face_distance([encodings_conhecidos], encodings_desconhecidos)[0]
        similaridade = (1 - distancia) * 100  # Converter a distância em probabilidade de similaridade
        tolerancia = 0.6

        # Comparar o rosto com a tolerância
        resultado = face_recognition.compare_faces(
            [encodings_conhecidos], encodings_desconhecidos, tolerance=tolerancia
        )

        if resultado[0]:
            log_content = f"Pessoa reconhecida: {nome_pessoa} com {similaridade:.2f}% de similaridade."
            print(log_content)
            salvar_log(diretorio_log, log_content)

            img = cv2.imread(temp_image_path)
            face_locations = face_recognition.face_locations(imagem_conhecida)

            # Salvar a imagem "limpa" da base sem as informações técnicas
            nome_arquivo_limpo = f"{diretorio_log}/limpo_{nome_pessoa}.jpg"
            cv2.imwrite(nome_arquivo_limpo, img)
            log_content = f"Imagem 'limpa' salva como: {nome_arquivo_limpo}"
            print(log_content)
            salvar_log(diretorio_log, log_content)

            # Desenhar retângulo verde ao redor do rosto reconhecido
            for top, right, bottom, left in face_locations:
                cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

            # Detectar os pontos faciais (landmarks)
            face_landmarks_list = face_recognition.face_landmarks(imagem_conhecida)

            if tem_mascara == 0:
                face_landmarks_list = ajustar_areas_com_mascara(face_landmarks_list)  # script se adapta para máscara

            # Desenhar os pontos faciais
            for face_landmarks in face_landmarks_list:
                for landmark_name, points in face_landmarks.items():
                    for point in points:
                        cv2.circle(img, point, 2, (255, 0, 0), -1)  # pontos azuis

            # Exibir vetores e outras informações técnicas no log
            log_content = f"Coordenadas da face conhecida: {face_locations}\n"
            log_content += "=== Vetores de Codificação Facial (imagem de entrada) ===\n"
            log_content += np.array_str(encodings_desconhecidos) + "\n"
            log_content += "=== Vetores de Codificação Facial (imagem da base) ===\n"
            log_content += np.array_str(encodings_conhecidos) + "\n"
            log_content += f"Tolerância aplicada: {tolerancia}"
            salvar_log(diretorio_log, log_content)
            print(log_content)

            # Salvar a imagem processada no diretório de Log
            nome_arquivo = f"{diretorio_log}/reconhecido_{nome_pessoa}.jpg"
            cv2.imwrite(nome_arquivo, img)
            log_content = f"Imagem com informações técnicas salva como: {nome_arquivo}"
            print(log_content)
            salvar_log(diretorio_log, log_content)

            # Exibir a imagem com o retângulo e os pontos faciais
            cv2.imshow(f"Pessoa Reconhecida: {nome_pessoa}", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            # Apagar a imagem temporária
            os.remove(temp_image_path)
            log_content = f"Imagem temporária {temp_image_path} removida."
            print(log_content)
            salvar_log(diretorio_log, log_content)

            # Medir o tempo total de processamento
            tempo_fim = time.time()
            log_content = f"Tempo total de processamento: {tempo_fim - tempo_inicio:.2f} segundos"
            print(log_content)
            salvar_log(diretorio_log, log_content)
            return

    log_content = "Nenhuma correspondência encontrada."
    print(log_content)
    salvar_log(diretorio_log, log_content)
    messagebox.showerror("Erro", "A pessoa não foi reconhecida!")
    tempo_fim = time.time()
    log_content = f"Tempo total de processamento: {tempo_fim - tempo_inicio:.2f} segundos"
    print(log_content)
    salvar_log(diretorio_log, log_content)


# Interface gráfica com Tkinter (apenas para reconhecimento facial)
root = tk.Tk()
root.title("Reconhecimento Facial")

tk.Button(root, text="Selecionar Imagem para Reconhecimento", command=reconhecimento_facial).pack(pady=20)

root.mainloop()

cur.close()
conn.close()
