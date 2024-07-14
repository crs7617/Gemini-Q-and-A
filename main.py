from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load API key from environment variables
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY environment variable not set")
    raise Exception("GEMINI_API_KEY environment variable not set")

try:
    genai.configure(api_key=api_key)
    # Test the API key by generating a simple response
    model = genai.GenerativeModel('gemini-1.5-flash')
    test_response = model.generate_content("Test")
    if not test_response.text:
        raise Exception("Invalid API key or model access")
except Exception as e:
    logger.error(f"Error configuring Gemini API: {str(e)}")
    raise Exception(f"Error configuring Gemini API: {str(e)}")

class Question(BaseModel):
    question: str
    options: list[str]
    ans: str
    hint: str

CHAPTERS = {
    "introduction_to_personal_finance": "Introduction to Personal Finance",
    "setting_financial_goals": "Setting Financial Goals",
    "budgeting_and_expense_tracking": "Budgeting and Expense Tracking",
    "online_and_mobile_banking": "Online and Mobile Banking"
}

@app.get("/")
async def root():
    return JSONResponse(content={
        "message": "Welcome to the Finance Q&A Generator",
        "usage": "Use the /generate_questions/{chapter} endpoint to generate questions",
        "available_chapters": list(CHAPTERS.keys())
    })

def generate_question(chapter):
    try:
        prompt = f"""
        Generate a finance question related to {CHAPTERS[chapter]} with 4 options, the correct answer, and a hint.
        The question should be suitable for someone learning about personal finance.
        Format:
        Question: [question text]
        Options:
        A) [option A]
        B) [option B]
        C) [option C]
        D) [option D]
        Answer: [correct option letter]
        Hint: [hint text]
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        logger.debug(f"Model response: {response.text}")
        
        # Parse the response
        lines = response.text.strip().split('\n')
        question_text = next((line.split(': ', 1)[1] for line in lines if line.startswith("Question:")), "")
        options = [line.split(') ', 1)[1] for line in lines if line.strip().startswith(('A)', 'B)', 'C)', 'D)'))]
        correct_answer = next((line.split(': ', 1)[1] for line in lines if line.startswith("Answer:")), "")
        hint = next((line.split(': ', 1)[1] for line in lines if line.startswith("Hint:")), "")

        if not question_text or len(options) != 4 or not correct_answer or not hint:
            raise ValueError("Invalid response format from model")

        return Question(
            question=question_text,
            options=options,
            ans=correct_answer,
            hint=hint
        )

    except Exception as err:
        logger.error(f"Error generating question for {CHAPTERS[chapter]}: {str(err)}")
        raise ValueError(f"Failed to generate question: {str(err)}")

@app.get("/generate_questions/{chapter}")
async def generate_questions(chapter: str):
    if chapter not in CHAPTERS:
        raise HTTPException(status_code=400, detail="Invalid chapter")

    questions = {}
    for i in range(10):  # Generate 10 questions per chapter
        try:
            question = generate_question(chapter)
            questions[f"question_{i+1}"] = question.dict()
        except Exception as err:
            logger.error(f"Error generating question {i+1} for {CHAPTERS[chapter]}: {str(err)}")
            continue  # Continue generating other questions even if one fails

    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate any questions")

    return JSONResponse(content={CHAPTERS[chapter]: questions})

@app.get("/generate_all_questions")
async def generate_all_questions():
    all_questions = {}
    for chapter in CHAPTERS:
        questions = {}
        for i in range(10):  # Generate 10 questions per chapter
            try:
                question = generate_question(chapter)
                questions[f"question_{i+1}"] = question.dict()
            except Exception as err:
                logger.error(f"Error generating question {i+1} for {CHAPTERS[chapter]}: {str(err)}")
                continue  # Continue generating other questions even if one fails
        
        if questions:
            all_questions[CHAPTERS[chapter]] = questions
        else:
            logger.warning(f"Failed to generate any questions for {CHAPTERS[chapter]}")

    if not all_questions:
        raise HTTPException(status_code=500, detail="Failed to generate any questions for any chapter")

    return JSONResponse(content=all_questions)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)