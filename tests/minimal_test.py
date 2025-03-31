import streamlit as st

# Basic page config
st.set_page_config(
    page_title="Minimal Test",
    page_icon="🧪",
    layout="wide"
)

# Simple content
st.title("Minimal Streamlit Test")
st.write("If you can see this, Streamlit is working correctly!")

# Simple interaction
if st.button("Click me"):
    st.success("Button clicked!")
