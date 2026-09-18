import json
import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field
from fastapi import FastAPI
from pathlib import Path
from pypdf import PdfReader
from time import sleep
import time

load_dotenv()
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

model = "openai/gpt-oss-120b"


app=FastAPI() #converts the python file into a web application,which will run on uvicorn server
#Function of Decorators: Decorators are used to modify the behavior of a function or class. In FastAPI, decorators are used to define routes and specify the HTTP methods (GET, POST, etc.) that the route will respond to. They allow you to easily associate a URL path with a specific function that will handle requests to that path.

class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = []

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    total_experience_years: float | None = None

    skills: list[str] = []
    experiences: list[Experience] = []
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []
resume_schema = Resume.model_json_schema()

#Question that will be asked to my LLM
class ChatRequest(BaseModel):
    question:str

#A function that will take the question response and my resume in JSON format and combine both to give an answer using a LLM
def ask_candidate(question: str,resume: Resume):
    system_prompt=f"""
You are an AI assistant representing a job candidate.

Below is everything you know about the candidate.
{resume.model_dump_json(indent=2)}

Rules:

1. Answer using this information as your foundation.
2. You may reasonably infer things like strengths, weaknesses, or interview-style answers by reasoning from the candidate's actual skills, projects, and experience — but never invent specific facts (like companies, job titles, numbers, or experiences) that aren't present in the data.
3. Never hallucinate
4. If the candidate does not know a perfect skillset,just respond from your perspective that he has not learnt that yet,but if the role requires,he/she is ready to learn
5. Be professional
6. Answer as if HR is interviewing this candidate. 
7. Always answer from the your(AI's) perspective. For example,any questions asked,always tell from your perspective,as if you are the candidate's personal AI assistant,and not the candidate himself/herself.
8. Do not use Markdown formatting (no asterisks, no bullet points with dashes, no headers). Respond in plain, natural sentences only.
9. Answer only what is being asked and stay to the point,do not provide extra information.Stay relevant to your answer
"""
    stream=client.chat.completions.create(
        model=model,

        messages=[
            {
                "role":"system",
                "content":system_prompt
            },

            

            {
                "role":"user",
                "content":question #User role will be the question asked in the LLM

            }
        ],
        stream=True
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
            time.sleep(0.02)

    #return response.choices[0].message.content



#Parsing Resume
def parse_resume(resume_text):
    system_prompt = f"""
    You are an expert resume parser.

    Extract information from the resume based on its meaning,
    not only based on exact section headings.

    Different resumes may use different headings.

    For example:
    - Experience
    - Professional Experience
    - Work History
    - Employment
    - Internships

    These may all contain relevant experience.

    Skills may also appear in the skills section, work experience,
    internships or projects.

    Return ONLY valid JSON matching this schema:

    {resume_schema}

    Important rules:

    1. Do not invent information.
    2. If a value is not available, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills mentioned across the entire resume.
    """
    user_prompt = f"""
    Parse the following resume:

    {resume_text}
    """
    message_system={
        "role" : "system",
        "content" : system_prompt
    }
    message_user={
        "role" : "user",
        "content" : user_prompt
    }
    messages=[message_system, message_user]
    response_format={
        "type": "json_object"
    }
    response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)
    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)
    return resume

#pdf extraction function
def read_pdf(file_path: Path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

@app.get("/") #decorator which is used to define a route for the root URL ("/") of the application. It specifies that this route will respond to HTTP GET requests.

#What will be there as we open the home page of the application, it will return a JSON response with a message indicating that the portfolio is running.
def home():
    resume_text = read_pdf(Path("Sayan_Kumar_ECE_CV.pdf"))
    resume = parse_resume(resume_text)
    print(resume.model_dump_json(indent=2))  #Converting my resume to JSON format and printing it to the console. The model_dump_json method is used to convert the Pydantic model instance (resume) into a JSON string representation. The indent=2 argument is used to format the JSON output with an indentation of 2 spaces for better readability.
    return{
        "message": "Resume Parsed"  #Everything we return here is displayed in the browser as a JSON response. The key is "message" and the value is "Resume Parsed".
    }

from fastapi.responses import StreamingResponse

@app.post("/chat")
def chat(request: ChatRequest):
    resume_text = read_pdf(Path("Sayan_Kumar_ECE_CV.pdf"))
    resume = parse_resume(resume_text)
    def generate():
        for piece in ask_candidate(request.question,resume):
            yield piece
    return StreamingResponse(generate(),media_type="text/plain")







 