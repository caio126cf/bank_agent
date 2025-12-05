# 🤖 Banco Ágil – Assistente Virtual



---

## Link testando o Assistente

O vídeo foi levemente editado, como rodei consumi o gpt

https://youtu.be/EMrnbtZROLM

## 📌 Visão Geral do Projeto

Este projeto implementa um assistente virtual bancário capaz de autenticar usuários, realizar solicitações de aumento de limite, conduzir entrevistas de crédito e consultar cotações de câmbio.  
Ele utiliza **LangChain**, **LangGraph**, **csv**, **uv** e **Ollama**.

Este repositório é um **fork** do projeto open source original:  
https://github.com/luizomf/react_agent_langgraph_course

O objetivo do projeto é criar um **agente bancário inteligente**, seguindo regras fortes de atendimento e tomando decisões com base nas interações do cliente.

Funcionalidades principais:

- Autenticação de clientes via CPF + data de nascimento  
- Solicitação de aumento de limite  
- Entrevista de crédito quando o aumento é negado  
- Cotação de câmbio  
- Encerramento de atendimento  
- Execução totalmente guiada por ferramentas (tools) integradas ao LLM

---

## 🏗 Arquitetura do Sistema

A arquitetura combina:

### **1. LangGraph**
Usado para padronizar o fluxo, mas não controlar as decisões:

- `call_llm` → chama o modelo  
- `tool_node` → executa ferramentas solicitadas pelo LLM  
- `router` → verifica se há tool_call e encerrar caso não tenha

O fluxo é cíclico:

START → call_llm → (router) → tool_node → call_llm → ... → END

![Imagem de fluxo graph](assets\fluxo graph.png)

### **2. Prompt Engineering**
Grande parte do comportamento do agente vem do `SYSTEM_PROMPT` em `prompt.py` (arquivo singular):

- Define fluxo de triagem  
- Regras de autenticação  
- Fluxo de aumento de limite  
- Entrevista de crédito  
- Cotação de câmbio  
- Comportamento empático  
- Regras de quando chamar tools  

Por enquanto, **a lógica do fluxo está no prompt** — ainda não 100% determinístico via grafo.

### **3. Tools**
As ferramentas ficam em `tools.py` e realizam tarefas com:

- `triagem` (autenticação de usuários)
- `solicitar_aumento_limite`
- `recalcular_score`
- `quote_currency`
- `encerrar_conversa`

Todas as tools acessam os CSVs dentro da pasta `db/`.

### **4. Base de Dados**
A pasta `db/` atua como um banco de dados simples contendo score_limite.csv, solicitacoes_aumento_limite.csv e users.csv.


### **5. Threads e Memória**

Ciclo de Vida de uma Thread

Criação:
`main.py`
config = RunnableConfig(configurable={"thread_id": 1})

Uso:
# Cada interação usa o mesmo thread_id
`main.py`
result = graph.invoke({"messages": current_loop_messages}, config=config)

Persistência:
O InMemorySaver mantém o estado na RAM.
Checkpoints são salvos automaticamente após cada invoke.
O histórico completo é acumulado.

Finalização:
Quando o programa termina, a memória é liberada.

---

## 🧩 Desafios Enfrentados

- **Tornar o fluxo determinístico com LangGraph, lidar com Multiagentes**
  O LangGraph exige rotas claras entre os nós, mas o comportamento do LLM é dinâmico.  
  Foi difícil garantir previsibilidade 100% só via grafo. 

  **Solução atual:**  
  Centralizei a maior parte da lógica no prompt, planejando migrar para um fluxo mais determinístico no futuro via Graph.py. Também normalizar o idioma do código completamente para inglês.

- Manter validação de dados (CPF, datas etc.) robusta.
- Garantir que o LLM só chame tools nos momentos corretos.
- Controlar limites de tentativas sem perder o estado.
- Organizar o loop `llm → tool → llm` e permitir uma saída ao encerrar.

---

## 🔧 Escolhas Técnicas & Justificativas

### **LangChain e LangGraph**
Permite criar fluxos determinísticos e separar:
- consumo de LLM em cloud e local.
- execução de ferramentas como agentes.
- controle do estado e memória.
- lidar com multiagents.
- é o framework mais utilizado atualmente e por isso optei por ele.

### **CSV como "banco de dados"**
Para um teste técnico CSV é simples, rápido e útil.

### **Prompt Engineering**
Controla o fluxo enquanto o grafo ainda está simples.

---

### Tutorial de Execução

### 🚀 Instalação do Ollama e configuração do modelo gpt-oss:20b (Windows)  

Este projeto roda **totalmente offline**, utilizando o **Ollama** como servidor local de modelos. Não exclusivamente, no arquivo utils.py podemos consumir uma LLM hospedada em cloud.
Siga os passos abaixo para instalar o Ollama no Windows e baixar o modelo necessário.

---

### 🔧 1. Instale o Ollama (Windows)

Baixe o instalador oficial:

👉 https://ollama.com/download

Após instalar, reinicie o terminal.  

Para verificar se está funcionando:

```bash
ollama --version
```
### 🔧 2. Baixe o modelo gpt-oss:20b

Execute no terminal:

```bash
ollama pull gpt-oss:20b
```

Isso fará o download completo do modelo (pode demorar).

### 🔧 3. Certifique-se de que o Ollama está rodando no Windows
```bash
ollama serve
```

### 🔧 4. Instalar e sincronizar uv

```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Verifique se está instalado:

```bash
uv --version
```

Para sincronizar (dependências), na raiz do projeto rode:

```bash
uv sync
```

### 🔧 5. Rodar projeto.

Com o uv instalado e sincronizado, rode:

```bash
uv run src/main.py
```