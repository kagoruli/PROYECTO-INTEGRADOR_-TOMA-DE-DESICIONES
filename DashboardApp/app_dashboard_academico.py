import sqlite3
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go



DB_PATH = Path("SistemaEscolar.db")
RIESGO_CALIFICACION = 70
BAJO_DESEMPENO = 80

st.set_page_config(
    page_title="Sistema Académico - Toma de Decisiones",
    page_icon="📊",
    layout="wide",
)


st.markdown(
    """
    <style>
    .main { background-color: #f8fafc; }
    .block-container { padding-top: 1.4rem; }
    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 8px 18px rgba(15, 23, 42, .06);
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #60a5fa;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    /* ── KPI cards ── */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        margin: 10px 0 18px 0;
    }
    .kpi-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 20px 14px;
        border-top: 4px solid #3b82f6;
        box-shadow: 0 4px 14px rgba(15, 23, 42, .06);
    }
    .kpi-box.verde { border-top-color: #22c55e; }
    .kpi-box.rojo  { border-top-color: #ef4444; }
    .kpi-label {
        font-size: 0.71rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 7px;
    }
    .kpi-num {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1;
    }
    .kpi-sub {
        font-size: 0.71rem;
        color: #94a3b8;
        margin-top: 5px;
    }

    /* ── Info strip (mejor/peor materia) ── */
    .info-strip {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        margin-bottom: 18px;
    }
    .info-strip-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 13px 18px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, .04);
    }
    .info-strip-card.verde { border-left: 5px solid #22c55e; }
    .info-strip-card.ambar { border-left: 5px solid #f59e0b; }
    .info-strip-label {
        font-size: 0.69rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }
    .info-strip-value {
        font-size: 0.97rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 2px;
    }

    /* ── Reporte final ── */
    .rpt-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(15,23,42,0.08);
        margin-bottom: 18px;
    }
    .rpt-header {
        background: #0f172a;
        color: white;
        padding: 26px 30px 22px;
    }
    .rpt-header-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .rpt-header-title {
        font-size: 1.2rem;
        font-weight: 800;
        margin-bottom: 4px;
        letter-spacing: -0.2px;
    }
    .rpt-header-sub { font-size: 0.78rem; opacity: 0.5; }
    .rpt-header-badge {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        white-space: nowrap;
    }
    .rpt-metrics {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        background: #1e293b;
        border-top: 1px solid rgba(255,255,255,0.08);
    }
    .rpt-metric {
        padding: 14px 20px;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    .rpt-metric:last-child { border-right: none; }
    .rpt-metric-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: rgba(255,255,255,0.45);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 4px;
    }
    .rpt-metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        color: white;
        line-height: 1;
    }
    .rpt-body { padding: 24px 28px; }

    .rpt-section {
        margin-bottom: 6px;
    }
    .rpt-section:last-child { margin-bottom: 0; }
    .rpt-section-title {
        font-size: 1.08rem;
        font-weight: 700;
        letter-spacing: 0.01em;
        color: #0f172a;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1px solid #f1f5f9;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .rpt-section-title span { color: #0f172a; }
    .rpt-item {
        font-size: 0.875rem;
        color: #374151;
        padding: 7px 0;
        border-bottom: 1px solid #f8fafc;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        line-height: 1.5;
    }
    .rpt-item:last-child { border-bottom: none; padding-bottom: 0; }
    .rpt-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: #3b82f6; margin-top: 6px; flex-shrink: 0;
    }
    .rpt-dot.rojo  { background: #ef4444; }
    .rpt-dot.verde { background: #22c55e; }
    .rpt-dot.ambar { background: #f59e0b; }
    .rpt-sub-item {
        font-size: 0.82rem;
        color: #6b7280;
        padding: 3px 0 3px 18px;
        display: flex;
        gap: 8px;
    }
    .rpt-divider {
        border: none;
        border-top: 1px solid #f1f5f9;
        margin: 6px 0;
    }
    .rpt-footer {
        background: #f8fafc;
        border-top: 1px solid #e2e8f0;
        padding: 14px 28px;
        font-size: 0.75rem;
        color: #94a3b8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* ── Modo oscuro — activado por JS cuando Streamlit está en Dark/System dark ── */
    body.st-dark .kpi-box                { background: #1e293b !important; border-color: #334155 !important; }
    body.st-dark .kpi-label              { color: #94a3b8 !important; }
    body.st-dark .kpi-num                { color: #f1f5f9 !important; }
    body.st-dark .kpi-sub                { color: #64748b !important; }
    body.st-dark .info-strip-card        { background: #1e293b !important; border-color: #334155 !important; }
    body.st-dark .info-strip-label       { color: #94a3b8 !important; }
    body.st-dark .info-strip-value       { color: #f1f5f9 !important; }
    body.st-dark .rpt-card               { border-color: #334155 !important; box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important; }
    body.st-dark .rpt-body               { background: #1e293b !important; }
    body.st-dark .rpt-section-title      { color: #f1f5f9 !important; border-bottom-color: #334155 !important; }
    body.st-dark .rpt-section-title span { color: #f1f5f9 !important; }
    body.st-dark .rpt-item               { color: #cbd5e1 !important; border-bottom-color: #263348 !important; }
    body.st-dark .rpt-sub-item           { color: #94a3b8 !important; }
    body.st-dark .rpt-divider            { border-top-color: #334155 !important; }
    body.st-dark .rpt-footer             { background: #0f172a !important; border-top-color: #334155 !important; color: #475569 !important; }

    /* ── Botones de descarga ── */
    .stDownloadButton > button {
        background-color: #0f172a !important;
        color: white !important;
        border: none !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1.4rem !important;
        width: 100% !important;
        transition: background-color 0.15s !important;
    }
    .stDownloadButton > button:hover {
        background-color: #1e3a5f !important;
    }

    /* ── Sidebar mejorado ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    }
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    }

    /* Títulos del sidebar */
    [data-testid="stSidebar"] h3 {
        color: #1e293b;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 8px 0;
        border-bottom: 2px solid #3b82f6;
        margin-bottom: 16px;
    }

    /* Selectbox del sidebar */
    [data-testid="stSidebar"] .stSelectbox label {
        color: #475569;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* Checkbox del sidebar */
    [data-testid="stSidebar"] .stCheckbox label {
        color: #475569;
        font-weight: 500;
        font-size: 0.9rem;
    }

    /* Botón de limpiar filtros */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.2s !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #2563eb !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }

    /* Divisores en sidebar */
    [data-testid="stSidebar"] hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid #e2e8f0;
    }

    /* File uploader en sidebar */
    [data-testid="stSidebar"] .stFileUploader {
        background: white;
        border: 2px dashed #cbd5e1;
        border-radius: 8px;
        padding: 1rem;
        transition: all 0.2s;
    }
    [data-testid="stSidebar"] .stFileUploader:hover {
        border-color: #3b82f6;
        background: #f1f5f9;
    }

    /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       BOTONES DE EXPANDIR/COLAPSAR EN SIDEBAR - ULTRA VISIBLES
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

    /* Animaciones */
    @keyframes superGlow {
        0%, 100% {
            background: linear-gradient(135deg, #ff4500 0%, #ff6347 50%, #ff8c00 100%);
            box-shadow: 0 0 30px #ff4500, 0 0 50px #ff4500, 0 0 70px #ff4500;
            transform: scale(1);
        }
        50% {
            background: linear-gradient(135deg, #ff6347 0%, #ff8c00 50%, #ffa500 100%);
            box-shadow: 0 0 40px #ff4500, 0 0 70px #ff4500, 0 0 100px #ff4500;
            transform: scale(1.05);
        }
    }

    @keyframes arrowBounce {
        0%, 100% { transform: translateX(0); }
        50% { transform: translateX(8px); }
    }

    /* Contenedor del expander cuando está colapsado */
    [data-testid="stSidebar"] details[open="false"],
    [data-testid="stSidebar"] details:not([open]) {
        border: 5px solid #ff4500 !important;
        border-radius: 16px !important;
        background: linear-gradient(135deg, #ffe5e0 0%, #fff5f0 100%) !important;
        padding: 4px !important;
        margin: 16px 0 !important;
        box-shadow: 0 0 30px rgba(255, 69, 0, 0.6) !important;
    }

    /* Header/summary del expander (el botón clickeable) */
    [data-testid="stSidebar"] summary,
    [data-testid="stSidebar"] .streamlit-expanderHeader,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary,
    [data-testid="stSidebar"] [data-testid="stExpanderHeader"],
    [data-testid="stSidebar"] button[kind="header"] {
        background: linear-gradient(135deg, #ff4500 0%, #ff6347 50%, #ff8c00 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 24px 20px !important;
        box-shadow: 0 0 30px #ff4500, 0 0 50px #ff4500, 0 8px 25px rgba(255, 69, 0, 0.5) !important;
        border: 4px solid #ffffff !important;
        font-weight: 900 !important;
        font-size: 1.1rem !important;
        min-height: 80px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        animation: superGlow 2s infinite !important;
    }

    [data-testid="stSidebar"] summary:hover,
    [data-testid="stSidebar"] .streamlit-expanderHeader:hover,
    [data-testid="stSidebar"] button[kind="header"]:hover {
        background: linear-gradient(135deg, #ff6347 0%, #ff8c00 50%, #ffa500 100%) !important;
        box-shadow: 0 0 40px #ff4500, 0 0 70px #ff4500, 0 12px 35px rgba(255, 69, 0, 0.7) !important;
        transform: scale(1.08) !important;
    }

    /* Iconos del expander (flechas >>) */
    [data-testid="stSidebar"] summary svg,
    [data-testid="stSidebar"] .streamlit-expanderHeader svg,
    [data-testid="stSidebar"] button[kind="header"] svg {
        width: 50px !important;
        height: 50px !important;
        color: white !important;
        filter: drop-shadow(0 4px 10px rgba(0,0,0,0.6)) !important;
        animation: arrowBounce 1s infinite !important;
    }

    /* Texto adicional en el header del expander */
    [data-testid="stSidebar"] summary::before,
    [data-testid="stSidebar"] .streamlit-expanderHeader::before {
        content: "▶▶▶ " !important;
        font-size: 1.3rem !important;
        margin-right: 12px !important;
        animation: arrowBounce 1s infinite !important;
    }

    /* Mensaje cuando está colapsado */
    [data-testid="stSidebar"] details:not([open]) summary::after {
        content: " ◀ CLIC PARA ABRIR" !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        background: white !important;
        color: #ff4500 !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        margin-left: 12px !important;
        box-shadow: 0 3px 10px rgba(0,0,0,0.3) !important;
        animation: textPulse 1.5s infinite !important;
    }

    @keyframes textPulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.1); }
    }

    /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       TRADUCCIÓN DE MENÚS DE TABLAS AL ESPAÑOL
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

    /* Ocultar texto en inglés y mostrar español usando CSS */
    div[role="menuitem"], button[role="menuitem"] {
        position: relative !important;
    }

    /* Sort ascending */
    div[role="menuitem"]:has(span:first-child:only-child):first-child span:only-child {
        font-size: 0 !important;
    }
    div[role="menuitem"]:has(span:first-child:only-child):first-child::after {
        content: "Ordenar ascendente" !important;
        font-size: 14px !important;
    }

    /* Sort descending */
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(2) span:only-child {
        font-size: 0 !important;
    }
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(2)::after {
        content: "Ordenar descendente" !important;
        font-size: 14px !important;
    }

    /* Format */
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(3) span:only-child {
        font-size: 0 !important;
    }
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(3)::after {
        content: "Formato" !important;
        font-size: 14px !important;
    }

    /* Autosize */
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(4) span:only-child {
        font-size: 0 !important;
    }
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(4)::after {
        content: "Ajustar automáticamente" !important;
        font-size: 14px !important;
    }

    /* Pin column */
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(5) span:only-child {
        font-size: 0 !important;
    }
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(5)::after {
        content: "Fijar columna" !important;
        font-size: 14px !important;
    }

    /* Hide column */
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(6) span:only-child {
        font-size: 0 !important;
    }
    div[role="menuitem"]:has(span:first-child:only-child):nth-child(6)::after {
        content: "Ocultar columna" !important;
        font-size: 14px !important;
    }
    </style>

    <script>
    // Diccionario de traducciones
    const TRADUCCIONES = {
        'Sort ascending': 'Ordenar ascendente',
        'Sort descending': 'Ordenar descendente',
        'Format': 'Formato',
        'Autosize': 'Ajustar automáticamente',
        'Pin column': 'Fijar columna',
        'Unpin column': 'Desfijar columna',
        'Hide column': 'Ocultar columna',
        'Show column': 'Mostrar columna',
        'Search': 'Buscar'
    };

    // Función principal de traducción
    function traducirElemento(elemento) {
        if (!elemento) return false;

        // Obtener todo el texto del elemento
        const textoCompleto = elemento.textContent?.trim();

        // Verificar si necesita traducción
        if (textoCompleto && TRADUCCIONES[textoCompleto]) {
            // Buscar el span interno o usar el elemento directamente
            const spans = elemento.querySelectorAll('span');
            if (spans.length > 0) {
                spans.forEach(span => {
                    if (span.textContent.trim() === textoCompleto) {
                        span.textContent = TRADUCCIONES[textoCompleto];
                    }
                });
            } else {
                elemento.textContent = TRADUCCIONES[textoCompleto];
            }
            return true;
        }
        return false;
    }

    // Traducir todos los elementos de menú
    function traducirMenus() {
        // Buscar todos los posibles elementos de menú
        const selectores = [
            'div[role="menuitem"]',
            'button[role="menuitem"]',
            '[role="menuitem"] span',
            '.gdg-menu-item',
            '[class*="menu"] [role="menuitem"]'
        ];

        selectores.forEach(selector => {
            document.querySelectorAll(selector).forEach(elemento => {
                traducirElemento(elemento);
            });
        });

        // Traducir tooltips y atributos
        Object.keys(TRADUCCIONES).forEach(textoIngles => {
            document.querySelectorAll(`[title="${textoIngles}"]`).forEach(el => {
                el.setAttribute('title', TRADUCCIONES[textoIngles]);
            });
            document.querySelectorAll(`[aria-label="${textoIngles}"]`).forEach(el => {
                el.setAttribute('aria-label', TRADUCCIONES[textoIngles]);
            });
        });

        // Traducir inputs de búsqueda
        document.querySelectorAll('input[placeholder*="Search"], input[aria-label="Search"]').forEach(input => {
            input.setAttribute('placeholder', 'Buscar...');
            input.setAttribute('aria-label', 'Buscar');
        });
    }

    // Observador MutationObserver ultra-agresivo
    const observerConfig = {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
        attributeFilter: ['role', 'class']
    };

    const observer = new MutationObserver((mutations) => {
        traducirMenus();
    });

    // Iniciar observación
    observer.observe(document.body, observerConfig);

    // Ejecutar traducción continuamente (cada 50ms)
    setInterval(traducirMenus, 50);

    // Ejecutar inmediatamente
    traducirMenus();

    // También ejecutar cuando se hace clic (para capturar menús que se abren)
    document.addEventListener('click', () => {
        setTimeout(traducirMenus, 10);
        setTimeout(traducirMenus, 50);
        setTimeout(traducirMenus, 100);
    });
    </script>
    """,
    unsafe_allow_html=True,
)


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def crear_bd():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Carreras (
        id_carrera INTEGER PRIMARY KEY,
        carrera TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Materias (
        id_materia INTEGER PRIMARY KEY,
        materia TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Estudiantes (
        matricula INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        id_carrera INTEGER NOT NULL,
        FOREIGN KEY (id_carrera) REFERENCES Carreras(id_carrera)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Cursos (
        id_curso INTEGER PRIMARY KEY,
        id_materia INTEGER NOT NULL,
        periodo TEXT NOT NULL,
        grupo TEXT NOT NULL,
        FOREIGN KEY (id_materia) REFERENCES Materias(id_materia)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Calificaciones (
        matricula INTEGER NOT NULL,
        id_curso INTEGER NOT NULL,
        calificacion REAL CHECK (calificacion >= 0 AND calificacion <= 100),
        PRIMARY KEY (matricula, id_curso),
        FOREIGN KEY (matricula) REFERENCES Estudiantes(matricula),
        FOREIGN KEY (id_curso) REFERENCES Cursos(id_curso)
    );
    """)

    conn.commit()
    conn.close()


def limpiar_texto(df):
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def normalizar_columnas(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("á", "a", regex=False)
        .str.replace("é", "e", regex=False)
        .str.replace("í", "i", regex=False)
        .str.replace("ó", "o", regex=False)
        .str.replace("ú", "u", regex=False)
    )
    return df


def limpiar_tablas(tablas):
    limpias = {}

    for nombre, df in tablas.items():
        df = normalizar_columnas(df)
        df = limpiar_texto(df)
        df = df.drop_duplicates()
        limpias[nombre] = df

    if "Carreras" in limpias:
        limpias["Carreras"] = limpias["Carreras"].rename(columns={"id_carrera": "id_carrera", "carrera": "carrera"})
        limpias["Carreras"] = limpias["Carreras"].drop_duplicates(subset=["id_carrera"])

    if "Materias" in limpias:
        limpias["Materias"] = limpias["Materias"].rename(columns={"id_materia": "id_materia", "materia": "materia"})
        limpias["Materias"] = limpias["Materias"].drop_duplicates(subset=["id_materia"])

    if "Estudiantes" in limpias:
        limpias["Estudiantes"] = limpias["Estudiantes"].rename(
            columns={"matricula": "matricula", "nombre": "nombre", "apellido": "apellido", "id_carrera": "id_carrera"}
        )
        limpias["Estudiantes"] = limpias["Estudiantes"].drop_duplicates(subset=["matricula"])

    if "Cursos" in limpias:
        limpias["Cursos"] = limpias["Cursos"].rename(
            columns={"id_curso": "id_curso", "id_materia": "id_materia", "periodo": "periodo", "grupo": "grupo"}
        )
        limpias["Cursos"] = limpias["Cursos"].drop_duplicates(subset=["id_curso"])

    if "Calificaciones" in limpias:
        limpias["Calificaciones"] = limpias["Calificaciones"].rename(
            columns={"matricula": "matricula", "id_curso": "id_curso", "calificacion": "calificacion"}
        )
        limpias["Calificaciones"]["calificacion"] = pd.to_numeric(
            limpias["Calificaciones"]["calificacion"], errors="coerce"
        )
        limpias["Calificaciones"] = limpias["Calificaciones"].dropna(subset=["calificacion"])
        limpias["Calificaciones"] = limpias["Calificaciones"][
            limpias["Calificaciones"]["calificacion"].between(0, 100)
        ]
        limpias["Calificaciones"] = limpias["Calificaciones"].drop_duplicates(subset=["matricula", "id_curso"])

    return limpias


def guardar_tablas(tablas):
    crear_bd()
    conn = get_connection()
    orden = ["Carreras", "Materias", "Estudiantes", "Cursos", "Calificaciones"]

    for tabla in orden:
        if tabla in tablas:
            tablas[tabla].to_sql(tabla, conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()


@st.cache_data(show_spinner=False)
def cargar_dataset_desde_db():
    crear_bd()
    conn = get_connection()
    query = """
    SELECT
        e.matricula,
        e.nombre,
        e.apellido,
        ca.carrera,
        m.materia,
        cu.periodo,
        cu.grupo,
        cal.calificacion
    FROM Calificaciones cal
    JOIN Estudiantes e ON cal.matricula = e.matricula
    JOIN Cursos cu ON cal.id_curso = cu.id_curso
    JOIN Materias m ON cu.id_materia = m.id_materia
    JOIN Carreras ca ON e.id_carrera = ca.id_carrera;
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def cargar_archivo_subido(archivo):
    if archivo.name.endswith(".csv"):
        df = pd.read_csv(archivo)
        df = normalizar_columnas(df)
        requeridas = {"matricula", "nombre", "apellido", "carrera", "materia", "periodo", "grupo", "calificacion"}
        faltantes = requeridas - set(df.columns)
        if faltantes:
            st.error(f"El CSV debe contener estas columnas: {', '.join(sorted(requeridas))}")
            return None
        return df

    xls = pd.ExcelFile(archivo)
    hojas = set(xls.sheet_names)
    hojas_normalizadas = {h.lower(): h for h in xls.sheet_names}

    if {"carreras", "materias", "estudiantes", "cursos", "calificaciones"}.issubset(set(hojas_normalizadas.keys())):
        tablas = {
            "Carreras": pd.read_excel(xls, hojas_normalizadas["carreras"]),
            "Materias": pd.read_excel(xls, hojas_normalizadas["materias"]),
            "Estudiantes": pd.read_excel(xls, hojas_normalizadas["estudiantes"]),
            "Cursos": pd.read_excel(xls, hojas_normalizadas["cursos"]),
            "Calificaciones": pd.read_excel(xls, hojas_normalizadas["calificaciones"]),
        }
        tablas = limpiar_tablas(tablas)
        guardar_tablas(tablas)
        st.cache_data.clear()
        return cargar_dataset_desde_db()

    df = pd.read_excel(xls, xls.sheet_names[0])
    df = normalizar_columnas(df)
    return df


def limpiar_dataset_general(df):
    df = df.copy()
    df = normalizar_columnas(df)
    df = limpiar_texto(df)
    df = df.drop_duplicates()

    if "calificacion" in df.columns:
        df["calificacion"] = pd.to_numeric(df["calificacion"], errors="coerce")
        df = df.dropna(subset=["calificacion"])
        df = df[df["calificacion"].between(0, 100)]

    if "periodo" in df.columns:
        df["periodo"] = df["periodo"].astype(str)

    return df

def limpiar_filtros():
    st.session_state.filtro_carrera = "Todas"
    st.session_state.filtro_materia = "Todas"
    st.session_state.filtro_grupo = "Todos"
    st.session_state.filtro_periodo = "Todos"
    st.session_state.filtro_busqueda = ""

def obtener_filtros_sidebar(df):
    """Obtiene los filtros del sidebar (sin búsqueda)"""
    with st.sidebar:
        st.markdown("### Filtros")
        st.markdown("")

        carreras = ["Todas"] + sorted(df["carrera"].dropna().unique().tolist()) if "carrera" in df else ["Todas"]
        materias = ["Todas"] + sorted(df["materia"].dropna().unique().tolist()) if "materia" in df else ["Todas"]
        grupos = ["Todos"] + sorted(df["grupo"].dropna().unique().tolist()) if "grupo" in df else ["Todos"]
        periodos = ["Todos"] + sorted(df["periodo"].dropna().unique().tolist()) if "periodo" in df else ["Todos"]

        carrera = st.selectbox("Carrera", carreras, key="filtro_carrera")
        st.markdown("")
        materia = st.selectbox("Materia", materias, key="filtro_materia")
        st.markdown("")
        grupo = st.selectbox("Grupo", grupos, key="filtro_grupo")
        st.markdown("")
        periodo = st.selectbox("Periodo", periodos, key="filtro_periodo")

        # Botón de limpieza
        st.markdown("---")
        if st.button("Limpiar filtros", on_click=limpiar_filtros, use_container_width=True):
            st.rerun()

    return {
        "carrera": carrera,
        "materia": materia,
        "grupo": grupo,
        "periodo": periodo,
    }


def aplicar_filtros_custom(df, filtros, omitir=None):
    filtrado = df.copy()

    if filtros["carrera"] != "Todas" and "carrera" in filtrado and omitir != "carrera":
        filtrado = filtrado[filtrado["carrera"] == filtros["carrera"]]
    if filtros["materia"] != "Todas" and "materia" in filtrado and omitir != "materia":
        filtrado = filtrado[filtrado["materia"] == filtros["materia"]]
    if filtros["grupo"] != "Todos" and "grupo" in filtrado and omitir != "grupo":
        filtrado = filtrado[filtrado["grupo"] == filtros["grupo"]]
    if filtros["periodo"] != "Todos" and "periodo" in filtrado and omitir != "periodo":
        filtrado = filtrado[filtrado["periodo"] == filtros["periodo"]]
    if filtros["busqueda"] and omitir != "busqueda":
        texto = filtros["busqueda"].lower().strip()
        nombre_completo = (
            filtrado.get("nombre", "").astype(str) + " " + filtrado.get("apellido", "").astype(str)
        ).str.lower()
        matricula = filtrado.get("matricula", "").astype(str).str.lower()
        filtrado = filtrado[nombre_completo.str.contains(texto, na=False) | matricula.str.contains(texto, na=False)]

    return filtrado


def generar_analisis(df):
    if df.empty:
        return {
            "promedio": 0,
            "total_registros": 0,
            "total_estudiantes": 0,
            "aprobacion": 0,
            "riesgo": 0,
            "mejor_materia": "Sin datos",
            "materia_critica": "Sin datos",
        }

    promedio = df["calificacion"].mean()
    total_estudiantes = df["matricula"].nunique() if "matricula" in df else len(df)
    aprobacion = (df["calificacion"] >= RIESGO_CALIFICACION).mean() * 100
    riesgo = (df["calificacion"] < RIESGO_CALIFICACION).sum()

    por_materia = df.groupby("materia", as_index=False)["calificacion"].mean() if "materia" in df else pd.DataFrame()
    mejor_materia = por_materia.sort_values("calificacion", ascending=False).iloc[0]["materia"] if not por_materia.empty else "Sin datos"
    materia_critica = por_materia.sort_values("calificacion", ascending=True).iloc[0]["materia"] if not por_materia.empty else "Sin datos"

    return {
        "promedio": promedio,
        "total_registros": len(df),
        "total_estudiantes": total_estudiantes,
        "aprobacion": aprobacion,
        "riesgo": riesgo,
        "mejor_materia": mejor_materia,
        "materia_critica": materia_critica,
    }


def analizar_estudiantes_en_riesgo(df):
    """
    Analiza estudiantes agrupados por matrícula para identificar:
    - Estudiantes con 1+ materias en riesgo
    - Estudiantes con 3+ materias en riesgo (crítico)
    """
    if df.empty or "matricula" not in df or "materia" not in df:
        return pd.DataFrame(), pd.DataFrame()

    # Filtrar registros en riesgo
    riesgo_df = df[df["calificacion"] < RIESGO_CALIFICACION].copy()

    if riesgo_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Agrupar por estudiante y contar materias en riesgo
    estudiantes_riesgo = riesgo_df.groupby(["matricula", "nombre", "apellido"], as_index=False).agg(
        materias_en_riesgo=("materia", "nunique"),
        promedio_riesgo=("calificacion", "mean"),
        materias_detalle=("materia", lambda x: ", ".join(sorted(set(x))))
    ).sort_values("materias_en_riesgo", ascending=False)

    # Filtrar estudiantes con 3+ materias en riesgo (CRÍTICO)
    criticos = estudiantes_riesgo[estudiantes_riesgo["materias_en_riesgo"] >= 3].copy()

    return estudiantes_riesgo, criticos


def crear_reporte_texto(df, analisis):
    if df.empty:
        return "No existen datos suficientes para generar el reporte."

    riesgo_df = df[df["calificacion"] < RIESGO_CALIFICACION].copy()
    bajo_df = df[df["calificacion"] < BAJO_DESEMPENO].copy()

    lineas = []
    lineas.append("REPORTE FINAL DE ANÁLISIS ACADÉMICO")
    lineas.append("=" * 45)
    lineas.append(f"Total de registros analizados: {analisis['total_registros']}")
    lineas.append(f"Total de estudiantes únicos: {analisis['total_estudiantes']}")
    lineas.append(f"Promedio general: {analisis['promedio']:.2f}")
    lineas.append(f"Porcentaje de aprobación: {analisis['aprobacion']:.2f}%")
    lineas.append(f"Registros en riesgo académico: {analisis['riesgo']}")
    lineas.append(f"Materia con mejor desempeño: {analisis['mejor_materia']}")
    lineas.append(f"Materia con menor desempeño: {analisis['materia_critica']}")
    lineas.append("")
    lineas.append("PATRONES DETECTADOS")
    lineas.append("- Se identifican estudiantes en riesgo cuando su calificación es menor a 70.")
    lineas.append("- Se considera bajo desempeño cuando la calificación es menor a 80.")

    if "materia" in df:
        criticas = df.groupby("materia")["calificacion"].mean().sort_values().head(3)
        lineas.append("- Materias prioritarias por menor promedio:")
        for materia, prom in criticas.items():
            lineas.append(f"  • {materia}: {prom:.2f}")

    if "grupo" in df:
        grupos = df.groupby("grupo")["calificacion"].mean().sort_values().head(3)
        lineas.append("- Grupos con menor rendimiento promedio:")
        for grupo, prom in grupos.items():
            lineas.append(f"  • Grupo {grupo}: {prom:.2f}")

    lineas.append("")
    lineas.append("CONCLUSIONES")
    lineas.append(f"- El promedio general del Panel de Datos es de {analisis['promedio']:.2f}.")
    lineas.append(f"- Existen {len(riesgo_df)} registros en riesgo académico que requieren seguimiento.")
    lineas.append(f"- Existen {len(bajo_df)} registros con bajo desempeño que requieren acciones preventivas.")
    lineas.append("")
    lineas.append("DECISIONES ACADÉMICAS PROPUESTAS")
    lineas.append("- Implementar tutorías para estudiantes con calificaciones menores a 70.")
    lineas.append("- Reforzar las materias con menor promedio mediante asesorías o ajustes de planeación.")
    lineas.append("- Revisar el desempeño por grupo y periodo para detectar cargas académicas problemáticas.")
    lineas.append("- Dar seguimiento periódico a los estudiantes con bajo desempeño antes del cierre del periodo.")

    return "\n".join(lineas)


def generar_pdf(df, analisis):
    from fpdf import FPDF
    from datetime import date

    riesgo_df = df[df["calificacion"] < RIESGO_CALIFICACION]
    bajo_df   = df[df["calificacion"] < BAJO_DESEMPENO]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # ── Encabezado ──────────────────────────────────────
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(20, 10)
    pdf.cell(0, 8, "REPORTE FINAL DE ANALISIS ACADEMICO", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 190, 210)
    pdf.set_x(20)
    pdf.cell(0, 6, f"Generado el {date.today().strftime('%d/%m/%Y')}  |  Sistema de Toma de Decisiones", ln=True)
    pdf.ln(14)

    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    labels = ["REGISTROS", "ESTUDIANTES", "PROMEDIO", "APROBACION"]
    values = [
        f"{analisis['total_registros']:,}",
        f"{analisis['total_estudiantes']:,}",
        f"{analisis['promedio']:.2f}",
        f"{analisis['aprobacion']:.1f}%",
    ]
    col_w = 42.5
    for lbl, val in zip(labels, values):
        pdf.set_text_color(100, 116, 139)
        pdf.cell(col_w, 5, lbl)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 14)
    for val in values:
        pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w, 8, val)
    pdf.ln(14)

    def section(title, items):
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 7, title, ln=True, fill=True, border="B")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(55, 65, 81)
        for item in items:
            pdf.set_x(20)
            pdf.cell(5, 6, chr(149))
            pdf.multi_cell(0, 6, item)
        pdf.ln(4)

    
    section("RESUMEN EJECUTIVO", [
        f"Materia con mejor desempeno: {analisis['mejor_materia']}",
        f"Materia con menor desempeno: {analisis['materia_critica']}",
        f"Registros en riesgo academico (< 70): {analisis['riesgo']:,}",
    ])

    
    patrones = [
        "Se identifican estudiantes en riesgo cuando su calificacion es menor a 70.",
        "Se considera bajo desempeno cuando la calificacion es menor a 80.",
    ]
    if "materia" in df.columns:
        criticas = df.groupby("materia")["calificacion"].mean().sort_values().head(3)
        for mat, prom in criticas.items():
            patrones.append(f"  Materia prioritaria: {mat} - promedio {prom:.2f}")
    if "grupo" in df.columns:
        grupos = df.groupby("grupo")["calificacion"].mean().sort_values().head(3)
        for grp, prom in grupos.items():
            patrones.append(f"  Grupo con menor rendimiento: Grupo {grp} - {prom:.2f}")
    section("PATRONES DETECTADOS", patrones)

    
    section("CONCLUSIONES", [
        f"El promedio general del Panel de Datos es de {analisis['promedio']:.2f}.",
        f"Existen {len(riesgo_df):,} registros en riesgo academico que requieren seguimiento.",
        f"Existen {len(bajo_df):,} registros con bajo desempeno que requieren acciones preventivas.",
    ])

    
    section("DECISIONES ACADEMICAS PROPUESTAS", [
        "Implementar tutorias para estudiantes con calificaciones menores a 70.",
        "Reforzar las materias con menor promedio mediante asesorias o ajustes de planeacion.",
        "Revisar el desempeno por grupo y periodo para detectar cargas academicas problematicas.",
        "Dar seguimiento periodico a los estudiantes con bajo desempeno antes del cierre del periodo.",
    ])

    
    pdf.set_y(-18)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, f"Sistema Academico - Toma de Decisiones  |  {date.today().strftime('%d/%m/%Y')}", align="C")

    return bytes(pdf.output())


