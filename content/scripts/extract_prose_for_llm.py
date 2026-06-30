import sys
import json
from pathlib import Path

def extract_prose(lesson):
    text = []
    
    # Overview
    ov = lesson.get('overview', {})
    if isinstance(ov, dict):
        text.append(ov.get('what', ''))
        text.append(ov.get('why', ''))
    
    # Why learning this
    text.extend(lesson.get('why_learning_this', []))
    
    # Explanation
    text.append(lesson.get('explanation', ''))
    
    # Mental model
    mm = lesson.get('mental_model', {})
    if isinstance(mm, dict):
        text.append(mm.get('intuition', ''))
        text.append(mm.get('description', ''))
        
    # Sections (born-visual)
    for s in lesson.get('sections', []):
        text.append(s.get('body', ''))
        text.append(s.get('recap', ''))
        
    # Key points
    for p in lesson.get('key_points', []):
        text.append(p.get('detail', ''))
        
    # Common mistakes
    for m in lesson.get('common_mistakes', []):
        text.append(m.get('explanation', ''))
        
    # Method
    text.extend(lesson.get('method', []))
    
    # Formula
    f = lesson.get('formula', {})
    if isinstance(f, dict):
        text.append(f.get('explain', ''))
        
    # Analogy
    text.append(lesson.get('analogy', ''))
    
    # Worked example
    we = lesson.get('worked_example', {})
    if isinstance(we, dict):
        text.append(we.get('problem', ''))
        text.extend(we.get('steps', []))
    elif isinstance(we, list):
        for w in we:
            text.append(w.get('problem', ''))
            text.extend(w.get('steps', []))
            
    # filter out empty strings and join
    return " ".join([t for t in text if isinstance(t, str) and t.strip()])

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_prose_for_llm.py <file.json>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        lesson = json.load(f)
        
    if 'glossary' in lesson:
        print("ALREADY_HAS_GLOSSARY")
        return
        
    prose = extract_prose(lesson)
    print(prose)

if __name__ == '__main__':
    main()
