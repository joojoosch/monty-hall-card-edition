import streamlit as st #for the app
import random #for the random selection of the winning card
import time 
import pandas as pd #for the dataframes
from datetime import datetime #for the filenames
from github import Github # for getting the csv to my github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

max_experiment_rounds = 20

# --- Initializing all the session states ---
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "trial_mode" not in st.session_state:
    st.session_state.trial_mode = None #TRUE for trial mode and FALSE for real experiment
if "experiment_rounds" not in st.session_state:
    st.session_state.experiment_rounds = 0 #completed experiment rounds
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠"]*3
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0,2) #position of the winning card
if "first_choice" not in st.session_state:
    st.session_state.first_choice = None
if "flipped_card" not in st.session_state:
    st.session_state.flipped_card = None
if "second_choice" not in st.session_state:
    st.session_state.second_choice = None
if "phase" not in st.session_state:
    st.session_state.phase = "first_pick" #first_pick, second_pick, reveal_all
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["round_number","first_choice","flipped_card","second_choice","result","phase_type"])

# --- Reset game function ---
def reset_game():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False

# --- Instructions and name input ---
if st.session_state.trial_mode is None: #only shows this if you are neither in trial nor test mode
    st.title("🏆 Card Game Experiment")
    st.write("""
Instructions:
You will be shown three cards and your goal is to find the card with the trophy 🏆 behind it.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will then be revealed.  
3️⃣ Choose to stick with your choice or switch to the other card.  
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
    st.write("Do you want to do a few trial runs first?")
    col1, col2 = st.columns(2)
    if col1.button("Yes, trial runs"):
        st.session_state.trial_mode = True
        st.rerun()
    if col2.button("No, start experiment"):
        st.session_state.trial_mode = False
        st.rerun()
    st.stop()

phase_type = 0 if st.session_state.trial_mode else 1 #0 equals trials

# --- Trial sidebar control ---
if st.session_state.trial_mode and st.session_state.phase == "first_pick":
    with st.sidebar:
        st.subheader("Trial Runs Control")
        if st.button("Stop trials and start real experiment"):
            st.session_state.trial_mode = False
            st.session_state.experiment_rounds = 0
            reset_game()
            st.success("Real experiment started you have 20 rounds to complete!")
            st.rerun()

# --- Determine emojis for each card ---
def get_card_emojis():
    emojis = []
    for i in range(3):
        if st.session_state.phase == "reveal_all" or st.session_state.game_over:
            emojis.append("🏆" if i == st.session_state.trophy_pos else "❌")
        elif st.session_state.phase == "second_pick":
            emojis.append("❌" if i == st.session_state.flipped_card else "🂠")
        else:
            emojis.append("🂠")
    return emojis



# --- Display cards ---
if st.session_state.experiment_rounds < max_experiment_rounds or phase_type == 0:
    cols = st.columns(3)
    emojis = get_card_emojis()
    for i, col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:14rem; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            # --- First pick ---
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                time.sleep(1.5)
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.rerun()
            # --- Second pick ---
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.rerun()  
            # --- Reveal all ---   
            elif st.session_state.phase == "reveal_all":
                st.session_state.game_over = True
            
                # --- Display results above cards ---
        if st.session_state.game_over:
            won = st.session_state.second_choice == st.session_state.trophy_pos
            st.subheader("Result:")
            if won:
                st.success("🎉 You won the 🏆 trophy!")
                st.balloons()
            else:
                st.error("❌ You picked the wrong card. 😢")
                first = st.session_state.first_choice
                trophy = st.session_state.trophy_pos
                if first == trophy:
                    st.info("💡 You should have stayed to win.")
                else:
                    st.info("💡 You should have switched to win.")

                # --- Log the round ---
                won = st.session_state.second_choice == st.session_state.trophy_pos
                round_number = len(st.session_state.log_df[st.session_state.log_df["phase_type"]==phase_type]) + 1
                new_row = pd.DataFrame([{
                    "round_number": round_number,
                    "first_choice": st.session_state.first_choice,
                    "flipped_card": st.session_state.flipped_card,
                    "second_choice": st.session_state.second_choice,
                    "result": won,
                    "phase_type": phase_type
                }])
                st.session_state.log_df = pd.concat([st.session_state.log_df, new_row], ignore_index=True)

                # --- Wait 3 seconds then reset ---
                time.sleep(3)
                if phase_type == 0:
                    reset_game()
                    st.rerun()
                else:
                    st.session_state.experiment_rounds += 1
                    if st.session_state.experiment_rounds < max_experiment_rounds:
                        reset_game()
                        st.rerun()
                    else:
                        st.subheader("✅ You have finished the experiment!")
                        total_correct = st.session_state.log_df[st.session_state.log_df["phase_type"]==1]["result"].sum()
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



# --- Show game log ---
st.divider()
st.subheader("📊 Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)