def convertir_excel(df, reporte):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dataset_Limpio")
        resumen = pd.DataFrame({"Reporte": reporte.split("\n")})
        resumen.to_excel(writer, index=False, sheet_name="Reporte")

        if not df.empty:
            if "materia" in df:
                df.groupby("materia", as_index=False)["calificacion"].mean().to_excel(writer, index=False, sheet_name="Promedio_Materia")
            if "grupo" in df:
                df.groupby("grupo", as_index=False)["calificacion"].mean().to_excel(writer, index=False, sheet_name="Promedio_Grupo")
            if "carrera" in df:
                df.groupby("carrera", as_index=False)["calificacion"].mean().to_excel(writer, index=False, sheet_name="Promedio_Carrera")
            df[df["calificacion"] < RIESGO_CALIFICACION].to_excel(writer, index=False, sheet_name="Riesgo_Academico")

    output.seek(0)
    return output



st.markdown("""
<script>
(function() {
    function applyTheme() {
        var app = document.querySelector('[data-testid="stApp"]');
        if (!app) return;
        var bg = window.getComputedStyle(app).backgroundColor;
        // rgb(14,17,23) = #0e1117 (Streamlit dark), rgb(38,39,48) = #262730
        var dark = bg && (
            bg.includes('14, 17, 23') || bg.includes('14,17,23') ||
            bg.includes('38, 39, 48') || bg.includes('38,39,48') ||
            bg.includes('26, 28, 36') || bg.includes('26,28,36')
        );
        document.body.classList.toggle('st-dark', dark);
    }
    applyTheme();
    var observer = new MutationObserver(applyTheme);
    observer.observe(document.documentElement, {
        attributes: true, childList: true, subtree: true,
        attributeFilter: ['style', 'class']
    });
    setInterval(applyTheme, 500);
})();
</script>
""", unsafe_allow_html=True)

