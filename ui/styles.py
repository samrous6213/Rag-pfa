"""
styles.py - Styles CSS personnalisés pour Streamlit
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    color: #18181b;
    background-color: #fafafa;
}

.main {
    padding: 0rem 1rem;
}

.block-container {
    /* padding-top: 2rem; */
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* ===== HEADER ===== */
.main-header {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 24px;
    margin-bottom: 24px;
}
.main-header h1 {
    color: #18181b !important;
    margin: 0 0 6px 0;
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: -0.01em;
}
.main-header p {
    margin: 0;
    color: #71717a;
    font-size: 0.875rem;
    line-height: 1.5;
}

/* ===== MESSAGES ===== */
.chat-message {
    padding: 16px 20px;
    border-radius: 6px;
    margin: 16px 0;
    font-size: 0.925rem;
    line-height: 1.6;
    animation: fadeIn 0.2s ease forwards;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

.user-message {
    background-color: #18181b;
    color: #ffffff;
    margin-left: 20%;
    border-radius: 6px 6px 0 6px;
}
.user-message .message-author {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #a1a1aa;
    display: block;
    margin-bottom: 4px;
}
.user-message .message-body { color: #ffffff; }

.assistant-message {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #e4e4e7;
    border-left: 3px solid #18181b;
    margin-right: 20%;
    border-radius: 6px 6px 6px 0;
}
.assistant-message .message-author {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #71717a;
    display: block;
    margin-bottom: 4px;
    font-weight: 600;
}

/* ===== SOURCES ===== */
.source-card {
    background: #fafafa;
    border: 1px solid #e4e4e7;
    border-radius: 4px;
    padding: 12px 14px;
    margin: 10px 0;
    font-size: 0.775rem;
}
.source-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.source-name { font-weight: 600; color: #18181b; }
.source-score {
    background: #d1fae5;
    color: #065f46;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
}
.source-score.low { background: #fef3c7; color: #92400e; }
.source-details { color: #71717a; margin-bottom: 6px; font-size: 0.725rem; }
.source-text { color: #71717a; font-style: italic; line-height: 1.4; }

/* ===== CONFIANCE ===== */
.confidence-bar {
    margin-top: 12px;
    font-size: 0.8rem;
    color: #71717a;
}
.confidence-fill {
    height: 4px;
    background: #f4f4f5;
    border-radius: 2px;
    overflow: hidden;
    margin-top: 6px;
    width: 100%;
}
.confidence-fill > div { height: 100%; border-radius: 2px; transition: width 0.4s; }
.confidence-high > div { background: #10b981; }
.confidence-medium > div { background: #f59e0b; }
.confidence-low > div { background: #ef4444; }

.message-meta {
    font-size: 0.725rem;
    color: #71717a;
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px dashed #e4e4e7;
}

/* ===== BOUTONS ===== */
.stButton > button {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 8px 16px;
    transition: all 0.2s ease;
    box-shadow: none;
    width: 100%;
}
.stButton > button:hover {
    border-color: #18181b;
    background-color: #f4f4f5;
    transform: translateY(-1px);
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e4e4e7;
}

[data-testid="stSidebar"] h2 {
    font-size: 0.85rem;
    margin-top: 20px;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    color: #71717a;
}

[data-testid="stSidebar"] h3 {
    font-size: 0.8rem;
    margin-top: 14px;
    margin-bottom: 8px;
}

[data-testid="stSidebar"] label {
    font-size: 0.78rem !important;
    color: #52525b;
}

[data-testid="stSidebar"] .stButton > button {
    font-size: 0.78rem;
    padding: 6px 12px;
}

[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    font-size: 0.72rem;
    color: #71717a;
}
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    font-size: 1.1rem;
    font-weight: 600;
}

[data-testid="stSidebar"] [data-testid="stAlert"] {
    font-size: 0.78rem;
    padding: 8px 10px;
}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li {
    font-size: 0.78rem;
    line-height: 1.5;
    color: #52525b;
}

[data-testid="stSidebar"] hr {
    margin: 12px 0;
    border-color: #e4e4e7;
}

/* Compenser la hauteur du chat input fixé en bas */
.block-container {
    padding-bottom: 8rem !important;
}

/* Sécuriser l'espace sous le dernier message */
.stChatInputContainer,
[data-testid="stChatInput"] {
    background-color: #fafafa;
}

/* Espace supplémentaire après le dernier expander de sources */
.main .block-container > div:last-child {
    margin-bottom: 4rem;
}

/* ===== SIDEBAR — ESPACEMENT HAUT RÉDUIT ===== */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 0.5rem;
}

/* Réduire l'espace au-dessus du premier titre */
[data-testid="stSidebar"] .stMarkdown:first-child h2 {
    margin-top: 0;
}

/* Réduire l'espace des blocs stMarkdown en général */
[data-testid="stSidebar"] .stMarkdown {
    margin-bottom: 0;
}

/* Réduire l'espace des éléments natifs (sliders, boutons, etc.) */
[data-testid="stSidebar"] .element-container {
    margin-bottom: 0.5rem;
}

/* Réduire l'espace vertical du bloc de sliders */
[data-testid="stSidebar"] [data-testid="stSlider"] {
    padding-top: 0;
    padding-bottom: 0;
}

/* ===== SIDEBAR — ESPACEMENT BAS RÉDUIT ===== */
[data-testid="stSidebar"] > div:first-child {
    padding-bottom: 1rem;
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-bottom: 0.5rem;
}

/* Réduire l'espace du dernier élément de la sidebar */
[data-testid="stSidebar"] .stMarkdown:last-child {
    margin-bottom: 0;
}

[data-testid="stSidebar"] .element-container:last-child {
    margin-bottom: 0;
}
</style>
"""