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
TRIALS_PER_ROUND = 3  # 3 trials per round, 2 rounds => 6 experiment trials total

# ---------------- Session state initialization ----------------
if "player_name" not in st.session_state:
    st.session_state.player_name = None
if "email" not in st.session_state:
    st.session_state.email = ""  # optional

# page values: instructions, trial, trial_summary, round1_instr, round1, round2_instr, round2, summary
if "page" not in st.session_state:
    st.session_state.page = "instructions"

# Trials
if "trial_runs_done" not in st.session_state:
    st.session_state.trial_runs_done = 0
if "trial_log" not in st.session_state:
    st.session_state.trial_log = pd.DataFrame(columns=[
        "trial_number", "first_choice", "flipped_card", "second_choice",
        "trophy_card", "result", "switch_win", "stay_win", "email"
    ])

# Experiment
if "experiment_round" not in st.session_state:
    st.session_state.experiment_round = 0  # number of completed experiment trials (0..6)
if "current_round_set" not in st.session_state:
    st.session_state.current_round_set = 1  # 1 or 2
if "experiment_log" not in st.session_state:
    st.session_state.experiment_log = pd.DataFrame(columns=[
        "round_number", "first_choice", "flipped_card", "second_choice",
        "trophy_card", "result", "phase_type", "points_after_round",
        "switch_win", "stay_win", "email"
    ])

# Game state
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
    st.session_state.phase = "first_pick"  # first_pick, second_pick, reveal_all
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "points" not in st.session_state:
    st.session_state.points = 50  # start points when real experiment begins
if "logged_this_round" not in st.session_state:
    st.session_state.logged_this_round = False

# ---------------- Helpers ----------------
def reset_game_state_for_trial():
    st.session_state.cards = ["🂠"] * 3
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.first_choice = None
    st.session_state.flipped_card = None
    st.session_state.second_choice = None
    st.session_state.phase = "first_pick"
    st.session_state.game_over = False
    st.session_state.logged_this_round = False

def card_emojis():
    em = []
    for i in range(3):
        if st.session_state.phase == "reveal_all" or st.session_state.game_over:
            em.append("🏆" if i == st.session_state.trophy_pos else "❌")
        elif st.session_state.phase == "second_pick":
            em.append("❌" if i == st.session_state.flipped_card else "🂠")
        else:
            em.append("🂠")
    return em

def compute_switch_stay(first, second, trophy):
    if second == trophy:
        if first == second:
            return 0, 1
        else:
            return 1, 0
    return 0, 0

def current_trial_index_in_set():
    # experiment_round counts completed trials (0..6). For display, we want 1..3 within current round set.
    completed = st.session_state.experiment_round
    idx = (completed % TRIALS_PER_ROUND) + 1
    return idx

# ---------------- Page 1: Instructions + Name + optional email ----------------
if st.session_state.page == "instructions":
    # ensure clean state
    reset_game_state_for_trial()

    st.title("🏆 Card Game Experiment")
    st.write("""
You will be shown three cards and your goal is to find the trophy 🏆 behind one of them.

1️⃣ Choose a card.  
2️⃣ One of the NOT chosen cards will be revealed.  
3️⃣ Choose to stick with your first choice or switch to the other remaining card.  
The winning trophy card is then revealed!
""")

    name_input = st.text_input("Enter your first and last name:", value=st.session_state.player_name or "")
    email_input = st.text_input("(Optional) Enter your email to be eligible for a prize if you're a top scorer:", value=st.session_state.email or "")

    if st.button("✅ Confirm Name and Continue"):
        if name_input.strip() == "":
            st.warning("Please enter a valid name.")
        else:
            st.session_state.player_name = name_input.strip()
            st.session_state.email = email_input.strip()
            # proceed to trials
            st.session_state.page = "trial"
            reset_game_state_for_trial()
            st.rerun()
    st.stop()

