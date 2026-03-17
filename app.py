import streamlit as st
import random
import csv
import os
import uuid
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Pesquisa Eluj", layout="wide")

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

CSV_PATH = "votos.csv"
ADMIN_PASSWORD = "sinhoeloi13"

imagens = [f"imagens/img{i}.JPG" for i in range(1, 21)]

QTD_BLUSAS = len(imagens)
ESCOLHAS_POR_RODADA = QTD_BLUSAS // 2

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

def registrar_voto(pid, rodada, escolha, esq, dir_, esc):
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            pid,
            rodada,
            escolha,
            esq,
            dir_,
            esc
        ])

def carregar_votos():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=[
            "timestamp",
            "participante_id",
            "rodada_numero",
            "escolha_na_rodada",
            "imagem_esquerda",
            "imagem_direita",
            "escolhida"
        ])
    try:
        return pd.read_csv(CSV_PATH)
    except Exception:
        return pd.DataFrame(columns=[
            "timestamp",
            "participante_id",
            "rodada_numero",
            "escolha_na_rodada",
            "imagem_esquerda",
            "imagem_direita",
            "escolhida"
        ])

def atualizar_elo(ratings, vencedor, perdedor):
    esperado_v = 1 / (1 + 10 ** ((ratings[perdedor] - ratings[vencedor]) / 400))
    esperado_p = 1 / (1 + 10 ** ((ratings[vencedor] - ratings[perdedor]) / 400))
    ratings[vencedor] += 32 * (1 - esperado_v)
    ratings[perdedor] += 32 * (0 - esperado_p)

def ranking():
    ratings = {img: 1000.0 for img in imagens}
    df = carregar_votos()

    if df.empty:
        return sorted(ratings.items(), key=lambda x: x[1], reverse=True)

    for _, row in df.iterrows():
        esquerda = row["imagem_esquerda"]
        direita = row["imagem_direita"]
        escolhida = row["escolhida"]

        if escolhida == esquerda:
            vencedor, perdedor = esquerda, direita
        else:
            vencedor, perdedor = direita, esquerda

        if vencedor in ratings and perdedor in ratings:
            atualizar_elo(ratings, vencedor, perdedor)

    return sorted(ratings.items(), key=lambda x: x[1], reverse=True)

def mostrar_ranking_com_imagem():
    st.subheader("🏁 Top 10")
    for i, (img, pts) in enumerate(ranking()[:10], 1):
        c1, c2, c3 = st.columns([0.7, 1.1, 2])

        with c1:
            st.markdown(f"**{i}º**")

        with c2:
            st.image(img, width=70)

        with c3:
            st.markdown(f"**{os.path.splitext(os.path.basename(img))[0]}**")
            st.caption(f"{round(pts)} pts")

def mostrar_resumo_admin():
    df = carregar_votos()
    st.subheader("📊 Resumo por blusa")

    if df.empty:
        st.info("Ainda não há votos salvos.")
        return

    ratings = {img: 1000.0 for img in imagens}
    aparicoes = {img: 0 for img in imagens}
    vitorias = {img: 0 for img in imagens}

    for _, row in df.iterrows():
        esquerda = row["imagem_esquerda"]
        direita = row["imagem_direita"]
        escolhida = row["escolhida"]

        if esquerda in aparicoes:
            aparicoes[esquerda] += 1
        if direita in aparicoes:
            aparicoes[direita] += 1
        if escolhida in vitorias:
            vitorias[escolhida] += 1

        if escolhida == esquerda:
            vencedor, perdedor = esquerda, direita
        else:
            vencedor, perdedor = direita, esquerda

        if vencedor in ratings and perdedor in ratings:
            atualizar_elo(ratings, vencedor, perdedor)

    resumo = []
    for img in imagens:
        ap = aparicoes.get(img, 0)
        vt = vitorias.get(img, 0)
        taxa = (vt / ap * 100) if ap > 0 else 0
        resumo.append({
            "imagem": os.path.splitext(os.path.basename(img))[0],
            "aparições": ap,
            "vitórias": vt,
            "taxa_vitória_%": round(taxa, 1),
            "elo": round(ratings[img])
        })

    resumo_df = pd.DataFrame(resumo).sort_values(by="elo", ascending=False)
    st.dataframe(resumo_df, use_container_width=True, hide_index=True)

def gerar_pares():
    temp = imagens[:]
    random.shuffle(temp)
    return [(temp[i], temp[i+1]) for i in range(0, len(temp), 2)]

def painel_admin():
    with st.sidebar:
        senha = st.text_input("Senha admin", type="password")
        if senha == ADMIN_PASSWORD:
            st.session_state.admin = True

if "admin" not in st.session_state:
    st.session_state.admin = False

painel_admin()
garantir_csv()

if "id" not in st.session_state:
    st.session_state.id = str(uuid.uuid4())[:8]

if "rodada" not in st.session_state:
    st.session_state.rodada = 1

if "indice" not in st.session_state:
    st.session_state.indice = 0

if "pares" not in st.session_state:
    st.session_state.pares = gerar_pares()

if "fim" not in st.session_state:
    st.session_state.fim = False

if st.session_state.fim:
    st.success("Muito obrigado por nos ajudar ❤️")
    st.markdown(
        """
        Deus te abençoe imensamente ❤️  
        Sua ajuda foi muito importante para nós.  
        """
    )

    with st.expander("Ver ranking final"):
        mostrar_ranking_com_imagem()

    if st.session_state.admin:
        with st.expander("Ver resumo por blusa"):
            mostrar_resumo_admin()

    st.stop()

st.progress(st.session_state.indice / ESCOLHAS_POR_RODADA)

if st.session_state.indice >= ESCOLHAS_POR_RODADA:
    st.success(f"Rodada {st.session_state.rodada} concluída ✅")
    st.info(
        "Se quiser continuar, melhor ainda para a gente ❤️ "
        "Mas, se já estiver cansado(a), pode finalizar tranquilo(a), porque você já nos ajudou muito."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Finalizar pesquisa"):
            st.session_state.fim = True
            st.rerun()

    with col2:
        if st.button("Continuar para mais 1 rodada"):
            st.session_state.rodada += 1
            st.session_state.indice = 0
            st.session_state.pares = gerar_pares()
            st.rerun()

    with st.expander("Ver ranking atual"):
        mostrar_ranking_com_imagem()

    if st.session_state.admin:
        with st.expander("Ver resumo por blusa"):
            mostrar_resumo_admin()

    st.stop()

img1, img2 = st.session_state.pares[st.session_state.indice]

st.image(img1, width=320)
if st.button("Escolho essa", key=f"b1_{st.session_state.rodada}_{st.session_state.indice}", use_container_width=True):
    registrar_voto(
        st.session_state.id,
        st.session_state.rodada,
        st.session_state.indice + 1,
        img1,
        img2,
        img1
    )
    st.session_state.indice += 1
    st.rerun()

st.write("")

st.image(img2, width=320)
if st.button("Escolho essa", key=f"b2_{st.session_state.rodada}_{st.session_state.indice}", use_container_width=True):
    registrar_voto(
        st.session_state.id,
        st.session_state.rodada,
        st.session_state.indice + 1,
        img1,
        img2,
        img2
    )
    st.session_state.indice += 1
    st.rerun()

with st.expander("Ver ranking atual"):
    mostrar_ranking_com_imagem()

if st.session_state.admin:
    with st.expander("Ver resumo por blusa"):
        mostrar_resumo_admin()