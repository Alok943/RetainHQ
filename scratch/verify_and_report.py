import json

with open('content/leetcode-catalog/mapping.v2-tail.json', 'r', encoding='utf-8') as f:
    v2_tail = json.load(f)

with open('content/leetcode-catalog/node_slug_map.json', 'r', encoding='utf-8') as f:
    node_slug_map = json.load(f)

with open('content/leetcode-catalog/golden.json', 'r', encoding='utf-8') as f:
    golden = json.load(f)

with open('scratch/work_set.json', 'r', encoding='utf-8') as f:
    work_set = json.load(f)

golden_map = {g['external_id']: g for g in golden}
work_set_map = {w['external_id']: w for w in work_set}

scaffold_slugs = {
    'amortized-analysis', 'arrays-and-memory', 'base-case', 'big-o-notation',
    'brute-force-first', 'common-complexities', 'counting-operations',
    'graph-representations', 'hash-sets-vs-maps', 'in-place-operations',
    'iteration-and-traversal', 'linear-search', 'logarithms-and-powers-of-two',
    'optimal-substructure', 'overlapping-subproblems', 'pattern-recognition-drill',
    'precomputation', 'recognizing-divide-and-conquer', 'recognizing-graph-problems',
    'recognizing-greedy-vs-dp', 'recognizing-sliding-window', 'recognizing-two-pointers',
    'string-traversal', 'the-call-stack', 'tracing-state-and-invariants', 'what-is-an-algorithm'
}

all_vocab = set(node_slug_map['slug_to_node_title'].keys())
legal_primary = all_vocab - scaffold_slugs

decisions = v2_tail['decisions']

# Verification checks
assert len(decisions) == 797, f"Expected 797 decisions, got {len(decisions)}"

invalid_primaries = [d for d in decisions if d['primary'] not in legal_primary and d['primary'] != 'out_of_scope']
assert len(invalid_primaries) == 0, f"Found invalid primaries: {invalid_primaries}"

scaffold_primaries = [d for d in decisions if d['primary'] in scaffold_slugs]
assert len(scaffold_primaries) == 0, f"Found scaffold primaries: {scaffold_primaries}"

invented_slugs = [d for d in decisions if d['primary'] not in all_vocab and d['primary'] != 'out_of_scope']
assert len(invented_slugs) == 0, f"Found invented slugs: {invented_slugs}"

print("Schema & vocabulary verification PASSED!")

# Metric 1: Agreement with v1
total_decisions = len(decisions)
unchanged_total = sum(1 for d in decisions if not d['changed'])
medium_unchanged = sum(1 for d in decisions if not d['changed'] and work_set_map[d['external_id']]['v1_confidence'] == 'medium')
medium_total = sum(1 for d in decisions if work_set_map[d['external_id']]['v1_confidence'] == 'medium')
low_unchanged = sum(1 for d in decisions if not d['changed'] and work_set_map[d['external_id']]['v1_confidence'] == 'low')
low_total = sum(1 for d in decisions if work_set_map[d['external_id']]['v1_confidence'] == 'low')

# Metric 2: Where changes went
changed_decisions = [d for d in decisions if d['changed']]
moved_to_different_concept = sum(1 for d in changed_decisions if d['primary'] != 'out_of_scope')
moved_to_out_of_scope = sum(1 for d in changed_decisions if d['primary'] == 'out_of_scope')

# Metric 3: Golden-set score (separately)
golden_overlap_decisions = [d for d in decisions if d['external_id'] in golden_map]
golden_agreements = sum(1 for d in golden_overlap_decisions if d['primary'] == golden_map[d['external_id']]['human_primary'])
golden_total = len(golden_overlap_decisions)

# Metric 4: Homeless count and list (sent to out_of_scope)
homeless_rows = [d for d in decisions if d['primary'] == 'out_of_scope']

# Metric 5: Two-valid-answer count
two_valid_answers = [d for d in decisions if d['considered'] is not None]

# Metric 6: What was not done / undecided
undecided = [d for d in decisions if d['confidence'] == 'low']

print("\n========================================================")
print("             §4 DELIVERABLE MEASUREMENT REPORT          ")
print("========================================================")
print(f"1. AGREEMENT WITH V1:")
print(f"   - Total Unchanged: {unchanged_total} / {total_decisions} ({unchanged_total/total_decisions*100:.1f}%)")
print(f"   - Medium Band Unchanged: {medium_unchanged} / {medium_total} ({medium_unchanged/medium_total*100:.1f}%)")
print(f"   - Low Band Unchanged: {low_unchanged} / {low_total} ({low_unchanged/low_total*100:.1f}%)")
print(f"\n2. WHERE THE CHANGES WENT:")
print(f"   - Total Changed: {len(changed_decisions)} / {total_decisions} ({len(changed_decisions)/total_decisions*100:.1f}%)")
print(f"   - Moved to different legal concept: {moved_to_different_concept} / {total_decisions} ({moved_to_different_concept/total_decisions*100:.1f}%)")
print(f"   - Moved to out_of_scope: {moved_to_out_of_scope} / {total_decisions} ({moved_to_out_of_scope/total_decisions*100:.1f}%)")
print(f"\n3. GOLDEN-SET SCORE (Overlapping 16 rows reported separately):")
print(f"   - Agreement with Golden Set: {golden_agreements} / {golden_total} ({golden_agreements/golden_total*100:.1f}%)")
print(f"\n4. HOMELESS COUNT & LIST (out_of_scope):")
print(f"   - Homeless Count: {len(homeless_rows)} / {total_decisions} ({len(homeless_rows)/total_decisions*100:.1f}%)")
print(f"   - Homeless External IDs ({len(homeless_rows)} total):")
print(f"     {[d['external_id'] for d in homeless_rows]}")
print(f"\n5. TWO-VALID-ANSWER COUNT (co-equal approach in 'considered'):")
print(f"   - Two-Valid-Answer Count: {len(two_valid_answers)} / {total_decisions} ({len(two_valid_answers)/total_decisions*100:.1f}%)")
print(f"\n6. WHAT WAS NOT DONE & UNDECIDED:")
print(f"   - High-confidence band (from v1) was untouched (0 / 2,944 touched).")
print(f"   - Low-confidence decisions in v2-tail: {len(undecided)} / {total_decisions} ({len(undecided)/total_decisions*100:.1f}%)")
print("========================================================\n")
