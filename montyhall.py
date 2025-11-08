import streamlit as st
import random
import pandas as pd
from datetime import datetime
from github import Github
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Card Game Experiment", page_icon="🏆", layout="wide")

# ---------------- Constants ----------------
TRIALS_REQUIRED = 10
TRIALS_PER_ROUND = 3

# ---------------- Session state ----------------
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "email" not in st.session_state:
    st.session_state.email = ""
if "page" not in st.session_state:
    st.session_state.page = "instructions"
if "trial_runs_done" not in st.session_state:
    st.session_state.trial_runs_done = 0
if "trial_log" not in st.session_state:
    st.session_state.trial_log = pd.DataFrame(columns=[
        "trial_number","first_choice","flipped_card","second_choice",
        "trophy_card","result","switch_win","stay_win","email"
    ])
if "experiment_round" not in st.session_state:
    st.session_state.experiment_round = 0
if "current_round_set" not in st.session_state:
    st.session_state.current_round_set = 1
if "experiment_log" not in st.session_state:
    st.session_state.experiment_log = pd.DataFrame(columns=[
        "round_number","first_choice","flipped_card","second_choice",
        "trophy_card","result","phase_type","points_after_round",
        "switch_win","stay_win","email"
    ])
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠"] * 3
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0, 2)
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
if "points" not in st.session_state:
    st.session_state.points = 50
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False

