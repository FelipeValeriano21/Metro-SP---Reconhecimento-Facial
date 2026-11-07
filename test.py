import cv2
import numpy as np
import conn
from datetime import datetime

# Carregar o classificador treinado
classificadorFace = cv2.CascadeClassifier('content/haarcascade_frontalface_default.xml')
eigen_classifier = cv2.face.EigenFaceRecognizer_create()
eigen_classifier.read('content/eigen_classifier.yml')
largura, altura = 220, 220

# Dicionário de mapeamento de IDs para nomes (ajuste conforme necessário)
id_para_nome = {
    # Adicione todos os mapeamentos necessários aqui
}


print(id_para_nome)

# Função para detectar a face na imagem e retornar a face redimensionada
def detecta_face(imagem):
    imagemCinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    facesDetectadas = classificadorFace.detectMultiScale(imagemCinza, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    for (x, y, w, h) in facesDetectadas:
        face = cv2.resize(imagemCinza[y:y + h, x:x + w], (largura, altura))
        return face, (x, y, w, h)
    return None, None

# Função para realizar o reconhecimento facial
def reconhece_face(face):
    id, confianca = eigen_classifier.predict(face)
    return id, confianca

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Falha ao capturar imagem.")
        break

    cv2.imshow("Reconhecimento Facial", frame)

    key = cv2.waitKey(1)
    if key == 27:  # Pressione ESC para capturar a imagem e verificar o reconhecimento
        face, bbox = detecta_face(frame)
        if face is not None:
            id, confianca = reconhece_face(face)
            nome = id_para_nome.get(id)
            data = datetime.now()
            presenca = 1
            conn_chamada = conn.Connection()
            conn_chamada.inserir_chamada(id, presenca, data)
            print(f"Atenção aluno do ra final: {id}, sua presença foi confirmado na aula as {data}")

        else:
            print("Nenhuma face detectada.")
        break

cap.release()
cv2.destroyAllWindows()
