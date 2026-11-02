import streamlit as st

st.title("AI Study Buddy")

topic=st.text_area("What do you want to learn?")

if st.button("Explain"):
    if(topic.strip()):
        st.write("You want to learn:" , topic)
    else:
        st.warning("Please enter a topic.")