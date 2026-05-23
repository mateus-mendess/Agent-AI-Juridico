# ⚖️ Legal Assistant — Assistente Jurídico via Telegram

Assistente jurídico inteligente que opera via Telegram, utilizando IA para auxiliar advogados e escritórios de advocacia com tarefas do dia a dia.

---

## 🎯 Objetivo

Facilitar o trabalho de advogados e escritórios de advocacia através de um assistente de IA acessível diretamente pelo Telegram, eliminando a necessidade de sistemas complexos ou interfaces web.

---

## 🔍 Problema que Resolve

Advogados frequentemente precisam:
- Resumir documentos jurídicos extensos rapidamente
- Gerar documentos padronizados (procurações, contratos, termos)
- Tirar dúvidas jurídicas de forma ágil

Essas tarefas consomem tempo e exigem atenção a detalhes. O Legal Assistant automatiza essas atividades com IA, diretamente pelo Telegram — sem instalar nada, sem acessar sistemas externos.

---

## ✨ Funcionalidades

### 💬 ChatBot Jurídico
Responde perguntas sobre direito **civil**, **criminal** e **trabalhista** brasileiro com fundamento legal, citando artigos e jurisprudência quando relevante. Recusa automaticamente perguntas fora do escopo jurídico.

### 📄 Resumo de Documentos
O usuário envia um arquivo **PDF** ou **Word (.docx/.doc)** e recebe um resumo jurídico conciso com:
- Tipo do documento
- Partes envolvidas
- Objeto principal
- Pontos de atenção relevantes

### 📝 Geração de Documentos
Gera documentos jurídicos personalizados em formato **Word (.docx)** a partir de um formulário interativo no próprio chat:
- **Procuração** (cível ou criminal)
- **Termo de Declaração de Inaptidão Provisória**
- **Contrato de Honorários Advocatícios**

---

## 🏗️ Como Funciona

```
[Usuário no Telegram]
        ↓
[Bot Python — python-telegram-bot]
        ↓
[OpenRouter API]
        ↓
[LLM — Llama 3.3 70B (Meta)]
```

1. O usuário interage com o bot pelo Telegram
2. O bot identifica a intenção (chat, resumo ou geração de documento)
3. A requisição é enviada ao modelo de linguagem via OpenRouter
4. O resultado é retornado ao usuário no Telegram — como mensagem de texto ou arquivo `.docx`

---

## 🛠️ Stack Tecnológica

| Tecnologia | Função |
|---|---|
| **Python 3.11** | Linguagem principal |
| **python-telegram-bot** | Integração com a API do Telegram |
| **OpenRouter** | Gateway de acesso a modelos de IA |
| **Llama 3.3 70B (Meta)** | Modelo de linguagem principal |
| **Docker** | Containerização e isolamento da aplicação |
| **python-docx** | Geração de documentos Word |
| **PyPDF2** | Extração de texto de arquivos PDF |

---

## 🚀 Como Executar

### Pré-requisitos
- Docker Desktop instalado
- Conta no [Telegram](https://telegram.org/) com um bot criado via [@BotFather](https://t.me/BotFather)
- Chave de API do [OpenRouter](https://openrouter.ai/)

---

## 🔒 Segurança

- Todas as chaves de API ficam em variáveis de ambiente no arquivo `.env`
- O `.env` está listado no `.gitignore` e nunca é versionado
- A aplicação roda isolada em container Docker

---

## ⚠️ Aviso Legal

Este assistente é uma ferramenta de apoio e **não substitui a consulta com um advogado habilitado**. Todos os documentos gerados devem ser revisados por um profissional antes de serem utilizados.

---
