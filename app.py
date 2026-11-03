import os
import streamlit as st
from google import genai
from dotenv import load_dotenv

load_dotenv()

st.title("AI Study Buddy")
st.write("Learn any topic with the help of AI!")

topic=st.text_area("What do you want to learn?",placeholder="Example: Binary Search...")

audience=st.selectbox("Beginner, Intermediate, or Advanced?",["Beginner","Intermediate","Advanced"])
length=st.radio("How long should the explanation be?",["Short","Medium","Long"])
style=st.selectbox("How do you want to learn the topic as?",["Professor" , "Friendly Mentor" , "Interviewer"])

prompt_type = st.selectbox("Choose a Prompt Technique",["Zero-shot","Role-based","Constraint-based","Few-shot","Context-based"])

length_guide = {
    "Short": "Explain in approximately 100 words.",
    "Medium": "Explain in approximately 250 words.",
    "Long": "Explain in approximately 500 words."
}

def create_prompt(topic,audience,style, prompt_type, length_instruction):
    
    if prompt_type == "Zero-shot":
        return f"""
        Explain {topic} in simple language in {length_instruction}.
        Give one practical example.
        """

    elif prompt_type == "Role-based":
        return f"""
            You are an experienced {style} who specializes
            in teaching computer science and DSA.
            Adapt your teaching style to a {audience} student.
            Explain {topic} in simple language.
            Give a practical example.
            """

    elif prompt_type == "Constraint-based":
        return f"""
        Explain {topic} as my {style}.

        Follow these constraints:
        - Use simple language as if you are explaining to a {audience}.
        - Keep the answer to {length_instruction}.
        - Include one example.
        - Avoid unnecessary technical jargon.
        """

    elif prompt_type == "Few-shot":
        return f"""
            Follow the style of these examples:

            Topic: Stack
            Explanation:
            A stack is a linear data structure that follows LIFO which is...
            Example: A stack of plates.

            Topic: Queue
            Explanation:
            A queue is a linear data structure that follows FIFO which is...
            Example: People waiting in a line.

            Now explain the topic {topic} in a detailed style to a {audience}
            in {length_instruction}.
        """
    elif prompt_type == "Context-based":
        return f"""
            I am a {audience}-level learner studying {topic}.
            I am currently learning DSA for placements.

            Explain {topic} with this background in
            mind with {length_instruction}
            in style of my {style}.
            Connect the concept to coding interviews.
            Include one practical C++ example.
            """
    else:
        raise ValueError("Unsupported prompt technique")

if st.button("Generate Explanation..."):
    if not(topic.strip()):
        st.warning("Please enter a topic.")
    elif not(os.getenv("GEMINI_API_KEY")):
        st.warning("Please set your GEMINI_API_KEY in the .env file.")
    else:
        try:
            client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            length_instruction = length_guide[length]
            prompt=f"{create_prompt(topic,audience,style,prompt_type,length_instruction)}"
            with st.expander("View Generated Prompt"):
                st.code(prompt)

            with st.spinner("AI is thinking..."):
                response=client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                st.write("Your Output: ")
                st.write(response.text)
        
        except Exception as error:
            st.error(f"Something went wrong: {error}")