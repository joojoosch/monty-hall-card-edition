import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime

# Optional: PyGithub (for saving to GitHub)
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

# Make the cards look bigger and clickable
st.markdown("""
<style>
button[kind="secondary"] {
    height: 12rem !important;
    width: 100% !important;
    font-size: 12rem !important;
    border: none !important;
    background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Card Game Experiment")
st.write("""
Instructions: Your goal is to find the card with the trophy 🏆. To start, choose a card. Afterwards, a losing card is revealed.  
You can then either stick with the card you just chose or switch to the other one that is still upside down. The winning card is then revealed.
""")

# --- Ask player for their name once ---
player_name = st.text_input("Enter your name to start:", key="player_name")
if not player_name:
    st.stop()

# --- Initialize session state variables ---
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

# --- Reset the game ---
if st.button("🔄 Reset Game"):
    st.session_state.cards = ["🂠"] * 3
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.first_choice = None
    st.session_state.monty_flipped = None
    st.session_state.second_choice = None
    st.session_state.phase = "pick_first"
    st.session_state.game_over = False
    st.success("Game reset. Pick a card to start again!")

# --- Helper: display big card emoji ---
def display_card(emoji):
    return f"<h1 style='text-align:center; font-size:12rem; margin:0'>{emoji}</h1>"

# --- Display cards in three columns ---
cols = st.columns(3)
for i, col in enumerate(cols):
    # Decide which emoji to show
    if st.session_state.phase == "reveal_all" or st.session_state.game_over:
        emoji = "🏆" if i == st.session_state.trophy_pos else "❌"
    elif st.session_state.phase == "pick_second" and i == st.session_state.monty_flipped:
        emoji = "❌"
    else:
        emoji = "🂠"

    # Render the emoji
    col.markdown(display_card(emoji), unsafe_allow_html=True)

    # Make card clickable
    if col.button(" ", key=f"btn_{i}"):
        if st.session_state.phase == "pick_first":
            st.session_state.first_choice = i
            st.session_state.phase = "reveal_monty"
            st.write("Monty is thinking...")
            time.sleep(1.5)
            losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
            st.session_state.monty_flipped = random.choice(losing_cards)
            st.session_state.phase = "pick_second"

        elif st.session_state.phase == "pick_second" and i != st.session_state.monty_flipped:
            st.session_state.second_choice = i
            st.session_state.phase = "reveal_all"
            st.session_state.game_over = True

            won = st.session_state.second_choice == st.session_state.trophy_pos
            new_row = {
                "first_choice": st.session_state.first_choice,
                "monty_flipped": st.session_state.monty_flipped,
                "second_choice": st.session_state.second_choice,
                "won": won
            }
            st.session_state.log_df = pd.concat(
                [st.session_state.log_df, pd.DataFrame([new_row])],
                ignore_index=True
            )

# --- Show final result ---
if st.session_state.game_over:
    st.write("### Result:")
    first = st.session_state.first_choice
    second = st.session_state.second_choice
    trophy = st.session_state.trophy_pos

    if second == trophy:
        st.success("🎉 You won the 🏆 trophy!")
        st.balloons()
    else:
        st.error("❌ You picked a losing card.")
        if first == trophy:
            st.info("💡 You should have **stayed** to win.")
        else:
            st.info("💡 You should have **switched** to win.")

# --- Show session log ---
st.write("### Your Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)


if st.button("💾 Save My Results"):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("joojoosch/monty-hall-card-edition")

        csv_data = st.session_state.log_df.to_csv(index=False)
        path = f"player_logs/{player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        repo.create_file(path, f"Add results for {player_name}", csv_data)
        st.success(f"✅ Results saved to GitHub as `{path}`")

    except Exception as e:
        st.error(f"⚠️ Couldn't save: {e}")
