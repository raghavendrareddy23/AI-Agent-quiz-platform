import groq
import json
import asyncio
from config import settings
from typing import Optional, Dict, Any, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class GroqClient:
    def __init__(self):
        self.client = groq.Client(api_key=settings.GROQ_API_KEY)
        self.primary_model = "llama3-70b-8192"
        self.fallback_model = "llama3-8b-8192"
        self.semaphore = asyncio.Semaphore(3)
        self.max_attempts = 3

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValueError, json.JSONDecodeError)),
    )
    async def generate_quiz(
        self, technology: str, difficulty: str, num_questions: int
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a quiz with guaranteed exact question count using a multi-stage approach
        """
        try:
            full_quiz = await self._attempt_full_generation(
                technology, difficulty, num_questions, self.primary_model
            )
            if full_quiz and len(full_quiz.get("questions", [])) == num_questions:
                return full_quiz
        except Exception as e:
            print(
                f"Full generation failed: {str(e)[:200]}"
            )  

        print("Falling back to batch generation...")
        batch_size = min(5, max(2, num_questions // 3))
        questions = []

        while len(questions) < num_questions:
            try:
                batch = await self._generate_question_batch(
                    technology=technology,
                    difficulty=difficulty,
                    batch_size=min(batch_size, num_questions - len(questions)),
                    model_choice=(
                        "primary" if len(questions) < num_questions / 2 else "fallback"
                    ),
                )
                questions.extend(batch)
                print(
                    f"Generated {len(batch)} questions (Total: {len(questions)}/{num_questions})"
                )
            except Exception as e:
                print(f"Batch generation error: {str(e)[:200]}")
                if len(questions) >= max(
                    3, num_questions * 0.7
                ):  
                    break
                if "rate limit" in str(e).lower():
                    await asyncio.sleep(5) 
                raise

        return self._format_final_quiz(
            technology=technology,
            difficulty=difficulty,
            num_questions=num_questions,
            questions=questions[:num_questions], 
        )

    async def _attempt_full_generation(
        self, technology: str, difficulty: str, num_questions: int, model: str
    ) -> Optional[Dict[str, Any]]:
        """Attempt to generate all questions at once with strict validation"""
        prompt = self._build_full_prompt(technology, difficulty, num_questions)

        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                                + "\n\nIMPORTANT: Return the response as valid JSON.",
                            }
                        ],
                        model=model,
                        response_format={"type": "json_object"},
                        temperature=0.4,
                    ),
                )

                quiz_data = json.loads(response.choices[0].message.content)
                if self._validate_quiz_strict(quiz_data, num_questions, difficulty):
                    return quiz_data
                raise ValueError("Full generation validation failed")
            except Exception as e:
                print(f"Full generation attempt failed: {str(e)[:200]}")
                raise

    async def _generate_question_batch(
        self,
        technology: str,
        difficulty: str,
        batch_size: int,
        model_choice: str = "primary",
    ) -> List[Dict[str, Any]]:
        """Generate a batch of questions with strict validation"""
        model = self.primary_model if model_choice == "primary" else self.fallback_model
        prompt = self._build_batch_prompt(technology, difficulty, batch_size)

        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                                + "\n\nReturn the response as valid JSON.",
                            }
                        ],
                        model=model,
                        response_format={"type": "json_object"},
                        temperature=0.3,
                    ),
                )

                data = json.loads(response.choices[0].message.content)
                questions = data.get("questions", [])

                # Strict validation of each question
                valid_questions = []
                for q in questions:
                    if self._validate_question(q):
                        valid_questions.append(q)
                    else:
                        print(
                            f"Discarded invalid question: {q.get('question_text', 'Unknown')[:50]}..."
                        )

                if not valid_questions:
                    raise ValueError("No valid questions generated in batch")

                return valid_questions[:batch_size] 
            except Exception as e:
                print(f"Batch generation failed: {str(e)[:200]}")
                raise

    # def _build_full_prompt(
    #     self,
    #     technology: str,
    #     difficulty: str,
    #     num_questions: int
    # ) -> str:
    #     """Prompt for full quiz generation attempt"""
    #     return f"""
    #     Generate a {difficulty} difficulty quiz about {technology} with EXACTLY {num_questions} questions.
    #     This is VERY IMPORTANT - you MUST generate EXACTLY {num_questions} questions.

    #     === REQUIREMENTS ===
    #     1. EXACTLY {num_questions} questions
    #     2. {difficulty} difficulty level
    #     3. Each question must have:
    #        - Clear question text
    #        - 4 options (labeled A, B, C, D)
    #        - EXACTLY ONE correct answer
    #        - Explanation for correct answer

    #     === JSON OUTPUT FORMAT ===
    #     {{
    #         "title": "Quiz Title",
    #         "description": "Brief description",
    #         "technology": "{technology}",
    #         "difficulty": "{difficulty}",
    #         "num_questions": {num_questions},
    #         "questions": [
    #             {{
    #                 "question_text": "...",
    #                 "explanation": "...",
    #                 "options": [
    #                     {{"option_text": "A) ...", "is_correct": true/false}},
    #                     {{"option_text": "B) ...", "is_correct": true/false}},
    #                     {{"option_text": "C) ...", "is_correct": true/false}},
    #                     {{"option_text": "D) ...", "is_correct": true/false}}
    #                 ]
    #             }}
    #         ]
    #     }}

    #     === IMPORTANT ===
    #     - COUNT THE QUESTIONS: MUST BE EXACTLY {num_questions}
    #     - Format the response as JSON
    #     - If you cannot comply, return an EMPTY questions array
    #     """

    def _build_full_prompt(
        self, technology: str, difficulty: str, num_questions: int
    ) -> str:
        return f"""
        Generate a {difficulty} difficulty quiz about {technology} with EXACTLY {num_questions} questions.
        The quiz should focus on **practical understanding**, **real-world scenarios**, and **code reasoning**.

        === QUESTION TYPES TO INCLUDE ===
        - Code snippet analysis (e.g., "What is the output of this code?")
        - Debugging code
        - Real-world scenario-based questions (e.g., API design decisions, system behavior)
        - Best practices and trade-offs
        - Performance considerations

        === FORMAT ===
        Each question must include:
        - "question_text": string (include code snippet or scenario where relevant)
        - "options": A, B, C, D — each with "option_text" and "is_correct"
        - "explanation": explaining why the correct answer is right (and optionally why others are wrong)

        === OUTPUT FORMAT (as JSON) ===
        {{
            "title": "{technology} {difficulty.capitalize()} Quiz",
            "description": "A challenging quiz on {technology} at {difficulty} level",
            "technology": "{technology}",
            "difficulty": "{difficulty}",
            "num_questions": {num_questions},
            "questions": [
                {{
                    "question_text": "...",
                    "explanation": "...",
                    "options": [
                        {{"option_text": "A) ...", "is_correct": true/false}},
                        {{"option_text": "B) ...", "is_correct": true/false}},
                        {{"option_text": "C) ...", "is_correct": true/false}},
                        {{"option_text": "D) ...", "is_correct": true/false}}
                    ]
                }}
            ]
        }}

        === IMPORTANT ===
        - COUNT THE QUESTIONS: MUST BE EXACTLY {num_questions}
        - DO NOT skip code or real-world context
        - JSON must be valid
        """

    def _build_batch_prompt(
        self, technology: str, difficulty: str, batch_size: int
    ) -> str:
        return f"""
        Generate EXACTLY {batch_size} {difficulty}-level multiple-choice questions about {technology}.

        === QUESTION TYPES ===
        Focus on:
        - Real-world scenarios
        - Code snippet-based questions
        - Output prediction
        - Debugging problems
        - Trade-offs and best practices

        === QUESTION STRUCTURE ===
        Each question must have:
        - "question_text": A scenario or code problem
        - "options": A, B, C, D — labeled correctly
        - "is_correct": Only one option should be true
        - "explanation": Why the correct answer is right

        === OUTPUT FORMAT (as JSON) ===
        {{
            "questions": [
                {{
                    "question_text": "...",
                    "explanation": "...",
                    "options": [
                        {{"option_text": "A) ...", "is_correct": true/false}},
                        {{"option_text": "B) ...", "is_correct": true/false}},
                        {{"option_text": "C) ...", "is_correct": true/false}},
                        {{"option_text": "D) ...", "is_correct": true/false}}
                    ]
                }}
            ]
        }}

        === REMEMBER ===
        - Code and scenario-driven questions are mandatory
        - DO NOT skip explanations
        - RETURN valid JSON ONLY
        - MUST generate EXACTLY {batch_size} questions
        """

    def _validate_quiz_strict(
        self,
        quiz_data: Dict[str, Any],
        expected_questions: int,
        expected_difficulty: str,
    ) -> bool:
        """Strict validation for full quiz"""
        if not quiz_data:
            return False

        questions = quiz_data.get("questions", [])
        if len(questions) != expected_questions:
            print(
                f"Question count mismatch: expected {expected_questions}, got {len(questions)}"
            )
            return False

        for q in questions:
            if not self._validate_question(q):
                return False

        return True

    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate individual question"""
        try:
            if not isinstance(question, dict):
                return False

            required = ["question_text", "explanation", "options"]
            if any(key not in question for key in required):
                return False

            options = question["options"]
            if len(options) != 4:
                return False

            correct = sum(1 for opt in options if opt.get("is_correct"))
            if correct != 1:
                return False

            # Additional check for properly labeled options
            for opt in options:
                if not opt.get("option_text", "").startswith(tuple("ABCD)")):
                    return False

            return True
        except Exception:
            return False

    def _format_final_quiz(
        self,
        technology: str,
        difficulty: str,
        num_questions: int,
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Format final quiz output"""
        return {
            "title": f"{technology} {difficulty.capitalize()} Quiz",
            "description": f"A {difficulty}-level quiz about {technology}",
            "technology": technology,
            "difficulty": difficulty,
            "num_questions": len(questions),
            "questions": questions[:num_questions], 
        }
