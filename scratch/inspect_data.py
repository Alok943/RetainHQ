import json

with open('scratch/work_set.json', 'r', encoding='utf-8') as f:
    work_set = json.load(f)

print(f"Total work set: {len(work_set)}")
print("\nFirst 20 items:")
for w in work_set[:20]:
    print(f"ID {w['external_id']:<5} | {w['title']:<35} | {w['difficulty']:<7} | v1: {w['v1_primary']:<25} | {w['tags']}")

print("\nLast 20 items:")
for w in work_set[-20:]:
    print(f"ID {w['external_id']:<5} | {w['title']:<35} | {w['difficulty']:<7} | v1: {w['v1_primary']:<25} | {w['tags']}")
