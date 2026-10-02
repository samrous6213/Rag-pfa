"""
Styles CSS personnalisés pour Streamlit (Style chic, minimaliste, neutre et professionnel)
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    color: #18181b;
    background-color: #fafafa;
}

/* Forcer l'application à occuper toute la hauteur et pousser le footer en bas */
.stApp {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.main { 
    padding: 0rem 1rem; 
    flex: 1;
}

.block-container { 
    padding-top: 6rem; 
    padding-bottom: 6rem; /* Espace réservé pour le footer en bas */
    max-width: 1100px; 
}

/* En-tête principal épuré */
.main-header {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 24px;
    margin-bottom: 32px;
    box-shadow: none;
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

/* Accueil et suggestions */
.welcome-container {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 24px;
    margin-bottom: 24px;
}
.welcome-container h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 8px;
    color: #18181b;
}
.welcome-container p {
    color: #71717a;
    font-size: 0.875rem;
    margin-bottom: 0;
}

/* Bulles de chat avec espacement adéquat */
.chat-message {
    padding: 16px 20px;
    border-radius: 6px;
    margin: 32px 0 16px 0; /* Espacement supérieur accru pour éviter le chevauchement */
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
.user-message .message-body {
    color: #ffffff;
}

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

/* Cartes de sources */
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
.source-name { 
    font-weight: 600; 
    color: #18181b; 
}
.source-score {
    background: #d1fae5;
    color: #065f46;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
}
.source-score.low { 
    background: #fef3c7; 
    color: #92400e; 
}
.source-details {
    color: #71717a;
    margin-bottom: 6px;
    font-size: 0.725rem;
}
.source-text { 
    color: #71717a; 
    font-style: italic; 
    line-height: 1.4; 
}

/* Barre de confiance */
.confidence-bar { 
    margin-top: 14px; 
    padding-top: 12px; 
    border-top: 1px solid #e4e4e7; 
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

/* Boutons et éléments de formulaire */
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

[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e4e4e7;
}

[data-testid="stSidebar"] h2 {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    color: #71717a;
    margin-top: 16px;
    margin-bottom: 8px;
}

/* Footer fixé élégamment en bas */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #fafafa;
    text-align: center;
    padding: 12px 0;
    color: #71717a;
    font-size: 0.75rem;
    border-top: 1px solid #e4e4e7;
    z-index: 999;
}
</style>
"""