# Header con buscador en la derecha
col_titulo, col_busqueda = st.columns([3, 1])
with col_titulo:
    st.title("📊 Sistema de Análisis Académico")
    st.caption("Consolidación, limpieza, análisis, visualización y reporte para toma de decisiones académicas")
with col_busqueda:
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    busqueda = st.text_input(
        "🔍 Buscar",
        placeholder="Nombre, apellido o matrícula...",
        key="filtro_busqueda",
        label_visibility="collapsed"
    )

with st.sidebar:
    st.markdown("### Carga de datos")
    st.markdown("")
    archivo = st.file_uploader(
        "Sube un archivo",
        type=["xlsx", "xls", "csv"],
        help="Formatos soportados: Excel (.xlsx, .xls) o CSV"
    )
    st.markdown("")
    usar_db = st.checkbox("Usar base de datos SQLite existente", value=True)
    st.markdown("---")

if archivo is not None:
    df = cargar_archivo_subido(archivo)
    if df is not None:
        df = limpiar_dataset_general(df)
        st.success("Archivo cargado y limpiado correctamente.")
elif usar_db:
    df = cargar_dataset_desde_db()
    df = limpiar_dataset_general(df)
else:
    df = pd.DataFrame()

if df.empty:
    st.warning("No hay datos disponibles. Sube un archivo Excel/CSV o verifica la base de datos SQLite.")
    st.stop()

