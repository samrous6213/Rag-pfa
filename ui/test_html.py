import streamlit as st

st.markdown("""
<div style="background: red; color: white; padding: 1rem;">
    TEST 1 : style inline
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="test-class">
    TEST 2 : class CSS
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div>
    TEST 3 : simple div
</div>
""", unsafe_allow_html=True)
