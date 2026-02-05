import streamlit as st
st.title('IST 488 Labs')
lab1 = st.Page('Labs/Lab1.py', title = 'Lab 1', icon = '⭐️')
lab2 = st.Page('Labs/Lab2.py', title = 'Lab 2', icon = '🌈')
lab3 = st.Page('Labs/Lab3.py', title = 'Lab 3', icon = '🍓')
pg = st.navigation([lab3, lab2, lab1])
st.set_page_config(page_title = 'IST 488 Labs',
                   initial_sidebar_state = 'expanded')
pg.run()


#emojis saved for later: 🍇🍄✨🌼🐞🫧🥥🎨🪩💗
