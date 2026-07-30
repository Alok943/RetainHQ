import json

with open('scratch/work_set.json', 'r', encoding='utf-8') as f:
    work_set = json.load(f)

with open('content/leetcode-catalog/golden.json', 'r', encoding='utf-8') as f:
    golden = json.load(f)

golden_map = {g['external_id']: g for g in golden}

print('The 16 work set items that overlap with golden.json:')
for w in work_set:
    if w['external_id'] in golden_map:
        g = golden_map[w['external_id']]
        print(f"ID {w['external_id']:<5} | Title: {w['title']:<35} | v1_primary: {w['v1_primary']:<25} | golden_primary: {g['human_primary']:<25} | v1_conf: {w['v1_confidence']}")
