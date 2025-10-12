import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
from github import Github

st.set_page_config(page_title="Monty Hall Experiment", page_icon="🏆", layout="wide")

max_experiment_rounds = 20

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

# --- Reset game function ---
def reset_game():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.monty_flipped = None
    st.session_state.second_choice = None
    st.session_state.phase = "pick_first"
    st.session_state.game_over = False

# --- Instructions and name input ---
if st.session_state.trial_mode is None:
    st.title("🏆 Monty Hall Experiment")
    st.write("""
Your goal is to find the card with the trophy 🏆.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your choice or switch the card.  
The winning trophy card is then revealed!
""")

if st.session_state.player_name is None:
    name_input = st.text_input("Enter your first and last name:", key="name_input")
    if st.button("✅ Confirm Name"):
        if name_input.strip() != "":
            st.session_state.player_name = name_input.strip()
            st.rerun()
        else:
            st.warning("Please enter a valid name.")
    st.stop()

player_name = st.session_state.player_name

# --- Trial or experiment selection ---
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

# --- Trial sidebar control ---
if st.session_state.trial_mode and st.session_state.phase != "pick_first":
    with st.sidebar:
        st.subheader("Trial Runs Control")
        if st.button("Stop trials and start real experiment"):
            st.session_state.trial_mode = False
            st.session_state.experiment_rounds = 0
            reset_game()
            st.success("Real experiment started!")
            st.rerun()

# --- Display results above cards ---
if st.session_state.game_over:
    won = st.session_state.second_choice == st.session_state.trophy_pos
    st.subheader("Result:")
    if won:
        st.success("🎉 You won the 🏆 trophy!")
        st.balloons()
    else:
        st.error("❌ You picked a losing card. 😢")
        first = st.session_state.first_choice
        trophy = st.session_state.trophy_pos
        if first == trophy:
            st.info("💡 You should have stayed to win.")
        else:
            st.info("💡 You should have switched to win.")

# --- Display cards ---
if st.session_state.experiment_rounds < max_experiment_rounds or phase_type == 0:
    cols = st.columns(3)
    for i, col in enumerate(cols):
        if st.session_state.game_over:
            emoji = "🏆" if i==st.session_state.trophy_pos else "❌"
        elif st.session_state.phase=="pick_second" and i==st.session_state.monty_flipped:
            emoji = "❌"
        else:
            emoji = "🂠"

        col.markdown(f"<h1 style='font-size:14rem; text-align:center'>{emoji}</h1>", unsafe_allow_html=True)

        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            # --- First pick ---
            if st.session_state.phase=="pick_first":
                st.session_state.first_choice = i
                st.session_state.phase="reveal_monty"
                st.write("The card is being revealed...")
                time.sleep(1.5)
                losing_cards = [j for j in range(3) if j!=i and j!=st.session_state.trophy_pos]
                st.session_state.monty_flipped = random.choice(losing_cards)
                st.session_state.phase="pick_second"

            # --- Second pick ---
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

                # --- Wait 3 seconds then reset ---
                time.sleep(3)
                if phase_type == 0:
                    reset_game()  # trial continues
                else:
                    st.session_state.experiment_rounds += 1
                    if st.session_state.experiment_rounds < max_experiment_rounds:
                        reset_game()
                    else:
                        # End of experiment
                        st.subheader("✅ You have finished the experiment!")
                        total_correct = st.session_state.log_df[st.session_state.log_df["phase_type"]==1]["won"].sum()
                        total_wrong = max_experiment_rounds - total_correct
                        st.write(f"Correct picks: {total_correct}")
                        st.write(f"Wrong picks: {total_wrong}")
                        # Save CSV to GitHub
                        try:
                            token = st.secrets["GITHUB_TOKEN"]
                            g = Github(token)
                            repo = g.get_repo("joojoosch/monty-hall-card-edition")
                            csv_data = st.session_state.log_df.to_csv(index=False)
                            path = f"player_logs/{player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            repo.create_file(path, f"Add results for {player_name}", csv_data)
                            st.success(f"Results saved to GitHub as {path}")
                        except Exception as e:
                            st.error(f"⚠️ Couldn't save: {e}")


