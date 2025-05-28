import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam

# ========================
# Carregar Dataset
# ========================
dataset_dir = "imagens/dataset"
categories = ['with_mask', 'without_mask']

data = []
labels = []
img_size = 128

for category in categories:
    path = os.path.join(dataset_dir, category)
    class_num = categories.index(category)
    for img in os.listdir(path):
        try:
            img_array = cv2.imread(os.path.join(path, img))
            resized_img = cv2.resize(img_array, (img_size, img_size))
            data.append(resized_img)
            labels.append(class_num)
        except Exception as e:
            print(f"Erro ao processar a imagem {img}: {e}")
            os.remove(os.path.join(path, img))  # remover o arquivo corrompido

# converter listas em arrays e normalizar
data = np.array(data) / 255.0
labels = np.array(labels)

# dividir entre treino e teste
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, stratify=labels, random_state=42)

# categorizar as labels
y_train = to_categorical(y_train)
y_test = to_categorical(y_test)

# ================================
# Passo 2: Criar o Modelo (Transfer Learning)
# ================================
# Usar MobileNetV2 pré-treinado (sem a cabeça/final)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(128, 128, 3))
base_model.trainable = False  # Congelar as camadas do MobileNetV2

# criar o modelo final com camadas adicionais
model = Sequential([
    base_model,
    GlobalAveragePooling2D(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(2, activation='softmax')  # 2 classes: com máscara e sem máscara
])

# compilar o modelo
model.compile(optimizer=Adam(learning_rate=0.0001), loss='categorical_crossentropy', metrics=['accuracy'])

# Exibir o resumo do modelo
model.summary()

# =========================
# Passo 3: Treinamento do Modelo
# =========================
# Geradores de dados com aumento para treinamento e validação
train_datagen = ImageDataGenerator(rotation_range=20, zoom_range=0.15,
                                   width_shift_range=0.2, height_shift_range=0.2,
                                   shear_range=0.15, horizontal_flip=True, fill_mode="nearest")

val_datagen = ImageDataGenerator()

# treinar o modelo
history = model.fit(train_datagen.flow(X_train, y_train, batch_size=32),
                    validation_data=val_datagen.flow(X_test, y_test),
                    epochs=10,
                    steps_per_epoch=len(X_train) // 32,
                    validation_steps=len(X_test) // 32)

# =============================
# Passo 4: Avaliar o Modelo
# =============================
loss, accuracy = model.evaluate(val_datagen.flow(X_test, y_test))
print(f"Perda no conjunto de teste: {loss}")
print(f"Acurácia no conjunto de teste: {accuracy * 100:.2f}%")

# ==========================
# Passo 5: Salvar o Modelo
# ==========================
model.save("modelo_detector_mascara.h5")
print("Modelo salvo como 'modelo_detector_mascara.h5'.")

# =============================
# Passo 6: Função para Predição
# =============================
# def detectar_mascara(imagem_caminho):
#     imagem = cv2.imread(imagem_caminho)
#     imagem_redimensionada = cv2.resize(imagem, (128, 128))
#     imagem_preprocessada = np.expand_dims(imagem_redimensionada / 255.0, axis=0)
    
#     predicao = model.predict(imagem_preprocessada)
#     classe = np.argmax(predicao, axis=1)

#     if classe == 1:
#         return "Com máscara"
#     else:
#         return "Sem máscara"

# # Exemplo de uso
# caminho_imagem = "imagens/Screenshot_6.jpg"
# resultado = detectar_mascara(caminho_imagem)
# print(f"Resultado: {resultado}")
