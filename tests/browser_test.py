import streamlit as st
import sys
import platform

# Basic page config
st.set_page_config(
    page_title="Browser Test",
    page_icon="🌐",
    layout="wide"
)

# Page header
st.title("Browser Compatibility Test")
st.markdown("This page tests if Streamlit can properly render content in your browser.")

# Display environment info
st.header("Environment Information")
st.code(f"""
Python version: {sys.version}
Platform: {platform.platform()}
Streamlit version: {st.__version__}
""")

# Interactive elements
st.header("Interactive Elements Test")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Basic Elements")
    name = st.text_input("Enter your name")
    if name:
        st.write(f"Hello, {name}!")

    if st.button("Click me"):
        st.success("Button clicked successfully!")

with col2:
    st.subheader("Visual Elements")
    st.slider("Test slider", 0, 100, 50)
    st.selectbox("Test dropdown", ["Option 1", "Option 2", "Option 3"])

# Instructions
st.header("Troubleshooting Steps")
st.markdown("""
If you can see this page correctly:
1. Your Streamlit installation is working
2. Your browser can render Streamlit content properly

If you're seeing a black screen:
1. Try a different browser (Chrome, Firefox, Safari)
2. Check browser console for JavaScript errors (F12 or right-click > Inspect > Console)
3. Try disabling browser extensions
4. Clear browser cache and cookies
""")

# Footer
st.markdown("---")
st.caption("Streamlit Browser Compatibility Test")
