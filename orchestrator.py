import json
import time
import hashlib
import requests
import re
import concurrent.futures
import random
import google.generativeai as genai
from solvers import SolverSquad
from validator import StrictValidator
from researcher import ResearcherAgent

# --- CONFIGURATION ---
API_KEY = ""
genai.configure(api_key=API_KEY)

GENERATOR_MODEL = "gemini-pro-latest" # Updated model name for better stability
APPS_SCRIPT_URL = "[https://script.google.com/macros/s/AKfycbwI79TvHGc9shdXx9_Writ1R5s_CiIb6jpQxRcaAFUE0gCvekUYE1ZwVD0y1rIEjd2sUQ/exec](https://script.google.com/macros/s/AKfycbwI79TvHGc9shdXx9_Writ1R5s_CiIb6jpQxRcaAFUE0gCvekUYE1ZwVD0y1rIEjd2sUQ/exec)"

class Orchestrator:
    def __init__(self):
        self.squad = SolverSquad()
        self.judge = StrictValidator()
        self.researcher = ResearcherAgent(API_KEY)
        
        self.history_hashes = set()
        self.stats = {
            "SUCCESS": 0, "HALLUCINATION": 0, "CONSENSUS_FAILURE": 0,
            "PARSING_ERROR": 0, "DUPLICATE": 0
        }
        
        self.research_findings = None
        self.available_topics = []

    def perform_research(self, custom_file=None):
        # Always re-run research if custom file provided, OR if we have no findings yet
        if custom_file or not self.research_findings:
            print("   🕵️ Researcher is analyzing...")
            json_text = self.researcher.conduct_research(custom_file)
            
            try:
                self.research_findings = json.loads(json_text)
                self.available_topics = self.research_findings.get("topics", ["General Math"])
                
                # Sanity check: Ensure topics is actually a list
                if isinstance(self.available_topics, str):
                    self.available_topics = [self.available_topics]
                    
                print(f"   ✅ Topics Found: {len(self.available_topics)} Categories loaded.")
            except Exception as e:
                print(f"   ❌ Research Parsing Failed: {e}")
                self.available_topics = ["General Math"]
            
        return self.research_findings

    def init_generator(self, custom_file=None):
        findings = self.perform_research(custom_file)
        
        # Pass the full list of topics to the system prompt so it understands the scope
        topics_list = ", ".join(findings.get('topics', ['General Math']))
        style_guide = findings.get('style_rules', [])
        
        system_prompt = f"""
        You are a Specialized Quant Generator for HydraHacks.
        
        MANDATE: Generate questions based on this Research.
        AVAILABLE CATEGORIES: {topics_list}
        STYLE: {style_guide}
        
        OUTPUT JSON FORMAT:
        {{ 
            "category": "The specific category chosen",
            "story": "The problem text...", 
            "options": ["A", "B", "C", "D"], 
            "correct_answer_numeric": "10", 
            "correct_option": "10",
            "difficulty": "Easy/Medium/Hard" 
        }}
        """
        
        self.generator = genai.GenerativeModel(
            model_name=GENERATOR_MODEL,
            system_instruction=system_prompt
        )
        self.reviewer = genai.GenerativeModel("gemini-1.5-flash")

    def clean_json(self, text):
        try:
            # Try standard replace first
            clean = text.replace("```json", "").replace("```", "").strip()
            return clean
        except:
            return text

    def is_duplicate(self, story):
        norm_story = re.sub(r'\s+', ' ', story.strip().lower())
        story_hash = hashlib.md5(norm_story.encode()).hexdigest()
        if story_hash in self.history_hashes: return True
        self.history_hashes.add(story_hash)
        return False

    def quality_check(self, story):
        try:
            resp = self.reviewer.generate_content(f"Review grammar. Return PASS or FAIL. Q: {story}")
            return "PASS" in resp.text
        except: return True

    def deploy_to_form(self, data):
        payload = {
            "question": data['story'],
            "difficulty": data.get('difficulty', 'Medium'),
            "category": data.get('category', 'General Quant'),
            "op1": data['options'][0], "op2": data['options'][1],
            "op3": data['options'][2], "op4": data['options'][3],
            "correct option": data['correct_option'],
            "explanation of option": data.get('explanation', 'Solved by AI.')
        }
        try: requests.post(APPS_SCRIPT_URL, json=payload)
        except Exception as e: print(f"Upload failed: {e}")

    def run_loop(self, custom_file=None):
        if not hasattr(self, 'generator'):
            self.init_generator(custom_file)

        # --- FIXED: FORCE RANDOM TOPIC SELECTION ---
        target_topic = "General Math"
        if self.available_topics and len(self.available_topics) > 0:
            target_topic = random.choice(self.available_topics)
            prompt = f"Generate a unique question specifically about: {target_topic}"
        else:
            prompt = "Generate a unique math question."

        # 1. Generate
        try:
            resp = self.generator.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            cleaned_text = self.clean_json(resp.text)
            data = json.loads(cleaned_text)
            
            # Force the category name to match what we requested
            data["category"] = target_topic

        except Exception as e:
            self.stats["PARSING_ERROR"] += 1
            return {"failure_type": "PARSING_ERROR", "reason": f"Invalid JSON: {e}"}

        # 2. Duplicate Detector
        if self.is_duplicate(data['story']):
            self.stats["DUPLICATE"] += 1
            return {"failure_type": "DUPLICATE", "reason": "Similar question exists"}

        # 3. Solve (PARALLEL EXECUTION)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_a = executor.submit(self.squad.solve_with_code, data['story'])
            future_b = executor.submit(self.squad.solve_with_logic, data['story'])
            future_c = executor.submit(self.squad.solve_with_skeptic, data['story'])
            
            ans_a = future_a.result()
            ans_b = future_b.result()
            ans_c = future_c.result()
        
        data['solver_a_raw'] = ans_a
        data['solver_b_raw'] = ans_b
        data['solver_c_raw'] = ans_c

        # 4. Validate
        is_valid, category, log = self.judge.validate(data['correct_answer_numeric'], ans_a, ans_b, ans_c)
        
        # Update stats safely
        if category in self.stats:
            self.stats[category] += 1
        else:
            # Fallback if validator returns a new category key
            self.stats["SUCCESS"] += 1

        if is_valid:
            if self.quality_check(data['story']):
                eq = "x=y"
                if "EQUATION:" in ans_a:
                    try: eq = ans_a.split("EQUATION:")[1].strip().split("\n")[0]
                    except: pass
                data['equation_visual'] = eq
                data['explanation'] = f"**Category:** {data.get('category')}\n**Equation:** {eq}\n\n**Logic:**\n{ans_b[:1500]}"
                self.deploy_to_form(data)
                return data
            else:
                self.stats["PARSING_ERROR"] += 1
                return {"failure_type": "QUALITY_CHECK", "reason": "Grammar check failed"}
        else:
            return {"failure_type": category, "reason": log}

