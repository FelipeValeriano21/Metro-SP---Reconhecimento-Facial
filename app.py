from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS 
import traceback
from decimal import Decimal, InvalidOperation
from reconhecimento_facial import reconhecer_rosto, LIMITE_DISTANCIA, salvar_amostras, treinar_modelo, MINIMO_AMOSTRAS
from new_conn import conectar 


app = Flask(__name__)
app.secret_key = "chave_de_teste_metro_facil"
CORS(app, supports_credentials=True) 


TARIFA = Decimal("5.40")

@app.route("/inicio")
def tela_login():
 return render_template("view/login.html") 

@app.route("/cadastro")
def tela_cadastro():
 return render_template("view/cadastro.html") 

@app.route("/perfil")
def tela_perfil():
    if "usuario_id" not in session:
        return redirect(url_for("tela_login"))

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT nome, email, senha FROM usuarios WHERE id = %s",
            (session["usuario_id"],)
        )
        usuario = cursor.fetchone()
    finally:
        cursor.close()
        conexao.close()

    if not usuario:
        session.clear()
        return redirect(url_for("tela_login"))

    return render_template("view/perfil.html", usuario=usuario)

@app.route("/cadastrar", methods=["POST"])
def cadastro():
    dados = request.get_json()

    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({"erro": "Preencha todos os campos."}), 400

    if len(senha) < 8:
        return jsonify({"erro": "A senha deve ter pelo menos 8 caracteres."}), 400

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        senha_hash = generate_password_hash(senha)
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
        """, (nome, email, senha_hash))

        usuario_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO carteiras (usuario_id, saldo)
            VALUES (%s, %s)
        """, (usuario_id, 0.00))

        conexao.commit()

        return jsonify({
            "mensagem": "Cadastro realizado com sucesso!"
        }), 201

    except Exception as erro:
        conexao.rollback()

        if getattr(erro, "errno", None) == 1062:
            return jsonify({"erro": "Este e-mail já está cadastrado."}), 409

        print("Erro no cadastro:", erro)
        return jsonify({"erro": "Não foi possível realizar o cadastro."}), 500

    finally:
        cursor.close()
        conexao.close()


@app.route("/login", methods=["POST"])
def autenticar():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados não enviados corretamente."}), 400

    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, nome, email, senha
            FROM usuarios
            WHERE email = %s AND status_usuario = 'ativo'
        """, (email,))

        usuario = cursor.fetchone()
        if usuario and check_password_hash(usuario["senha"], senha):
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            
            return jsonify({
                "mensagem": "Login realizado com sucesso!",
                "nome": usuario["nome"]
            }), 200
        return jsonify({"erro": "E-mail ou senha inválidos."}), 401

    except Exception as e:
        print(f"ERRO INTERNO NO SERVIDOR: {e}")
        return jsonify({"erro": "Erro interno no servidor de banco de dados."}), 500

    finally:
        cursor.close()
        conexao.close()

@app.route("/menu")
def menu():
    if "usuario_id" not in session:
        return redirect(url_for("tela_login")) 

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT c.saldo, c.status_carteira
            FROM carteiras c
            WHERE c.usuario_id = %s
        """, (session["usuario_id"],))

        carteira = cursor.fetchone()

        return render_template(
            "view/menu.html",
            nome=session["nome"],
            carteira=carteira,
            TARIFA=TARIFA,
            movimentacoes = buscar_movimentacoes(session["usuario_id"], limite=10, tipo="debito")
        )

    finally:
        cursor.close()
        conexao.close()
@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("tela_login"))


@app.route("/reconhecimento")
def reconhecimento():
    return render_template("view/catraca.html") 


