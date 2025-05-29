import os
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import face_recognition
import numpy as np
import psycopg2
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv()

# Conecta ao banco de dados usando variáveis de ambiente
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS")
)
cur = conn.cursor()


# salvar logs
def salvar_log(diretorio_log, conteudo_log):
    with open(f"{diretorio_log}/log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(conteudo_log + "\n")


# reconhecimento facial com logs e armazenamento de imagem processada
def reconhecimento_facial():
    print("Abrindo diálogo para selecionar a imagem...")
    caminho_foto = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])

    if not caminho_foto:
        print("Nenhuma imagem selecionada.")
        messagebox.showerror("Erro", "Nenhuma imagem foi selecionada!")
        return

    # criar diretório de log baseado no timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    diretorio_log = f"log_reconhecimento_{timestamp}"
    os.makedirs(diretorio_log, exist_ok=True)

    tempo_inicio = time.time()

    print(f"Carregando imagem desconhecida: {caminho_foto}")
    imagem_desconhecida = face_recognition.load_image_file(caminho_foto)

    try:
        encodings_desconhecidos = face_recognition.face_encodings(imagem_desconhecida)[0]
    except IndexError:
        log_content = f"Nenhum rosto encontrado na imagem: {caminho_foto}."
        salvar_log(diretorio_log, log_content)
        print(log_content)
        messagebox.showerror("Erro", "Nenhum rosto foi encontrado na imagem!")
        return

    # salvar a imagem de entrada "limpa" sem as informações
    imagem_entrada_limpa = cv2.imread(caminho_foto)
    nome_arquivo_entrada_limpa = f"{diretorio_log}/entrada_limpa.jpg"
    cv2.imwrite(nome_arquivo_entrada_limpa, imagem_entrada_limpa)
    print(f"Imagem de entrada 'limpa' salva como: {nome_arquivo_entrada_limpa}")

    # detectar as faces e obter as coordenadas
    face_locations_desconhecidos = face_recognition.face_locations(imagem_desconhecida)
    log_content = f"Coordenadas da face detectada na imagem desconhecida: {face_locations_desconhecidos}"
    salvar_log(diretorio_log, log_content)
    print(log_content)

    # desenhar retângulo verde na imagem de entrada
    for top, right, bottom, left in face_locations_desconhecidos:
        cv2.rectangle(imagem_entrada_limpa, (left, top), (right, bottom), (0, 255, 0), 2)

    # detectar os pontos faciais na imagem de entrada
    face_landmarks_list = face_recognition.face_landmarks(imagem_desconhecida)

    for face_landmarks in face_landmarks_list:
        for landmark_name, points in face_landmarks.items():
            for point in points:
                # pontos azuis
                cv2.circle(imagem_entrada_limpa, point, 2, (255, 0, 0), -1)

    # salvar a imagem de entrada com as informações
    nome_arquivo_entrada_info = f"{diretorio_log}/entrada_com_info.jpg"
    cv2.imwrite(nome_arquivo_entrada_info, imagem_entrada_limpa)
    print(f"Imagem de entrada com informações salva como: {nome_arquivo_entrada_info}")

    print("Comparando com os rostos armazenados no banco de dados...")
    cur.execute("SELECT nome_pessoa, foto FROM pessoas")
    pessoas = cur.fetchall()

    for nome_pessoa, foto in pessoas:
        # salvar a foto temporariamente para processar com face_recognition
        temp_image_path = "temp_image.jpg"
        with open(temp_image_path, "wb") as f:
            f.write(foto)

        # carregar a imagem da pessoa no banco de dados
        imagem_conhecida = face_recognition.load_image_file(temp_image_path)
        encodings_conhecidos = face_recognition.face_encodings(imagem_conhecida)[0]

        # calcular a distância entre os vetores de codificação facial
        distancia = face_recognition.face_distance([encodings_conhecidos], encodings_desconhecidos)[0]
        # converter a distância em probabilidade de similaridade
        similaridade = (1 - distancia) * 100
        # definir a tolerância usada
        tolerancia = 0.6

        # comparar o rosto com a tolerância
        resultado = face_recognition.compare_faces(
            [encodings_conhecidos], encodings_desconhecidos, tolerance=tolerancia
        )

        if resultado[0]:
            log_content = f"Pessoa reconhecida: {nome_pessoa} com {similaridade:.2f}% de similaridade."
            salvar_log(diretorio_log, log_content)
            print(log_content)

            img = cv2.imread(temp_image_path)
            face_locations = face_recognition.face_locations(imagem_conhecida)

            # salvar a imagem "limpa" da base sem as informações técnicas
            nome_arquivo_limpo = f"{diretorio_log}/limpo_{nome_pessoa}.jpg"
            cv2.imwrite(nome_arquivo_limpo, img)
            print(f"Imagem 'limpa' salva como: {nome_arquivo_limpo}")

            # desenhar retângulo verde ao redor do rosto reconhecido
            for top, right, bottom, left in face_locations:
                cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

            # detectar os pontos faciais (landmarks)
            face_landmarks_list = face_recognition.face_landmarks(imagem_conhecida)

            # sesenhar os pontos faciais
            for face_landmarks in face_landmarks_list:
                for landmark_name, points in face_landmarks.items():
                    for point in points:
                        cv2.circle(img, point, 2, (255, 0, 0), -1)  # Pontos azuis

            # exibir vetores e outras informações técnicas no log
            log_content = f"Coordenadas da face conhecida: {face_locations}\n"
            log_content += "=== Vetores de Codificação Facial (imagem de entrada) ===\n"
            log_content += np.array_str(encodings_desconhecidos) + "\n"
            log_content += "=== Vetores de Codificação Facial (imagem da base) ===\n"
            log_content += np.array_str(encodings_conhecidos) + "\n"
            log_content += f"Tolerância aplicada: {tolerancia}"
            salvar_log(diretorio_log, log_content)
            print(log_content)

            # salvar a imagem processada no diretorio de Log
            nome_arquivo = f"{diretorio_log}/reconhecido_{nome_pessoa}.jpg"
            cv2.imwrite(nome_arquivo, img)
            print(f"Imagem com informações técnicas salva como: {nome_arquivo}")

            # exibir a imagem com o retângulo e os pontos faciais
            cv2.imshow(f"Pessoa Reconhecida: {nome_pessoa}", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            # apagar a imagem temporária
            os.remove(temp_image_path)
            print(f"Imagem temporária {temp_image_path} removida.")

            # medir o tempo total de processamento
            tempo_fim = time.time()
            log_content = f"Tempo total de processamento: {tempo_fim - tempo_inicio:.2f} segundos"
            salvar_log(diretorio_log, log_content)
            print(log_content)
            return

    log_content = "Nenhuma correspondência encontrada."
    salvar_log(diretorio_log, log_content)
    print(log_content)
    messagebox.showerror("Erro", "A pessoa não foi reconhecida!")
    tempo_fim = time.time()
    log_content = f"Tempo total de processamento: {tempo_fim - tempo_inicio:.2f} segundos"
    salvar_log(diretorio_log, log_content)
    print(log_content)


# Interface gráfica com Tkinter (apenas para reconhecimento facial)
root = tk.Tk()
root.title("Reconhecimento Facial")

tk.Button(root, text="Selecionar Imagem para Reconhecimento", command=reconhecimento_facial).pack(pady=20)

root.mainloop()

cur.close()
conn.close()
