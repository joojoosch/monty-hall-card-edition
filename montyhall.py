import streamlit as st
import random
import time

st.set_page_config(page_title="Monty Hall - Big Cards", page_icon="🏆", layout="wide")

st.title("🏆 Monty Hall Problem — Huge Interactive Cards")
st.write("""
Click on a card to make your first choice. Monty will then reveal a losing card.  
After that, click the card you want to keep — either stay with your first pick or switch to the remaining card.  
The cards are huge and almost fill the screen!
""")

# --- Initialize session state ---
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠", "🂠", "🂠"]  # face-down
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0, 2)
if "first_choice" not in st.session_state:
    st.session_state.first_choice = None
if "monty_flipped" not in st.session_state:
    st.session_state.monty_flipped = None
if "second_choice" not in st.session_state:
    st.session_state.second_choice = None
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "phase" not in st.session_state:
    st.session_state.phase = "pick_first"  # pick_first → reveal_monty → pick_second → reveal_all

# --- Reset ---
if st.button("Reset Game"):
    st.session_state.cards = ["🂠", "🂠", "🂠"]
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.first_choice = None
    st.session_state.monty_flipped = None
    st.session_state.second_choice = None
    st.session_state.game_over = False
    st.session_state.phase = "pick_first"

# --- Helper function to display huge cards ---
def display_card(emoji):
    return f"<h1 style='font-size:12rem; text-align:center'>{emoji}</h1>"

# --- Game Phases ---
cols = st.columns(3)
for i in range(3):
    card_display = st.session_state.cards[i]
    if st.session_state.game_over:
        card_display = "🏆" if i == st.session_state.trophy_pos else "❌"
    elif st.session_state.phase == "reveal_monty" and i == st.session_state.monty_flipped:
        card_display = "❌"

    with cols[i]:
        if st.button(display_card(card_display), key=f"card_{i}", unsafe_allow_html=True):
            if st.session_state.phase == "pick_first":
                st.session_state.first_choice = i
                st.session_state.phase = "reveal_monty"
                # delay for suspense
                st.write("Monty is thinking...")
                time.sleep(2)
                # Monty flips a losing card
                losing_options = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.monty_flipped = random.choice(losing_options)
                st.session_state.cards[st.session_state.monty_flipped] = "❌"
                st.session_state.phase = "pick_second"

            elif st.session_state.phase == "pick_second":
                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True

# --- Reveal results ---
if st.session_state.game_over:
    st.write("### Result:")
    cols = st.columns(3)
    for i in range(3):
        final_emoji = "🏆" if i == st.session_state.trophy_pos else "❌"
        with cols[i]:
            st.markdown(display_card(final_emoji), unsafe_allow_html=True)
    if st.session_state.second_choice == st.session_state.trophy_pos:
        st.success("🎉 You won the 🏆 trophy!")
        st.balloons()
    else:
        st.error("❌ You picked a losing card.")
