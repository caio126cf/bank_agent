import csv
import os
from pathlib import Path
import requests
from datetime import datetime
from langchain.tools import BaseTool, tool
from pathlib import Path

DB_PATH = Path(__file__).parents[1] / "db"


@tool
def triagem(cpf: str, data_nascimento: str) -> dict:
    """Autentica um usuário consultando o banco de dados CSV com CPF e data de nascimento

    Args:
        cpf: string com o CPF do usuário (11 dígitos)
        data_nascimento: string com a data de nascimento no formato YYYY-MM-DD

    Returns:
        dict com os dados do usuário autenticado ou mensagem de erro
    """
    try:
        # Caminho do arquivo CSV
        users_path = DB_PATH / "users.csv"
        
        if not users_path.exists():
            return {"sucesso": False, "mensagem": "Arquivo de usuários não encontrado"}
        
        # Ler o CSV
        with open(users_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["cpf"] == cpf and row["data_nascimento"] == data_nascimento:
                    return {
                        "sucesso": True,
                        "mensagem": "Autenticação realizada com sucesso",
                        "usuario": {
                            "cpf": row["cpf"],
                            "nome": row["nome"],
                            "data_nascimento": row["data_nascimento"]
                        }
                    }
        
        return {"sucesso": False, "mensagem": "CPF ou data de nascimento inválidos"}
    
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao autenticar: {str(e)}"}


@tool
def quote_currency(from_currency: str = "USD", to_currency: str = "BRL") -> dict:
    """Busca a cotação em tempo real entre duas moedas usando AwesomeAPI.

    Responsabilidades:
    1. Buscar a cotação atual via `https://economia.awesomeapi.com.br/json/last/{FROM}-{TO}` (sem necessidade de chave).
    2. Apresentar a cotação atual ao cliente.
    3. Encerrar o atendimento específico de cotação com uma mensagem amigável.

    Args:
        from_currency: moeda base (ex: "USD")
        to_currency: moeda alvo (ex: "BRL")

    Returns:
        dict com chaves: `success`, `from`, `to`, `rate`, `message` e `closing_message`.
    """
    try:
        # Construir par de moedas dinâmico
        currency_pair = f"{from_currency.upper()}-{to_currency.upper()}"
        url = f"https://economia.awesomeapi.com.br/json/last/{currency_pair}"
        
        resp = requests.get(url, timeout=10)
        
        if resp.ok:
            data = resp.json()
            # A resposta vem com chave igual ao par (ex: "USD-BRL")
            pair_key = currency_pair
            if pair_key in data:
                quote_data = data[pair_key]
                rate = float(quote_data.get("bid"))  # "bid" é o valor de cotação
                
                return {
                    "success": True,
                    "from": from_currency.upper(),
                    "to": to_currency.upper(),
                    "rate": rate,
                    "raw": data,
                    "message": f"Cotação {from_currency.upper()}/{to_currency.upper()} obtida com sucesso",
                    "closing_message": "Cotação finalizada. Precisa de outra consulta?"
                }
            else:
                return {"success": False, "message": "Par de moedas não encontrado na resposta", "raw": data}
        else:
            return {"success": False, "message": f"Erro ao consultar API: {resp.status_code}", "raw": resp.text}

    except Exception as e:
        return {"success": False, "message": f"Erro ao buscar cotação: {str(e)}"}


@tool
def solicitar_aumento_limite(cpf: str, novo_limite_solicitado: float) -> dict:
    """Registra e processa solicitação de Alteração de Limite.

    Fluxo:
    - Busca conta em `accounts.csv` (obtém `limite_atual` e `score`).
    - Monta o pedido e registra em `solicitacoes_aumento_limite.csv` com timestamp ISO 8601.
    - Verifica a tabela `score_limite.csv` para checar se o `novo_limite_solicitado`
      é permitido para o score atual do cliente.
    - Define `status_pedido` como 'aprovado' ou 'rejeitado' e salva.
    - Se reprovado, inclui sugestão de redirecionamento para o Agente de Entrevista de Crédito.

    Args:
        cpf: CPF do cliente (string)
        novo_limite_solicitado: novo limite desejado (float)

    Returns:
        dict com resultado, status final e mensagens amigáveis.
    """
    try:
        users_path = DB_PATH / "users.csv"
        score_table_path = DB_PATH / "score_limite.csv"
        solicitacoes_path = DB_PATH / "solicitacoes_aumento_limite.csv"
        # base = Path(__file__).parent
        # users_path = base / "users.csv"
        # score_table_path = base / "score_limite.csv"
        # solicitacoes_path = base / "solicitacoes_aumento_limite.csv"

        if not users_path.exists():
            return {"success": False, "message": "Arquivo users.csv não encontrado"}
        

        conta = None
        with open(users_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("cpf") == cpf:
                    conta = row
                    break

        if conta is None:
            return {"success": False, "message": "Conta/CPF não encontrado em accounts.csv"}

        try:
            limite_atual = float(conta.get("limite_atual", 0))
        except Exception:
            limite_atual = 0.0

        try:
            score = int(conta.get("score", 0))
        except Exception:
            score = 0

        # Determinar limite permitido a partir da tabela de score
        if not score_table_path.exists():
            return {"success": False, "message": "Arquivo score_limite.csv não encontrado"}

        permitido = False
        max_allowed = None
        with open(score_table_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    min_s = int(row.get("min_score", 0))
                    max_s = int(row.get("max_score", 0))
                    allowed = float(row.get("max_allowed_limit", 0))
                except Exception:
                    continue
                if min_s <= score <= max_s:
                    max_allowed = allowed
                    break

        if max_allowed is None:
            return {"success": False, "message": "Nenhuma regra de limite encontrada para o score do cliente"}

        status = "rejeitado"
        if float(novo_limite_solicitado) <= float(max_allowed):
            status = "aprovado"

        # Registrar solicitação (append). Se arquivo vazio, manter header já criado.
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        header = ["cpf_cliente", "data_hora_solicitacao", "limite_atual", "novo_limite_solicitado", "status_pedido"]
        write_header = False
        if not solicitacoes_path.exists():
            write_header = True

        with open(solicitacoes_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(header)
            writer.writerow([cpf, timestamp, f"{limite_atual:.2f}", f"{float(novo_limite_solicitado):.2f}", status])

        # Se aprovado, atualizar o limite_atual em users.csv
        if status == "aprovado":

            all_users = []
            fieldnames = ["cpf", "data_nascimento", "nome", "limite_atual", "score"]

            with open(users_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["cpf"] == cpf:
                        row["limite_atual"] = f"{float(novo_limite_solicitado):.2f}"
                    all_users.append(row)

            with open(users_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_users)

            
            if fieldnames is not None:
                with open(users_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_users)

        response = {
            "success": True,
            "cpf": cpf,
            "limite_atual": limite_atual,
            "novo_limite_solicitado": float(novo_limite_solicitado),
            "status_pedido": status,
            "max_allowed_for_score": max_allowed,
            "message": ("Solicitação aprovada" if status == "aprovado" else "Solicitação rejeitada"),
        }

        if status == "rejeitado":
            response["closing_message"] = "Lamentamos — sua solicitação foi rejeitada. Se precisar de mais informações, entre em contato com o atendimento."
        else:
            response["closing_message"] = "Parabéns — seu aumento foi aprovado. Se precisar de mais ajuda, estou à disposição."

        return response

    except Exception as e:
        return {"success": False, "message": f"Erro ao processar solicitação: {str(e)}"}


@tool
def recalcular_score(
    cpf: str,
    renda_mensal: float,
    tipo_emprego: str,
    despesas_fixas: float,
    num_dependentes: int,
    tem_dividas: str
) -> dict:
    """Recalcula o score do cliente.

    Responsabilidades:
    1. Recebe dados financeiros do cliente (renda, emprego, despesas, dependentes, dívidas).
    2. Calcula novo score de crédito usando fórmula ponderada (0 a 1000).
    3. Atualiza o score na base de dados (users.csv).
    4. Retorna resultado com novo score e redirecionamento ao Agente de Crédito.

    Fórmula de Score (ponderada):
    score = (
        (renda_mensal / (despesas_fixas + 1)) * peso_renda +
        peso_emprego[tipo_emprego] +
        peso_dependentes[num_dependentes] +
        peso_dividas[tem_dividas]
    )

    Args:
        cpf: CPF do cliente (string, 11 dígitos)
        renda_mensal: renda mensal em reais (float)
        tipo_emprego: tipo de emprego ("formal", "autônomo", "desempregado")
        despesas_fixas: despesas fixas mensais em reais (float)
        num_dependentes: número de dependentes (int: 0, 1, 2, 3+)
        tem_dividas: se possui dívidas ativas ("sim", "não")

    Returns:
        dict com sucesso, novo_score, score_anterior, mensagem e redirecionamento.
    """
    try:
        users_path = DB_PATH / "users.csv"

        if not users_path.exists():
            return {"success": False, "message": "Arquivo users.csv não encontrado"}

        # Pesos da fórmula
        peso_renda = 30
        peso_emprego = {
            "formal": 300,
            "autônomo": 200,
            "desempregado": 0
        }
        peso_dependentes = {
            0: 100,
            1: 80,
            2: 60,
            "3+": 30
        }
        peso_dividas = {
            "sim": -100,
            "não": 100
        }

        # Validar tipo de emprego
        if tipo_emprego.lower() not in peso_emprego:
            return {
                "success": False,
                "message": f"Tipo de emprego inválido. Use: formal, autônomo ou desempregado"
            }

        # Validar tem_dividas
        if tem_dividas.lower() not in peso_dividas:
            return {
                "success": False,
                "message": "Resposta sobre dívidas inválida. Use: sim ou não"
            }

        # Validar num_dependentes e mapear para a chave correta
        if num_dependentes < 0:
            return {
                "success": False,
                "message": "Número de dependentes não pode ser negativo"
            }
        
        dependentes_key = "3+" if num_dependentes >= 3 else num_dependentes

        # Validar renda e despesas
        if renda_mensal < 0 or despesas_fixas < 0:
            return {
                "success": False,
                "message": "Renda e despesas não podem ser negativas"
            }

        # Calcular novo score
        relacao_renda_despesa = renda_mensal / (despesas_fixas + 1)
        novo_score = int(
            (relacao_renda_despesa * peso_renda) +
            peso_emprego[tipo_emprego.lower()] +
            peso_dependentes[dependentes_key] +
            peso_dividas[tem_dividas.lower()]
        )

        # Limitar score entre 0 e 1000
        novo_score = max(0, min(1000, novo_score))

        # Buscar score anterior e atualizar users.csv
        score_anterior = None
        all_users = []
        fieldnames = ["cpf", "data_nascimento", "nome", "limite_atual", "score"]

        with open(users_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["cpf"] == cpf:
                    score_anterior = int(row.get("score", 0))
                    row["score"] = str(novo_score)
                all_users.append(row)

        if score_anterior is None:
            return {
                "success": False,
                "message": f"Cliente com CPF {cpf} não encontrado na base de dados"
            }

        # Escrever dados atualizados
        with open(users_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_users)

        # Calcular mudança de score
        diferenca_score = novo_score - score_anterior

        return {
            "success": True,
            "cpf": cpf,
            "score_anterior": score_anterior,
            "novo_score": novo_score,
            "diferenca_score": diferenca_score,
            "renda_mensal": renda_mensal,
            "tipo_emprego": tipo_emprego,
            "despesas_fixas": despesas_fixas,
            "num_dependentes": num_dependentes,
            "tem_dividas": tem_dividas,
            "message": f"Entrevista de crédito realizada com sucesso. Score atualizado de {score_anterior} para {novo_score}",
            "closing_message": "Obrigado por participar da entrevista. Você será redirecionado ao Agente de Crédito para análise de sua solicitação."
        }

    except Exception as e:
        return {"success": False, "message": f"Erro ao processar entrevista de crédito: {str(e)}"}

@tool
def encerrar_conversa() -> dict:
    """Encerra a conversa."""
    try:
        return {"success": True, "message": "Conversa encerrada com sucesso."}
    except Exception as e:
        return {"success": False, "message": f"Falha ao encerrar a conversa: {str(e)}"}


TOOLS: list[BaseTool] = [multiply, triagem, quote_currency, solicitar_aumento_limite, recalcular_score, encerrar_conversa]
TOOLS_BY_NAME: dict[str, BaseTool] = {tool.name: tool for tool in TOOLS}
