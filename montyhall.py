import streamlit as st
import random

st.set_page_config(page_title="Monty Hall - Card Flip", page_icon="🏆", layout="centered")

st.title("🏆 Monty Hall Problem — Interactive Cards")
st.write("""
Click on one of the three cards. One hides a 🏆 trophy (win), the other two hide ❌.  
After you pick, Monty will reveal a losing card and you can choose to **switch** or **stay**.
""")

# --- Initialize session state ---
if "cards" not in st.session_state:
    st.session_state.cards = ["🂠", "🂠", "🂠"]  # face-down
if "trophy_pos" not in st.session_state:
    st.session_state.trophy_pos = random.randint(0, 2)
if "chosen" not in st.session_state:
    st.session_state.chosen = None
if "monty_flipped" not in st.session_state:
    st.session_state.monty_flipped = None
if "game_over" not in st.session_state:
    st.session_state.game_over = False

# --- Reset game ---
if st.button("Reset Game"):
    st.session_state.cards = ["🂠", "🂠", "🂠"]
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.chosen = None
    st.session_state.monty_flipped = None
    st.session_state.game_over = False

# --- Display cards ---
cols = st.columns(3)
for i in range(3):
    if st.session_state.game_over:
        # Reveal all cards at the end
        display = "🏆" if i == st.session_state.trophy_pos else "❌"
        with cols[i]:
            st.button(display, disabled=True)
    else:
        with cols[i]:
            if st.button(st.session_state.cards[i], key=f"card_{i}"):
                if st.session_state.chosen is None:
                    # Player chooses a card
                    st.session_state.chosen = i
                    # Monty flips a losing card
                    losing_options = [j for j in range(3) if j != i and j != st.session_state.trophy_pos]
                    st.session_state.monty_flipped = random.choice(losing_options)
                    st.session_state.cards[st.session_state.monty_flipped] = "❌"

# --- Switch or Stay ---
if st.session_state.chosen is not None and not st.session_state.game_over:
    remaining = [i for i in range(3) if i not in [st.session_state.chosen, st.session_state.monty_flipped]][0]
    choice = st.radio("Do you want to stay or switch?", ["Stay", "Switch"])
    if st.button("Reveal Cards"):
        # Determine final choice
        final_choice = st.session_state.chosen if choice == "Stay" else remaining
        # Reveal all cards
        st.session_state.cards = ["🏆" if i == st.session_state.trophy_pos else "❌" for i in range(3)]
        st.session_state.game_over = True
        if final_choice == st.session_state.trophy_pos:
            st.success("🎉 You won the 🏆 trophy!")
            st.balloons()
        else:
            st.error("❌ You picked a losing card.")
