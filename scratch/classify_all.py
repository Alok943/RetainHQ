import json
import datetime

with open('scratch/work_set.json', 'r', encoding='utf-8') as f:
    work_set = json.load(f)

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

all_vocabulary = set(node_slug_map['slug_to_node_title'].keys())
legal_primary_slugs = all_vocabulary - scaffold_slugs

def classify_problem(item):
    ext_id = item['external_id']
    title = item['title']
    slug = item['slug']
    diff = item['difficulty']
    tags = item['tags']
    v1_p = item['v1_primary']
    v1_c = item['v1_confidence']
    
    # Defaults
    primary = v1_p
    considered = None
    confidence = v1_c
    reason = item.get('v1_reason', '')

    title_lower = title.lower()

    # Rule 0: Out of scope checks (SQL, Shell, Multi-threading, Pandas, Pure basic simulation with no pattern)
    # Check SQL / Shell / Concurrency / Pandas
    if any(t in tags for t in ['database', 'shell', 'concurrency', 'pandas']):
        primary = 'out_of_scope'
        considered = None
        confidence = 'high'
        reason = 'Database, shell, concurrency or pandas domain problem with no DSA pattern.'
        return primary, considered, confidence, reason

    if any(k in title_lower for k in ['print in order', 'fizz buzz multithreaded', 'building H2O', 'zero even odd', 'the dining philosophers', 'combine two tables', 'second highest salary', 'nth highest salary', 'delete duplicate emails']):
        primary = 'out_of_scope'
        considered = None
        confidence = 'high'
        reason = 'Concurrency or SQL problem outside algorithmic scope.'
        return primary, considered, confidence, reason

    # Trivial implementation / simulation with no named pattern (homeless problems)
    homeless_titles = [
        'concatenate array', 'truncate sentence', 'defanging an ip address', 'shuffle the array',
        'build array from permutation', 'richest customer wealth', 'number of good pairs',
        'convert the temperature', 'final value of variable after performing operations',
        'jewels and stones', 'goal parser interpretation', 'decode xored array',
        'count items matching a rule', 'how many numbers are smaller than the current number',
        'subtract the product and sum of digits of an integer', 'decompress run-length encoded list',
        'create target array in the given order', 'check if two string arrays are equivalent',
        'count the number of consistent strings', 'split a string in balanced strings',
        'maximum number of words found in sentences', 'replace all digits with characters',
        'sorting the sentence', 'count asterisks', 'check if all a\'s appears before all b\'s',
        'minimum sum of four digit number after splitting digits', 'cells in a range on an excel sheet',
        'sum of all odd length subarrays', 'matrix diagonal sum', 'count Equal and divisible pairs in an array',
        'count pairs whose sum is less than target', 'find words containing character',
        'determine if string halves are alike', 'number of arithmetic triplets',
        'capitalize the title', 'check if numbers are ascending in a sentence',
        'rings and rods', 'maximum number of pairs in array', 'minimum number of operations to move all balls to each box',
        'reformat phone number', 'check if number has equal digit count and digit value',
        'greatest english letter in upper and lower case', 'calculate amount paid in taxes',
        'count integers with even digit sum', 'percentage of letter in string',
        'count hills and valleys in an array', 'divide a string into groups of size k',
        'check if word equals summation of two words', 'minimum distance to the target element',
        'determine whether matrix can be obtained by rotation', 'check if all characters have equal number of occurrences',
        'three consecutive odds', 'count special quad'
    ]
    
    if any(ht in title_lower for ht in homeless_titles):
        primary = 'out_of_scope'
        considered = None
        confidence = 'high'
        reason = 'Basic simulation or element-wise iteration; no reusable DSA pattern taught.'
        return primary, considered, confidence, reason

    # Refine specific patterns
    # Trapping rain water
    if 'trapping rain water' in title_lower:
        primary = 'two-pointers'
        considered = 'monotonic-stack'
        confidence = 'high'
        reason = 'Two pointers maintain boundary maxima to compute trapped water.'
        return primary, considered, confidence, reason

    # Pascal's triangle
    if title_lower in ["pascal's triangle", "pascal's triangle ii"]:
        primary = 'combinatorics-and-counting'
        considered = '2d-arrays-and-matrices'
        confidence = 'high'
        reason = 'Generates binomial coefficients nCr via additive recurrences.'
        return primary, considered, confidence, reason

    # Best time to buy and sell stock
    if title_lower == 'best time to buy and sell stock':
        primary = 'kadane-s-algorithm'
        considered = 'sliding-window-variable'
        confidence = 'high'
        reason = 'Tracks running minimum price to maximize max profit difference.'
        return primary, considered, confidence, reason

    # Word break
    if title_lower == 'word break':
        primary = 'tabulation-bottom-up'
        considered = 'memoization-top-down'
        confidence = 'medium'
        reason = '1D DP tracks reachable prefix indices using dictionary words.'
        return primary, considered, confidence, reason

    # Search a 2D Matrix II
    if title_lower == 'search a 2d matrix ii':
        primary = 'two-pointers'
        considered = 'binary-search'
        confidence = 'medium'
        reason = 'Starts at top-right corner, pruning row or column based on target comparison.'
        return primary, considered, confidence, reason

    # Serialize and Deserialize Binary Tree
    if title_lower == 'serialize and deserialize binary tree':
        primary = 'binary-tree-and-traversals'
        considered = 'level-order-bfs'
        confidence = 'medium'
        reason = 'Encodes tree structure into string using preorder/levelorder traversal.'
        return primary, considered, confidence, reason

    # Longest Increasing Path in a Matrix
    if title_lower == 'longest increasing path in a matrix':
        primary = 'memoization-top-down'
        considered = 'dfs-on-graphs'
        confidence = 'high'
        reason = 'DFS with memoization computes longest increasing paths on DAG grid.'
        return primary, considered, confidence, reason

    # Task Scheduler
    if title_lower == 'task scheduler':
        primary = 'why-greedy-works'
        considered = 'top-k-with-a-heap'
        confidence = 'medium'
        reason = 'Schedules highest-frequency tasks greedily with idle slot formula.'
        return primary, considered, confidence, reason

    # Shortest Subarray with Sum at Least K
    if title_lower == 'shortest subarray with sum at least k':
        primary = 'monotonic-deque'
        considered = 'prefix-sums'
        confidence = 'high'
        reason = 'Monotonic deque maintains prefix sum indices for min length subarray.'
        return primary, considered, confidence, reason

    # Check if v1_primary was a scaffold slug (illegal as primary)
    if v1_p in scaffold_slugs:
        # Re-bin scaffold primary
        if v1_p == 'arrays-and-memory' or v1_p == 'iteration-and-traversal' or v1_p == 'in-place-operations':
            if 'two-pointers' in tags or 'two-pointers' in title_lower:
                primary = 'two-pointers'
            elif 'hash-table' in tags:
                primary = 'hash-tables'
            elif 'prefix-sum' in tags:
                primary = 'prefix-sums'
            elif 'matrix' in title_lower or '2d-array' in title_lower or 'matrix' in tags:
                primary = '2d-arrays-and-matrices'
            else:
                primary = 'out_of_scope'
                reason = 'General array manipulation with no pattern; out of scope.'
        elif v1_p == 'string-traversal':
            if 'two-pointers' in tags or 'palindrome' in title_lower:
                primary = 'two-pointers-on-strings'
            elif 'string' in tags and 'hash-table' in tags:
                primary = 'frequency-counting'
            else:
                primary = 'out_of_scope'
                reason = 'Basic string iteration without specialized pattern.'
        elif v1_p in ['recognizing-greedy-vs-dp', 'recognizing-sliding-window', 'recognizing-two-pointers', 'recognizing-graph-problems', 'recognizing-divide-and-conquer']:
            if 'greedy' in tags:
                primary = 'why-greedy-works'
            elif 'sliding-window' in tags:
                primary = 'sliding-window-variable'
            elif 'two-pointers' in tags:
                primary = 'two-pointers'
            elif 'depth-first-search' in tags or 'breadth-first-search' in tags:
                primary = 'dfs-on-graphs'
            else:
                primary = 'brute-force-first' if 'brute-force-first' not in scaffold_slugs else 'out_of_scope'
        else:
            primary = 'out_of_scope'
            reason = f'Scaffold slug {v1_p} reclassified.'

    # Handle dual primary / runner-up logic for common patterns
    if primary == 'hash-tables' and ('two-pointers' in tags or 'two-pointers' in title_lower):
        considered = 'two-pointers'
    elif primary == 'two-pointers' and ('hash-table' in tags or 'hashmap' in title_lower):
        considered = 'hash-tables'
    elif primary == 'sliding-window-variable' and 'hash-table' in tags:
        considered = 'hash-tables'
    elif primary == 'top-k-with-a-heap' and ('quickselect' in tags or 'quickselect' in title_lower):
        considered = 'quickselect'
    elif primary == 'quickselect':
        considered = 'top-k-with-a-heap'
    elif primary == 'merge-sort' and 'counting' in tags:
        considered = 'fenwick-tree-bit'
    elif primary == 'prefix-sums' and 'hash-table' in tags:
        considered = 'hash-tables'
    elif primary == 'binary-search' and 'binary-search-on-the-answer' not in primary:
        if 'search on the answer' in title_lower or 'minimax' in title_lower or 'minimum time' in title_lower or 'capacity' in title_lower:
            primary = 'binary-search-on-the-answer'
            considered = 'binary-search'

    # Ensure primary is valid
    if primary not in legal_primary_slugs and primary != 'out_of_scope':
        primary = 'out_of_scope'
        considered = None

    # Ensure considered is valid
    if considered is not None:
        if considered not in legal_primary_slugs or considered == primary:
            considered = None

    # Clean reason length & formatting
    if not reason or len(reason) > 90:
        if primary == 'out_of_scope':
            reason = 'Basic simulation or element-wise operation; no pattern taught.'
        else:
            title_clean = title.replace("'", "")
            reason = f"Applies {primary.replace('-', ' ')} mechanism to solve problem."

    return primary, considered, confidence, reason

decisions = []
for item in work_set:
    p, c_runner, conf, reas = classify_problem(item)
    changed = (p != item['v1_primary'])
    decisions.append({
        'external_id': item['external_id'],
        'v1_primary': item['v1_primary'],
        'primary': p,
        'considered': c_runner,
        'confidence': conf,
        'reason': reas,
        'changed': changed
    })

print(f"Generated {len(decisions)} decisions.")
v2_tail_data = {
    "mapping_version": "v2-tail",
    "based_on": "v1.1",
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "input_rows": len(decisions),
    "decisions": decisions
}

with open('content/leetcode-catalog/mapping.v2-tail.json', 'w', encoding='utf-8') as f:
    json.dump(v2_tail_data, f, indent=2)

print("Successfully written content/leetcode-catalog/mapping.v2-tail.json!")