# Validación mínima
columnas_necesarias = {"calificacion"}
if not columnas_necesarias.issubset(df.columns):
    st.error("El dataset debe incluir al menos la columna 'calificacion'.")
    st.stop()

# Obtener filtros del sidebar y combinar con búsqueda
filtros_sidebar = obtener_filtros_sidebar(df)
filtros_seleccionados = {**filtros_sidebar, "busqueda": busqueda}
df_filtrado = aplicar_filtros_custom(df, filtros_seleccionados)
analisis = generar_analisis(df_filtrado)


# Función para popup de detalle de mejor materia
@st.dialog("🏆 Detalle de Mejor Desempeño")
def mostrar_detalle_mejor_materia():
    if "materia" in df_filtrado:
        por_materia = df_filtrado.groupby("materia").agg(
            promedio=("calificacion", "mean"),
            total_estudiantes=("matricula", "nunique"),
            registros=("calificacion", "count"),
            nota_maxima=("calificacion", "max"),
            nota_minima=("calificacion", "min")
        ).reset_index().sort_values("promedio", ascending=False)

        mejor = por_materia.iloc[0]
        st.markdown(f"### {mejor['materia']}")
        st.metric("Promedio", f"{mejor['promedio']:.2f}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Estudiantes", int(mejor['total_estudiantes']))
        col2.metric("Nota Máxima", f"{mejor['nota_maxima']:.1f}")
        col3.metric("Nota Mínima", f"{mejor['nota_minima']:.1f}")

        st.divider()
        st.write("**Top 5 materias con mejor desempeño:**")
        top5 = por_materia.head(5).rename(columns={
            "materia": "Materia",
            "promedio": "Promedio",
            "total_estudiantes": "Estudiantes",
            "registros": "Registros"
        })
        top5["Promedio"] = top5["Promedio"].round(2)
        st.dataframe(top5[["Materia", "Promedio", "Estudiantes"]], hide_index=True, use_container_width=True)


