# 📄 Agentic Document Analysis System

An intelligent document processing web app that summarizes, analyzes, 
and answers questions about any document — powered by NLP.

🔗 **Live Demo:** [agentic-docs-umme.streamlit.app](https://agentic-docs-umme.streamlit.app)

---

## ✨ Features

- 📝 **Smart Summarization** — Extractive and abstractive approaches
- 📄 **PDF Upload** — Extract and analyze any PDF instantly
- 🌍 **Multilingual Output** — English, Hindi, French, Spanish, Arabic, German
- 📊 **Visual Analysis** — Keyword frequency charts and document stats
- 💬 **Ask Me Anything** — Built-in chatbot to Q&A your document
- 💾 **Stored Documents** — Save and reload documents across sessions
- ⬇️ **Download Summary** — Export your summary as a text file

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Frontend | Streamlit |
| NLP | Python, NLTK, Regex |
| Visualization | Plotly |
| PDF Processing | PyPDF2 |
| Deployment | Streamlit Cloud |

---

## 🚀 Run Locally

```bash
git clone https://github.com/umme23/agentic-document-analysis
cd agentic-document-analysis
pip install -r requirements.txt
streamlit run app.py
