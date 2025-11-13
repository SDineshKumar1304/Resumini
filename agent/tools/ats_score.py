from agent.prompts import ATS_SCORING_PROMPT
# from google.generativeai.types import tool  

class ATSAnalyzer:
    def __init__(self, llm):
        self.llm = llm

    # @tool
    def analyze(self, resume_text: str, role_description: str):
        """
        Analyze resume vs job role using AI for ATS compatibility.
        Returns a score and summary explanation.
        """
        try:
            # Build the structured prompt
            prompt = ATS_SCORING_PROMPT.format(
                resume=resume_text,
                job=role_description
            )

            # Generate response via Gemini LLM
            response = self.llm.generate(prompt)

            # Safety check
            if not response or not response.strip():
                return {
                    "score": 0,
                    "message": "AI analysis not available. Please check API key or network."
                }

            # Extract ATS score (percentage if mentioned)
            score = 0
            for token in response.split():
                if token.strip('%').isdigit():
                    score = int(token.strip('%'))
                    break

            return {
                "score": score,
                "feedback": response.strip()
            }

        except Exception as e:
            return {
                "score": 0,
                "feedback": f"Error in AI analysis: {e}"
            }

