import json
import os
import sys

slugs = [
    "in-place-operations", "prefix-sums", "frequency-counting", 
    "palindromes", "two-pointers-on-strings", "frequency-arrays", 
    "bubble-sort", "selection-sort", "insertion-sort", 
    "linear-search", "binary-search"
]

base_dir = r"c:\Users\aloks\Desktop\RetainHQ\content\roadmaps\dsa"

for slug in slugs:
    path = os.path.join(base_dir, f"{slug}.json")
    if not os.path.exists(path):
        print(f"Missing file: {path}")
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"=== {slug} ===")
    has_steps = "steps" in data.get("viz", {})
    has_predictions = "predictions" in data.get("viz", {})
    has_decision = "repeated_decision" in data.get("mental_model", {})
    
    print(f"  steps: {has_steps}")
    print(f"  predictions: {has_predictions}")
    print(f"  repeated_decision: {has_decision}")
    if has_decision:
        print(f"  decision text: {data['mental_model']['repeated_decision']}")