# ---------------- Page 2: Trial Runs (Practice) ----------------
if st.session_state.page == "trial":
    st.title("🔁 Trial Runs (Practice)")
    # Determine display trial number (1..TRIALS_REQUIRED). If all done, show TRIALS_REQUIRED.
    if st.session_state.trial_runs_done >= TRIALS_REQUIRED:
        trial_display = TRIALS_REQUIRED
    else:
        # If we're mid-trial (game_over False) we show next trial index = done + 1
        trial_display = st.session_state.trial_runs_done + (0 if st.session_state.game_over else 1)
        if trial_display > TRIALS_REQUIRED:
            trial_display = TRIALS_REQUIRED
    st.write(f"Trial {trial_display}/{TRIALS_REQUIRED}")

    # Top Next / See Results button appears only after reveal (game_over True)
    if st.session_state.game_over:
        col_top, _ = st.columns([1, 4])
        with col_top:
            if st.session_state.trial_runs_done < TRIALS_REQUIRED:
                if st.button("Next", key="trial_next_top"):
                    reset_game_state_for_trial()
                    st.rerun()
            else:
                # After finishing the 10th trial (trial_runs_done == TRIALS_REQUIRED), offer See Results
                if st.button("📄 See Results", key="trial_see_results_top"):
                    st.session_state.page = "trial_summary"
                    st.rerun()

    # Phase header below top button
    if st.session_state.phase == "first_pick":
        st.subheader("Pick your first card")
    elif st.session_state.phase == "second_pick":
        st.subheader("Pick Again (same or switch)")

# ---------------- Card display & logic (Trials & Experiment) ----------------
if st.session_state.page in ["trial", "round1", "round2"]:
    # For real experiment pages, show header & points above cards
    if st.session_state.page == "round1":
        idx = ((st.session_state.experiment_round) % TRIALS_PER_ROUND) + 1
        st.title(f"Round 1 — Trial {idx}/{TRIALS_PER_ROUND}")
        st.markdown(f"### 💰 Current Score: {st.session_state.points} points")
    elif st.session_state.page == "round2":
        idx = ((st.session_state.experiment_round) % TRIALS_PER_ROUND) + 1
        st.title(f"Round 2 — Trial {idx}/{TRIALS_PER_ROUND}")
        st.markdown(f"### 💰 Current Score: {st.session_state.points} points")

    cols = st.columns(3)
    emojis = card_emojis()
    for i, col in enumerate(cols):
        col.markdown(f"<h1 style='font-size:10rem; text-align:center'>{emojis[i]}</h1>", unsafe_allow_html=True)
        if not st.session_state.game_over and col.button("Pick", key=f"card_{i}", use_container_width=True):
            if st.session_state.phase == "first_pick":
                st.session_state.first_choice = i
                losing_cards = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                st.session_state.flipped_card = random.choice(losing_cards)
                st.session_state.phase = "second_pick"
                st.rerun()

            elif st.session_state.phase == "second_pick" and i != st.session_state.flipped_card:
                staying = (i == st.session_state.first_choice)
                cost = 0
                # apply cost only in real experiment
                if st.session_state.page != "trial":
                    if st.session_state.current_round_set == 1 and not staying:
                        cost = 10
                    elif st.session_state.current_round_set == 2 and staying:
                        cost = 10
                    if st.session_state.points < cost:
                        st.warning("⚠️ You don’t have enough points for this action!")
                        st.stop()
                    st.session_state.points -= cost

                st.session_state.second_choice = i
                st.session_state.phase = "reveal_all"
                st.session_state.game_over = True
                st.rerun()

