import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

st.title("🏆 Card Game Experiment")
st.write("""
Your goal is to find the card with the trophy 🏆.

1️⃣ Choose a card.  
2️⃣ Monty will reveal a losing card.  
3️⃣ Choose again — either stay or switch.  
The winning card is then revealed!
""")

# --- Ask for player name once ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None

if not st.session_state.player_name:
    name_input = st.text_input("Enter your name to start:", key="name_input")
    if st.button("✅ Confirm Name"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.rerun()
        else:
            st.warning("Please enter a valid name.")
else:
    player_name = st.session_state.player_name
    st.success(f"Welcome, **{player_name}**! 🎮")
    st.write("Pick a card to start!")

# Stop execution until a name is entered
if not st.session_state.player_name:
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

# --- Display cards ---
cols = st.columns(3)
for i, col in enumerate(cols):
    # Determine which emoji to show
    if st.session_state.phase == "reveal_all" or st.session_state.game_over:
        emoji = "🏆" if i == st.session_state.trophy_pos else "❌"
    elif st.session_state.phase == "pick_second" and i == st.session_state.monty_flipped:
        emoji = "❌"
    else:
        emoji = "🂠"

    # Big clickable button for the card
    if col.button(emoji, key=f"card_{i}", use_container_width=True):
        # --- First pick ---
        if st.session_state.phase == "pick_first":
            st.session_state.first_choice = i
            st.session_state.phase = "reveal_monty"
            st.toast("Monty is thinking... 🤔")
            time.sleep(1.5)

            # Reveal one losing card
            losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
            st.session_state.monty_flipped = random.choice(losing_cards)
            st.session_state.phase = "pick_second"

        # --- Second pick ---
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

# --- Show results ---
if st.session_state.game_over:
    st.divider()
    st.subheader("Result:")
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

# --- Show log ---
st.divider()
st.subheader("📊 Your Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)

# --- Save to GitHub ---
st.divider()
st.subheader("💾 Save Results to GitHub")
if st.button("💾 Save My Results"):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("joojoosch/monty-hall-card-edition")

        csv_data = st.session_state.log_df.to_csv(index=False)
        path = f"player_logs/{st.session_state.player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        repo.create_file(path, f"Add results for {player_name}", csv_data)
        st.success(f"✅ Results saved to GitHub as `{path}`")

    except Exception as e:
        st.error(f"⚠️ Couldn't save: {e}")

