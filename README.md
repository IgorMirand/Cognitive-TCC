# Cognitive 🧠
### Plataforma de Acompanhamento Terapêutico

> Trabalho de Conclusão de Curso (TCC) — Bacharelado em Ciência da Computação

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Kivy](https://img.shields.io/badge/Kivy-Mobile-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)

---

# 📌 Sobre o Projeto

O **Cognitive** é uma plataforma desenvolvida para auxiliar no acompanhamento terapêutico utilizando princípios da Terapia Cognitivo-Comportamental (TCC).

O sistema é composto por:

- 📱 Aplicativo Mobile para pacientes
- ⚙️ API REST para gerenciamento de dados
- 📊 Dashboard analítico para psicólogos

A plataforma permite o acompanhamento contínuo do paciente entre sessões terapêuticas através de registros emocionais, atividades diárias e geração de relatórios inteligentes.

---

# 🏗 Arquitetura do Projeto

```txt
Cognitive-TCC/
 ├── Cognitive-API/      # Backend FastAPI
 ├── Cognitive-Front/    # Aplicativo Mobile Kivy
 └── README.md
```

---

# 🚀 Funcionalidades

## 👤 Paciente
- Registro diário de humor
- Registro de atividades
- Diário emocional
- Histórico de evolução

## 👨‍⚕️ Psicólogo
- Gestão de pacientes
- Visualização de gráficos
- Relatórios analíticos
- Agenda de consultas

---

# 🛠 Tecnologias Utilizadas

## Backend
- FastAPI
- PostgreSQL
- Pandas
- Matplotlib
- Bcrypt

## Frontend Mobile
- Python
- Kivy
- KivyMD

---

# 📷 Screenshots

| Dashboard | Relatório | Diário |
|---|---|---|
| Screenshot | Screenshot | Screenshot |

---

# ⚙️ Como Executar

## 1. Clone o projeto

```bash
git clone https://github.com/IgorMirand/Cognitive-TCC.git
```

---

## 2. Backend

```bash
cd Cognitive-API
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## 3. Frontend Mobile

```bash
cd Cognitive-Front
pip install -r requirements.txt
python main_app.py
```

---

# 📄 Licença

Este projeto está sob a licença MIT.

---

# 👨‍💻 Desenvolvedores

- Igor Miranda Moura
- Raiel Ferreira Araujo
- Igor Nunes Araujo
