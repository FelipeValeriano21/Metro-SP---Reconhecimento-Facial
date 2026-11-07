import base64
import os
import cv2
import numpy as np

# O OpenCV no Windows não abre arquivos em caminhos com acento (ex.: "Área", "3º").
# Entramos na pasta do projeto e usamos caminhos relativos, que não têm acento.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

ARQ_PROTO = "content/deploy.prototxt.txt"
ARQ_MODELO = "content/res10_300x300_ssd_iter_140000.caffemodel"
ARQ_EIGEN = "content/eigen_classifier.yml"

for arq in (ARQ_PROTO, ARQ_MODELO, ARQ_EIGEN):
    print(arq, "->", "OK" if os.path.exists(arq) else "NÃO ENCONTRADO")

rede = cv2.dnn.readNetFromCaffe(ARQ_PROTO, ARQ_MODELO)
reconhecedor = cv2.face.EigenFaceRecognizer_create()
reconhecedor.read(ARQ_EIGEN)

# Quanto MENOR a distância, mais parecido. Ajuste olhando o terminal.
LIMITE_DISTANCIA = 5000


PASTA_IMAGENS = "imagens"
MINIMO_AMOSTRAS = 3


def gravar_imagem(caminho, frame):
    """Grava JPG por caminho com acentos (o cv2.imwrite falha no Windows)."""
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        return False
    with open(caminho, "wb") as f:
        f.write(buffer.tobytes())
    return True


def ler_imagem(caminho):
    """Lê imagem por caminho com acentos (o cv2.imread falha no Windows)."""
    dados = np.fromfile(caminho, dtype=np.uint8)
    if dados.size == 0:
        return None
    return cv2.imdecode(dados, cv2.IMREAD_COLOR)


def salvar_amostras(usuario_id, data_urls):
    """Salva as fotos como imagens/aluno{id}.{n}.jpg. Retorna quantas foram gravadas."""
    validos = []
    for i, d in enumerate(data_urls, start=1):
        frame = decodificar_imagem(d)
        if frame is not None and extrair_face(frame) is not None:
            validos.append(frame)

    print(f"[cadastro] fotos recebidas: {len(data_urls)} | com rosto: {len(validos)}")

    if len(validos) < MINIMO_AMOSTRAS:
        return len(validos)

    pasta = os.path.join(BASE_DIR, PASTA_IMAGENS)
    os.makedirs(pasta, exist_ok=True)

    # Recadastro: apaga as fotos antigas desta mesma pessoa
    for nome in os.listdir(pasta):
        if nome.startswith(f"aluno{usuario_id}."):
            os.remove(os.path.join(pasta, nome))

    gravadas = 0
    for n, frame in enumerate(validos, start=1):
        caminho = os.path.join(pasta, f"aluno{usuario_id}.{n}.jpg")
        try:
            if gravar_imagem(caminho, frame):
                gravadas += 1
        except Exception as e:
            print(f"[cadastro] FALHOU ao gravar {caminho}: {repr(e)}")

    print(f"[cadastro] gravadas em disco: {gravadas} (pasta: {pasta})")
    return gravadas


def treinar_modelo():
    """Treina com todas as imagens 'aluno*' e recarrega o modelo em memória."""
    global reconhecedor
    faces, ids = [], []
    pasta = os.path.join(BASE_DIR, PASTA_IMAGENS)

    for nome in sorted(os.listdir(pasta)):
        if not nome.startswith("aluno"):
            continue
        try:
            id_ = int(nome.split(".")[0].replace("aluno", ""))
        except ValueError:
            print("[treino] id inválido no nome:", nome)
            continue

        frame = ler_imagem(os.path.join(pasta, nome))
        if frame is None:
            print("[treino] não consegui ler:", nome)
            continue

        face = extrair_face(frame)
        if face is None:
            print("[treino] nenhum rosto detectado em:", nome)
            continue

        faces.append(face)
        ids.append(id_)

    print(f"[treino] amostras usadas: {len(faces)}")

    if len(faces) < 2:
        raise ValueError("Poucas fotos com rosto para treinar.")

    novo = cv2.face.EigenFaceRecognizer_create()
    novo.train(faces, np.array(ids))
    novo.write(ARQ_EIGEN)
    reconhecedor = novo
    return len(faces)

def decodificar_imagem(data_url):
    """Converte 'data:image/jpeg;base64,...' em imagem do OpenCV."""
    dados = base64.b64decode(data_url.split(",")[1])
    return cv2.imdecode(np.frombuffer(dados, np.uint8), cv2.IMREAD_COLOR)


def extrair_face(frame, conf_min=0.5, debug=False):
    """Detecta em 300x300 (tamanho do modelo), recorta e devolve 220x220 em cinza."""
    if frame is None:
        return None

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0)
    )
    rede.setInput(blob)
    deteccoes = rede.forward()

    confiancas = deteccoes[0, 0, :, 2]
    i = int(np.argmax(confiancas))          # pega a melhor detecção
    if debug:
        print(f"    maior confiança: {confiancas[i]:.2f} | imagem {w}x{h}")

    if confiancas[i] < conf_min:
        return None

    x1, y1, x2, y2 = (deteccoes[0, 0, i, 3:7] * np.array([w, h, w, h])).astype("int")
    x1, y1 = max(x1, 0), max(y1, 0)
    x2, y2 = min(x2, w), min(y2, h)

    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    roi = cv2.resize(roi, (220, 220))
    return cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)


def reconhecer_rosto(data_url):
    """Retorna (id, distancia). id = None se não achou rosto."""
    frame = decodificar_imagem(data_url)
    face = extrair_face(frame)
    if face is None:
        return None, None
    id_previsto, distancia = reconhecedor.predict(face)
    return id_previsto, distancia