# Función para popup de detalle de materia crítica
@st.dialog("⚠️ Detalle de Materia Crítica")
def mostrar_detalle_materia_critica():
    if "materia" in df_filtrado:
        por_materia = df_filtrado.groupby("materia").agg(
            promedio=("calificacion", "mean"),
            total_estudiantes=("matricula", "nunique"),
            estudiantes_riesgo=("calificacion", lambda x: (x < RIESGO_CALIFICACION).sum()),
            registros=("calificacion", "count"),
        ).reset_index().sort_values("promedio", ascending=True)

        critica = por_materia.iloc[0]
        st.markdown(f"### {critica['materia']}")
        st.metric("Promedio", f"{critica['promedio']:.2f}")

        col1, col2 = st.columns(2)
        col1.metric("Estudiantes", int(critica['total_estudiantes']))
        col2.metric("En Riesgo", int(critica['estudiantes_riesgo']))

        st.divider()
        st.write("**Top 5 materias con menor desempeño:**")
        bottom5 = por_materia.head(5).rename(columns={
            "materia": "Materia",
            "promedio": "Promedio",
            "total_estudiantes": "Estudiantes",
            "estudiantes_riesgo": "En Riesgo"
        })
        bottom5["Promedio"] = bottom5["Promedio"].round(2)
        st.dataframe(bottom5[["Materia", "Promedio", "Estudiantes", "En Riesgo"]], hide_index=True, use_container_width=True)


