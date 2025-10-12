import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

# --- Initialize session state ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "trial_mode" not in st.session_state:
    st.session_state.trial_mode = None
if "experiment_rounds" not in st.session_state:
    st.session_state.experiment_rounds = 0
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠"]*3
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0,2)
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
    st.session_state.log_df = pd.DataFrame(columns=["first_choice","monty_flipped","second_choice","won","phase_type"])

max_experiment_rounds = 20

# --- Show instructions only before starting trial/experiment ---
if st.session_state.trial_mode is None:
    st.title("🏆 Card Game Experiment")
    st.write("""
Your goal is to find the card with the trophy 🏆.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your choice or switch the card.  
The winning trophy card is then revealed!
""")

# --- Ask for name ---
if st.session_state.player_name is None:
    name_input = st.text_input("Enter your first and last name to start:", key="name_input")
    if st.button("✅ Confirm Name"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.rerun()
        else:
            st.warning("Please enter a valid name.")
    st.stop()

player_name = st.session_state.player_name

# --- Trial or Experiment selection ---
if st.session_state.trial_mode is None:
    st.write("Do you want to do trial runs first?")
    col1, col2 = st.columns(2)
    if col1.button("Yes, trial runs"):
        st.session_state.trial_mode = True
        st.rerun()
    if col2.button("No, start experiment"):
        st.session_state.trial_mode = False
        st.rerun()
    st.stop()

phase_type = 0 if st.session_state.trial_mode else 1

# --- Stop trial runs box ---
if st.session_state.trial_mode and st.session_state.phase != "pick_first":
    with st.sidebar:
        st.subheader("Trial Runs Control")
        if st.button("Stop trials and start real experiment"):
            st.session_state.trial_mode = False
            st.session_state.experiment_rounds = 0
            st.session_state.phase = "pick_first"
            st.session_state.game_over = False
            st.session_state.cards = ["🂠"]*3
            st.session_state.trophy_pos = random.randint(0,2)
            st.success("Real experiment started!")
            st.rerun()

# --- Reset game function ---
def reset_game():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.monty_flipped = None
    st.session_state.second_choice = None
    st.session_state.phase = "pick_first"
    st.session_state.game_over = False

# --- Display cards ---
cols = st.columns(3)
for i, col in enumerate(cols):
    # Determine emoji to show
    if st.session_state.phase=="reveal_all" or st.session_state.game_over:
        emoji = "🏆" if i==st.session_state.trophy_pos else "❌"
    elif st.session_state.phase=="pick_second" and i==st.session_state.monty_flipped:
        emoji = "❌"
    else:
        emoji = "🂠"

    # Show card visually
    col.markdown(f"<h1 style='font-size:14rem; text-align:center'>{emoji}</h1>", unsafe_allow_html=True)

    # Button for picking the card
    if col.button("Pick", key=f"card_{i}", use_container_width=True):
        if st.session_state.phase=="pick_first":
            st.session_state.first_choice = i
            st.session_state.phase="reveal_monty"
            st.write("The card is being revealed...")  # <-- changed message
            time.sleep(1.5)
            losing_cards = [j for j in range(3) if j!=i and j!=st.session_state.trophy_pos]
            st.session_state.monty_flipped = random.choice(losing_cards)
            st.session_state.phase="pick_second"

        elif st.session_state.phase=="pick_second" and i!=st.session_state.monty_flipped:
            st.session_state.second_choice = i
            st.session_state.phase="reveal_all"
            st.session_state.game_over = True

            won = st.session_state.second_choice==st.session_state.trophy_pos
            st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([{
                "first_choice":st.session_state.first_choice,
                "monty_flipped":st.session_state.monty_flipped,
                "second_choice":st.session_state.second_choice,
                "won":won,
                "phase_type":phase_type
            }])], ignore_index=True)

# --- Show results ---
if st.session_state.game_over:
    st.subheader("Result:")
    won = st.session_state.second_choice==st.session_state.trophy_pos
    if won:
        st.success("🎉 You won the 🏆 trophy!")
        st.balloons()
    else:
        st.error("❌ You picked a losing card. 😢")

    first = st.session_state.first_choice
    trophy = st.session_state.trophy_pos
    if not won:
        if first==trophy:
            st.info("💡 You should have stayed to win.")
        else:
            st.info("💡 You should have switched to win.")

    # Pause 3 seconds, then reset for next round
    time.sleep(3)
    reset_game()
    st.experimental_rerun()

