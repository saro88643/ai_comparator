from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv
from openai import OpenAI
import os
import markdown
# ---------------- LOAD ENV ----------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- MONGODB ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["ai_project"]
users = db["users"]
chats = db["chats"]

# ---------------- GEMINI REAL AI ----------------
from google import genai

def ask_gemini(question):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
Answer the following question clearly and briefly.

Limit the answer to:
- Maximum 6 lines
- Simple explanation
- No extra examples
- No long paragraphs

Question: {question}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Gemini Error: {str(e)}"
def ask_groq(question):
    try:
        client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )

        prompt = f"""
Answer briefly and clearly.
Maximum 6 lines.
No long explanations.

Question: {question}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Groq Error: {str(e)}"
# ---------------- MOCK AI ----------------
def mock_ai(question):
    return f"This is a simulated AI response for the question: '{question}'. It provides a simplified explanation."

# ---------------- COMPARATOR USING GEMINI ----------------
def comparator_ai(question, answers):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        combined = "\n\n".join(
            [f"Answer {i+1}: {ans}" for i, ans in enumerate(answers)]
        )

        prompt = f"""
The user asked: {question}

Below are answers from multiple AI systems:

{combined}

Now:
- Identify common key points
- Remove unnecessary repetition
- Generate one final answer
- Maximum 8 lines
- Structured format
- Clear and concise

Final Answer:
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"Comparator Error: {str(e)}"
# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users.insert_one({
            "username": request.form.get("username"),
            "password": request.form.get("password")
        })
        return redirect("/login")
    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = users.find_one({
            "username": request.form.get("username"),
            "password": request.form.get("password")
        })

        if user:
            session["user_id"] = str(user["_id"])
            return redirect("/chat")

        return "Invalid Login"

    return render_template("login.html")

# ---------------- CHAT ----------------
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        question = request.form.get("question")

        gemini_answer = ask_gemini(question)
        groq_answer = ask_groq(question)

        answers = [gemini_answer, groq_answer]
        final_answer = comparator_ai(question, answers)

        chats.insert_one({
            "user_id": session["user_id"],
            "question": question,
            "gemini_answer": gemini_answer,
            "groq_answer": groq_answer,
            "final_answer": final_answer
        })

    # ✅ This must be OUTSIDE POST block but INSIDE function
    user_chats = list(chats.find({"user_id": session["user_id"]}))

    # ✅ Markdown formatting loop
    for chat in user_chats:
        if "gemini_answer" in chat:
            chat["gemini_answer"] = markdown.markdown(chat["gemini_answer"])
        if "groq_answer" in chat:
            chat["groq_answer"] = markdown.markdown(chat["groq_answer"])
        if "final_answer" in chat:
            chat["final_answer"] = markdown.markdown(chat["final_answer"])

    return render_template("chat.html", chats=user_chats)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)