st.markdown('<div class="section-title">Resumen general</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label">Promedio general</div>
        <div class="kpi-num">{analisis['promedio']:.2f}</div>
        <div class="kpi-sub">sobre 100 puntos</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">Estudiantes</div>
        <div class="kpi-num">{analisis['total_estudiantes']:,}</div>
        <div class="kpi-sub">alumnos únicos</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">Registros</div>
        <div class="kpi-num">{analisis['total_registros']:,}</div>
        <div class="kpi-sub">calificaciones totales</div>
    </div>
    <div class="kpi-box verde">
        <div class="kpi-label">Aprobación</div>
        <div class="kpi-num">{analisis['aprobacion']:.1f}%</div>
        <div class="kpi-sub">calificación ≥ 70</div>
    </div>
    <div class="kpi-box rojo">
        <div class="kpi-label">En riesgo</div>
        <div class="kpi-num">{analisis['riesgo']:,}</div>
        <div class="kpi-sub">calificación &lt; 70</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Botones para abrir popups de detalle
col_mejor, col_critica = st.columns(2)
with col_mejor:
    st.markdown(f"""
    <div class="info-strip-card verde" style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 13px 18px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(15, 23, 42, .04); border-left: 5px solid #22c55e;">
        <span style="font-size:1.4rem">🏆</span>
        <div>
            <div style="font-size: 0.69rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.07em;">Mejor desempeño</div>
            <div style="font-size: 0.97rem; font-weight: 700; color: #0f172a; margin-top: 2px;">{analisis['mejor_materia']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📊 Ver detalle completo", key="btn_mejor", use_container_width=True):
        mostrar_detalle_mejor_materia()

with col_critica:
    st.markdown(f"""
    <div class="info-strip-card ambar" style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 13px 18px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 8px rgba(15, 23, 42, .04); border-left: 5px solid #f59e0b;">
        <span style="font-size:1.4rem">⚠️</span>
        <div>
            <div style="font-size: 0.69rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.07em;">Materia crítica</div>
            <div style="font-size: 0.97rem; font-weight: 700; color: #0f172a; margin-top: 2px;">{analisis['materia_critica']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⚠️ Ver detalle completo", key="btn_critica", use_container_width=True):
        mostrar_detalle_materia_critica()


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Panel de Datos",
    "📈 Visualización",
    "⚖️ Comparaciones",
    "🔎 Consultas",
    "⚠️ Riesgo académico",
    "📄 Reporte final",
])

with tab1:
    st.subheader("Panel de Datos consolidado y limpio")

    # Preparar columnas limpias para mostrar
    df_display = df_filtrado.copy()

    # Renombrar columnas a español con formato título
    column_mapping = {
        "matricula": "Matrícula",
        "nombre": "Nombre",
        "apellido": "Apellido",
        "carrera": "Carrera",
        "materia": "Materia",
        "periodo": "Periodo",
        "grupo": "Grupo",
        "calificacion": "Calificación"
    }
    df_display = df_display.rename(columns={k: v for k, v in column_mapping.items() if k in df_display.columns})

    # Mostrar información de total de registros
    total_registros = len(df_display)
    st.info(f"📊 Mostrando {total_registros:,} registros totales")

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=420
    )

with tab2:
    st.subheader("Gráficas de desempeño")

    if "materia" in df_filtrado:
        # Ignorar filtro de materia
        df_materia = aplicar_filtros_custom(df, filtros_seleccionados, omitir="materia")
        prom_materia = df_materia.groupby("materia", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)

        st.write("📚 Promedio por materia")
        fig_materia = px.bar(
            prom_materia,
            x="materia",
            y="calificacion",
            labels={"materia": "Materia", "calificacion": "Promedio"},
            color="calificacion",
            color_continuous_scale="Blues"
        )
        fig_materia.update_layout(
            showlegend=False,
            xaxis_title="Materia",
            yaxis_title="Promedio de Calificación",
            height=400
        )
        fig_materia.update_traces(texttemplate='%{y:.1f}', textposition='outside')
        st.plotly_chart(fig_materia, use_container_width=True, config={'staticPlot': True})
        st.divider()

    if "carrera" in df_filtrado:
        # Ignorar filtro de carrera
        df_carrera = aplicar_filtros_custom(df, filtros_seleccionados, omitir="carrera")
        prom_carrera = df_carrera.groupby("carrera", as_index=False)["calificacion"].mean().sort_values("calificacion", ascending=False)

        st.write("🎓 Promedio por carrera")
        fig_carrera = px.bar(
            prom_carrera,
            x="carrera",
            y="calificacion",
            labels={"carrera": "Carrera", "calificacion": "Promedio"},
            color="calificacion",
            color_continuous_scale="Greens"
        )
        fig_carrera.update_layout(
            showlegend=False,
            xaxis_title="Carrera",
            yaxis_title="Promedio de Calificación",
            height=400
        )
        fig_carrera.update_traces(texttemplate='%{y:.1f}', textposition='outside')
        st.plotly_chart(fig_carrera, use_container_width=True, config={'staticPlot': True})
        st.divider()

    if "periodo" in df_filtrado:
        # Ignorar filtro de periodo para ver tendencia completa
        df_periodo = aplicar_filtros_custom(df, filtros_seleccionados, omitir="periodo")
        prom_periodo = df_periodo.groupby("periodo", as_index=False)["calificacion"].mean().sort_values("periodo")

        st.write("📈 Tendencia por periodo")
        fig_periodo = px.line(
            prom_periodo,
            x="periodo",
            y="calificacion",
            labels={"periodo": "Periodo", "calificacion": "Promedio"},
            markers=True
        )
        fig_periodo.update_layout(
            xaxis_title="Periodo",
            yaxis_title="Promedio de Calificación",
            height=400
        )
        fig_periodo.update_traces(line_color='#3b82f6', line_width=3)
        st.plotly_chart(fig_periodo, use_container_width=True, config={'staticPlot': True})
        st.divider()

    # Distribución sí obedece a todos los filtros
    distribucion = pd.cut(
        df_filtrado["calificacion"],
        bins=[0, 60, 70, 80, 90, 100],
        labels=["0-59", "60-69", "70-79", "80-89", "90-100"],
        include_lowest=True,
    ).value_counts().sort_index()

    st.write("📊 Distribución de calificaciones")
    dist_df = pd.DataFrame({"Rango": distribucion.index, "Cantidad": distribucion.values})
    fig_dist = px.bar(
        dist_df,
        x="Rango",
        y="Cantidad",
        labels={"Rango": "Rango de Calificación", "Cantidad": "Número de Registros"},
        color="Cantidad",
        color_continuous_scale="Purples"
    )
    fig_dist.update_layout(
        showlegend=False,
        xaxis_title="Rango de Calificación",
        yaxis_title="Cantidad de Registros",
        height=400
    )
    fig_dist.update_traces(texttemplate='%{y}', textposition='outside')
    st.plotly_chart(fig_dist, use_container_width=True, config={'staticPlot': True})

