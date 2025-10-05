import streamlit as st
import random
import time
import pandas as pd

st.set_page_config(page_title="Monty Hall - Interactive Cards", page_icon="🏆", layout="wide")

st.title("🏆 Monty Hall Problem — Interactive Cards")
st.write("""
Click on a card to make your first choice. Monty will reveal a losing card.  
Then click the card you want to keep. The same cards flip to show the results, and you’ll see whether switching would have helped.
""")

# --- Session state ---
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠"] * 3
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
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["first_choice", "monty_flipped", "second_choice", "won"])

# --- Reset ---
if st.button("Reset Game"):
    st.session_state.cards = ["🂠"] * 3
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.first_choice = None
    st.session_state.monty_flipped = None
    st.session_state.second_choice = None
    st.session_state.phase = "pick_first"
    st.session_state.game_over = False

# --- Helper ---
def display_card(emoji):
    return f"<h1 style='text-align:center; font-size:12rem'>{emoji}</h1>"

# --- Display cards and handle clicks ---
cols = st.columns(3)
for i, col in enumerate(cols):
    # determine emoji to show
    emoji = st.session_state.cards[i]
    if st.session_state.phase == "reveal_monty" and i == st.session_state.monty_flipped:
        emoji = "❌"
    if st.session_state.phase == "reveal_all" or st.session_state.game_over:
        emoji = "🏆" if i == st.session_state.trophy_pos else "❌"

    col.markdown(display_card(emoji), unsafe_allow_html=True)

    # invisible button to pick the card
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
            st.session_state.phase = "reveal_all"
            st.session_state.game_over = True
            won = st.session_state.second_choice == st.session_state.trophy_pos
            # log play
            new_row = {
                "first_choice": st.session_state.first_choice,
                "monty_flipped": st.session_state.monty_flipped,
                "second_choice": st.session_state.second_choice,
                "won": won
            }
            st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([new_row])], ignore_index=True)

# --- Reveal results with advice ---
if st.session_state.game_over:
    st.write("### Result:")
    choice = st.session_state.second_choice
    first = st.session_state.first_choice
    trophy = st.session_state.trophy_pos
    if choice == trophy:
        st.success("🎉 You won the 🏆 trophy!")
        st.balloons()
    else:
        st.error("❌ You picked a losing card.")

    # Advice
    remaining = [i for i in range(3) if i not in [first, st.session_state.monty_flipped]][0]
    if first == trophy:
        st.info("💡 You should have **stayed** to win.")
    else:
        st.info("💡 You should have **switched** to win.")

# --- Show log ---
st.write("### Player log")
st.dataframe(st.session_state.log_df)
