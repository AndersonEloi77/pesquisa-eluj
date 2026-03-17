import streamlit as st
import random
import csv
import os
import uuid
from datetime import datetime
from collections import defaultdict

import pandas as pd

st.set_page_config(page_title="Pesquisa Eluj", layout="wide")

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 1rem;
    max-width: 1100px;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    padding: 0.55rem 0.75rem;
    font-size: 1rem;
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 0.6rem;
        padding-left: 0.55rem;
        padding-right: 0.55rem;
    }

    h1 {
        font-size: 2rem !important;
        margin-bottom: 0.3rem !important;
    }

    p, div, label {
        font-size: 0.95rem !important;
    }

    .stButton > button {
        font-size: 0.95rem !important;
        padding: 0.55rem 0.45rem !important;
    }

    img {
        border-radius: 10px;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("Pesquisa Eluj 👕")
st.write("Qual dessas você compraria?")

# =========================
# CONFIGURAÇÕES
# =========================
CSV_PATH = "votos.csv"
ADMIN_PASSWORD = "sinhoeloi13"

imagens = [f"imagens/img{i}.JPG" for i in range(1, 21)]

QTD_BLUSAS = len(imagens)
ESCOLHAS_POR_RODADA = QTD_BLUSAS // 2
RODADAS_OBRIGATORIAS = 1
MAX_TENTATIVAS_PARES = 200

# =========================
# CSV
# =========================
def garantir_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "participante_id",
                "rodada_numero",
                "escolha_na_rodada",
                "imagem_esquerda",
                "imagem_direita",
                "escolhida"
            ])

def registrar_voto(pid, rodada, escolha, esq, dir, esc):
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            pid, rodada, escolha, esq, dir, esc
        ])

def carregar_votos():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()
    try:
        return pd.read_csv(CSV_PATH)
    except:
        return pd.DataFrame()

# =========================
# RANKING
# =========================
def atualizar_elo(r, v, p):
    ev = 1 / (1 + 10 ** ((r[p] - r[v]) / 400))
    ep = 1 / (1 + 10 ** ((r[v] - r[p]) / 400))
    r[v] += 32 * (1 - ev)
    r[p] += 32 * (0 - ep)

def ranking():
    r = {img: 1000 for img in imagens}
    df = carregar_votos()

    for _, row in df.iterrows():
        e, d, esc = row["imagem_esquerda"], row["imagem_direita"], row["escolhida"]
        v, p = (e, d) if esc == e else (d, e)
        atualizar_elo(r, v, p)

    return sorted(r.items(), key=lambda x: x[1], reverse=True)

# =========================
# ADMIN
# =========================
def painel_admin():
    with st.sidebar:
        senha = st.text_input("Senha admin", type="password")
        if senha == ADMIN_PASSWORD:
            st.session_state.admin = True

if "admin" not in st.session_state:
    st.session_state.admin = False

painel_admin()

# =========================
# ESTADO
# =========================
garantir_csv()

if "id" not in st.session_state:
    st.session_state.id = str(uuid.uuid4())[:8]

if "rodada" not in st.session_state:
    st.session_state.rodada = 1

if "indice" not in st.session_state:
    st.session_state.indice = 0

if "pares" not in st.session_state:
    temp = imagens[:]
    random.shuffle(temp)
    st.session_state.pares = [(temp[i], temp[i+1]) for i in range(0, len(temp), 2)]

if "fim" not in st.session_state:
    st.session_state.fim = False

# =========================
# FINAL
# =========================
if st.session_state.fim:
    st.success("Obrigado por nos ajudar ❤️")

    with st.expander("Ver ranking"):
        for i, (img, pts) in enumerate(ranking()[:10], 1):
            st.write(f"{i}º - {os.path.basename(img)}")

    st.stop()

# =========================
# PROGRESSO
# =========================
st.progress(st.session_state.indice / ESCOLHAS_POR_RODADA)

# =========================
# FIM DA RODADA
# =========================
if st.session_state.indice >= ESCOLHAS_POR_RODADA:

    if st.button("Finalizar"):
        st.session_state.fim = True
        st.rerun()

    if st.button("Continuar"):
        st.session_state.rodada += 1
        st.session_state.indice = 0
        temp = imagens[:]
        random.shuffle(temp)
        st.session_state.pares = [(temp[i], temp[i+1]) for i in range(0, len(temp), 2)]
        st.rerun()

    with st.expander("Ver ranking"):
        for i, (img, pts) in enumerate(ranking()[:10], 1):
            st.write(f"{i}º - {os.path.basename(img)}")

    st.stop()

# =========================
# VOTAÇÃO (VERTICAL)
# =========================
img1, img2 = st.session_state.pares[st.session_state.indice]

# PRIMEIRA IMAGEM
st.image(img1, width=320)
if st.button("Escolho essa", key="b1", use_container_width=True):
    registrar_voto(st.session_state.id, st.session_state.rodada,
                   st.session_state.indice, img1, img2, img1)
    st.session_state.indice += 1
    st.rerun()

st.write("")

# SEGUNDA IMAGEM
st.image(img2, width=320)
if st.button("Escolho essa", key="b2", use_container_width=True):
    registrar_voto(st.session_state.id, st.session_state.rodada,
                   st.session_state.indice, img1, img2, img2)
    st.session_state.indice += 1
    st.rerun()

# =========================
# RANKING
# =========================
with st.expander("Ver ranking atual"):
    for i, (img, pts) in enumerate(ranking()[:10], 1):
        st.write(f"{i}º - {os.path.basename(img)}")