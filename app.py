from adaptive import Adaptive_Quiz
import streamlit as st
import openai
from mem0 import MemoryClient
import time
import os
from langchain_openai import ChatOpenAI  # Update this import

class AdaptiveLearningPlatform:
    # ... (keep the existing AdaptiveLearningPlatform class as is)
    
    def __init__(self, student_name, mem0_api_key, openai_api_key):
        self.student = student_name
        self.client = MemoryClient(api_key=mem0_api_key)
        openai.api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.adaptive_quiz = None

    def chat_with_gpt4(self, messages):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def get_student_memories(self):
        user_memories = self.client.get_all(user_id=self.student)
        memories = ""
        for i in user_memories:
            memories += i["memory"] + "\n"
        return memories

    def update_system_prompt(self):
        memories = self.get_student_memories()
        return f"You are a tutor for {self.student}. Be more elaborate on a topic if one struggles with it more. Keep the following information about the student in mind:\n\n{memories}"

    def add_memory(self, content):
        self.client.add(content, user_id=self.student)

    def run_tutoring_session(self):
        print(f"Starting tutoring session for {self.student}. Type 'bye' to end the session or 'quiz' to start an adaptive quiz.")
        while True:
            system_prompt = self.update_system_prompt()
            messages = [{"role": "system", "content": system_prompt}]

            user_input = input(f"{self.student}: ")
            if user_input.lower() == 'bye':
                print("Tutor: Goodbye! It was nice helping you.")
                break
            elif user_input.lower() == 'quiz':
                self.start_adaptive_quiz()
                continue

            messages.append({"role": "user", "content": user_input})
            self.add_memory(user_input)

            ai_response = self.chat_with_gpt4(messages)
            print(f"Tutor: {ai_response}")
            print()

    def start_adaptive_quiz(self):
        if not self.adaptive_quiz:
            topic = input("What topic would you like to be quizzed on? ")
            num_questions = int(input("How many questions would you like? "))
            difficulty = input("What difficulty level would you like to start with? (Easy/Medium/Hard) ")
            
            llm = ChatOpenAI(model="gpt-4o-mini")
            self.adaptive_quiz = Adaptive_Quiz(
                llm=llm,
                topic=topic,
                num_questions=num_questions,
                difficulty_increase_threshold=difficulty,
                show_options=True
            )
        
        self.adaptive_quiz.start_quiz()
        
        # After the quiz, we can add a summary to the student's memories
        quiz_summary = f"Completed an adaptive quiz on {self.adaptive_quiz.topic}. " \
                       f"Score: {self.adaptive_quiz.score}/{self.adaptive_quiz.num_questions}"
        self.add_memory(quiz_summary)

    def review_progress(self):
        memories = self.get_student_memories()
        prompt = f"Based on the following student interactions and quiz results, provide a summary of the student's progress and suggest areas for improvement:\n\n{memories}"
        messages = [{"role": "system", "content": prompt}]
        review = self.chat_with_gpt4(messages)
        print("Progress Review:")
        print(review)
        return review  # Return the review text

def main():
    st.set_page_config(page_title="Adaptive Learning Platform", page_icon="🎓", layout="wide")
    
    st.title("🧠 Adaptive Learning Platform")
    st.markdown("Experience personalized learning with our AI-powered tutor and adaptive quizzes!")

    # Sidebar for user input and session management
    with st.sidebar:
        st.header("👤 User Information")
        student_name = st.text_input("Enter your name:", value="TestStudent")
        
        st.header("🔑 API Keys")
        mem0_api_key = st.text_input("Mem0 API Key:", type="password")
        openai_api_key = st.text_input("OpenAI API Key:", type="password")
        
        if st.button("Start New Session"):
            st.session_state.platform = AdaptiveLearningPlatform(student_name, mem0_api_key, openai_api_key)
            st.session_state.messages = []
            st.success("New session started!")

    # Main area for chat and quiz
    if 'platform' in st.session_state:
        # Chat area
        st.header("💬 Chat with Your AI Tutor")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask your tutor something...")
        
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Simulate stream of response with milliseconds delay
                for chunk in st.session_state.platform.chat_with_gpt4([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]).split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    # Add a blinking cursor to simulate typing
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.platform.add_memory(user_input)

        st.markdown("---")

        # Quiz area
        st.header("📝 Take an Adaptive Quiz")
        if 'quiz_started' not in st.session_state:
            st.session_state.quiz_started = False
            st.session_state.current_question = None
            st.session_state.question_number = 0
            st.session_state.score = 0

        if not st.session_state.quiz_started:
            with st.form("quiz_setup"):
                topic = st.text_input("What topic would you like to be quizzed on?")
                num_questions = st.number_input("How many questions would you like?", min_value=1, max_value=10, value=5)
                difficulty = st.selectbox("What difficulty level would you like to start with?", ["Easy", "Medium", "Hard"])
                
                if st.form_submit_button("Begin Quiz"):
                    st.session_state.platform.adaptive_quiz = Adaptive_Quiz(
                        llm=ChatOpenAI(model="gpt-4o-mini"),
                        topic=topic,
                        num_questions=num_questions,
                        difficulty_increase_threshold=difficulty,
                        show_options=True
                    )
                    st.session_state.quiz_started = True
                    st.session_state.current_question = st.session_state.platform.adaptive_quiz.generate_initial_question()
                    st.session_state.question_number = 1
                    st.rerun()

        if st.session_state.quiz_started:
            if st.session_state.current_question and st.session_state.question_number <= st.session_state.platform.adaptive_quiz.num_questions:
                st.subheader(f"Question {st.session_state.question_number}")
                st.write(st.session_state.current_question.question)
                
                user_answer = st.radio("Select your answer:", st.session_state.current_question.options, key=f"q_{st.session_state.question_number}")
                
                if st.button("Submit Answer"):
                    correct = user_answer == st.session_state.current_question.answer
                    response_correct = "True" if correct else "False"
                    
                    if correct:
                        st.session_state.score += 1
                    
                    if st.session_state.question_number < st.session_state.platform.adaptive_quiz.num_questions:
                        next_question = st.session_state.platform.adaptive_quiz.generate_next_question(
                            st.session_state.current_question.question,
                            user_answer,
                            response_correct
                        )
                        st.session_state.current_question = next_question
                        st.session_state.question_number += 1
                        st.rerun()
                    else:
                        quiz_summary = f"Quiz completed! Final Score: {st.session_state.score}/{st.session_state.platform.adaptive_quiz.num_questions}"
                        st.success(quiz_summary)
                        st.session_state.platform.add_memory(quiz_summary)
                        st.session_state.quiz_started = False
                        st.session_state.current_question = None
                        st.session_state.question_number = 0
                        st.session_state.score = 0
            else:
                st.success("Quiz completed! Check your progress review for insights.")
                st.session_state.quiz_started = False
                st.session_state.question_number = 0
                st.session_state.score = 0

        st.markdown("---")

        # Progress Review
        st.header("📊 Progress Review")
        if st.button("Generate Progress Review"):
            progress_review = st.session_state.platform.review_progress()
            if progress_review:
                st.markdown(progress_review)
            else:
                st.error("Failed to generate progress review. Please try again.")

if __name__ == "__main__":
    main()