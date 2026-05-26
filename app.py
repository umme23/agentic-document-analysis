import streamlit as st
import PyPDF2
import io
import re
import time
from datetime import datetime
from collections import Counter

st.set_page_config(
    page_title="Agentic Document Analysis System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLES ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background: #f8fafc !important;
    color: #1e293b !important;
}
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
h1 { color: #1e293b; font-weight: 700; }
h2, h3 { color: #334155; font-weight: 600; }

.main-title {
    font-size: 2.2rem; font-weight: 700; color: #1e293b;
    margin-bottom: 4px;
}
.sub-title {
    color: #64748b; font-size: 1rem; margin-bottom: 28px;
}
.card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 22px 26px; margin-bottom: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.section-label {
    font-size: .75rem; font-weight: 700; color: #7c3aed;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;
}
.summary-box {
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 10px; padding: 16px 20px;
    color: #166534; font-size: .95rem; line-height: 1.7;
}
.insight-box {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 16px 20px;
    color: #1e40af; font-size: .9rem; line-height: 1.7; margin-top: 12px;
}
.warn-box {
    background: #fffbeb; border: 1px solid #fde68a;
    border-radius: 10px; padding: 14px 18px;
    color: #92400e; font-size: .88rem; margin-top: 10px;
}
.pill {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: .77rem; font-weight: 600; margin: 3px;
    background: #ede9fe; color: #5b21b6; border: 1px solid #c4b5fd;
}
.chat-wrap {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 16px;
    max-height: 420px; overflow-y: auto; margin: 12px 0;
}
.bubble-user {
    background: #7c3aed; color: white; padding: 10px 15px;
    border-radius: 18px 18px 4px 18px; max-width: 75%;
    font-size: .88rem; line-height: 1.55; display: inline-block;
}
.bubble-bot {
    background: #ffffff; border: 1px solid #e2e8f0; color: #1e293b;
    padding: 10px 15px; border-radius: 18px 18px 18px 4px;
    max-width: 75%; font-size: .88rem; line-height: 1.55; display: inline-block;
}
.msg-user { text-align: right; margin: 8px 0; }
.msg-bot  { text-align: left;  margin: 8px 0; }
.stat-box {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 14px 18px; text-align: center;
}
.stat-num { font-size: 1.6rem; font-weight: 700; color: #7c3aed; }
.stat-lbl { font-size: .75rem; color: #64748b; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ────────────────────────────────────────
if "doc_text"     not in st.session_state: st.session_state.doc_text = ""
if "chat"         not in st.session_state: st.session_state.chat = []
if "stored_docs"  not in st.session_state: st.session_state.stored_docs = {}
if "summary"      not in st.session_state: st.session_state.summary = ""
if "insights"     not in st.session_state: st.session_state.insights = ""

# ── HELPERS ──────────────────────────────────────────────
STOPWORDS = set([
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","being","have","has","had","do",
    "does","did","will","would","could","should","may","might","shall",
    "this","that","these","those","it","its","i","we","you","he","she",
    "they","their","our","your","his","her","what","which","who","how",
    "when","where","why","from","by","as","not","no","so","if","then",
    "than","more","also","just","been","into","up","out","about","can",
])

def extract_pdf_text(file) -> str:
    reader = PyPDF2.PdfReader(file)
    return "\n".join(p.extract_text() or "" for p in reader.pages)

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def get_sentences(text: str):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 20]

def score_sentence(sent: str, word_freq: dict) -> float:
    words = re.findall(r'\b\w+\b', sent.lower())
    return sum(word_freq.get(w, 0) for w in words) / max(len(words), 1)

def extractive_summary(text: str, n: int = 6) -> str:
    sentences = get_sentences(text)
    if len(sentences) <= n:
        return " ".join(sentences)
    words = re.findall(r'\b\w+\b', text.lower())
    freq = {w: c for w, c in Counter(words).items() if w not in STOPWORDS and len(w) > 2}
    scored = sorted(sentences, key=lambda s: score_sentence(s, freq), reverse=True)
    top = sorted(scored[:n], key=lambda s: sentences.index(s))
    return " ".join(top)

def bullet_summary(text: str, n: int = 6) -> str:
    sentences = get_sentences(text)
    if not sentences:
        return "• No content found."
    words = re.findall(r'\b\w+\b', text.lower())
    freq = {w: c for w, c in Counter(words).items() if w not in STOPWORDS and len(w) > 2}
    scored = sorted(sentences, key=lambda s: score_sentence(s, freq), reverse=True)
    return "\n".join(f"• {s}" for s in scored[:n])

def get_insights(text: str) -> str:
    words = re.findall(r'\b\w+\b', text.lower())
    total_words = len(words)
    sentences = get_sentences(text)
    avg_sent_len = total_words / max(len(sentences), 1)
    freq = Counter(w for w in words if w not in STOPWORDS and len(w) > 3)
    top_keywords = [w for w, _ in freq.most_common(8)]
    read_time = max(1, round(total_words / 200))
    lines = [
        f"📊 **Document Stats:** {total_words:,} words · {len(sentences)} sentences · ~{read_time} min read",
        f"🔑 **Key Topics Detected:** {', '.join(top_keywords)}",
        f"📝 **Avg Sentence Length:** {avg_sent_len:.0f} words",
    ]
    if total_words < 100:
        lines.append("⚠️ Document is very short — summary may not be meaningful.")
    elif total_words > 2000:
        lines.append("📚 Long document detected — summary captures the most important sentences.")
    return "\n\n".join(lines)

def translate_simple(text: str, lang: str) -> str:
    notes = {
        "Hindi":   "**[Hindi translation]** Translation requires an external API. Showing original:\n\n",
        "French":  "**[French translation]** Translation requires an external API. Showing original:\n\n",
        "Spanish": "**[Spanish translation]** Translation requires an external API. Showing original:\n\n",
        "Arabic":  "**[Arabic translation]** Translation requires an external API. Showing original:\n\n",
        "German":  "**[German translation]** Translation requires an external API. Showing original:\n\n",
    }
    return notes.get(lang, "") + text

def chatbot_reply(question: str, doc_text: str) -> str:
    q = question.lower()
    if not doc_text.strip():
        return "Please load a document first using the sidebar, then I can answer questions about it!"
    words = re.findall(r'\b\w+\b', doc_text.lower())
    freq = Counter(w for w in words if w not in STOPWORDS and len(w) > 3)
    top_kw = [w for w, _ in freq.most_common(5)]
    sentences = get_sentences(doc_text)
    total_words = len(words)

    if any(x in q for x in ["summarize","summary","brief","overview","short"]):
        return "Here's a quick summary:\n\n" + bullet_summary(doc_text, 5)
    elif any(x in q for x in ["keyword","topic","about","main","key"]):
        return f"The main topics in this document are:\n\n" + "\n".join(f"• **{k}**" for k in top_kw)
    elif any(x in q for x in ["how long","word count","length","size"]):
        return f"The document has **{total_words:,} words** across **{len(sentences)} sentences**. Estimated read time: ~{max(1,round(total_words/200))} minutes."
    elif any(x in q for x in ["insight","analys","important","key finding"]):
        return get_insights(doc_text)
    elif any(x in q for x in ["first","beginning","start","introduction"]):
        return "Here's the opening of the document:\n\n" + " ".join(sentences[:3])
    elif any(x in q for x in ["last","end","conclusion","final"]):
        return "Here's the ending of the document:\n\n" + " ".join(sentences[-3:])
    else:
        # keyword search
        relevant = [s for s in sentences if any(w in s.lower() for w in q.split() if len(w) > 3)]
        if relevant:
            return "Here's what I found related to your question:\n\n" + "\n\n".join(f"• {s}" for s in relevant[:4])
        return f"I couldn't find a specific answer to that in the document. The document mainly covers: **{', '.join(top_kw)}**. Try asking about one of these topics!"

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings & Documents")
    st.markdown("---")

    input_method = st.radio("Choose input method", ["Text Input", "PDF Upload", "Stored Documents"])

    st.markdown("---")
    st.markdown("**Select output language**")
    language = st.selectbox("", ["English", "Hindi", "French", "Spanish", "Arabic", "German"])

    st.markdown("**Summarization approach**")
    approach = st.selectbox(" ", ["abstractive (extractive)", "bullet points"])

    st.markdown("**Summary length**")
    num_sentences = st.slider("Sentences", min_value=3, max_value=12, value=6)

    st.markdown("---")
    st.markdown("### 📋 Task Specification")
    task = st.text_area("Describe your task in natural language",
                        value="Summarize the document and extract key information.",
                        height=100)

    st.markdown("---")
    if st.session_state.stored_docs:
        st.markdown(f"**Stored Documents ({len(st.session_state.stored_docs)})**")
        for name in st.session_state.stored_docs:
            st.markdown(f"📄 {name}")

# ── MAIN ─────────────────────────────────────────────────
st.markdown('<div class="main-title">📄 Agentic Document Analysis System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Summarize · Analyze · Ask — powered by NLP</div>', unsafe_allow_html=True)

# ── INPUT ─────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)

if input_method == "Text Input":
    st.markdown('<div class="section-label">Enter Your Text</div>', unsafe_allow_html=True)
    text_input = st.text_area("Paste or type your text here", height=200,
                               value=st.session_state.doc_text,
                               placeholder="Paste any article, report, research paper, or document here...")
    if text_input:
        st.session_state.doc_text = text_input

elif input_method == "PDF Upload":
    st.markdown('<div class="section-label">Upload PDF</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded:
        with st.spinner("Extracting text from PDF..."):
            st.session_state.doc_text = clean_text(extract_pdf_text(uploaded))
        st.success(f"✅ Extracted {len(st.session_state.doc_text.split())} words from PDF")
        save_name = uploaded.name
        st.session_state.stored_docs[save_name] = st.session_state.doc_text

elif input_method == "Stored Documents":
    st.markdown('<div class="section-label">Stored Documents</div>', unsafe_allow_html=True)
    if st.session_state.stored_docs:
        chosen = st.selectbox("Select a stored document", list(st.session_state.stored_docs.keys()))
        if chosen:
            st.session_state.doc_text = st.session_state.stored_docs[chosen]
            st.success(f"✅ Loaded: {chosen}")
    else:
        st.info("No stored documents yet. Upload a PDF to save it automatically.")

doc = st.session_state.doc_text
st.markdown('</div>', unsafe_allow_html=True)

# ── STATS ROW ─────────────────────────────────────────────
if doc.strip():
    words = re.findall(r'\b\w+\b', doc)
    sents = get_sentences(doc)
    read_time = max(1, round(len(words) / 200))
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(words):,}</div><div class="stat-lbl">Words</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(sents)}</div><div class="stat-lbl">Sentences</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(set(w.lower() for w in words))}</div><div class="stat-lbl">Unique Words</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{read_time} min</div><div class="stat-lbl">Read Time</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── ACTION BUTTONS ────────────────────────────────────────
col1, col2 = st.columns(2)
process_clicked = col1.button("🚀 Process Document", use_container_width=True, type="primary")
analyze_clicked  = col2.button("🔍 Analyze Document Visually", use_container_width=True)

if process_clicked:
    if not doc.strip():
        st.warning("Please enter or upload a document first.")
    else:
        with st.spinner("Processing..."):
            time.sleep(0.5)
            if "bullet" in approach:
                result = bullet_summary(doc, num_sentences)
            else:
                result = extractive_summary(doc, num_sentences)
            if language != "English":
                result = translate_simple(result, language)
            st.session_state.summary  = result
            st.session_state.insights = get_insights(doc)

if st.session_state.summary:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">📝 Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="summary-box">{st.session_state.summary.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)
    st.download_button("⬇️ Download Summary", st.session_state.summary,
                       file_name="summary.txt", mime="text/plain", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if analyze_clicked or st.session_state.insights:
    if not doc.strip():
        st.warning("Please enter or upload a document first.")
    else:
        if analyze_clicked:
            st.session_state.insights = get_insights(doc)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🔍 Visual Analysis</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-box">{st.session_state.insights}</div>', unsafe_allow_html=True)

        # keyword pills
        all_words = re.findall(r'\b\w+\b', doc.lower())
        freq = Counter(w for w in all_words if w not in STOPWORDS and len(w) > 3)
        top = freq.most_common(15)
        if top:
            st.markdown("<br>**Top Keywords:**", unsafe_allow_html=True)
            pills = " ".join(f'<span class="pill">{w} ({c})</span>' for w, c in top)
            st.markdown(pills, unsafe_allow_html=True)

        # bar chart
        if top:
            import plotly.graph_objects as go
            words_chart = [w for w, _ in top[:10]]
            counts_chart = [c for _, c in top[:10]]
            fig = go.Figure(go.Bar(
                x=counts_chart, y=words_chart, orientation='h',
                marker_color='#7c3aed', text=counts_chart, textposition='outside'
            ))
            fig.update_layout(
                title="Top 10 Keywords",
                xaxis_title="Frequency", yaxis_title="",
                plot_bgcolor='#f8fafc', paper_bgcolor='#f8fafc',
                font=dict(family="Inter", size=12),
                margin=dict(l=20, r=20, t=40, b=20),
                height=320,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── CHATBOT ──────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">💬 Ask Me Anything</div>', unsafe_allow_html=True)
st.caption("Ask questions about your document — 'What is this about?', 'Summarize it', 'What are the key topics?'")

quick_btns = [
    ("📝 Summarize", "Summarize the document"),
    ("🔑 Key Topics", "What are the main topics?"),
    ("📊 Word Count", "How long is this document?"),
    ("💡 Insights",   "Give me key insights"),
    ("🏁 Conclusion", "What is the conclusion?"),
    ("🔍 Introduction","What is the introduction?"),
]
quick = None
cols = st.columns(3)
for i, (label, q) in enumerate(quick_btns):
    if cols[i % 3].button(label, key=f"qb{i}", use_container_width=True):
        quick = q

st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
if not st.session_state.chat:
    st.markdown('<p style="text-align:center;color:#94a3b8;padding:20px 0;font-size:.85rem">👋 Load a document and ask me anything about it!</p>', unsafe_allow_html=True)
for sender, msg in st.session_state.chat:
    if sender == "user":
        st.markdown(f'<div class="msg-user"><div class="bubble-user">{msg}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-bot"><div class="bubble-bot">{msg.replace(chr(10),"<br>")}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

user_input = st.chat_input("Type your question about the document...")
final_input = quick or user_input

if final_input:
    reply = chatbot_reply(final_input, doc)
    st.session_state.chat.append(("user", final_input))
    st.session_state.chat.append(("bot", reply))
    st.rerun()

if st.session_state.chat:
    if st.button("🗑 Clear chat", use_container_width=False):
        st.session_state.chat = []
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Agentic Document Analysis System · Built by Umme Kulsum · 2025")
