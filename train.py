import cv2
import numpy as np
from PIL import Image
import os

# Carregar a rede de detecção de faces e o classificador treinado
network = cv2.dnn.readNetFromCaffe('content/deploy.prototxt.txt', 'content/res10_300x300_ssd_iter_140000.caffemodel')
classificadorFace = cv2.CascadeClassifier('content/haarcascade_frontalface_default.xml')

def detecta_face(network, path_imagem, conf_min=0.7):
    imagem = Image.open(path_imagem).convert('L')
    imagem = np.array(imagem, 'uint8')
    imagem = cv2.cvtColor(imagem, cv2.COLOR_GRAY2BGR)
    (h, w) = imagem.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(imagem, (100, 100)), 1.0, (100, 100), (104.0, 117.0, 123.0))
    network.setInput(blob)
    deteccoes = network.forward()

    face = None
    for i in range(0, deteccoes.shape[2]):
        confianca = deteccoes[0, 0, i, 2]
        if confianca > conf_min:
            bbox = deteccoes[0, 0, i, 3:7] * np.array([w, h, w, h])
            (start_x, start_y, end_x, end_y) = bbox.astype('int')
            roi = imagem[start_y:end_y, start_x:end_x]
            if roi.shape[0] != 0 and roi.shape[1] != 0:  # Verificar se a ROI não está vazia
                roi = cv2.resize(roi, (220, 220))
                face = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                break  # Sair do loop após encontrar a primeira detecção válida
    return face

def get_image_data():
    image_dir = 'imagens'
    if not os.path.exists(image_dir):
        raise FileNotFoundError(f"Diretório '{image_dir}' não encontrado.")
    
    paths = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
    faces = []
    ids = []
    for path in paths:
        face = detecta_face(network, path)
        if face is not None:
            # Corrigido a extração do ID
            filename = os.path.basename(path)
            id_str = filename.split('.')[0].replace('ra', '').replace('aluno','')
            try:
                id = int(id_str)
                ids.append(id)
                faces.append(face)
            except ValueError:
                print(f"Erro ao extrair ID do arquivo {filename}")
                continue
    if len(faces) < 2:
        raise ValueError("Dados de treinamento insuficientes. É necessário pelo menos duas amostras.")
    return np.array(ids), faces

ids, faces = get_image_data()

eigen_classifier = cv2.face.EigenFaceRecognizer_create()
eigen_classifier.train(faces, ids)
eigen_classifier.write('content/eigen_classifier.yml')

# Crear un archivo de señalización para indicar que el entrenamiento ha finalizado
with open("entrenamiento_exitoso.txt", "w") as f:
    f.write("Entrenamiento exitoso")
