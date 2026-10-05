# 🧠 Cognitive — Plataforma de Saúde Mental

> Trabalho de Conclusão de Curso — Sistema de acompanhamento psicológico com diário emocional, agenda e relatórios analíticos.

---

## 📌 Sobre o Projeto

O **Cognitive** conecta **psicólogos e pacientes** em um ambiente digital seguro. O paciente registra seu humor diário, agenda consultas e recebe notificações. O psicólogo acompanha a evolução emocional do paciente por meio de relatórios e gráficos gerados automaticamente.

A plataforma tem **dois clientes** que consomem a mesma API:

- **Desktop** (Kivy/KivyMD): aplicativo original.
- **Web** (React + Vite): versão em navegador, em desenvolvimento.

### 🌐 Demo online

| Serviço | URL |
|---|---|
| Aplicação web | https://cognitive-tcc-ld6g.vercel.app |
|  Documentação da API| https://cognitive-tcc.vercel.app |

As credenciais de demonstração estão na seção [Credenciais de Demonstração](#-credenciais-de-demonstração).

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
- Relatório analítico por paciente:
  - Gráfico de evolução do bem-estar ao longo do tempo
  - Gráfico de distribuição de emoções
  - Gráfico de atividades realizadas
  - Resumo textual com classificação (Positivo / Estável / Atenção / Crítico)
- Gerenciamento de atividades sugeridas
- Anotações privadas por consulta
- Agenda: abertura e remoção de horários
- Geração de código de vínculo para convidar pacientes
- Edição de perfil e troca de senha

---

## 🏗️ Arquitetura

O projeto é um **monorepo** com três pastas:

```
Projeto-TCC/
├── Cognitive-API/      ← Backend (FastAPI), hospedado na Vercel
├── Cognitive-Front/    ← Cliente desktop (Kivy/KivyMD)
└── cognitive-web/      ← Cliente web (React + Vite)
```

```
[ Cognitive-Front (Kivy) ]──┐
                            │  HTTP + X-Api-Key + Bearer JWT
[ cognitive-web (React) ]───┤
                            ▼
                [ Cognitive-API (FastAPI) ]  ←→  [ PostgreSQL — Neon ]
```

### Segurança da API
- **API Key global:** as rotas exigem o header `X-Api-Key`
- **JWT por usuário:** o login retorna um token Bearer; rotas sensíveis validam o tipo de usuário (Psicólogo / Paciente)

> 🔐 No cliente web, a API Key **não vai para o navegador**. O front chama `/api/...` no próprio domínio, e uma função serverless da Vercel (`api/proxy.js`) repassa a requisição para a API adicionando o `X-Api-Key` no servidor. A chave fica apenas nas variáveis de ambiente da Vercel.

---

## 🛠️ Stack

| Camada | Tecnologia |
|---|---|
| Frontend desktop | Python, Kivy 2.x, KivyMD |
| Frontend web | React 18, Vite, React Router |
| Backend | Python, FastAPI, Uvicorn |
| Banco de dados | PostgreSQL (Neon, serverless) |
| Autenticação | JWT (PyJWT) + API Key |
| Gráficos | Matplotlib, Pandas |
| Deploy | Vercel (API e web) |
| Hash de senha | bcrypt |

---

## 🚀 Como rodar localmente

### Pré-requisitos

- Python 3.11 ou superior
- Node.js 18 ou superior (apenas para o cliente web)
- Git

### 1. Clone o repositório

```bash
git clone https://github.com/IgorMirand/Cognitive-TCC.git
cd Cognitive-TCC
```

### 2. API

```bash
cd Cognitive-API

python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt

cp .env.example .env
# Edite o .env com as credenciais (veja a seção de variáveis)

uvicorn main:app --reload
```

- API local: `http://127.0.0.1:8000`
- Swagger local: `http://127.0.0.1:8000/docs`
- API em produção: `https://cognitive-tcc.vercel.app`

### 3. Cliente desktop (Kivy)

```bash
cd Cognitive-Front

python -m venv .venv
.venv\Scripts\activate       # Windows

pip install -r requirements.txt

cp .env.example .env
# Edite o .env com a URL da API e a API Key

python main.py
```

### 4. Cliente web (React)

```bash
cd cognitive-web

npm install

cp .env.example .env
# Edite o .env com a URL da API e a API Key

npm run dev
```

O app abre em `http://localhost:5173`. Em desenvolvimento, o `vite.config.js` faz o papel do proxy: encaminha `/api/*` para a `API_URL` e injeta o `X-Api-Key`.

Outros comandos: `npm run build` (build de produção) e `npm run preview` (servir o build).

---

## ⚙️ Variáveis de Ambiente

### Cognitive-API: `.env`

```env
# Banco de dados (Neon / PostgreSQL)
NEON_DB_URL=postgres://usuario:senha@host/banco

# API Key global (o cliente envia este valor no header X-Api-Key)
API_KEY=sua_chave_aqui

# Secret para assinar os tokens JWT
JWT_SECRET=seu_secret_aqui

# Email (opcional, para envio de convites)
GMAIL_USER=seu.email@gmail.com
GMAIL_PASS=senha_de_app
```

### Cognitive-Front (desktop): `.env`

```env
API_URL=http://127.0.0.1:8000
API_KEY=sua_chave_aqui
```

### cognitive-web: `.env`

```env
# Sem prefixo VITE_: são lidas só pelo servidor (proxy), nunca vão para o navegador
API_URL=http://127.0.0.1:8000
API_KEY=sua_chave_aqui
```

Em todos os casos, a chave deve ser igual ao `API_KEY` configurado na API.

---

## ☁️ Deploy (Vercel)

O repositório é um monorepo, então a API e o cliente web são **dois projetos separados** na Vercel, cada um apontando para a sua pasta (*Root Directory*).

| Projeto | Root Directory | Variáveis de ambiente |
|---|---|---|
| API (`cognitive-tcc`) | `Cognitive-API` | `NEON_DB_URL`, `API_KEY`, `JWT_SECRET`, `GMAIL_USER`, `GMAIL_PASS`, `CORS_ORIGINS` |
| Web (`cognitive-tcc-ld6g`) | `cognitive-web` | `API_URL`, `API_KEY` |

Pontos de atenção:

- `API_KEY` deve ter **o mesmo valor** nos dois projetos.
- `API_URL` é a URL da API **sem barra no final** (`https://cognitive-tcc.vercel.app`).
- Variáveis só valem para deploys novos: depois de alterá-las, faça **Redeploy**.
- O `vercel.json` do web encaminha `/api/*` para `api/proxy.js` e devolve o `index.html` para as demais rotas (necessário para o React Router).
- `requirements.txt` precisa estar em **UTF-8**; arquivos gerados com `>` no PowerShell saem em UTF-16 e quebram o build da Vercel.

---

## 🎮 Credenciais de Demonstração

> O banco contém dados gerados aleatoriamente para demonstração. As respostas não são reais nem sensíveis, pois foram preenchidas por uma IA.

| Perfil | Email | Senha |
|---|---|---|
| Psicólogo | `renata@gmail.com` | `123` |
| Paciente | `maria@gmail.com` | `123` |

A API Key da demonstração é fornecida à banca avaliadora separadamente e **não** é publicada neste repositório.

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
        └── analytics_routes.py    ← Relatórios e gráficos
```

### Cognitive-Front (desktop)
```
Cognitive-Front/
├── main.py                        ← Entry point Kivy
├── requirements.txt
└── app/
    ├── core/
    │   ├── database.py            ← Chamadas HTTP à API
    │   └── auth.py                ← Lógica de registro e login
    └── ui/
        ├── manager.py             ← Gerenciador de telas
        ├── styles.kv              ← Estilos globais
        └── telas/                 ← Login, registro, home, diário, agenda, conta...
```

### cognitive-web
```
cognitive-web/
├── index.html
├── package.json
├── vite.config.js                 ← Proxy /api em desenvolvimento
├── vercel.json                    ← Rewrites (SPA + proxy)
├── .env.example
├── api/
│   └── proxy.js                   ← Função serverless: adiciona X-Api-Key e repassa à API
└── src/
    ├── api/api.js                 ← Cliente HTTP central (chama /api + JWT)
    ├── context/AuthContext.jsx    ← Sessão do usuário
    ├── components/                ← Sidebars e componentes compartilhados
    └── pages/
        ├── LoginPage.jsx / RegisterPage.jsx
        ├── paciente/              ← Área do paciente
        └── psicologo/             ← Dashboard, agenda, pacientes, vínculos,
                                     atividades e perfil
```

---

## 🔒 Segurança

- Senhas armazenadas com hash `bcrypt`, nunca em texto puro
- Autenticação em duas camadas: API Key (app) + JWT (usuário)
- Roles por tipo de usuário: psicólogo não acessa rotas de paciente e vice-versa
- Variáveis sensíveis isoladas em `.env`, nunca versionadas no Git
- `.env` listado no `.gitignore` de todos os projetos; use o `.env.example` como modelo

---

## 👨‍💻 Autores

**Igor Miranda Moura**

**Raiel Ferreira Araujo**

**Igor Nunes Araujo**

TCC — Ciência da Computação — UDF

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
