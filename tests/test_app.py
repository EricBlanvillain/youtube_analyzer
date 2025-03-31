import streamlit as st

st.set_page_config(
    page_title="Test App",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Streamlit Test App")
st.write("If you can see this, the basic Streamlit functionality is working correctly.")

with st.sidebar:
    st.header("Sidebar Test")
    st.write("This is a sidebar test.")

if st.button("Click me"):
    st.success("Button clicked! Everything seems to be working.")

st.markdown("---")
st.subheader("Debug Information")
st.text("Check if this text is visible on your screen.")