# ---------------- Display results area (below cards) ----------------
if st.session_state.game_over:
    first = st.session_state.first_choice
    second = st.session_state.second_choice
    trophy = st.session_state.trophy_pos
    won = (second == trophy)
    stayed = (first == second)
    switch_win, stay_win = compute_switch_stay(first, second, trophy)

    # TRIAL behavior (advice only on loss)
    if st.session_state.page == "trial":
        if won:
            st.success("🎉 You found the correct card!")
        else:
            st.error("❌ You picked the wrong card.")
            if first == trophy and second != trophy:
                st.info("💡 You should have stayed to win.")
            elif first != trophy and second != trophy:
                st.info("💡 You should have switched to win.")

        if not st.session_state.logged_this_round:
            trial_number = st.session_state.trial_runs_done + 1
            new_row = pd.DataFrame([{
                "trial_number": trial_number,
                "first_choice": first,
                "flipped_card": st.session_state.flipped_card,
                "second_choice": second,
                "trophy_card": trophy,
                "result": won,
                "switch_win": switch_win,
                "stay_win": stay_win,
                "email": st.session_state.email
            }])
            st.session_state.trial_log = pd.concat([st.session_state.trial_log, new_row], ignore_index=True)
            st.session_state.trial_runs_done += 1
            st.session_state.logged_this_round = True

    # REAL experiment behavior
    else:
        # bonus and lost points for display
        bonus = 100 if won else 0
        if st.session_state.current_round_set == 1:
            lost_points = 10 if (not stayed) else 0
        else:
            lost_points = 10 if stayed else 0

        if not st.session_state.logged_this_round:
            st.session_state.points += bonus

        st.markdown(f"**You won +{bonus} points and lost −{lost_points} points this round.**")

        # log experiment trial once
        if not st.session_state.logged_this_round:
            round_number = st.session_state.experiment_round + 1
            new_row = pd.DataFrame([{
                "round_number": round_number,
                "first_choice": first,
                "flipped_card": st.session_state.flipped_card,
                "second_choice": second,
                "trophy_card": trophy,
                "result": won,
                "phase_type": st.session_state.current_round_set,
                "points_after_round": st.session_state.points,
                "switch_win": switch_win,
                "stay_win": stay_win,
                "email": st.session_state.email
            }])
            st.session_state.experiment_log = pd.concat([st.session_state.experiment_log, new_row], ignore_index=True)
            st.session_state.experiment_round += 1
            st.session_state.logged_this_round = True

    # TOP Next button for experiment pages (visual top placement is handled when page rendered; this ensures navigation)
    if st.session_state.page in ["round1", "round2"]:
        col_top, _ = st.columns([1, 4])
        with col_top:
            if st.button("Next", key=f"exp_next_top_{st.session_state.page}"):
                # If finished Round1 (3 trials) move to round2 instructions
                if st.session_state.current_round_set == 1 and st.session_state.experiment_round >= TRIALS_PER_ROUND:
                    st.session_state.page = "round2_instr"
                    reset_game_state_for_trial()
                    st.rerun()
                # If finished Round2 (6 trials total) -> final summary
                elif st.session_state.current_round_set == 2 and st.session_state.experiment_round >= (TRIALS_PER_ROUND * 2):
                    st.session_state.page = "summary"
                    st.rerun()
                else:
                    reset_game_state_for_trial()
                    st.rerun()

