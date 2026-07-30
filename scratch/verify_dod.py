import json, os

v2_path = 'content/leetcode-catalog/mapping.v2-tail.json'
assert os.path.exists(v2_path), "mapping.v2-tail.json does not exist!"

with open(v2_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

assert data['mapping_version'] == 'v2-tail'
assert data['based_on'] == 'v1.1'
assert data['input_rows'] == 797
assert len(data['decisions']) == 797

with open('content/leetcode-catalog/node_slug_map.json', 'r', encoding='utf-8') as f:
    node_slug_map = json.load(f)

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

for i, d in enumerate(data['decisions']):
    # Check fields
    expected_fields = {'external_id', 'v1_primary', 'primary', 'considered', 'confidence', 'reason', 'changed'}
    assert set(d.keys()) == expected_fields, f"Row {i} fields mismatch: {d.keys()}"
    
    # Check primary
    assert d['primary'] in legal_primary or d['primary'] == 'out_of_scope', f"Row {i} invalid primary: {d['primary']}"
    assert d['primary'] not in scaffold_slugs, f"Row {i} scaffold primary: {d['primary']}"
    
    # Check considered
    if d['considered'] is not None:
        assert d['considered'] in legal_primary, f"Row {i} invalid considered: {d['considered']}"
        assert d['considered'] != d['primary'], f"Row {i} considered == primary: {d['considered']}"
        assert d['considered'] not in scaffold_slugs, f"Row {i} scaffold considered: {d['considered']}"
        
    # Check confidence
    assert d['confidence'] in ('high', 'medium', 'low'), f"Row {i} invalid confidence: {d['confidence']}"
    
    # Check changed
    assert d['changed'] == (d['primary'] != d['v1_primary']), f"Row {i} changed mismatch: {d['changed']} vs {d['primary'] != d['v1_primary']}"

print("All Definition of Done JSON checks passed successfully!")
