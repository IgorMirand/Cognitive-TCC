import requests
from datetime import datetime
from dotenv import load_dotenv
import os

# =============================================================================
#  CONFIGURAÇÃO — altere apenas estas duas constantes
# =============================================================================

BASE_URL = "https://cognitive-tcc.vercel.app/"   # sem barra no final
load_dotenv()
API_KEY = os.getenv("API_KEY", "")

# =============================================================================
#  Database
# =============================================================================

class Database:
    def __init__(self):
        self.base_url = BASE_URL

        # Token JWT retornado pelo /login. Começa vazio.
        self._token: str = ""

    # -------------------------------------------------------------------------
    #  Helpers internos — toda requisição passa por aqui
    # -------------------------------------------------------------------------

    def _headers(self) -> dict:
        """
        Monta os headers obrigatórios para TODA requisição:
          - X-Api-Key  → libera o acesso à API (camada global)
          - Authorization → identifica o usuário logado (camada JWT)
        """
        h = {"X-Api-Key": API_KEY}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _get(self, path: str, **kwargs):
        return requests.get(f"{self.base_url}{path}", headers=self._headers(), **kwargs)

    def _post(self, path: str, **kwargs):
        return requests.post(f"{self.base_url}{path}", headers=self._headers(), **kwargs)

    def _put(self, path: str, **kwargs):
        return requests.put(f"{self.base_url}{path}", headers=self._headers(), **kwargs)

    def _delete(self, path: str, **kwargs):
        return requests.delete(f"{self.base_url}{path}", headers=self._headers(), **kwargs)

    # -------------------------------------------------------------------------
    #  AUTH
    # -------------------------------------------------------------------------

    def register_user(self, username, password, user_type, email, data_nascimento_str):
        try:
            res = self._post("/register", json={
                "username": username, "password": password,
                "user_type": user_type, "email": email,
                "data_nascimento": data_nascimento_str,
            })
            if res.status_code == 200:
                return True, "Registrado com sucesso!", res.json().get("id")
            return False, res.json().get("detail", "Erro"), None
        except Exception as e:
            return False, str(e), None

    def verify_user(self, email, password):
        try:
            res = self._post("/login", json={"email": email, "password": password})
            if res.status_code == 200:
                d = res.json()
                # Salva o token JWT para todas as próximas requisições
                self._token = d.get("access_token", "")
                return True, "Login OK", d["user_type"], d["id"], d["username"]
            return False, res.json().get("detail", "Erro"), None, None, None
        except Exception as e:
            return False, str(e), None, None, None

    def change_password(self, user_id, old_pass, new_pass):
        try:
            res = self._put(f"/users/{user_id}/password", json={
                "old_password": old_pass, "new_password": new_pass,
            })
            if res.status_code == 200:
                return True, "Senha alterada com sucesso!"
            return False, res.json().get("detail", "Erro ao alterar senha.")
        except Exception:
            return False, "Erro de conexão."

    # -------------------------------------------------------------------------
    #  PSICÓLOGO — dashboard
    # -------------------------------------------------------------------------

    def get_patient_count(self, psicologo_id):
        try:
            res = self._get(f"/psicologo/{psicologo_id}/stats")
            if res.status_code == 200:
                return True, res.json()["pacientes_count"]
            print(f"Erro Stats: {res.status_code} - {res.text}")
            return False, 0
        except Exception as e:
            print(f"Erro Conexão Stats: {e}")
            return False, 0

    def get_next_appointment(self, psicologo_id):
        try:
            res = self._get(f"/psicologo/{psicologo_id}/stats")
            if res.status_code == 200:
                data = res.json()["proxima_consulta"]
                return True, tuple(data) if data else None
            return False, None
        except Exception:
            return False, None

    def get_pacientes_do_psicologo(self, psicologo_id):
        try:
            res = self._get(f"/psicologo/{psicologo_id}/pacientes")
            if res.status_code == 200:
                return [tuple(x) for x in res.json()["pacientes"]]
            return []
        except Exception:
            return []

    def get_pacientes_do_psicologo_com_nomes(self, psicologo_id):
        try:
            res = self._get(f"/psicologo/{psicologo_id}/pacientes")
            if res.status_code == 200:
                return [tuple(x) for x in res.json().get("pacientes", [])]
            return []
        except Exception as e:
            print(f"[ERRO] get_pacientes_do_psicologo_com_nomes: {e}")
            return []

    # -------------------------------------------------------------------------
    #  ATIVIDADES
    # -------------------------------------------------------------------------

    def get_atividades_template(self):
        try:
            res = self._get("/atividades")
            if res.status_code == 200:
                return True, [tuple(x) for x in res.json()["atividades"]]
            return False, []
        except Exception:
            return False, []

    def adicionar_atividade_template(self, texto, psicologo_id):
        try:
            res = self._post("/atividades", json={"texto": texto, "psicologo_id": psicologo_id})
            if res.status_code == 200:
                return True, "Criado com sucesso"
            return False, res.json().get("detail")
        except Exception as e:
            return False, str(e)

    def delete_atividade_template(self, atividade_id):
        try:
            res = self._delete(f"/atividades/{atividade_id}")
            if res.status_code == 200:
                return True, "Excluído"
            return False, res.json().get("detail")
        except Exception as e:
            return False, str(e)

    def update_atividade_template(self, atividade_id, novo_texto):
        try:
            res = self._put(f"/atividades/{atividade_id}?novo_texto={novo_texto}")
            if res.status_code == 200:
                return True, "Atualizado"
            return False, res.json().get("detail")
        except Exception:
            return False, "Erro"

    # -------------------------------------------------------------------------
    #  DIÁRIO
    # -------------------------------------------------------------------------

    def add_entrada_completa_diario(self, user_id, data_hora, sentimento_id, anotacao, atividades_ids):
        try:
            res = self._post("/diario", json={
                "paciente_id": user_id,
                "data_hora_iso": data_hora,
                "sentimento_id": sentimento_id,
                "anotacao": anotacao,
                "atividades_ids": atividades_ids,
            })
            if res.status_code == 200:
                return True, "Salvo!"
            return False, res.json().get("detail")
        except Exception as e:
            return False, str(e)

    def get_entradas_historico(self, user_id):
        try:
            res = self._get(f"/diario/historico/{user_id}")
            if res.status_code == 200:
                return True, [tuple(x) for x in res.json()["historico"]]
            return False, []
        except Exception:
            return False, []

    # -------------------------------------------------------------------------
    #  VÍNCULO E CÓDIGOS
    # -------------------------------------------------------------------------

    def get_psicologo_id_by_paciente(self, paciente_id):
        try:
            res = self._get(f"/paciente/{paciente_id}/psicologo")
            if res.status_code == 200:
                return res.json().get("psicologo_id")
            return None
        except Exception as e:
            print(f"[ERRO] get_psicologo_id_by_paciente: {e}")
            return None

    def validar_codigo_master(self, codigo):
        try:
            res = self._get(f"/codigos/master/validar/{codigo}")
            if res.status_code == 200:
                data = res.json()
                if data.get("valid") is True:
                    return data.get("id")
            return None
        except Exception as e:
            print(f"[ERRO] validar_codigo_master: {e}")
            return None

    def marcar_codigo_master_usado(self, codigo_id, user_id):
        try:
            res = self._post("/codigos/master/usar", json={"codigo_id": codigo_id, "user_id": user_id})
            return res.status_code == 200
        except Exception as e:
            print(f"[ERRO] marcar_codigo_master_usado: {e}")
            return False

    def gerar_codigo_paciente(self, psicologo_id):
        try:
            res = self._post(f"/codigos/gerar/{psicologo_id}")
            if res.status_code == 200:
                return res.json().get("codigo")
            print(f"[ERRO] gerar_codigo: {res.status_code} - {res.text}")
            return None
        except Exception as e:
            print(f"[ERRO CONEXÃO] gerar_codigo_paciente: {e}")
            return None

    def vincular_paciente_por_codigo(self, paciente_id, codigo):
        try:
            res = self._post("/vincular", json={"paciente_id": paciente_id, "codigo": codigo})
            if res.status_code == 200:
                return True, "Vínculo realizado com sucesso! Agora seu psicólogo pode ver seus dados."
            return False, res.json().get("detail", "Erro desconhecido ao vincular.")
        except Exception as e:
            print(f"[ERRO] vincular_paciente_por_codigo: {e}")
            return False, "Falha de conexão com o servidor."

    # -------------------------------------------------------------------------
    #  USUÁRIO
    # -------------------------------------------------------------------------

    def get_user_details(self, user_id):
        try:
            res = self._get(f"/users/{user_id}")
            if res.status_code == 200:
                data = res.json()
                if data.get("data_nascimento"):
                    try:
                        dt = datetime.strptime(data["data_nascimento"], "%Y-%m-%d")
                        data["data_nascimento"] = dt.strftime("%d/%m/%Y")
                    except Exception:
                        pass
                return data
            return None
        except Exception as e:
            print(f"[ERRO] get_user_details: {e}")
            return None

    def update_user_details(self, user_id, username, email, data_nascimento):
        try:
            res = self._put(f"/users/{user_id}", json={
                "username": username,
                "email": email,
                "data_nascimento": data_nascimento,
            })
            if res.status_code == 200:
                return True, "Dados atualizados com sucesso!"
            return False, res.json().get("detail", "Erro ao atualizar.")
        except Exception as e:
            print(f"[ERRO] update_user_details: {e}")
            return False, "Erro de conexão."

    # -------------------------------------------------------------------------
    #  AGENDA
    # -------------------------------------------------------------------------

    def get_agenda_psicologo(self, psicologo_id):
        try:
            res = self._get(f"/agenda/psicologo/{psicologo_id}")
            if res.status_code == 200:
                return [tuple(x) for x in res.json().get("agenda", [])]
            return []
        except Exception as e:
            print(f"[ERRO] get_agenda_psicologo: {e}")
            return []

    def adicionar_disponibilidade(self, psicologo_id, data_hora_obj):
        try:
            data_iso = data_hora_obj.isoformat() if hasattr(data_hora_obj, "isoformat") else str(data_hora_obj)
            res = self._post("/agenda/disponibilidade", json={
                "psicologo_id": psicologo_id,
                "data_hora_iso": data_iso,
            })
            if res.status_code == 200:
                return True, "Horário adicionado com sucesso!"
            return False, res.json().get("detail", "Erro ao salvar horário.")
        except Exception as e:
            print(f"[ERRO] adicionar_disponibilidade: {e}")
            return False, "Erro de conexão com o servidor."

    def excluir_horario(self, agenda_id):
        try:
            res = self._delete(f"/agenda/{agenda_id}")
            if res.status_code == 200:
                return True, "Horário removido."
            return False, res.json().get("detail", "Erro ao excluir.")
        except Exception as e:
            print(f"[ERRO] excluir_horario: {e}")
            return False, "Erro de conexão."

    def get_horarios_paciente(self, psicologo_id, meu_id):
        try:
            res = self._get(f"/agenda/psicologo/{psicologo_id}")
            if res.status_code == 200:
                todos = res.json().get("agenda", [])
                return [tuple(x) for x in todos if x[2] is None or x[2] == meu_id]
            return []
        except Exception as e:
            print(f"[ERRO] get_horarios_paciente: {e}")
            return []

    def reservar_horario(self, agenda_id, paciente_id):
        try:
            res = self._put(f"/agenda/{agenda_id}/reservar", json={"paciente_id": paciente_id})
            if res.status_code == 200:
                return True, "Agendamento confirmado!"
            return False, res.json().get("detail", "Erro ao agendar.")
        except Exception as e:
            return False, str(e)

    def agendar_consulta(self, agenda_id, paciente_id):
        try:
            res = self._put(f"/agenda/{agenda_id}/reservar", json={"paciente_id": paciente_id})
            if res.status_code == 200:
                return True, "Agendamento confirmado com sucesso!"
            return False, res.json().get("detail", "Erro ao agendar.")
        except Exception as e:
            print(f"[ERRO] agendar_consulta: {e}")
            return False, "Erro de conexão."

    # -------------------------------------------------------------------------
    #  CONSULTAS / ANOTAÇÕES
    # -------------------------------------------------------------------------

    def get_anotacoes_paciente(self, psicologo_id, paciente_id):
        try:
            res = self._get(f"/consultas/{psicologo_id}/{paciente_id}")
            if res.status_code == 200:
                return [tuple(x) for x in res.json().get("anotacoes", [])]
            return []
        except Exception as e:
            print(f"[ERRO] get_anotacoes_paciente: {e}")
            return []

    def salvar_anotacao_psicologo(self, psicologo_id, paciente_id, texto, data_hora_iso):
        try:
            res = self._post("/consultas", json={
                "psicologo_id": psicologo_id,
                "paciente_id": paciente_id,
                "anotacao": texto,
                "data_hora_iso": data_hora_iso,
            })
            if res.status_code == 200:
                return True, "Relatório salvo com sucesso!"
            return False, res.json().get("detail", "Erro ao salvar relatório.")
        except Exception as e:
            print(f"[ERRO] salvar_anotacao_psicologo: {e}")
            return False, "Erro de conexão com o servidor."

    # -------------------------------------------------------------------------
    #  EMAIL / CONVITE
    # -------------------------------------------------------------------------

    def enviar_convite(self, psicologo_id, email_paciente):
        try:
            res = self._post("/email/enviar_convite", json={
                "psicologo_id": psicologo_id,
                "email_paciente": email_paciente,
            })
            if res.status_code == 200:
                return True, "Convite enviado com sucesso!"
            return False, res.json().get("detail", "Erro ao enviar convite.")
        except Exception as e:
            print(f"[ERRO] enviar_convite: {e}")
            return False, "Erro de conexão com o servidor."

    # -------------------------------------------------------------------------
    #  NOTIFICAÇÕES
    # -------------------------------------------------------------------------

    def get_minhas_notificacoes(self, user_id):
        try:
            res = self._get(f"/notificacoes/{user_id}")
            return res.json().get("notificacoes", []) if res.status_code == 200 else []
        except Exception:
            return []

    def deletar_notificacao(self, notif_id):
        try:
            self._delete(f"/notificacoes/{notif_id}")
            return True
        except Exception:
            return False

    def marcar_notificacoes_lidas(self, user_id):
        try:
            self._put(f"/notificacoes/marcar_lida/{user_id}")
            return True
        except Exception:
            return False

    # -------------------------------------------------------------------------
    #  CONFIG
    # -------------------------------------------------------------------------

    def get_powerbi_url(self):
        try:
            res = self._get("/config/powerbi")
            if res.status_code == 200:
                return res.json().get("url")
            return None
        except Exception as e:
            print(f"[ERRO] get_powerbi_url: {e}")
            return None

    # -------------------------------------------------------------------------
    #  RELATÓRIOS / ANALYTICS
    # -------------------------------------------------------------------------

    def get_relatorio_paciente(self, paciente_id):
        try:
            res = self._get(f"/relatorios/analise/{paciente_id}")
            if res.status_code == 200:
                return True, res.json()
            print(f"[ERRO] get_relatorio_paciente: {res.status_code} - {res.text}")
            return False, {}
        except Exception as e:
            print(f"[ERRO] get_relatorio_paciente: {e}")
            return False, {}

    def get_grafico_atividades(self, paciente_id):
        try:
            res = self._get(f"/relatorios/grafico_atividades/{paciente_id}")
            if res.status_code == 200:
                return res.json().get("base64")
            return None
        except Exception as e:
            print(f"[ERRO] get_grafico_atividades: {e}")
            return None