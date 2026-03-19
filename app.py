import streamlit as st
import pandas as pd

st.title("Iowa Electricity Explorer")

# ── Load data ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path_or_buffer):
    df = pd.read_csv(path_or_buffer)
    df["year"] = pd.to_datetime(df["year"]).dt.year
    return df

uploaded = st.file_uploader("Upload a dataset (optional)", type="csv")
df = load_data(uploaded) if uploaded else load_data("Esade_Data_Vis_S6/iowa-electricity.csv")

sources = sorted(df["source"].unique().tolist())
years   = sorted(df["year"].unique().tolist())

# ── Session state init ─────────────────────────────────────────────────────
for k, v in {
    "stage": "question",
    "user_answer": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.header("Settings")
source  = st.sidebar.selectbox("Source", sources)
year_t0 = st.sidebar.selectbox("Year X", years, index=0)
year_t1 = st.sidebar.selectbox("Year Y", years, index=len(years)-1)

# ── Helpers ────────────────────────────────────────────────────────────────
def real_answer():
    v0 = df[(df["source"] == source) & (df["year"] == year_t0)]["net_generation"].sum()
    v1 = df[(df["source"] == source) & (df["year"] == year_t1)]["net_generation"].sum()
    return v1 > v0  # True = increased

def stacked_bar():
    """Stacked bar chart with only the two selected years."""
    sub = df[df["year"].isin([year_t0, year_t1])]
    pivot = sub.pivot(index="year", columns="source", values="net_generation")
    st.bar_chart(pivot)

def two_bar_source():
    """Bar chart of selected source only, just the two years."""
    sub = df[(df["source"] == source) & (df["year"].isin([year_t0, year_t1]))]
    sub = sub.set_index("year")["net_generation"]
    st.bar_chart(sub)

def line_all():
    """Line chart of all sources, all years."""
    pivot = df.pivot(index="year", columns="source", values="net_generation")
    st.line_chart(pivot)

# ── Question ───────────────────────────────────────────────────────────────
st.subheader("Question")
st.info(f"Is there a difference in **{source}** generation between **{year_t0}** and **{year_t1}**?")

# ── STAGE: question ────────────────────────────────────────────────────────
if st.session_state.stage == "question":
    if st.button("Show chart"):
        st.session_state.stage = "chart1"
        st.rerun()

# ── STAGE: chart1 — stacked bar (two years) ────────────────────────────────
elif st.session_state.stage == "chart1":
    stacked_bar()
    st.markdown("---")
    st.write("Did this chart answer your question?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.stage = "verdict"
            st.rerun()
    with col2:
        if st.button("No, show another chart"):
            st.session_state.stage = "chart2"
            st.rerun()

# ── STAGE: chart2 — bar chart of selected source only ─────────────────────
elif st.session_state.stage == "chart2":
    two_bar_source()
    st.markdown("---")
    st.write("Did this chart answer your question?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.stage = "verdict"
            st.rerun()
    with col2:
        if st.button("No"):
            st.warning("No more charts available! Try changing the settings.")

# ── STAGE: verdict ─────────────────────────────────────────────────────────
elif st.session_state.stage == "verdict":
    st.write("### So… has it increased?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, it increased"):
            st.session_state.user_answer = True
            st.session_state.stage = "result"
            st.rerun()
    with col2:
        if st.button("No, it didn't"):
            st.session_state.user_answer = False
            st.session_state.stage = "result"
            st.rerun()

# ── STAGE: result ──────────────────────────────────────────────────────────
elif st.session_state.stage == "result":
    correct = (st.session_state.user_answer == real_answer())
    if correct:
        st.success("Correct!")
        st.balloons()
        st.markdown("---")
        st.write("Do you want to see the generation of each source across all years?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, show me!"):
                st.session_state.stage = "compare"
                st.rerun()
        with col2:
            if st.button("No, I'm done"):
                st.session_state.stage = "done"
                st.rerun()
    else:
        st.error("Not quite! Maybe this other graph helps…")
        two_bar_source()
        st.markdown("---")
        st.write("Try again:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, it increased"):
                st.session_state.user_answer = True
                st.session_state.stage = "result"
                st.rerun()
        with col2:
            if st.button("No, it didn't"):
                st.session_state.user_answer = False
                st.session_state.stage = "result"
                st.rerun()

# ── STAGE: compare ─────────────────────────────────────────────────────────
elif st.session_state.stage == "compare":
    st.subheader("All sources — all years")
    line_all()
    if st.button("Finish"):
        st.session_state.stage = "done"
        st.rerun()

# ── STAGE: done ────────────────────────────────────────────────────────────
elif st.session_state.stage == "done":
    st.success("Thanks! Hit 'Start over' to go again.")
    if st.button("Start over"):
        st.session_state.stage = "question"
        st.session_state.user_answer = None
        st.rerun()