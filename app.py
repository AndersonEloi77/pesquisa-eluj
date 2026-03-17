import streamlit as st
import random
import csv
import os
import uuid
from datetime import datetime
from collections import defaultdict

import pandas as pd

st.set_page_config(page_title="Pesquisa Eluj", layout="wide")

st.title("Pesquisa Eluj 👕")
st.write("Qual dessas você compraria?")

# =========================
# CONFIGURAÇÕES
# =========================
CSV_PATH = "votos.csv"
ADMIN_PASSWORD = "sinhoeloi13"  # troque pela senha que você quiser

imagens = [f"imagens/img{i}.JPG" for i in range(1, 21)]

QTD_BLUSAS = len(imagens)
ESCOLHAS_POR_RODADA = QTD_BLUSAS // 2  # 20 / 2 = 10
RODADAS_OBRIGATORIAS = 1
MAX_TENTATIVAS_PARES = 200

# =========================
# FUNÇÕES CSV
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

def registrar_voto(participante_id, rodada_numero, escolha_na_rodada, esquerda, direita, escolhida):
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            participante_id,
            rodada_numero,
            escolha_na_rodada,
            esquerda,
            direita,
            escolhida
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

# =========================
# FUNÇÕES RANKING
# =========================
def atualizar_elo_dict(ratings, vencedor, perdedor, k=32):
    rating_v = ratings[vencedor]
    rating_p = ratings[perdedor]

    esperado_v = 1 / (1 + 10 ** ((rating_p - rating_v) / 400))
    esperado_p = 1 / (1 + 10 ** ((rating_v - rating_p) / 400))

    ratings[vencedor] += k * (1 - esperado_v)
    ratings[perdedor] += k * (0 - esperado_p)

def reconstruir_ranking_global():
    ratings = {img: 1000.0 for img in imagens}
    aparicoes = {img: 0 for img in imagens}
    vitorias = {img: 0 for img in imagens}

    df = carregar_votos()
    if df.empty:
        return ratings, aparicoes, vitorias, df

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
            atualizar_elo_dict(ratings, vencedor, perdedor)

    return ratings, aparicoes, vitorias, df

# =========================
# FUNÇÕES RODADA
# =========================
def gerar_pares_rodada():
    historico_pares = st.session_state.historico_pares_sessao
    melhor_pares = None
    melhor_repeticao = None

    for _ in range(MAX_TENTATIVAS_PARES):
        embaralhadas = imagens[:]
        random.shuffle(embaralhadas)
        pares = [(embaralhadas[i], embaralhadas[i + 1]) for i in range(0, len(embaralhadas), 2)]

        repeticoes = 0
        for a, b in pares:
            par_key = frozenset([a, b])
            repeticoes += historico_pares.get(par_key, 0)

        if melhor_repeticao is None or repeticoes < melhor_repeticao:
            melhor_repeticao = repeticoes
            melhor_pares = pares

        if repeticoes == 0:
            break

    return melhor_pares

def iniciar_nova_rodada():
    st.session_state.rodada_numero += 1
    st.session_state.pares_rodada = gerar_pares_rodada()
    st.session_state.indice_par_atual = 0

def obter_par_atual():
    return st.session_state.pares_rodada[st.session_state.indice_par_atual]

def concluir_voto(escolhida, esquerda, direita):
    escolha_na_rodada = st.session_state.indice_par_atual + 1

    registrar_voto(
        participante_id=st.session_state.participante_id,
        rodada_numero=st.session_state.rodada_numero,
        escolha_na_rodada=escolha_na_rodada,
        esquerda=esquerda,
        direita=direita,
        escolhida=escolhida
    )

    par_key = frozenset([esquerda, direita])
    st.session_state.historico_pares_sessao[par_key] += 1
    st.session_state.indice_par_atual += 1

# =========================
# FUNÇÕES EXIBIÇÃO
# =========================
def nome_curto(caminho):
    return os.path.splitext(os.path.basename(caminho))[0]

def mostrar_top10_com_imagem():
    ratings, _, _, _ = reconstruir_ranking_global()
    ranking = sorted(ratings.items(), key=lambda x: x[1], reverse=True)[:10]

    st.subheader("🏁 Top 10")

    for pos, (img, pts) in enumerate(ranking, start=1):
        c1, c2, c3 = st.columns([0.7, 1.2, 1.6])

        with c1:
            st.markdown(f"**{pos}º**")

        with c2:
            st.image(img, width=70)

        with c3:
            st.markdown(f"**{nome_curto(img)}**")
            st.caption(f"{round(pts)} pts")

