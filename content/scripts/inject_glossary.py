import json
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/inject_glossary.py <file.json> '<json_glossary_string>'")
        sys.exit(1)
    
    file_path = sys.argv[1]
    glossary_str = sys.argv[2]
    
    try:
        glossary = json.loads(glossary_str)
    except Exception as e:
        print(f"Error parsing glossary JSON: {e}")
        sys.exit(1)
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # preserve keys order if possible, inserting after metadata
    new_data = {}
    for k, v in data.items():
        new_data[k] = v
        if k == 'metadata':
            new_data['glossary'] = glossary
            
    if 'metadata' not in data:
        new_data['glossary'] = glossary
        
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully injected glossary into {file_path}")

if __name__ == '__main__':
    main()
