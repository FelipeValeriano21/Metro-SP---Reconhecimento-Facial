create database metro_db;
use metro_db;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    biometria TEXT,
    status_usuario VARCHAR(20) DEFAULT 'ativo'
);

CREATE TABLE IF NOT EXISTS carteiras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    saldo DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status_carteira VARCHAR(20) DEFAULT 'ativa',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS transacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carteira_id INT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    status_transacao VARCHAR(20) DEFAULT 'concluida',
    FOREIGN KEY (carteira_id) REFERENCES carteiras(id)
);


