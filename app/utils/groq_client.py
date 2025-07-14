import groq
import json
import asyncio
from config import settings
from typing import Optional, Dict, Any


class GroqClient:
    def __init__(self):
        self.client = groq.Client(api_key=settings.GROQ_API_KEY)
        self.model = "llama3-8b-8192"

    async def generate_quiz(
        self, technology: str, difficulty: str, num_questions: int
    ) -> Optional[Dict[str, Any]]:
        prompt = f"""
        Generate a {difficulty} difficulty quiz about {technology} with exactly {num_questions} questions.
        The quiz should have:
        - A title
        - A brief description
        - {num_questions} questions with:
          * Clear question text
          * 4 options (only one correct)
          * Explanation for the correct answer

        Format the response as JSON with this exact structure:
        {{
            "title": "Quiz title",
            "description": "Brief description",
            "technology": "{technology}",
            "difficulty": "{difficulty}",
            "num_questions": {num_questions},
            "questions": [
                {{
                    "question_text": "Question text",
                    "explanation": "Explanation of correct answer",
                    "options": [
                        {{"option_text": "Option 1", "is_correct": true/false}},
                        {{"option_text": "Option 2", "is_correct": true/false}},
                        {{"option_text": "Option 3", "is_correct": true/false}},
                        {{"option_text": "Option 4", "is_correct": true/false}}
                    ]
                }}
            ]
        }}
        """

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    response_format={"type": "json_object"},
                    temperature=0.7,
                ),
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return None

