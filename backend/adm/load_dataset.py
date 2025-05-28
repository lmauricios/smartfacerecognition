import os
import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical

# Caminho para o dataset
dataset_dir = "imagens/dataset"
categories = ['with_mask', 'without_mask']

data = []
labels = []

# Tamanho que será redimensionado para os modelos
img_size = 128  # Usar tamanho menor para evitar sobrecarga de memória

# Função para verificar se o arquivo é uma imagem válida
def is_valid_image(file_path):
    valid_extensions = ['.jpg', '.jpeg', '.png']  # Extensões de imagem permitidas
    return os.path.splitext(file_path)[1].lower() in valid_extensions

# Função para excluir arquivos inválidos
def remove_invalid_file(file_path):
    try:
        os.remove(file_path)
        print(f"Arquivo inválido removido: {file_path}")
    except Exception as e:
        print(f"Erro ao tentar remover o arquivo {file_path}: {e}")

for category in categories:
    path = os.path.join(dataset_dir, category)
    class_num = categories.index(category)
    for img in os.listdir(path):
        img_path = os.path.join(path, img)
        if is_valid_image(img):  # Verificar se o arquivo tem extensão válida
            try:
                img_array = cv2.imread(img_path)
                resized_img = cv2.resize(img_array, (img_size, img_size))
                data.append(resized_img)
                labels.append(class_num)
            except Exception as e:
                print(f"Erro ao processar a imagem {img}: {e}")
        else:
            # Se o arquivo não for uma imagem válida, será excluído
            remove_invalid_file(img_path)

data = np.array(data) / 255.0
labels = np.array(labels)

# Dividir o dataset entre treinamento e validação
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, stratify=labels, random_state=42)

# Transformar rótulos em categorias
y_train = to_categorical(y_train)
y_test = to_categorical(y_test)

print(f"Dataset carregado com sucesso. Total de imagens: {len(data)}")