# ---------------- Helper functions ----------------
def reset_game_state():
    st.session_state.cards = ["🂠"]*3
    st.session_state.trophy_pos = random.randint(0,2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False
    st.session_state.logged_this_round = False

def card_emojis():
    em = []
    for i in range(3):
        if st.session_state.phase=="reveal_all" or st.session_state.game_over:
            em.append("🏆" if i==st.session_state.trophy_pos else "❌")
        elif st.session_state.phase=="second_pick":
            em.append("❌" if i==st.session_state.flipped_card else "🂠")
        else:
            em.append("🂠")
    return em

def compute_switch_stay(first, second, trophy):
    if second == trophy:
        if first==second:
            return 0,1
        else:
            return 1,0
    return 0,0

# ---------------- Pages ----------------
# Page 1: Instructions + Name input
if st.session_state.page=="instructions":
    reset_game_state()
    st.title("🏆 Card Game Experiment")
    st.write("""You will be shown three cards. Goal: find the trophy 🏆 behind one of them.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your first choice or switch.  
The winning trophy card is then revealed!""")
    name_input = st.text_input("Enter your first and last name:", value=st.session_state.player_name or "")
    email_input = st.text_input("(Optional) Email for prize:", value=st.session_state.email or "")
    if st.button("✅ Confirm Name and Continue"):
        if name_input.strip()=="":
            st.warning("Enter valid name.")
        else:
            st.session_state.player_name=name_input.strip()
            st.session_state.email=email_input.strip()
            st.session_state.page="trial"
            reset_game_state()
            st.rerun()
    st.stop()

# Page 2: Trial Runs
if st.session_state.page=="trial":
    st.title("🔁 Trial Runs (Practice)")
    trial_display = min(st.session_state.trial_runs_done + (0 if st.session_state.game_over else 1), TRIALS_REQUIRED)
    st.write(f"Trial {trial_display}/{TRIALS_REQUIRED}")

# ---------------- Card display ----------------
if st.session_state.page in ["trial","round1","round2"]:
    if st.session_state.page in ["round1","round2"]:
        st.markdown(f"### 💰 Current Score: {st.session_state.points} points")
        st.header("Pick a card" if st.session_state.phase=="first_pick" else "Pick again (same or switch)")
        round_label = f"Round {st.session_state.current_round_set} — Trial {((st.session_state.experiment_round)%TRIALS_PER_ROUND)+1}/{TRIALS_PER_ROUND}"
        st.subheader(round_label)

    cols=st.columns(3)
    emojis=card_emojis()
    for i,col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:10rem;text-align:center'>{emojis[i]}</h1>",unsafe_allow_html=True)
        if not st.session_state.game_over and col.button("Pick",key=f"card_{i}",use_container_width=True):
            if st.session_state.phase=="first_pick":
                st.session_state.first_choice=i
                losing_cards=[j for j in range(3) if j!=i and j!=st.session_state.trophy_pos]
                st.session_state.flipped_card=random.choice(losing_cards)
                st.session_state.phase="second_pick"
                st.rerun()
            elif st.session_state.phase=="second_pick" and i!=st.session_state.flipped_card:
                staying=(i==st.session_state.first_choice)
                cost=0
                if st.session_state.page!="trial":
                    if st.session_state.current_round_set==1 and not staying:
                        cost=10
                    elif st.session_state.current_round_set==2 and staying:
                        cost=10
                    if st.session_state.points<cost:
                        st.warning("⚠️ Not enough points!")
                        st.stop()
                    st.session_state.points-=cost
                st.session_state.second_choice=i
                st.session_state.phase="reveal_all"
                st.session_state.game_over=True
                st.rerun()

# ---------------- Results ----------------
if st.session_state.game_over:
    first=st.session_state.first_choice
    second=st.session_state.second_choice
    trophy=st.session_state.trophy_pos
    won=(second==trophy)
    stayed=(first==second)
    switch_win, stay_win=compute_switch_stay(first,second,trophy)

    if st.session_state.page=="trial":
        if won:
            st.success("🎉 You found the correct card!")
        else:
            st.error("❌ You picked the wrong card.")
            if first==trophy and second!=trophy:
                st.info("💡 You should have stayed to win.")
            elif first!=trophy and second!=trophy:
                st.info("💡 You should have switched to win.")
        if not st.session_state.logged_this_round:
            trial_number=st.session_state.trial_runs_done+1
            new_row=pd.DataFrame([{
                "trial_number":trial_number,
                "first_choice":first,
                "flipped_card":st.session_state.flipped_card,
                "second_choice":second,
                "trophy_card":trophy,
                "result":won,
                "switch_win":switch_win,
                "stay_win":stay_win,
                "email":st.session_state.email
            }])
            st.session_state.trial_log=pd.concat([st.session_state.trial_log,new_row],ignore_index=True)
            st.session_state.trial_runs_done+=1
            st.session_state.logged_this_round=True
    else:
        bonus=100 if won else 0
        lost_points=0
        if st.session_state.current_round_set==1:
            lost_points=10 if not stayed else 0
        else:
            lost_points=10 if stayed else 0
        if not st.session_state.logged_this_round:
            st.session_state.points+=bonus
        st.markdown(f"**You won +{bonus} points and lost −{lost_points} points this round.**")
        if not st.session_state.logged_this_round:
            round_number=st.session_state.experiment_round+1
            new_row=pd.DataFrame([{
                "round_number":round_number,
                "first_choice":first,
                "flipped_card":st.session_state.flipped_card,
                "second_choice":second,
                "trophy_card":trophy,
                "result":won,
                "phase_type":st.session_state.current_round_set,
                "points_after_round":st.session_state.points,
                "switch_win":switch_win,
                "stay_win":stay_win,
                "email":st.session_state.email
            }])
            st.session_state.experiment_log=pd.concat([st.session_state.experiment_log,new_row],ignore_index=True)
            st.session_state.experiment_round+=1
            st.session_state.logged_this_round=True

    # Next button
    col_top,_=st.columns([1,4])
    with col_top:
        if st.button("Next",key=f"next_top_{st.session_state.page}"):
            if st.session_state.page=="trial" and st.session_state.trial_runs_done>=TRIALS_REQUIRED:
                st.session_state.page="trial_summary"
            elif st.session_state.page=="round1" and st.session_state.experiment_round>=TRIALS_PER_ROUND:
                st.session_state.page="round2_instr"
            elif st.session_state.page=="round2" and st.session_state.experiment_round>=TRIALS_PER_ROUND*2:
                st.session_state.page="summary"
            reset_game_state()
            st.rerun()

# ---------------- Trial Summary ----------------
if st.session_state.page=="trial_summary":
    st.title("📊 Trial Summary")
    switch_attempts = st.session_state.trial_log['first_choice'] != st.session_state.trial_log['second_choice']
    stay_attempts = ~switch_attempts
    switch_wins = st.session_state.trial_log[switch_attempts]['result'].sum()
    stay_wins = st.session_state.trial_log[stay_attempts]['result'].sum()

    labels = ['Switch','Stay']
    attempts_counts = [switch_attempts.sum(), stay_attempts.sum()]
    wins_counts = [switch_wins, stay_wins]

    x = np.arange(len(labels))
    width=0.5
    fig, ax = plt.subplots(figsize=(5,4))
    ax.bar(x, wins_counts, width, label='Wins', color='green')
    ax.bar(x, [a-w for a,w in zip(attempts_counts,wins_counts)], width, bottom=wins_counts, label='Losses', color='blue')
    ax.set_ylabel('Count')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.set_title('Trial Wins')
    ax.legend()
    st.pyplot(fig)

    st.write(f"Total wins: **{st.session_state.trial_log['result'].sum()}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Another 10 Trials"):
            st.session_state.trial_runs_done = 0
            st.session_state.trial_log = pd.DataFrame(columns=st.session_state.trial_log.columns)
            st.session_state.page="trial"
            reset_game_state()
            st.rerun()
    with col2:
        if st.button("🚀 Go to Real Experiment"):
            st.session_state.page="round1_instr"
            reset_game_state()
            st.rerun()
# ---------------- Round 1 Instructions ----------------
if st.session_state.page=="round1_instr":
    st.title("🎯 Round 1 Instructions")
    st.write("""
Now we start the real experiment! New rules apply:

- You start with 50 points.
- Choosing the correct card: +100 points
- Switching from your first choice costs 10 points.
- Staying with your first choice is free.

Press the button when you are ready to start Round 1.
""")
    if st.button("✅ I understand, start Round 1"):
        st.session_state.page="round1"
        st.session_state.experiment_round=0
        st.session_state.current_round_set=1
        st.session_state.points=50
        reset_game_state()
        st.rerun()
    st.stop()

# ---------------- Round 2 Instructions ----------------
if st.session_state.page=="round2_instr":
    st.title("🎯 Round 2 Instructions")
    st.write("""
Round 2 rules:

- Correct card: +100 points
- Staying with your first choice costs 10 points
- Switching is free

Press the button when ready to start Round 2.
""")
    if st.button("✅ I understand, start Round 2"):
        st.session_state.page="round2"
        st.session_state.experiment_round=0
        st.session_state.current_round_set=2
        reset_game_state()
        st.rerun()
    st.stop()

# ---------------- Final Summary ----------------
if st.session_state.page=="summary":
    st.title("🏁 Final Summary")
    total_points=st.session_state.points
    st.write(f"**Total points: {total_points}**")

    total_correct = st.session_state.experiment_log['result'].sum()
    switch_wins = st.session_state.experiment_log['switch_win'].sum()
    stay_wins = st.session_state.experiment_log['stay_win'].sum()
    st.write(f"Total correct picks: {total_correct}")
    st.write(f"Wins when switching: {switch_wins}")
    st.write(f"Wins when staying: {stay_wins}")

    # Plot switching/staying results
    switch_attempts = st.session_state.experiment_log['phase_type']==1
    stay_attempts = st.session_state.experiment_log['phase_type']==2
    switch_total = (st.session_state.experiment_log['first_choice'] != st.session_state.experiment_log['second_choice']).sum()
    stay_total = (st.session_state.experiment_log['first_choice'] == st.session_state.experiment_log['second_choice']).sum()
    switch_success = switch_wins
    stay_success = stay_wins

    labels = ['Switch','Stay']
    attempts_counts = [switch_total, stay_total]
    wins_counts = [switch_success, stay_success]

    x = np.arange(len(labels))
    width=0.5
    fig, ax = plt.subplots(figsize=(5,4))
    ax.bar(x, wins_counts, width, label='Wins', color='green')
    ax.bar(x, [a-w for a,w in zip(attempts_counts,wins_counts)], width, bottom=wins_counts, label='Losses', color='blue')
    ax.set_ylabel('Count')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.set_title('Experiment Wins')
    ax.legend()
    st.pyplot(fig)

    # Save CSV to GitHub
    st.write("Saving results to GitHub...")
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("joojoosch/monty-hall-card-edition")
        csv_data = st.session_state.experiment_log.to_csv(index=False)
        path = f"player_logs/{st.session_state.player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        repo.create_file(path, f"Add results for {st.session_state.player_name}", csv_data)
        st.success(f"Results saved to GitHub as {path}")
    except Exception as e:
        st.error(f"⚠️ Couldn't save: {e}")
    st.stop()
