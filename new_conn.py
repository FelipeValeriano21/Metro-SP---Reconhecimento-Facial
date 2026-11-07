import mysql.connector

def conectar():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345',
            database='metro_db'
        )
        print("🎉 Conexão realizada com sucesso!")
        return conn
        
    except mysql.connector.Error as erro:
        print(print(f"❌ Erro ao conectar ao MySQL: {erro}"))
        return None

conexao = conectar()

if conexao and conexao.is_connected():
    conexao.close()
    print("🔌 Conexão fechada com segurança.")
