import re

class StrictValidator:
    def extract_number(self, text):
        if not text: return None
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", str(text))
        if not matches: return None
        values = [float(x) for x in matches]
        if len(values) > 1 and 1.0 in values: values.remove(1.0)
        return values[-1]

    def validate(self, gen_ans, sol_a, sol_b, sol_c):
        """
        Returns: (IsValid (bool), ErrorCategory (str), Log (str))
        Categories: 'SUCCESS', 'PARSING_ERROR', 'HALLUCINATION', 'CONSENSUS_FAILURE'
        """
        n_gen = self.extract_number(gen_ans)
        n_a = self.extract_number(sol_a)
        n_b = self.extract_number(sol_b)
        n_c = self.extract_number(sol_c)

        log = (f"\n      📊 COMPARISON: Gen[{n_gen}] | Code[{n_a}] | Logic[{n_b}] | Skeptic[{n_c}]")

        # 1. Parsing Check
        if None in [n_gen, n_a, n_b, n_c]:
            return False, "PARSING_ERROR", log + " -> ❌ Fail: Parsing Error"

        # 2. Consensus Check
        tol = 0.1
        # Check if Solvers agree with EACH OTHER
        solvers_agree = abs(n_a - n_b) < tol and abs(n_b - n_c) < tol
        
        # Check if Solvers agree with GENERATOR
        all_agree = solvers_agree and abs(n_gen - n_a) < tol

        if all_agree:
            return True, "SUCCESS", log + " -> ✅ Unanimous"
        elif solvers_agree and not all_agree:
            # Solvers agree, but Generator is different -> Generator Lied
            return False, "HALLUCINATION", log + " -> ❌ Fail: Generator Hallucination"
        else:
            # Solvers disagree with each other -> Math is ambiguous
            return False, "CONSENSUS_FAILURE", log + " -> ❌ Fail: Solvers Disagree"
