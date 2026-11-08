import os
import mysql.connector
from dotenv import load_dotenv

import certifi

load_dotenv()  # lê o .env localmente; no Render não faz nada

# 1) Ler as variáveis (fora do connect)
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ.get("DB_PORT", 4000))
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ["DB_NAME"]

# Caminho do certificado: no Render usa o do sistema,
# no seu PC aponte para o .pem pela variável DB_SSL_CA
DB_SSL_CA = os.environ.get("DB_SSL_CA", certifi.where())


def conectar():
    try:
        # 2) Passar para o connect como parâmetros nomeados
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            ssl_ca=DB_SSL_CA,
            ssl_verify_identity=True,
        )
        print("🎉 Conexão realizada com sucesso!")
        return conn

    except mysql.connector.Error as erro:
        print(f"❌ Erro ao conectar ao MySQL: {erro}")
        return None


if __name__ == "__main__":
    conexao = conectar()
    if conexao and conexao.is_connected():
        conexao.close()
        print("🔌 Conexão fechada com segurança.")