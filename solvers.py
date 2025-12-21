import google.generativeai as genai
import os

# CONFIGURATION
# API_KEY = "AIzaSy...PASTE_YOUR_KEY_HERE..."
# genai.configure(api_key=API_KEY)

# Use the stable model alias
MODEL_NAME = "gemini-flash-latest"

class SolverSquad:
    def __init__(self):
        # --- AGENT A: PYTHON ENGINEER (Calculates + Extracts Equation) ---
        self.agent_a = genai.GenerativeModel(
            model_name=MODEL_NAME,
            tools="code_execution",
            system_instruction="""
            You are Solver A (Python). 
            1. Write Python code to solve the problem.
            2. Ends with `print(final_answer)`.
            3. ALSO, write the core algebraic equation used as a comment or print it with prefix "EQUATION:".
            """
        )

        # --- AGENT B: LOGICIAN (Updated: NO LaTeX) ---
        self.agent_b = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction="""
            You are Solver B (Logician). Solve using step-by-step deduction.
            
            FORMATTING RULES (STRICT):
            1. DO NOT use LaTeX (no \\frac, \\times, $$, etc.).
            2. Write math in plain text:
               - Use "/" for division (e.g., "30/2 = 15").
               - Use "x" or "*" for multiplication.
               - Use "^" for exponents.
            3. Keep the explanation clean and readable for a general audience.
            4. End your response with exactly: "FINAL ANSWER: [Number]"
            """
        )

        # --- AGENT C: THE ADVERSARY (Updated: NO LaTeX) ---
        self.agent_c = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction="""
            You are Solver C (The Adversary). 
            Your goal is to find edge cases where the problem fails.
            If valid, solve it using estimation or a different method.
            
            FORMATTING RULES:
            1. No LaTeX formatting. Use plain text.
            2. End with "FINAL ANSWER: [Number]"
            """
        )

    def solve_with_code(self, problem):
        try:
            return self.agent_a.generate_content(f"Solve: {problem}").text.strip()
        except: return "Error"

    def solve_with_logic(self, problem):
        try:
            return self.agent_b.generate_content(f"Solve: {problem}").text.strip()
        except: return "Error"
        
    def solve_with_skeptic(self, problem):
        try:
            return self.agent_c.generate_content(f"Solve: {problem}").text.strip()
        except: return "Error"
