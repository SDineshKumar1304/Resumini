from agent.prompts import ATS_SCORING_PROMPT
class ATSAnalyzer:
    def __init__(self, llm):
        self.llm = llm

    def analyze(self, resume_text, role_description):
        try:
            prompt = ATS_SCORING_PROMPT.format(resume=resume_text, job=role_description)

            response = self.llm.generate(prompt)
            if not response or not response.strip():
                return 0, "AI analysis not available. Please check API key or network."

            score = 0
            for token in response.split():
                if token.strip('%').isdigit():
                    score = int(token.strip('%'))
                    break

            return score, response.strip()

        except Exception as e:
            return 0, f"Error in AI analysis: {e}"
