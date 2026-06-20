import json
import yaml
from google import genai
from google.genai import types
import re

import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    return {"score": 1, "explanation": "Failed to parse"}

with open("tests/eval/eval_config.yaml") as f:
    config = yaml.safe_load(f)

with open("artifacts/traces/generated_traces.json") as f:
    traces = json.load(f)

results = {
    "routing_correctness": {"valid": 0, "total": 0, "errors": 0},
    "security_containment": {"valid": 0, "total": 0, "errors": 0}
}

for metric in config["custom_metrics"]:
    name = metric["name"]
    prompt_template = metric["prompt_template"]
    
    print(f"\nEvaluating metric: {name}")
    for case in traces["eval_cases"]:
        case_id = case["eval_case_id"]
        agent_data_str = json.dumps(case["agent_data"], indent=2)
        prompt = prompt_template.replace("{agent_data}", agent_data_str)
        
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0
                )
            )
            res_json = extract_json(response.text)
            print(f"[{case_id}] Score: {res_json.get('score')} - {res_json.get('explanation')}")
            
            results[name]["total"] += 1
            if res_json.get("score") == 5:
                results[name]["valid"] += 1
                
        except Exception as e:
            print(f"[{case_id}] Error: {e}")
            results[name]["total"] += 1
            results[name]["errors"] += 1

print("\n--- Evaluation Summary ---")
for k, v in results.items():
    print(f"{k}: {v['valid']}/{v['total']} valid (Errors: {v['errors']})")
