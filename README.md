# 🚇 Metrô Fácil

Sistema de acesso ao metrô com **reconhecimento facial** e **carteira digital**. O passageiro faz login, recarrega o saldo e paga a passagem apenas com o rosto, sem cartão ou bilhete físico.

> Projeto acadêmico desenvolvido por Felipe Valeriano, no curso de Ciência da Computação (3º semestre) da Universidade Cruzeiro do Sul.

## 📋 Sobre o projeto metro sp

O Metrô Fácil simula o fluxo completo de uma passagem de metrô:

1. O usuário faz login.
2. Recarrega o saldo da carteira digital.
3. Na catraca, a câmera captura o rosto e o sistema verifica se ele pertence à conta logada.
4. Se o rosto for reconhecido e houver saldo, a tarifa é debitada e a viagem fica registrada.

Todas as movimentações (recargas e viagens) são gravadas no banco de dados e podem ser consultadas pelo usuário.

## ✨ Funcionalidades

- Login de usuários com sessão
- Reconhecimento facial para validar a passagem
- Verificação de que o rosto reconhecido corresponde à conta logada
- Carteira digital com saldo
- Débito da tarifa de forma atômica (só debita se houver saldo suficiente)
- Registro de cada transação no banco de dados
- **Histórico de Recargas** em modal (somente créditos)
- **Viagens Realizadas** na página inicial (somente débitos)
- Perfil do usuário

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Back-end | Python, Flask, Flask-CORS |
| Banco de dados | MySQL 8 |
| Front-end | HTML, CSS, JavaScript, Bootstrap 5, Bootstrap Icons |
| Templates | Jinja2 |
| Reconhecimento facial | Python (preencher: OpenCV / face_recognition / outra) |

## 🗂️ Banco de dados

Banco: `metro_db`

| Tabela | Descrição |
|---|---|
| `usuarios` | Dados dos passageiros |
| `carteiras` | Saldo de cada usuário |
| `transacoes` | Histórico de movimentações (`carteira_id`, `valor`, `data_hora`, `status_transacao`) |

Convenção dos valores na tabela `transacoes`:

- **Recargas** são gravadas com valor **positivo**.
- **Viagens** são gravadas com valor **negativo**.

O script do banco está em [`metro_db.sql`](./metro_db.sql).

## 🚀 Como executar

### Pré-requisitos

- Python 3.10 ou superior
- MySQL 8 (e MySQL Workbench, opcional)
- Webcam

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU-USUARIO/NOME-DO-REPOSITORIO.git
cd NOME-DO-REPOSITORIO
```

### 2. Criar e ativar o ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar o banco de dados

1. Abra o MySQL Workbench.
2. Vá em **Server → Data Import**, escolha **Import from Self-Contained File** e selecione o `metro_db.sql`.
3. Clique em **Start Import**.
4. Ajuste host, usuário, senha e nome do banco no arquivo de conexão do projeto.

### 5. Executar a aplicação

```bash
python app.py
```

Acesse `http://localhost:5000` no navegador.

## 🔒 Segurança

- O `usuario_id` vem sempre da sessão do usuário autenticado, nunca da URL.
- O débito usa `UPDATE ... WHERE saldo >= tarifa`, o que impede saldo negativo.
- O débito e o registro da transação ocorrem na mesma transação do banco (commit/rollback).
- As consultas SQL usam parâmetros, evitando SQL Injection.

## 📸 Capturas de tela

<!-- Adicione prints do projeto na pasta docs/ e referencie aqui -->
<img width="1915" height="867" alt="image" src="https://github.com/user-attachments/assets/b37b988f-7517-42d2-b161-570ca4299e62" />

<img width="1912" height="863" alt="image" src="https://github.com/user-attachments/assets/b457e410-56f7-44a0-95ab-666645473fe6" />

<img width="1916" height="861" alt="image" src="https://github.com/user-attachments/assets/f1ec414b-665b-4489-8afa-bda69b4be178" />

<img width="1917" height="871" alt="image" src="https://github.com/user-attachments/assets/07044ac7-bd3f-4c49-9bac-1a9f407aedf7" />






## 🔮 Melhorias futuras

- Recarga com pagamento real (Pix ou cartão)
- Painel administrativo
- Relatórios de uso
- Tarifas diferenciadas (estudante, idoso, integração)

## 👨‍💻 Autor

**Felipe Valeriano**
Ciência da Computação, Universidade Cruzeiro do Sul

[GitHub](https://github.com/FelipeValeriano21) · [LinkedIn](https://linkedin.com/in/FelipeValeriano)