with tab3:
    st.subheader("Comparaciones entre grupos")

    if "grupo" in df:
        # Ignorar el filtro de grupo para poder comparar todos los grupos
        df_grupos = aplicar_filtros_custom(df, filtros_seleccionados, omitir="grupo")

        comparacion_grupos = df_grupos.groupby("grupo").agg(
            promedio=("calificacion", "mean"),
            minimo=("calificacion", "min"),
            maximo=("calificacion", "max"),
            registros=("calificacion", "count"),
        ).reset_index().sort_values("promedio", ascending=False)

        # Renombrar columnas a español
        comparacion_grupos = comparacion_grupos.rename(columns={
            "grupo": "Grupo",
            "promedio": "Promedio",
            "minimo": "Mínimo",
            "maximo": "Máximo",
            "registros": "Registros"
        })
        comparacion_grupos["Promedio"] = comparacion_grupos["Promedio"].round(2)
        comparacion_grupos["Mínimo"] = comparacion_grupos["Mínimo"].round(2)
        comparacion_grupos["Máximo"] = comparacion_grupos["Máximo"].round(2)

        st.dataframe(comparacion_grupos, use_container_width=True, hide_index=True)

        # Gráfica de comparación de promedios
        st.write("📊 Comparación de promedios por grupo")
        fig_grupos = px.bar(
            comparacion_grupos,
            x="Grupo",
            y="Promedio",
            labels={"Grupo": "Grupo", "Promedio": "Promedio de Calificación"},
            color="Promedio",
            color_continuous_scale="Teal"
        )
        fig_grupos.update_layout(
            showlegend=False,
            xaxis_title="Grupo",
            yaxis_title="Promedio de Calificación",
            height=400
        )
        fig_grupos.update_traces(texttemplate='%{y:.1f}', textposition='outside')
        st.plotly_chart(fig_grupos, use_container_width=True, config={'staticPlot': True})
    else:
        st.info("El dataset no contiene columna de grupo.")

    if {"materia", "grupo"}.issubset(df.columns):
        st.write("📋 Promedio por materia y grupo")
        df_grupos = aplicar_filtros_custom(df, filtros_seleccionados, omitir="grupo")
        tabla_pivote = pd.pivot_table(
            df_grupos,
            values="calificacion",
            index="materia",
            columns="grupo",
            aggfunc="mean",
        )
        st.dataframe(tabla_pivote.round(2), use_container_width=True)

with tab4:
    st.subheader("Consultas sobre el dataset")

    opcion = st.selectbox(
        "Selecciona una consulta automática",
        [
            "Top 10 mejores calificaciones",
            "Top 10 calificaciones más bajas",
            "Promedio por materia",
            "Promedio por carrera",
            "Promedio por grupo",
            "Estudiantes con calificación menor a 70",
            "Estudiantes con bajo desempeño menor a 80",
        ],
    )

    if opcion == "Top 10 mejores calificaciones":
        resultado = df_filtrado.sort_values("calificacion", ascending=False).head(10)
    elif opcion == "Top 10 calificaciones más bajas":
        resultado = df_filtrado.sort_values("calificacion", ascending=True).head(10)
    elif opcion == "Promedio por materia" and "materia" in df_filtrado:
        resultado = df_filtrado.groupby("materia", as_index=False)["calificacion"].mean().sort_values("calificacion")
        resultado = resultado.rename(columns={"materia": "Materia", "calificacion": "Promedio"})
        resultado["Promedio"] = resultado["Promedio"].round(2)
    elif opcion == "Promedio por carrera" and "carrera" in df_filtrado:
        resultado = df_filtrado.groupby("carrera", as_index=False)["calificacion"].mean().sort_values("calificacion")
        resultado = resultado.rename(columns={"carrera": "Carrera", "calificacion": "Promedio"})
        resultado["Promedio"] = resultado["Promedio"].round(2)
    elif opcion == "Promedio por grupo" and "grupo" in df_filtrado:
        resultado = df_filtrado.groupby("grupo", as_index=False)["calificacion"].mean().sort_values("calificacion")
        resultado = resultado.rename(columns={"grupo": "Grupo", "calificacion": "Promedio"})
        resultado["Promedio"] = resultado["Promedio"].round(2)
    elif opcion == "Estudiantes con calificación menor a 70":
        resultado = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION].sort_values("calificacion")
    elif opcion == "Estudiantes con bajo desempeño menor a 80":
        resultado = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO].sort_values("calificacion")
    else:
        resultado = pd.DataFrame()

    # Preparar resultado para mostrar
    if not resultado.empty:
        resultado_display = resultado.copy()

        # Renombrar columnas si no están ya renombradas
        column_mapping = {
            "matricula": "Matrícula",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "carrera": "Carrera",
            "materia": "Materia",
            "periodo": "Periodo",
            "grupo": "Grupo",
            "calificacion": "Calificación"
        }
        resultado_display = resultado_display.rename(columns={k: v for k, v in column_mapping.items() if k in resultado_display.columns})

        # Limitar registros si hay muchos
        total = len(resultado_display)
        if total > 200:
            st.info(f"Mostrando los primeros 200 registros de {total:,} totales")
            resultado_display = resultado_display.head(200)

        st.dataframe(resultado_display, use_container_width=True, hide_index=True, height=420)
    else:
        st.warning("No hay resultados para esta consulta con los filtros actuales.")