def mostrar_resumo_admin():
    ratings, aparicoes, vitorias, df = reconstruir_ranking_global()

    st.subheader("📊 Resumo por blusa")

    if df.empty:
        st.info("Ainda não há votos salvos no CSV.")
        return

    st.write(f"Total de votos registrados: **{len(df)}**")
    st.write(f"Participantes únicos: **{df['participante_id'].nunique()}**")

    resumo = []
    for img in imagens:
        ap = aparicoes.get(img, 0)
        vt = vitorias.get(img, 0)
        taxa = (vt / ap * 100) if ap > 0 else 0
        resumo.append({
            "imagem": nome_curto(img),
            "aparições": ap,
            "vitórias": vt,
            "taxa_vitória_%": round(taxa, 1),
            "elo": round(ratings[img])
        })

    resumo_df = pd.DataFrame(resumo).sort_values(by="elo", ascending=False)
    st.dataframe(resumo_df, width="stretch", hide_index=True)

# =========================
# ADMIN
# =========================
def painel_admin():
    with st.sidebar:
        st.markdown("### Área administrativa")
        senha = st.text_input("Senha", type="password")

        if senha == ADMIN_PASSWORD:
            st.success("Modo administrador ativado")
            st.session_state.admin_ok = True
        elif senha:
            st.error("Senha incorreta")
            st.session_state.admin_ok = False

if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

painel_admin()

# =========================
# INICIALIZAÇÃO
# =========================
garantir_csv()

if "participante_id" not in st.session_state:
    st.session_state.participante_id = str(uuid.uuid4())[:8]

if "rodada_numero" not in st.session_state:
    st.session_state.rodada_numero = 0

if "pares_rodada" not in st.session_state:
    st.session_state.pares_rodada = []

if "indice_par_atual" not in st.session_state:
    st.session_state.indice_par_atual = 0

if "historico_pares_sessao" not in st.session_state:
    st.session_state.historico_pares_sessao = defaultdict(int)

if "finalizado" not in st.session_state:
    st.session_state.finalizado = False

if st.session_state.rodada_numero == 0:
    iniciar_nova_rodada()

# =========================
# FINALIZADO
# =========================
if st.session_state.finalizado:
    st.success("Pesquisa finalizada. Muito obrigado por nos ajudar ❤️")

    col_main, col_rank = st.columns([3, 1])

    with col_main:
        st.markdown(
            """
            Deus te abençoe imensamente, varão/varoa ❤️  
            Sua ajuda foi muito importante para nós.  
            Cada resposta faz diferença na escolha das próximas peças.
            """
        )

        if st.session_state.admin_ok:
            with st.expander("Ver resumo por blusa"):
                mostrar_resumo_admin()

    with col_rank:
        mostrar_top10_com_imagem()

    st.stop()

# =========================
# LAYOUT PRINCIPAL
# =========================
col_main, col_rank = st.columns([3, 1], gap="medium")

with col_rank:
    mostrar_top10_com_imagem()

with col_main:
    st.markdown(
        f"**Rodada atual:** {st.session_state.rodada_numero}  \n"
        f"**Escolha:** {min(st.session_state.indice_par_atual + 1, ESCOLHAS_POR_RODADA)} de {ESCOLHAS_POR_RODADA}"
    )

    progresso = st.session_state.indice_par_atual / ESCOLHAS_POR_RODADA
    st.progress(progresso)

    if st.session_state.indice_par_atual >= ESCOLHAS_POR_RODADA:
        st.success(f"Rodada {st.session_state.rodada_numero} concluída ✅")

        if st.session_state.rodada_numero >= RODADAS_OBRIGATORIAS:
            st.info(
                "Deus te abençoe imensamente, varão/varoa ❤️ "
                "Agora você pode finalizar ou seguir para mais uma rodada de 10 escolhas. "
                "Quanto mais respostas, melhor para a gente. "
                "Mas não queremos que fique entediado, então não se sinta obrigado a continuar. "
                "Pode finalizar tranquilo, porque você já nos ajudou muito ❤️"
            )

            c1, c2 = st.columns(2)

            with c1:
                if st.button("Finalizar pesquisa"):
                    st.session_state.finalizado = True
                    st.rerun()

            with c2:
                if st.button("Continuar para mais 1 rodada (10 escolhas)"):
                    iniciar_nova_rodada()
                    st.rerun()
        else:
            if st.button("Iniciar próxima rodada"):
                iniciar_nova_rodada()
                st.rerun()

        if st.session_state.admin_ok:
            with st.expander("Ver resumo por blusa"):
                mostrar_resumo_admin()

        st.stop()

    img1, img2 = obter_par_atual()

    col_esq, col_dir = st.columns(2, gap="small")

    with col_esq:
        st.image(img1, width="stretch")
        st.caption(nome_curto(img1))
        if st.button(
            "Escolho essa",
            key=f"btn_left_{st.session_state.rodada_numero}_{st.session_state.indice_par_atual}"
        ):
            concluir_voto(img1, img1, img2)
            st.rerun()

    with col_dir:
        st.image(img2, width="stretch")
        st.caption(nome_curto(img2))
        if st.button(
            "Escolho essa",
            key=f"btn_right_{st.session_state.rodada_numero}_{st.session_state.indice_par_atual}"
        ):
            concluir_voto(img2, img1, img2)
            st.rerun()

    if st.session_state.admin_ok:
        with st.expander("Ver resumo por blusa"):
            mostrar_resumo_admin()
