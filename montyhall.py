import streamlit as st
import random
import time

st.set_page_config(page_title="Monty Hall - Big Cards", page_icon="🏆", layout="wide")

st.title("🏆 Monty Hall Problem — Huge Interactive Cards")

# --- Session state ---
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠"]*3
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0, 2)
if "first_choice" not in st.session_state:
    st.session_state.first_choice = None
if "monty_flipped" not in st.session_state:
    st.session_state.monty_flipped = None
if "second_choice" not in st.session_state:
    st.session_state.second_choice = None
if "phase" not in st.session_state:
    st.session_state.phase = "pick_first"
if "game_over" not in st.session_state:
    st.session_state.game_over = False

# --- Reset ---
if st.button("Reset Game"):
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.first_choice = None
    st.session_state.monty_flipped = None
    st.session_state.second_choice = None
    st.session_state.phase = "pick_first"
    st.session_state.game_over = False

# --- Display cards ---
cols = st.columns(3)
for i, col in enumerate(cols):
    emoji = st.session_state.cards[i]
    if st.session_state.phase == "reveal_monty" and i == st.session_state.monty_flipped:
        emoji = "❌"
    if st.session_state.game_over:
        emoji = "🏆" if i == st.session_state.trophy_pos else "❌"

    col.markdown(f"<h1 style='text-align:center; font-size:12rem'>{emoji}</h1>", unsafe_allow_html=True)

    # invisible button for click handling
    if col.button("Pick", key=f"btn_{i}"):
        if st.session_state.phase == "pick_first":
            st.session_state.first_choice = i
            st.session_state.phase = "reveal_monty"
            st.write("Monty is thinking...")
            time.sleep(2)
            losing_options = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
            st.session_state.monty_flipped = random.choice(losing_options)
            st.session_state.cards[st.session_state.monty_flipped] = "❌"
            st.session_state.phase = "pick_second"
        elif st.session_state.phase == "pick_second":
            st.session_state.second_choice = i
            st.session_state.game_over = True

# --- Reveal results ---
if st.session_state.game_over:
    st.write("### Result:")
    cols = st.columns(3)
    for i, col in enumerate(cols):
        final_emoji = "🏆" if i == st.session_state.trophy_pos else "❌"
        col.markdown(f"<h1 style='text-align:center; font-size:12rem'>{final_emoji}</h1>", unsafe_allow_html=True)
    if st.session_state.second_choice == st.session_state.trophy_pos:
        st.success("🎉 You won the 🏆 trophy!")
        st.balloons()
    else:
        st.error("❌ You picked a losing card.")
