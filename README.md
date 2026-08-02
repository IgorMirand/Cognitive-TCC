# 🧠 Cognitive — Plataforma de Saúde Mental

> Trabalho de Conclusão de Curso — Sistema de acompanhamento psicológico com diário emocional, agenda e relatórios analíticos.

---

## 📌 Sobre o Projeto

O **Cognitive** é uma plataforma desktop desenvolvida como TCC que conecta **psicólogos e pacientes** em um ambiente digital seguro. O paciente registra seu humor diário, agenda consultas e recebe notificações. O psicólogo acompanha a evolução emocional do paciente através de relatórios e gráficos gerados automaticamente.

### Funcionalidades principais

**Paciente**
- Registro diário de humor com emojis de emoção e anotações livres
- Registro de atividades realizadas no dia
- Agendamento de consultas com seu psicólogo
- Notificações de novos horários disponíveis
- Área de perfil com edição de dados e senha

**Psicólogo**
- Dashboard com contagem de pacientes e próxima consulta
- Lista de pacientes vinculados
- Geração de relatório analítico por paciente:
  - Gráfico de evolução do bem-estar ao longo do tempo
  - Gráfico de distribuição de emoções
  - Gráfico de atividades realizadas
  - Resumo textual com classificação (Positivo / Estável / Atenção / Crítico)
- Gerenciamento de atividades sugeridas
- Anotações privadas por consulta
- Geração de código de vínculo para convidar pacientes

---

## 🏗️ Arquitetura

O projeto é dividido em dois repositórios independentes:

```
Projeto TCC/
├── Cognitive-API/      ← Backend (FastAPI) — hospedado na Vercel
└── Cognitive-Front/    ← Frontend desktop (Kivy/KivyMD)
```

```
[ Cognitive-Front (Kivy) ]
          │  HTTP + X-Api-Key + Bearer JWT
          ▼
[ Cognitive-API (FastAPI) ]  ←→  [ PostgreSQL — Neon ]
```

### Segurança da API
- **API Key global** — todas as rotas exigem o header `X-Api-Key`
- **JWT por usuário** — login retorna token Bearer; rotas sensíveis validam tipo de usuário (Psicólogo / Paciente)

---

## 🛠️ Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Python 3.13, Kivy 2.x, KivyMD |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Banco de dados | PostgreSQL (Neon — serverless) |
| Autenticação | JWT (PyJWT) + API Key |
| Gráficos | Matplotlib, Pandas |
| Deploy API | Vercel |
| Hash de senha | bcrypt |

---

## 🚀 Como rodar localmente

### Pré-requisitos

- Python 3.11 ou superior
- Git

---

### 1. Clone os repositórios

```bash
git clone https://github.com/IgorMirand/Cognitive-TCC.git
```

---

### 2. Configure e rode a API

```bash
cd Cognitive-API

# Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate       # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com as credenciais (veja seção abaixo)

# Rode a API
uvicorn main:app --reload
```

A API estará disponível em `https://cognitive-tcc.vercel.app/`

Documentação Swagger: `https://cognitive-tcc.vercel.app/docs`

---

### 3. Configure e rode o Front

```bash
cd Cognitive-Front

# Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate       # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com a API Key e URL da API

# Rode o app
python main.py
```

---

## ⚙️ Variáveis de Ambiente

### Cognitive-API — `.env`

```env
# Banco de dados (Neon / PostgreSQL)
NEON_DB_URL=postgres://usuario:senha@host/banco

# API Key global — o Front envia este valor no header X-Api-Key
API_KEY=sua_chave_aqui

# Secret para assinar os tokens JWT
JWT_SECRET=seu_secret_aqui

# Email (opcional — para envio de convites)
GMAIL_USER=seu.email@gmail.com
GMAIL_PASS=senha_de_app
```

### Cognitive-Front — `.env`

```env
# URL da API (local ou produção)
API_URL=http://127.0.0.1:8000

# Deve ser igual ao API_KEY da Cognitive-API
API_KEY=sua_chave_aqui
```

---

## 🎮 Credenciais de Demonstração

> O banco contém dados gerados aleatoriamente para fins de demonstração. As respostas não são reais ou sensíveis, pois foram preenchidas por uma IA.

| Perfil | Email | Senha |
|---|---|---|
| Psicólogo | `renata@gmail.com` | `123` |
| Paciente | `maria@gmail.com` | `123` |

**API Key de demo:** `e8cd477a6291839fd38574fd71ab6e6e2fe2774331ea4d90dc9aaa21b9aeff37`

> Para usar a versão em produção (Vercel), altere `API_URL` no `.env` do Front para a URL da sua Vercel.

---

## 📁 Estrutura do Projeto

### Cognitive-API
```
Cognitive-API/
├── main.py                        ← Entry point FastAPI
├── .env.example
├── requirements.txt
└── app/
    ├── core/
    │   ├── config.py              ← Settings e variáveis de ambiente
    │   ├── database.py            ← Conexão PostgreSQL
    │   └── security.py            ← JWT, API Key, bcrypt
    ├── models/
    │   ├── user_models.py
    │   ├── agenda_models.py
    │   ├── diario_models.py
    │   └── psicologo_models.py
    └── api/routes/
        ├── auth_routes.py         ← Register, login, perfil
        ├── agenda_routes.py       ← Disponibilidade e reservas
        ├── diario_routes.py       ← Entradas do diário
        ├── psicologo_routes.py    ← Vínculos, atividades, consultas
        ├── notificacoes_routes.py ← Notificações
        └── analytics_routes.py   ← Relatórios e gráficos
```

### Cognitive-Front
```
Cognitive-Front/
├── main.py                        ← Entry point Kivy
├── requirements.txt
└── app/
    ├── core/
    │   ├── database.py            ← Todas as chamadas HTTP à API
    │   └── auth.py                ← Lógica de registro e login
    └── ui/
        ├── manager.py             ← Gerenciador de telas
        ├── styles.kv              ← Estilos globais
        └── telas/
            ├── main.py / .kv
            ├── login.py / .kv
            ├── register.py / .kv
            ├── home.py / .kv
            ├── home_psicologo.py / .kv
            ├── diario.py / .kv
            ├── agenda.py / .kv
            ├── conta.py / .kv
            └── ...
```

---

## 🔒 Segurança

- Senhas armazenadas com hash `bcrypt` — nunca em texto puro
- Autenticação em duas camadas: API Key (app) + JWT (usuário)
- Roles por tipo de usuário — psicólogo não acessa rotas de paciente e vice-versa
- Variáveis sensíveis isoladas em `.env` — nunca versionadas no Git
- `.env` listado no `.gitignore` em ambos os repositórios

---

## 👨‍💻 Autores

**Igor Miranda Moura**

**Raiel Ferreira Araujo**

**Igor Nunes Araujo**

TCC — Ciência da Computação — UDF — 2025

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
