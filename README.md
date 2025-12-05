# 🤖 Banco Ágil – Assistente Virtual

Este projeto implementa um assistente virtual bancário capaz de autenticar usuários, realizar solicitações de aumento de limite, conduzir entrevistas de crédito e consultar cotações de câmbio.  
Ele utiliza **LangChain**, **LangGraph**,**CSV** e **uv**.

Este repositório é um **fork** do projeto open source original:  
https://github.com/luizomf/react_agent_langgraph_course

---

## Link testando o Assistente

https://youtu.be/EMrnbtZROLM

## 📌 Visão Geral do Projeto

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
Usado para organizar o fluxo:

- `call_llm` → chama o modelo  
- `tool_node` → executa ferramentas solicitadas pelo LLM  
- `router` → verifica se há tool_call e decide o próximo nó  

O fluxo é cíclico:

START → call_llm → (router) → tool_node → call_llm → ... → END


### **2. Prompt Engineering**
Grande parte do comportamento do agente vem do `SYSTEM_PROMPT` em `prompts.py`:

- Define fluxo de triagem  
- Regras de autenticação  
- Fluxo de aumento de limite  
- Entrevista de crédito  
- Cotação de câmbio  
- Comportamento empático  
- Regras de quando chamar tools  

Por enquanto, **a lógica do fluxo está no prompt** — ainda não 100% determinístico via grafo.

### **3. Tools**
As ferramentas ficam em `tools.py` e realizam tarefas como:

- `authenticate_user`
- `solicitar_aumento_limite`
- `recalcular_score`
- `quote_currency`
- `encerrar_conversa`

Todas as tools acessam os CSVs dentro da pasta `db/`.

### **4. Base de Dados**
A pasta `db/` atua como um banco de dados simples:

db/
├── score_limite.csv
├── solicitacoes_aumento_limite.csv
└── users.csv


### **5. Estado da Conversa**
A classe `State` define:

- Histórico de mensagens  
- Dados persistidos pelo fluxo  

Usado pelo LangGraph para coordenar a execução.

---

## ⚙ Funcionalidades Implementadas

- Saudar o usuário sempre na primeira interação
- Autenticação com até **3 tentativas**
- Bloqueio da conversa caso falhe as 3 tentativas
- Solicitação de aumento de limite via tool
- Redirecionamento automático para entrevista de crédito se rejeitado
- Entrevista de crédito completa exigindo 5 dados
- Recalcular score e permitir definir novo limite
- Cotação de câmbio (pede moedas se necessário)
- Encerrar atendimento de forma amigável
- Lidar com erros das tools de forma clara e educativa

---

## 🧩 Desafios Enfrentados

- **Tornar o fluxo determinístico com LangGraph**  
  O LangGraph exige rotas claras entre os nós, mas o comportamento do LLM é dinâmico.  
  Foi difícil garantir previsibilidade 100% só via grafo. 

  **Solução atual:**  
  Centralizei a maior parte da lógica no prompt, planeando migrar para um fluxo mais determinístico no futuro.

- Manter validação de dados (CPF, datas etc.) robusta
- Garantir que o LLM só chame tools nos momentos corretos
- Controlar limites de tentativas sem perder o estado
- Organizar o loop `llm → tool → llm` sem criar loops infinitos

---

## 🔧 Escolhas Técnicas & Justificativas

### **LangGraph**
Permite criar fluxos determinísticos e separar:
- processamento do LLM
- execução de ferramentas
- controle do estado

Mesmo que ainda haja lógica no prompt, o grafo já torna o sistema mais robusto.

### **CSV como "banco de dados"**
Para um protótipo/junior backend, CSV é simples e rápido para testar lógica.

Futuramente: PostgreSQL ou SQLite.

### **LangChain + LLM com tools**
- Facilita chamar funções reais diretamente  
- Boa integração para protótipos e automações  

### **Prompt Engineering forte**
Controla o fluxo enquanto o grafo ainda está simples.

---

## ▶ Tutorial de Execução

## 🚀 Instalação do Ollama e configuração do modelo gpt-oss:20b (Windows)

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