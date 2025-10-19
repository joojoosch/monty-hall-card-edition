import streamlit as st
import random
import pandas as pd
from datetime import datetime
from github import Github

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

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
if "flipped_card" not in st.session_state:
    st.session_state.flipped_card = None
if "second_choice" not in st.session_state:
    st.session_state.second_choice = None
if "phase" not in st.session_state:
    st.session_state.phase = "first_pick"
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["round_number","first_choice","flipped_card","second_choice","result","phase_type"])
if "experiment_finished" not in st.session_state:
    st.session_state.experiment_finished = False
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False
if "ready_page" not in st.session_state:
    st.session_state.ready_page = False  # For ready page

# --- Reset game function ---
def reset_game():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False
    st.session_state.logged_this_round = False

# --- Instructions and name input ---
if st.session_state.trial_mode is None and not st.session_state.ready_page:
    st.title("🏆 Card Game Experiment")
    st.write("""
Instructions:
You will be shown three cards and your goal is to find the trophy 🏆 behind one of them.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your choice or switch.  
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
if st.session_state.trial_mode is None and not st.session_state.ready_page:
    st.write("Do you want to do a few trial runs first?")
    col1, col2 = st.columns(2)
    if col1.button("Yes, trial runs"):
        st.session_state.trial_mode = True
        st.rerun()
    if col2.button("No, start experiment"):
        st.session_state.ready_page = True
        st.rerun()
    st.stop()

phase_type = 0 if st.session_state.trial_mode else 1

# --- Ready page for real experiment ---
if st.session_state.ready_page:
    st.title("🚀 Are you ready for the real experiment?")
    st.write(f"You will complete {max_experiment_rounds} rounds.")
    st.write("""
Instructions (again):
1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your choice or switch.  
The winning trophy card is then revealed!
""")
    if st.button("✅ Start Real Experiment"):
        st.session_state.trial_mode = False
        st.session_state.experiment_rounds = 0
        st.session_state.ready_page = False
        reset_game()
        st.success(f"Real experiment started — {max_experiment_rounds} rounds to complete!")
        st.rerun()
    st.stop()

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

# --- Show summary if finished ---
if st.session_state.experiment_finished:
    st.title("🎉 Thank you for participating!")
    st.subheader("📊 Experiment Summary")
    total_correct = st.session_state.log_df[st.session_state.log_df["phase_type"]==1]["result"].sum()
    total_wrong = max_experiment_rounds - total_correct
    st.write(f"Correct picks: {total_correct}")
    st.write(f"Wrong picks: {total_wrong}")
    st.stop()

# --- Display header depending on phase ---
header_text = ""
if st.session_state.phase == "first_pick":
    header_text = "Pick your first card"
elif st.session_state.phase == "second_pick":
    header_text = "Pick Again (same or new card)"
elif st.session_state.phase == "reveal_all" and not st.session_state.trial_mode:
    header_text = f"Round {st.session_state.experiment_rounds + 1}: Reveal"

# Add round number for real experiment
if not st.session_state.trial_mode and st.session_state.phase != "reveal_all":
    header_text = f"Round {st.session_state.experiment_rounds + 1}: {header_text}"

if header_text:
    st.header(header_text)

# --- Display cards ---
if not st.session_state.experiment_finished and (st.session_state.experiment_rounds < max_experiment_rounds or phase_type == 0):
    cols = st.columns(3)
    emojis = get_card_emojis()
    for i, col in enumerate(cols):
        # Add red border if this is the revealed losing card
        border_style = ""
        if st.session_state.phase == "second_pick" and i == st.session_state.flipped_card:
            border_style = "border: 5px solid red; border-radius:10px;"
        col.markdown(
            f"<h1 style='font-size:8rem; text-align:center; {border_style}'>{emojis[i]}</h1>",
            unsafe_allow_html=True
        )
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.rerun()
            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.rerun()

# --- Display results and control buttons ---
if st.session_state.game_over:
    st.header("Result:")
    won = st.session_state.second_choice == st.session_state.trophy_pos
    stayed = st.session_state.first_choice == st.session_state.second_choice

    if won:
        if stayed:
            st.success("🎉 You won the 🏆 trophy because you stayed with your first choice!")
        else:
            st.success("🎉 You won the 🏆 trophy because you switched!")
    else:
        st.error("❌ You picked the wrong card. 😢")
        first = st.session_state.first_choice
        trophy = st.session_state.trophy_pos
        if first == trophy:
            st.info("💡 You should have stayed to win.")
        else:
            st.info("💡 You should have switched to win.")

    # Log round only once
    if not st.session_state.logged_this_round:
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
        st.session_state.logged_this_round = True

    col1, col2 = st.columns(2)
    if not st.session_state.trial_mode and st.session_state.experiment_rounds + 1 >= max_experiment_rounds:
        with col1:
            if st.button("📊 Show Summary"):
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
                st.session_state.experiment_finished = True
                st.rerun()
    else:
        next_button_label = "Next Round" if not st.session_state.trial_mode else "🔄 Again"
        with col1:
            if st.button(next_button_label):
                st.session_state.logged_this_round = False
                if phase_type == 0:
                    reset_game()
                else:
                    st.session_state.experiment_rounds += 1
                    if st.session_state.experiment_rounds < max_experiment_rounds:
                        reset_game()
                st.rerun()
        if st.session_state.trial_mode:
            with col2:
                if st.button("🚀 Ready for Real Experiment"):
                    st.session_state.ready_page = True
                    st.rerun()

# --- Show game log ---
st.divider()
st.subheader("📊 Game Log")
st.dataframe(st.session_state.log_df, use_container_width=True)

