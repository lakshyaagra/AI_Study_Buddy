import os
import json
import streamlit as st
from google import genai
from google.genai import types
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


def get_schema(mode):

    schemas = {
        "Explain": EXPLAIN_SCHEMA,
        "Summarize": SUMMARY_SCHEMA,
        "Quiz": QUIZ_SCHEMA
    }

    return schemas[mode]

# -------------------------
# SCHEMA
# -------------------------


EXPLAIN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "definition": {"type": "STRING"},
        "key_points": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "example": {
            "type": "STRING",
            "description": "Provide a practical C++ code example. Return only the code, without Markdown code fences."

        }
    },
    "required": ["title", "definition", "key_points", "example"]
}

SUMMARY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "summary": {"type": "STRING"},
        "key_points": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["title", "summary", "key_points"]
}

QUIZ_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING"},
        "questions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING"},
                    "options": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "correct_answer": {"type": "STRING"},
                    "explanation": {"type": "STRING"}
                },
                "required": [
                    "question",
                    "options",
                    "correct_answer",
                    "explanation"
                ]
            }
        }
    },
    "required": ["topic", "questions"]
}


def validate_quiz(data):

    if not isinstance(data, dict):
        return False

    if not isinstance(data.get("topic"), str) or not data["topic"].strip():
        return False

    questions = data.get("questions")

    if not isinstance(questions, list) or len(questions) != 5:
        return False

    for question in questions:

        if not isinstance(question, dict):
            return False

        required = [
            "question",
            "options",
            "correct_answer",
            "explanation"
        ]

        if not all(key in question for key in required):
            return False

        options = question["options"]

        if not isinstance(options, list) or len(options) != 4:
            return False

        if not all(isinstance(option, str) and option.strip() for option in options):
            return False

        if question["correct_answer"] not in options:
            return False

        if not all(
            isinstance(question[key], str) and question[key].strip()
            for key in ["question", "correct_answer", "explanation"]
        ):
            return False

    return True
# -------------------------
# SESSION STATE
# -------------------------

API_KEY = os.getenv("GEMINI_API_KEY")

if "result" not in st.session_state:
    st.session_state.result = None

if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""

if "last_mode" not in st.session_state:
    st.session_state.last_mode = ""

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

# Session state variables for token tracking
if "input_tokens" not in st.session_state:
    st.session_state.input_tokens = 0

if "output_tokens" not in st.session_state:
    st.session_state.output_tokens = 0

if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

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
        return base_prompt + common + f"""
        Generate a quiz about: {topic}

        You must follow these rules:
        - Return exactly 5 multiple-choice questions.
        - Each question must have exactly 4 options.
        - Include one correct answer and a short explanation.
        - The topic field must contain ONLY the topic name: {topic}
        - Do NOT write a lecture, introduction, summary, or tutorial.
        - Do NOT include code examples in the topic field.
        """


def type_prompt(topic,audience,style, prompt_type, length_instruction):
    
    if prompt_type == "Zero-shot":
        return f"""
        Explain {topic} in simple language in {length_instruction}.
        Give one practical example.
        """

    elif prompt_type == "Role-based":
        return f"""
            You are helping a {audience} student.
            Use simple and clear language.
            Follow the requested task carefully.
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
    schema=get_schema(mode)

    prompt = create_prompt(
        topic, mode, audience, language, style, length_instruction,prompt_type
    )

    try:
        with st.spinner("AI is preparing your learning material..."):

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema
                )
            )

            usage = response.usage_metadata

            if usage:
                st.session_state.input_tokens = usage.prompt_token_count or 0
                st.session_state.output_tokens = usage.candidates_token_count or 0
                st.session_state.total_tokens = usage.total_token_count or 0
            else:
                st.session_state.input_tokens = 0
                st.session_state.output_tokens = 0
                st.session_state.total_tokens = 0

            data=json.loads(response.text)

            # Fix for escaped newlines in C++ code example
            if mode == "Explain" and "example" in data:
                # Agar JSON mein \\n ki tarah escape hokar aaya hai toh use proper newline bana dega
                data["example"] = data["example"].replace("\\n", "\n")

            if mode == "Quiz":
                if not validate_quiz(data):
                    st.error("AI returned an invalid quiz structure.")
                    return

        st.session_state.result = data
        st.session_state.last_topic = topic
        st.session_state.last_mode = mode
        st.session_state.quiz_answers = {}
    
    except json.JSONDecodeError:
        st.error("AI returned invalid JSON. Please try again.")

    except Exception as error:
        print(f"Technical error: {error}")
        st.error(
            "Unable to generate your response. "
            "Please try again."
        )


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

    # -------------------------
    # DISPLAY TOKEN USAGE METrics
    # -------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("📥 Input Tokens", st.session_state.input_tokens)
    col2.metric("📤 Output Tokens", st.session_state.output_tokens)
    col3.metric("📊 Total Tokens", st.session_state.total_tokens)

    with st.container(border=True):

        data = st.session_state.result
        mode = st.session_state.last_mode

        if mode == "Explain":

            st.header(data["title"])

            st.subheader("Definition")
            st.write(data["definition"])

            st.subheader("Key Points")
            for point in data["key_points"]:
                st.markdown(f"- {point}")

            st.subheader("Practical Example")
            st.code(data["example"], language="cpp")


        elif mode == "Summarize":

            st.header(data["title"])

            st.subheader("Summary")
            st.write(data["summary"])

            st.subheader("Key Points")
            for point in data["key_points"]:
                st.markdown(f"- {point}")


        elif mode == "Quiz":

            st.header(data["topic"])

            for i, question in enumerate(data["questions"]):
                st.subheader(f"Q{i + 1}. {question['question']}")
                answer = st.radio(
                    "Choose your answer:",
                    question["options"],
                    key=f"quiz_{i}",
                    index=None
                )

                if answer is not None:
                    st.session_state.quiz_answers[i] = answer

            if st.button("Submit Quiz"):
                if len(st.session_state.quiz_answers) != len(data["questions"]):
                    st.warning("Please answer all questions first.")
                else:
                    score = 0
                    for i, question in enumerate(data["questions"]):
                        user_answer = st.session_state.quiz_answers[i]
                        if user_answer == question["correct_answer"]:
                            score += 1
                            st.success(f"Q{i + 1}: Correct!")
                        else:
                            st.error(
                                f"Q{i + 1}: Incorrect. Correct answer: "
                                f"{question['correct_answer']}"
                            )

                        st.info(f"Explanation: {question['explanation']}")
                    st.subheader(f"Your Score: {score}/{len(data['questions'])}")

    st.download_button(
        label="📥 Download Notes",
        data=json.dumps(st.session_state.result,indent=4),
        file_name="study_notes.txt",
        mime="text/plain"
    )

    if st.button("Clear Result"):
        st.session_state.result = ""
        st.session_state.last_topic = ""
        st.session_state.last_mode = ""
        st.session_state.quiz_answers = {}
        st.session_state.input_tokens = 0
        st.session_state.output_tokens = 0
        st.session_state.total_tokens = 0
        st.rerun()