# ---------------- Trial Summary Page (with Matplotlib chart) ----------------
if st.session_state.page == "trial_summary":
    st.title("📄 Trial Summary")
    st.write(f"Trials completed: **{st.session_state.trial_runs_done}**")
    total_switch_wins = int(st.session_state.trial_log['switch_win'].sum())
    total_stay_wins = int(st.session_state.trial_log['stay_win'].sum())
    total_wins = int(st.session_state.trial_log['result'].sum())
    total_switch_attempts = int((st.session_state.trial_log['switch_win'] + (st.session_state.trial_log['result'] == False) * (st.session_state.trial_log['switch_win'] == 0)).sum())  # fallback, but we'll compute robustly below

    st.write(f"Wins by switching: **{total_switch_wins}**")
    st.write(f"Wins by staying: **{total_stay_wins}**")
    st.write(f"Total wins: **{total_wins}**")

    # Build counts for plotting: For trials, compute switch attempts and stay attempts and wins/losses
    # We'll compute directly:
    df = st.session_state.trial_log.copy()
    # Determine for each trial whether it was a switch or stay action
    def was_switch(row):
        return row['first_choice'] != row['second_choice']
    df['action'] = df.apply(was_switch, axis=1)  # True = switch, False = stay
    # Now aggregate
    switch_df = df[df['action'] == True]
    stay_df = df[df['action'] == False]
    switch_wins = int(switch_df['result'].sum())
    switch_losses = int(len(switch_df) - switch_wins)
    stay_wins = int(stay_df['result'].sum())
    stay_losses = int(len(stay_df) - stay_wins)

    # Matplotlib grouped bar chart
    labels = ['Switch', 'Stay']
    wins = [switch_wins, stay_wins]
    losses = [switch_losses, stay_losses]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots()
    ax.bar(x - width/2, wins, width, label='Wins')
    ax.bar(x + width/2, losses, width, label='Losses')
    ax.set_ylabel('Count')
    ax.set_title('Trial outcomes by action (Switch vs Stay)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    st.pyplot(fig)

    st.write("You may choose to repeat another 10 trial rounds or proceed to the real experiment.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Another 10 Trial Rounds"):
            st.session_state.trial_runs_done = 0
            st.session_state.trial_log = pd.DataFrame(columns=st.session_state.trial_log.columns)
            st.session_state.page = "trial"
            reset_game_state_for_trial()
            st.rerun()
    with col2:
        if st.button("🚀 Go to Real Experiment"):
            st.session_state.page = "round1_instr"
            st.rerun()

# ---------------- Round 1 Instructions (clean, no Next) ----------------
if st.session_state.page == "round1_instr":
    reset_game_state_for_trial()  # ensure no stray results
    st.title("🎯 Round 1 Instructions")
    st.write("""
Now we add the point system for the real experiment.

- You start with **50 points**.
- Each correct card gives **+100 points**.
- **Switching** after the reveal costs **10 points** in Round 1.
- Staying is free in Round 1.
""")
    if st.button("✅ I understand, start Round 1"):
        st.session_state.points = 50
        st.session_state.current_round_set = 1
        st.session_state.experiment_round = 0
        st.session_state.page = "round1"
        reset_game_state_for_trial()
        st.rerun()

# ---------------- Round 1 page is handled in the card display block above ----------------

# ---------------- Round 2 Instructions (already clean) ----------------
if st.session_state.page == "round2_instr":
    reset_game_state_for_trial()
    st.title("🎯 Round 2 Instructions")
    st.write("""
Round 2 rules:

- Each correct card gives **+100 points**.
- **Staying** with your first choice now costs **10 points**.
- Switching is free.
""")
    if st.button("✅ I understand, start Round 2"):
        st.session_state.current_round_set = 2
        st.session_state.page = "round2"
        reset_game_state_for_trial()
        st.rerun()

# ---------------- Final Summary (no DataFrame shown to participant, Matplotlib chart + GitHub upload) ----------------
if st.session_state.page == "summary":
    st.title("🎉 Experiment Complete!")
    st.markdown(f"### 💰 Final points: {st.session_state.points} points")
    total_correct = int(st.session_state.experiment_log['result'].sum())
    st.write(f"✅ Total correct picks: **{total_correct}**")
    total_switch_wins = int(st.session_state.experiment_log['switch_win'].sum())
    total_stay_wins = int(st.session_state.experiment_log['stay_win'].sum())
    st.write(f"Wins by switching: **{total_switch_wins}**")
    st.write(f"Wins by staying: **{total_stay_wins}**")

    # Build counts for plotting from experiment_log
    df_exp = st.session_state.experiment_log.copy()
    if len(df_exp) > 0:
        def was_switch(row):
            return row['first_choice'] != row['second_choice']
        df_exp['action'] = df_exp.apply(was_switch, axis=1)
        switch_df = df_exp[df_exp['action'] == True]
        stay_df = df_exp[df_exp['action'] == False]
        switch_wins = int(switch_df['result'].sum())
        switch_losses = int(len(switch_df) - switch_wins)
        stay_wins = int(stay_df['result'].sum())
        stay_losses = int(len(stay_df) - stay_wins)

        labels = ['Switch', 'Stay']
        wins = [switch_wins, stay_wins]
        losses = [switch_losses, stay_losses]

        x = np.arange(len(labels))
        width = 0.35
        fig, ax = plt.subplots()
        ax.bar(x - width/2, wins, width, label='Wins')
        ax.bar(x + width/2, losses, width, label='Losses')
        ax.set_ylabel('Count')
        ax.set_title('Experiment outcomes by action (Switch vs Stay)')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        st.pyplot(fig)
    else:
        st.info("No experiment trials logged yet.")

    # Upload to GitHub (include email column in CSV)
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("joojoosch/monty-hall-card-edition")
        csv_data = st.session_state.experiment_log.to_csv(index=False)
        path = f"player_logs/{st.session_state.player_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        repo.create_file(path, f"Add results for {st.session_state.player_name}", csv_data)
        st.success(f"Results saved to GitHub as {path}")
    except Exception as e:
        st.error(f"⚠️ Couldn't save to GitHub: {e}")

   