@app.route("/reconhecer", methods=["POST"])
def reconhecer():
    if "usuario_id" not in session:
        return jsonify({"erro": "Faça login primeiro."}), 401

    dados = request.get_json(silent=True) or {}
    imagem = dados.get("imagem")
    if not imagem:
        return jsonify({"erro": "Imagem não enviada."}), 400

    try:
        id_previsto, distancia = reconhecer_rosto(imagem)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"erro": f"Falha ao processar: {e}"}), 500

    print("ID previsto:", id_previsto, "| distância:", distancia)

    if id_previsto is None:
        return jsonify({"erro": "Nenhum rosto detectado."}), 404

    if distancia > LIMITE_DISTANCIA:
        return jsonify({"erro": "Rosto não reconhecido."}), 404

    if id_previsto != session["usuario_id"]:
        return jsonify({"erro": "Este rosto não corresponde à conta logada."}), 403

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            UPDATE carteiras
            SET saldo = saldo - %s
            WHERE usuario_id = %s AND saldo >= %s
        """, (TARIFA, session["usuario_id"], TARIFA))

        if cursor.rowcount == 0:
            conexao.rollback()
            return jsonify({"erro": "Saldo insuficiente."}), 402
        cursor.execute("""
            INSERT INTO transacoes (carteira_id, valor, data_hora, status_transacao)
            SELECT id, %s, NOW(), %s
            FROM carteiras
            WHERE usuario_id = %s
        """, (-TARIFA, "aprovada", session["usuario_id"]))

        conexao.commit()

    except Exception as e:
        conexao.rollback()
        traceback.print_exc()
        return jsonify({"erro": "Não foi possível debitar a tarifa."}), 500
    finally:
        cursor.close()
        conexao.close()

    return jsonify({"nome": session["nome"], "mensagem": f"Tarifa de R$ {TARIFA} debitada. Boa viagem!"}), 200
@app.route("/cadastro-facial")
def cadastro_facial():
    if "usuario_id" not in session:
        return redirect(url_for("tela_login"))
    return render_template("view/cadastro_facial.html")


@app.route("/cadastrar-rosto", methods=["POST"])
def cadastrar_rosto():
    if "usuario_id" not in session:
        return jsonify({"erro": "Faça login primeiro."}), 401

    dados = request.get_json(silent=True) or {}
    imagens = dados.get("imagens", [])
    if not imagens:
        return jsonify({"erro": "Nenhuma foto enviada."}), 400

    try:
        salvas = salvar_amostras(session["usuario_id"], imagens)
        if salvas < MINIMO_AMOSTRAS:
            return jsonify({"erro": f"Só {salvas} fotos tinham rosto visível. Precisamos de pelo menos {MINIMO_AMOSTRAS}."}), 400

        total = treinar_modelo()
    except Exception as e:
        traceback.print_exc()
        return jsonify({"erro": f"Falha ao cadastrar: {e}"}), 500

    return jsonify({"mensagem": f"{salvas} fotos salvas e modelo treinado ({total} amostras no total)."}), 200

@app.route("/perfil/atualizar", methods=["POST"])
def atualizar_perfil():
    if "usuario_id" not in session:
        return jsonify({"erro": "Faça login primeiro."}), 401

    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip().lower()
    senha_atual = dados.get("senha_atual", "")
    nova_senha = dados.get("nova_senha", "")

    if not nome or not email:
        return jsonify({"erro": "Nome e e-mail são obrigatórios."}), 400

    if nova_senha and len(nova_senha) < 8:
        return jsonify({"erro": "A nova senha deve ter pelo menos 8 caracteres."}), 400

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    try:
        if nova_senha:
            cursor.execute("SELECT senha FROM usuarios WHERE id = %s", (session["usuario_id"],))
            atual = cursor.fetchone()
            if not atual or not check_password_hash(atual["senha"], senha_atual):
                return jsonify({"erro": "Senha atual incorreta."}), 403

            cursor.execute("""
                UPDATE usuarios SET nome = %s, email = %s, senha = %s
                WHERE id = %s
            """, (nome, email, generate_password_hash(nova_senha), session["usuario_id"]))
        else:
            cursor.execute("""
                UPDATE usuarios SET nome = %s, email = %s
                WHERE id = %s
            """, (nome, email, session["usuario_id"]))

        conexao.commit()
        session["nome"] = nome 

        return jsonify({"mensagem": "Perfil atualizado com sucesso!"}), 200

    except Exception as erro:
        conexao.rollback()
        if getattr(erro, "errno", None) == 1062:
            return jsonify({"erro": "Este e-mail já está em uso."}), 409
        traceback.print_exc()
        return jsonify({"erro": "Não foi possível atualizar o perfil."}), 500

    finally:
        cursor.close()
        conexao.close()

def buscar_movimentacoes(usuario_id, limite=None, tipo=None):
    sql = """
        SELECT t.valor, t.data_hora, t.status_transacao
        FROM transacoes t
        JOIN carteiras c ON c.id = t.carteira_id
        WHERE c.usuario_id = %s
    """
    params = [usuario_id]

    if tipo == "credito":
        sql += " AND t.valor > 0"
    elif tipo == "debito":
        sql += " AND t.valor < 0"

    sql += " ORDER BY t.data_hora DESC"

    if limite:
        sql += " LIMIT %s"
        params.append(limite)

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()

def formatar_movimentacoes(lista):
    return [
        {
            "valor": float(m["valor"]),
            "data_hora": m["data_hora"].strftime("%d/%m/%Y %H:%M"),
            "status": m["status_transacao"],
        }
        for m in lista
    ]


@app.route("/api/recargas", methods=["GET"])
def api_recargas():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"erro": "Não autenticado"}), 401

    lista = buscar_movimentacoes(usuario_id, limite=20, tipo="credito")
    dados = [
        {
            "valor": float(m["valor"]),
            "data_hora": m["data_hora"].strftime("%d/%m/%Y %H:%M"),
            "status": m["status_transacao"],
        }
        for m in lista
    ]
    return jsonify(dados)


@app.route("/api/viagens", methods=["GET"])
def api_viagens():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"erro": "Não autenticado"}), 401

    lista = buscar_movimentacoes(usuario_id, limite=10, tipo="debito")
    return jsonify(formatar_movimentacoes(lista))

if __name__ == "__main__":
    app.run(debug=True)