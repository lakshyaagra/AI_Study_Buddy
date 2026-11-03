import os
import streamlit as st
from google import genai
from dotenv import load_dotenv

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

load_dotenv()

st.title("📚 AI Study Buddy")
st.caption("Your personal AI-powered learning assistant.")

st.divider()

# -------------------------
# SESSION STATE
# -------------------------

API_KEY = os.getenv("GEMINI_API_KEY")

if "result" not in st.session_state:
    st.session_state.result = ""

if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""

if "last_mode" not in st.session_state:
    st.session_state.last_mode = ""

# -------------------------
# CLIENT
# -------------------------

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None


topic=st.text_area("What do you want to learn?",placeholder="Example: Binary Search...")

with st.sidebar:
    st.header("⚙️ Learning Settings")

    audience = st.selectbox(
        "Your level",
        ["Beginner", "Intermediate", "Advanced"]
    )
    language = st.selectbox(
        "Response language",
        ["English", "Hinglish"]
    )
    length = st.selectbox(
        "Response length",
        ["Short", "Medium", "Long"]
    )
    style = st.selectbox(
        "Teaching style",
        ["Professor", "Friendly Mentor", "Interviewer"]
    )
    prompt_type = st.selectbox(
        "Choose a Prompt Technique",
        ["Zero-shot","Role-based","Constraint-based","Few-shot","Context-based"]
    )

    st.divider()
    st.caption("Built with Python, Streamlit and Gemini API")

length_guide = {
    "Short": "Explain in approximately 100 words.",
    "Medium": "Explain in approximately 250 words.",
    "Long": "Explain in approximately 500 words."
}

tab1, tab2, tab3 = st.tabs(
    ["📖 Explain", "📝 Summarize", "🧠 Quiz"]
)

def create_prompt(topic, mode, audience, language, style,length_instruction,prompt_type):

    base_prompt=type_prompt(topic,audience,style,prompt_type,length_instruction)

    common = f"""
    Respond in {language}.
    """

    if mode == "Explain":
        return base_prompt + common + """
        Explain the topic step by step.
        Include a practical example.
        """

    elif mode == "Summarize":
        return base_prompt + common + """
        Create concise revision notes.
        Include important concepts and key points.
        """

    elif mode == "Quiz":
        return base_prompt + common + """
        Create 5 multiple-choice questions.
        Each question must have 4 options.
        Include correct answers and explanations.
        """


def type_prompt(topic,audience,style, prompt_type, length_instruction):
    
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


def generate_response(topic,mode,audience,language,style,length_guide,prompt_type):

    if not topic.strip():
        st.warning("Please enter a topic first.")
        return

    if client is None:
        st.error("GEMINI_API_KEY is missing. Check your .env file.")
        return

    length_instruction = length_guide[length]
    prompt = create_prompt(
        topic, mode, audience, language, style, length_instruction,prompt_type
    )

    try:
        with st.spinner("AI is preparing your learning material..."):

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

        st.session_state.result = response.text or "No response received."
        st.session_state.last_topic = topic
        st.session_state.last_mode = mode

    except Exception as error:
        st.error(f"Something went wrong: {error}")


# -------------------------
# TAB 1 - EXPLAIN
# -------------------------
with tab1:
    st.write("Understand concepts step by step.")
    if st.button("Explain Topic", key="explain_btn"):
        generate_response(topic, "Explain", audience, language, style, length_guide,prompt_type)

# -------------------------
# TAB 2 - SUMMARIZE
# -------------------------
with tab2:
    st.write("Generate concise notes for revision.")
    if st.button("Summarize Topic", key="summary_btn"):
        generate_response(topic, "Summarize", audience, language, style, length_guide,prompt_type)

# -------------------------
# TAB 3 - QUIZ
# -------------------------
with tab3:
    st.write("Test your understanding with MCQs.")
    if st.button("Generate Quiz", key="quiz_btn"):
        generate_response(topic, "Quiz", audience, language, style, length_guide,prompt_type)

# -------------------------
# DISPLAY RESULT
# -------------------------

if st.session_state.result:

    st.divider()

    st.subheader(
        f"Your {st.session_state.last_mode} Result"
    )

    st.caption(
        f"Topic: {st.session_state.last_topic}"
    )

    with st.container(border=True):
        st.markdown(st.session_state.result)

    st.download_button(
        label="📥 Download Notes",
        data=st.session_state.result,
        file_name="study_notes.txt",
        mime="text/plain"
    )

    if st.button("Clear Result"):
        st.session_state.result = ""
        st.session_state.last_topic = ""
        st.session_state.last_mode = ""
        st.rerun()