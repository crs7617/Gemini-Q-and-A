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
logging.basicConfig(level=logging.DEBUG)  # Change to DEBUG for detailed logs
logger = logging.getLogger(__name__)

app = FastAPI()

# Load API key from environment variables
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY environment variable not set")
    raise Exception("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=api_key)

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
        lines = response.text.strip().split('\n')

        # Logging each line for better understanding
        for i, line in enumerate(lines):
            logger.debug(f"Line {i}: {line}")

        if len(lines) < 8:
            error_msg = f"Failed to generate question for {CHAPTERS[chapter]}: Insufficient response from model."
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        question_text = lines[0].split(': ', 1)[1] if len(lines) > 0 and ': ' in lines[0] else ""
        options = [
            lines[2].split(' ', 1)[1] if len(lines) > 2 and ' ' in lines[2] else "",
            lines[3].split(' ', 1)[1] if len(lines) > 3 and ' ' in lines[3] else "",
            lines[4].split(' ', 1)[1] if len(lines) > 4 and ' ' in lines[4] else "",
            lines[5].split(' ', 1)[1] if len(lines) > 5 and ' ' in lines[5] else ""
        ]
        correct_answer = lines[6].split(': ', 1)[1] if len(lines) > 6 and ': ' in lines[6] else ""
        hint = lines[7].split(': ', 1)[1] if len(lines) > 7 and ': ' in lines[7] else ""

        # Log extracted values
        logger.debug(f"Extracted question: {question_text}")
        logger.debug(f"Extracted options: {options}")
        logger.debug(f"Extracted answer: {correct_answer}")
        logger.debug(f"Extracted hint: {hint}")

        # Check if any field is empty and log error
        if not question_text or not all(options) or not correct_answer or not hint:
            error_msg = f"Failed to generate question for {CHAPTERS[chapter]}: Incomplete response from model."
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        question = Question(
            question=question_text,
            options=options,
            ans=correct_answer,
            hint=hint
        )

        return question

    except HTTPException as http_err:
        raise http_err

    except Exception as err:
        error_msg = f"Failed to generate question for {CHAPTERS[chapter]}: {str(err)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/generate_questions/{chapter}")
async def generate_questions(chapter: str):
    try:
        if chapter not in CHAPTERS:
            raise HTTPException(status_code=400, detail="Invalid chapter")

        questions = {}
        for i in range(5):  # Generate 5 questions per chapter
            try:
                question = generate_question(chapter)
                questions[f"question {i+1}"] = question.dict()
            except HTTPException as http_err:
                logger.error(f"Error generating question {i+1} for {CHAPTERS[chapter]}: {http_err.detail}")
                continue  # Continue generating other questions even if one fails

        if not questions:
            raise HTTPException(status_code=500, detail="Failed to generate any questions")

        return {CHAPTERS[chapter]: questions}

    except HTTPException as http_err:
        raise http_err

    except Exception as err:
        error_msg = f"Unexpected error while generating questions: {str(err)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
