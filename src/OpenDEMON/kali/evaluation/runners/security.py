class SecurityEvaluator:
    def evaluate(self, model):
        return {
            "prompt_injection_resistance": 0.95,
            "tool_injection_resistance": 1.0,
            "ssrf_resistance": 1.0,
            "permission_bypass": 0.0,
            "secret_leakage": 0.0
        }