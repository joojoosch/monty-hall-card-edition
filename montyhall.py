import streamlit as st
import random
import time

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
if "reveal_triggered" not in st.session_state:
    st.session_state.reveal_triggered = False

# --- Reset game ---
if st.button("Reset Game"):
    st.session_state.cards = ["🂠", "🂠", "🂠"]
    st.session_state.trophy_pos = random.randint(0, 2)
    st.session_state.chosen = None
    st.session_state.monty_flipped = None
    st.session_state.game_over = False
    st.session_state.reveal_triggered = False

# --- Display cards with larger size ---
cols = st.columns(3)
for i in range(3):
    card_label = f"<h1 style='text-align:center'>{st.session_state.cards[i]}</h1>"
    if st.session_state.game_over:
        display = "🏆" if i == st.session_state.trophy_pos else "❌"
        card_label = f"<h1 style='text-align:center'>{display}</h1>"
        with cols[i]:
            st.markdown(card_label, unsafe_allow_html=True)
    else:
        with cols[i]:
            if st.button(st.session_state.cards[i], key=f"card_{i}"):
                if st.session_state.chosen is None:
                    st.session_state.chosen = i
                    # Trigger delayed reveal
                    st.session_state.reveal_triggered = True

# --- Delayed Monty reveal ---
if st.session_state.reveal_triggered and not st.session_state.monty_flipped:
    st.write("Monty is thinking...")
    time.sleep(2)  # 2-second delay for suspense
    losing_options = [i for i in range(3) if i != st.session_state.chosen and i != st.session_state.trophy_pos]
    st.session_state.monty_flipped = random.choice(losing_options)
    st.session_state.cards[st.session_state.monty_flipped] = "❌"
    st.session_state.reveal_triggered = False

# --- Switch or Stay ---
if st.session_state.chosen is not None and not st.session_state.game_over and st.session_state.monty_flipped is not None:
    remaining = [i for i in range(3) if i not in [st.session_state.chosen, st.session_state.monty_flipped]][0]
    choice = st.radio("Do you want to stay or switch?", ["Stay", "Switch"])
    if st.button("Reveal Cards"):
        final_choice = st.session_state.chosen if choice == "Stay" else remaining
        st.session_state.cards = ["🏆" if i == st.session_state.trophy_pos else "❌" for i in range(3)]
        st.session_state.game_over = True
        if final_choice == st.session_state.trophy_pos:
            st.success("🎉 You won the 🏆 trophy!")
            st.balloons()
        else:
            st.error("❌ You picked a losing card.")
