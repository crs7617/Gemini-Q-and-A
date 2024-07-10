# Penny App Backend

This FastAPI application is a backend part of the penny app,it generates finance-related questions using the Gemini 1.5 Flash API.

## Setup

### Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
Install Dependencies
bash
Copy code
pip install fastapi google-generativeai python-dotenv uvicorn
Set Up Environment Variables
Create a .env file and add your Gemini API key:

makefile
Copy code
GEMINI_API_KEY=your_api_key
Endpoints
Root Endpoint
GET /

Provides a welcome message and available chapters.

Generate Questions
GET /generate_questions/{chapter}

Generates 5 finance-related questions for the specified chapter.

Available Chapters:

introduction_to_personal_finance
setting_financial_goals
budgeting_and_expense_tracking
online_and_mobile_banking
Testing
This application has been tested using Postman.

Running the Application:

Start the FastAPI application with:

In bash:

uvicorn main:app --host 0.0.0.0 --port 8000

Ensure you have the GEMINI_API_KEY set in your environment variables before running the app.
