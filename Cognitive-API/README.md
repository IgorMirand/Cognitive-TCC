# Cognitive API ⚙️

API REST responsável pelo gerenciamento de pacientes, autenticação, agenda e processamento analítico da plataforma Cognitive.

---

# 🚀 Tecnologias

- FastAPI
- PostgreSQL
- SQLAlchemy
- Pandas
- Matplotlib
- Bcrypt

---

# 📌 Funcionalidades

- Autenticação JWT
- Cadastro de pacientes
- Registro emocional
- Gestão de agenda
- Relatórios analíticos
- Geração de gráficos

---

# ⚙️ Configuração

## Instalar dependências

```bash
pip install -r requirements.txt
```

---

## Configurar variáveis de ambiente

Crie um arquivo `.env`

```env
DATABASE_URL=sua_url
SECRET_KEY=sua_chave
```

---

# ▶️ Executar API

```bash
uvicorn main:app --reload
```

---

# 📚 Documentação Swagger

Após iniciar a API:

```txt
https://api-tcc-cognitive.vercel.app/
```

---

# 🔒 Segurança

- Senhas criptografadas com Bcrypt
- Autenticação JWT
- Validação de dados com Pydantic

---

# 📄 Licença

MIT License