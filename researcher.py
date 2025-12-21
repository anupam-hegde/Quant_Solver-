import google.generativeai as genai
import os
import re
import json

EMBEDDED_PDF_CONTENT = """
HYDRAHACKS – SAMPLE QUANT WORD PROBLEMS (REFERENCE ONLY)
These examples illustrate the style and difficulty of questions participants are expected to generate.

CATEGORY 1: TIME, SPEED & DISTANCE (TSD)
Example 1 - Two Trains
Two trains start from stations A and B, which are 360 km apart, and travel toward each other. Train A travels at 60 km/h, and Train B travels at 80 km/h. After how many hours will they meet?
Options: A. 2 hours, B. 2.5 hours, C. 3 hours, D. 4 hours

Example 2 - Running Race
Ravi runs at 10 km/h, while Suman runs at 12 km/h. If Ravi starts 20 minutes earlier, after how long will Suman catch up?
Options: A. 1 hour, B. 1.5 hours, C. 2 hours, D. 2.5 hours

CATEGORY 2: WORK & TIME
Example 3 - Workers Completing a Job
Worker A can complete a job in 12 days. Worker B can complete the same job in 8 days. If both work together for 3 days, then A leaves, how many more days will B take to finish the remaining work?
Options: A. 2 days, B. 3 days, C. 4 days, D. 5 days

Example 4 - Partial Work
A and B together can finish a work in 6 days. B alone can finish it in 15 days. If A works alone for x days and then B completes the remaining work in 9 days, find x.
Options: A. 6, B. 8, C. 10, D. 12

CATEGORY 3: PIPES & CISTERNS
Example 5 - Filling a Tank
Pipe A fills a tank in 10 hours. Pipe B fills the tank in 15 hours. If both pipes are opened together, but Pipe B is closed after 3 hours, how much total time will it take to fill the tank?
Options: A. 7 hours, B. 8 hours, C. 9 hours, D. 10 hours

Example 6 - Filling + Leakage
A pipe can fill a tank in 12 hours, but due to a leak, it takes 15 hours to fill. How long will the leak alone take to empty the full tank?
Options: A. 30 hours, B. 36 hours, C. 45 hours, D. 60 hours

CATEGORY 4: PROFIT, LOSS & DISCOUNT
Example 7 - Cost Price and Selling Price
A shopkeeper buys a bag for 900 and sells it at a 20% profit. He then offers a 10% discount to a customer on the marked price. What is the marked price?
Options: A. 1200, B. 1250, C. 1300, D. 1350

Example 8 - Double Discount
An item is marked at 5000. A shopkeeper gives a 20% discount, and then a further 10% discount. What is the final selling price?
Options: A. 3400, B. 3500, C. 3600, D. 3700

CATEGORY 5: RATIO, MIXTURES & SHARING
Example 9 - Mixtures
A container has 40 liters of milk. 8 liters of milk is removed and replaced with water. This process is repeated once more. What is the final quantity of milk in the container?
Options: A. 24.32 L, B. 25.92 L, C. 26.22 L, D. 27.52 L

Example 10 - Dividing Money
A sum of 840 is divided between A, B, and C in the ratio 2:3:4. What is B's share?
Options: A. 240, B. 280, C. 320, D. 360

CATEGORY 6: AGE PROBLEMS
Example 11 - Present & Future Ages
The ratio of ages of a father and son is 5:2. Eight years ago, the ratio was 9:4. What is the father's present age?
Options: A. 40, B. 42, C. 45, D. 48

Example 12 - Reverse Age Problem
Ten years ago, A was twice as old as B. Ten years from now, A will be 10 years older than twice B's age. What is A's present age?
Options: A. 38, B. 40, C. 42, D. 44

CATEGORY 7: BOATS & STREAMS
Example 13 - Speed in Still Water
A boat travels 12 km downstream in 1 hour and the same distance upstream in 2 hours. What is the speed of the boat in still water?
Options: A. 9 km/h, B. 10 km/h, C. 11 km/h, D. 12 km/h

Example 14 - Stream Velocity
A boat can go 30 km downstream in 3 hours, and the speed of the stream is 2 km/h. Find the boat's speed in still water.
Options: A. 8, B. 10, C. 12, D. 14

CATEGORY 8: ALLOCATION & LOGICAL MATH
Example 15 - Scheduling Problem
A bus leaves station A every 30 minutes. Another bus leaves station B every 40 minutes. If both buses start at 6:00 AM, when will they next leave at the same time?
Options: A. 8:00 AM, B. 8:20 AM, C. 7:00 AM, D. 7:20 AM

FINAL NOTE:
These examples are NOT the questions you will generate tomorrow. They simply illustrate: story format, real-world math, multiple steps, solvable scenarios, clear variables, no contradictions, MCQ structure.
"""

class ResearcherAgent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def read_pdf_content(self):
        return EMBEDDED_PDF_CONTENT

    def conduct_research(self, custom_pdf_file=None):
        """
        Analyzes reference material. 
        """
        raw_text = ""
        
        if custom_pdf_file:
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(custom_pdf_file)
                for page in pdf_reader.pages:
                    raw_text += page.extract_text() + "\n"
                print("   📄 Successfully read custom PDF.")
            except Exception as e:
                return json.dumps({"error": f"Failed to read PDF: {str(e)}", "topics": ["General Math"]})
        else:
            print("   📄 Using Embedded Reference Material.")
            raw_text = self.read_pdf_content()
        
        # --- UPDATED PROMPT FOR STRICT JSON ---
        prompt = f"""
        You are an Expert Curriculum Researcher.
        Analyze the following reference material to extract specific Math Categories.
        
        REFERENCE MATERIAL:
        {raw_text[:25000]} 
        
        TASK:
        1. Identify ALL unique Categories/Domains listed (e.g., "Time Speed Distance", "Work & Time").
        2. Analyze difficulty and style.
        
        OUTPUT VALID JSON ONLY. NO MARKDOWN. NO TEXT BEFORE/AFTER.
        {{
            "topics": ["Exact Category Name 1", "Exact Category Name 2", "Exact Category Name 3"],
            "difficulty_analysis": "Brief analysis",
            "style_rules": ["Rule 1", "Rule 2"]
        }}
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            text = response.text.strip()
            
            # --- IMPROVED CLEANING LOGIC ---
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            
            # Attempt to parse JSON directly
            try:
                data = json.loads(text)
                # Validate it has topics
                if "topics" in data and isinstance(data["topics"], list):
                    return json.dumps(data)
            except json.JSONDecodeError:
                # Fallback: Regex to find the outermost brackets
                match = re.search(r'\{[\s\S]*\}', text)
                if match:
                    return match.group(0)
            
            return text

        except Exception as e:
            print(f"   ⚠️ Research Error: {e}")
            # Return a fallback that includes at least one specific topic so we know it failed
            return json.dumps({
                "topics": ["Time, Speed & Distance", "Work & Time", "Profit & Loss"],
                "error": str(e)
            })