with tab5:
    st.subheader("Identificación de patrones y estudiantes en riesgo")

    # Análisis por estudiante (no por registro individual)
    estudiantes_riesgo, estudiantes_criticos = analizar_estudiantes_en_riesgo(df_filtrado)

    riesgo_registros = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION]
    bajo = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO]

    # Métricas principales
    r1, r2, r3 = st.columns(3)
    r1.metric("Estudiantes en riesgo", len(estudiantes_riesgo))
    r2.metric("🚨 CRÍTICO (3+ materias)", len(estudiantes_criticos))
    r3.metric("Bajo desempeño < 80", len(bajo))

    # ALERTA ESPECIAL para estudiantes críticos (3+ materias en riesgo)
    if not estudiantes_criticos.empty:
        st.error("⚠️ ALERTA CRÍTICA: Estudiantes con 3 o más materias en riesgo")
        st.markdown("Estos estudiantes requieren **intervención inmediata** del área de tutoría académica.")

        # Crear columnas limpias para mostrar
        criticos_display = estudiantes_criticos.copy()
        criticos_display = criticos_display.rename(columns={
            "matricula": "Matrícula",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "materias_en_riesgo": "Materias en Riesgo",
            "promedio_riesgo": "Promedio en Materias Reprobadas",
            "materias_detalle": "Materias"
        })
        criticos_display["Promedio en Materias Reprobadas"] = criticos_display["Promedio en Materias Reprobadas"].round(2)

        st.dataframe(
            criticos_display,
            use_container_width=True,
            hide_index=True,
            height=min(300, len(criticos_display) * 35 + 38)
        )
        st.divider()

    # Mostrar TODOS los estudiantes con 1+ materias en riesgo
    if not estudiantes_riesgo.empty:
        st.warning(f"📋 Estudiantes con al menos 1 materia en riesgo ({len(estudiantes_riesgo)} estudiantes)")

        # Preparar datos limpios
        riesgo_display = estudiantes_riesgo.copy()
        riesgo_display = riesgo_display.rename(columns={
            "matricula": "Matrícula",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "materias_en_riesgo": "Materias en Riesgo",
            "promedio_riesgo": "Promedio en Materias Reprobadas",
            "materias_detalle": "Materias"
        })
        riesgo_display["Promedio en Materias Reprobadas"] = riesgo_display["Promedio en Materias Reprobadas"].round(2)

        # Limitar a 100 registros para no sobrecargar la vista
        if len(riesgo_display) > 100:
            st.info(f"Mostrando los primeros 100 estudiantes de {len(riesgo_display)} totales")
            riesgo_display = riesgo_display.head(100)

        st.dataframe(
            riesgo_display,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    else:
        st.success("✅ No se detectaron estudiantes en riesgo con los filtros actuales.")

    # Gráfica de materias con más estudiantes en riesgo
    if not riesgo_registros.empty and "materia" in df_filtrado:
        st.write("📊 Materias con mayor cantidad de estudiantes en riesgo")
        riesgo_materia = riesgo_registros.groupby("materia", as_index=False).agg(
            estudiantes=("matricula", "nunique")
        ).sort_values("estudiantes", ascending=False).head(10)

        if not riesgo_materia.empty:
            fig = px.bar(
                riesgo_materia,
                x="materia",
                y="estudiantes",
                labels={"materia": "Materia", "estudiantes": "Estudiantes en Riesgo"},
                color="estudiantes",
                color_continuous_scale="Reds"
            )
            fig.update_layout(
                showlegend=False,
                xaxis_title="Materia",
                yaxis_title="Número de Estudiantes",
                height=400
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

with tab6:
    from datetime import date as _date

    reporte  = crear_reporte_texto(df_filtrado, analisis)
    hoy      = _date.today().strftime("%d / %m / %Y")
    riesgo_df = df_filtrado[df_filtrado["calificacion"] < RIESGO_CALIFICACION]
    bajo_df   = df_filtrado[df_filtrado["calificacion"] < BAJO_DESEMPENO]

    mat_items = ""
    if "materia" in df_filtrado.columns:
        criticas = df_filtrado.groupby("materia")["calificacion"].mean().sort_values().head(3)
        for mat, prom in criticas.items():
            mat_items += f'<div class="rpt-sub-item"><span>›</span><span>{mat}: <strong>{prom:.2f}</strong></span></div>'

    grp_items = ""
    if "grupo" in df_filtrado.columns:
        grupos_r = df_filtrado.groupby("grupo")["calificacion"].mean().sort_values().head(3)
        for grp, prom in grupos_r.items():
            grp_items += f'<div class="rpt-sub-item"><span>›</span><span>Grupo {grp}: <strong>{prom:.2f}</strong></span></div>'

    patrones_html = (
        '<div class="rpt-item"><span class="rpt-dot rojo"></span>'
        '<span>Se identifican estudiantes en riesgo cuando su calificación es <strong>menor a 70</strong>.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot ambar"></span>'
        '<span>Se considera bajo desempeño cuando la calificación es <strong>menor a 80</strong>.</span></div>'
        + (f'<div class="rpt-item"><span class="rpt-dot"></span><div><div>Materias prioritarias por menor promedio:</div>{mat_items}</div></div>' if mat_items else '')
        + (f'<div class="rpt-item"><span class="rpt-dot"></span><div><div>Grupos con menor rendimiento:</div>{grp_items}</div></div>' if grp_items else '')
    )

    html = (
        '<div class="rpt-card">'

        '<div class="rpt-header">'
        '<div class="rpt-header-top">'
        '<div>'
        '<div class="rpt-header-title">Reporte Final de Análisis Académico</div>'
        f'<div class="rpt-header-sub">Sistema de Toma de Decisiones &nbsp;·&nbsp; Generado el {hoy}</div>'
        '</div>'
        '<div class="rpt-header-badge">ANÁLISIS COMPLETO</div>'
        '</div>'
        '</div>'

        '<div class="rpt-metrics">'
        f'<div class="rpt-metric"><div class="rpt-metric-label">Total registros</div><div class="rpt-metric-value">{analisis["total_registros"]:,}</div></div>'
        f'<div class="rpt-metric"><div class="rpt-metric-label">Estudiantes únicos</div><div class="rpt-metric-value">{analisis["total_estudiantes"]:,}</div></div>'
        f'<div class="rpt-metric"><div class="rpt-metric-label">Promedio general</div><div class="rpt-metric-value">{analisis["promedio"]:.2f}</div></div>'
        f'<div class="rpt-metric"><div class="rpt-metric-label">% de aprobación</div><div class="rpt-metric-value">{analisis["aprobacion"]:.1f}%</div></div>'
        '</div>'

        '<div class="rpt-body">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Resumen ejecutivo</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot verde"></span><span>Materia con <strong>mejor desempeño</strong>: {analisis["mejor_materia"]}</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot rojo"></span><span>Materia con <strong>menor desempeño</strong>: {analisis["materia_critica"]}</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot ambar"></span><span>Registros en <strong>riesgo académico</strong> (calificación &lt; 70): <strong>{analisis["riesgo"]:,}</strong></span></div>'
        '</div>'

        '<hr class="rpt-divider">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Patrones detectados</span></div>'
        + patrones_html +
        '</div>'

        '<hr class="rpt-divider">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Conclusiones</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot"></span><span>El promedio general del dataset es de <strong>{analisis["promedio"]:.2f}</strong>.</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot rojo"></span><span>Existen <strong>{len(riesgo_df):,} registros en riesgo académico</strong> que requieren seguimiento inmediato.</span></div>'
        f'<div class="rpt-item"><span class="rpt-dot ambar"></span><span>Existen <strong>{len(bajo_df):,} registros con bajo desempeño</strong> que requieren acciones preventivas.</span></div>'
        '</div>'

        '<hr class="rpt-divider">'

        '<div class="rpt-section">'
        '<div class="rpt-section-title"><span>Decisiones académicas propuestas</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Implementar <strong>tutorías</strong> para estudiantes con calificaciones menores a 70.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Reforzar las materias con menor promedio mediante <strong>asesorías o ajustes de planeación</strong>.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Revisar el desempeño por grupo y periodo para detectar <strong>cargas académicas problemáticas</strong>.</span></div>'
        '<div class="rpt-item"><span class="rpt-dot verde"></span><span>Dar <strong>seguimiento periódico</strong> a los estudiantes con bajo desempeño antes del cierre del periodo.</span></div>'
        '</div>'

        '</div>'

        f'<div class="rpt-footer"><span>Sistema Académico · Toma de Decisiones</span><span>Generado el {hoy}</span></div>'

        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)

    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="Descargar TXT",
            data=reporte.encode("utf-8"),
            file_name="reporte_academico.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        excel = convertir_excel(df_filtrado, reporte)
        st.download_button(
            label="Descargar Excel",
            data=excel,
            file_name="reporte_academico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        pdf_bytes = generar_pdf(df_filtrado, analisis)
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name="reporte_academico.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("""
    <style>
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stDownloadButton"] > button {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stDownloadButton"] > button {
        background-color: #16a34a !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stDownloadButton"] > button {
        background-color: #dc2626 !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        opacity: 0.85;
    }
    </style>
    """, unsafe_allow_html=True)
