import json
import os

DIR = 'content/roadmaps/dsa'

def load_json(filename):
    with open(os.path.join(DIR, filename), 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(os.path.join(DIR, filename), 'w') as f:
        json.dump(data, f, indent=2)
        f.write("\n")

def process():
    files = {
        'stack-fundamentals': load_json('stack-fundamentals.json'),
        'valid-parentheses': load_json('valid-parentheses.json'),
        'min-stack': load_json('min-stack.json'),
        'monotonic-stack': load_json('monotonic-stack.json'),
        'next-greater-element': load_json('next-greater-element.json'),
        'queue-and-deque': load_json('queue-and-deque.json')
    }

    # ROUND 2 - ALL 6 FILES: hook, why_it_exists.naive_solution, key_points
    hooks = {
        'stack-fundamentals': {"scenario": "Ever hit Ctrl+Z? That undo history is a stack — the last thing you did is the first thing undone.", "question": "How do we structurally enforce this reverse-chronological order?"},
        'valid-parentheses': {"scenario": "Imagine typing a math formula with multiple nested brackets. You need to ensure every opened bracket is properly closed.", "question": "How can a program verify this without getting confused by the nesting?"},
        'min-stack': {"scenario": "You have a stack of numbers, and you constantly need to know the smallest one. Scanning the whole stack takes too long.", "question": "How can we know the minimum instantly, even as numbers are added and removed?"},
        'monotonic-stack': {"scenario": "You're looking at a line of people and want to find the next person taller than you. You could ask everyone in line one by one.", "question": "Is there a way to find the next taller person for everyone in just a single pass?"},
        'next-greater-element': {"scenario": "You are tracking daily stock prices and want to know how many days you have to wait for a higher price.", "question": "How do you find the next greater price efficiently without comparing every day to every future day?"},
        'queue-and-deque': {"scenario": "Think of waiting in line at a grocery store. The first person to line up is the first to check out.", "question": "How do we build a structure that strictly respects this 'first come, first served' fairness?"}
    }

    naive_solutions = {
        'stack-fundamentals': "Using a standard array and manually tracking the 'last inserted' index, or shifting elements, which can lead to bugs or O(n) operations if not careful.",
        'valid-parentheses': "Counting the number of open and closed brackets. This fails for '([)]' because it ignores the correct nesting order.",
        'min-stack': "Scanning the entire stack from top to bottom every time you need the minimum value, taking O(n) time.",
        'monotonic-stack': "For every element, scanning all subsequent elements in a nested loop to find the next greater/smaller match, resulting in O(n^2) time.",
        'next-greater-element': "Scan forward from every element to find its next greater — O(n^2) nested loops.",
        'queue-and-deque': "Using a standard array and removing from the front, which requires shifting all remaining elements left in O(n) time."
    }

    key_points = {
        'stack-fundamentals': [{"title": "Invariant", "detail": "Elements are strictly added and removed from only one end (the top)."}, {"title": "Complexity", "detail": "O(1) time for push and pop operations."}, {"title": "Recognition cue", "detail": "Whenever you need to process data in a Last-In-First-Out (LIFO) or reverse-chronological order."}],
        'valid-parentheses': [{"title": "Invariant", "detail": "Every closing bracket must match the most recently opened unmatched bracket at the top of the stack."}, {"title": "Complexity", "detail": "O(n) time to scan the string, O(n) space for the stack."}, {"title": "Gotcha", "detail": "Don't forget to check if the stack is empty at the end; leftover open brackets mean it's invalid."}],
        'min-stack': [{"title": "Invariant", "detail": "The minimum state is perfectly synchronized with the main stack's lifecycle."}, {"title": "Complexity", "detail": "O(1) time for push, pop, and getMin."}, {"title": "Gotcha", "detail": "When popping, ensure the parallel minimum state is also popped to remain synchronized."}],
        'monotonic-stack': [{"title": "Invariant", "detail": "The stack elements remain strictly increasing or decreasing from bottom to top."}, {"title": "Complexity", "detail": "O(n) amortized time, as each element is pushed and popped at most once."}, {"title": "Recognition cue", "detail": "Finding the next greater/smaller element, or computing bounds like in histogram areas."}],
        'next-greater-element': [{"title": "Invariant", "detail": "The stack keeps track of elements waiting for a greater element. A new larger element resolves them."}, {"title": "Complexity", "detail": "O(n) amortized time, processing each element linearly."}, {"title": "Recognition cue", "detail": "Problems asking for the 'next largest' or 'first element greater than X to its right'."}],
        'queue-and-deque': [{"title": "Invariant", "detail": "Elements are processed strictly First-In-First-Out (FIFO), or from both ends (Deque)."}, {"title": "Complexity", "detail": "O(1) time for enqueue and dequeue operations."}, {"title": "Gotcha", "detail": "Removing from the front of a naive array is O(n); a proper queue uses pointers or a linked structure."}]
    }

    for k, v in files.items():
        v['hook'] = hooks[k]
        if 'why_it_exists' not in v:
            v['why_it_exists'] = {}
        v['why_it_exists']['naive_solution'] = naive_solutions[k]
        v['key_points'] = key_points[k]

    # ROUND 2 - RELATED
    if 'related' not in files['stack-fundamentals']: files['stack-fundamentals']['related'] = []
    files['stack-fundamentals']['related'].extend(["valid-parentheses", "min-stack", "monotonic-stack", "queue-and-deque"])
    files['stack-fundamentals']['related'] = list(set(files['stack-fundamentals']['related']))

    if 'related' not in files['valid-parentheses']: files['valid-parentheses']['related'] = []
    files['valid-parentheses']['related'].extend(["stack-fundamentals"])

    if 'related' not in files['min-stack']: files['min-stack']['related'] = []
    files['min-stack']['related'].extend(["stack-fundamentals"])

    if 'related' not in files['queue-and-deque']: files['queue-and-deque']['related'] = []
    files['queue-and-deque']['related'].extend(["stack-fundamentals"])

    # ROUND 2 - THIN COUNTS
    # stack-fundamentals practice
    if len(files['stack-fundamentals'].get('practice', [])) < 2:
        files['stack-fundamentals'].setdefault('practice', []).append({
            "title": "Valid Parentheses",
            "url": "https://leetcode.com/problems/valid-parentheses/",
            "difficulty": "easy",
            "why": "A classic LIFO problem checking structural validity."
        })
    # min-stack practice
    if len(files['min-stack'].get('practice', [])) < 2:
        files['min-stack'].setdefault('practice', []).append({
            "title": "Max Stack",
            "url": "https://leetcode.com/problems/max-stack/",
            "difficulty": "hard",
            "why": "The same concept applied to finding the maximum, with an added twist for removing the maximum."
        })
    # next-greater-element practice
    if len(files['next-greater-element'].get('practice', [])) < 2:
        files['next-greater-element'].setdefault('practice', []).append({
            "title": "Daily Temperatures",
            "url": "https://leetcode.com/problems/daily-temperatures/",
            "difficulty": "medium",
            "why": "Finding the distance to the next greater element."
        })

    # valid-parentheses sources (replace scribd)
    sources = files['valid-parentheses'].get('sources', [])
    new_sources = [s for s in sources if 'scribd' not in s.lower()]
    if len(new_sources) < 2:
        new_sources.append("https://en.wikipedia.org/wiki/Context-free_grammar")
        new_sources.append("https://www.geeksforgeeks.org/check-for-balanced-parentheses-in-an-expression/")
    files['valid-parentheses']['sources'] = new_sources

    # QUEUE AND DEQUE P2 (move oa_1 to stack-fundamentals)
    q_oa = files['queue-and-deque'].get('oa_questions', [])
    q_to_move = None
    new_q_oa = []
    for q in q_oa:
        if 'two Stacks' in q['question'] or 'two stacks' in q['question'].lower():
            q_to_move = q
        else:
            new_q_oa.append(q)
    files['queue-and-deque']['oa_questions'] = new_q_oa
    if q_to_move:
        files['stack-fundamentals'].setdefault('oa_questions', []).append(q_to_move)

    # QUEUE AND DEQUE P2 explanation
    qd_exp = files['queue-and-deque'].get('explanation', '')
    if 'sliding-window' not in qd_exp.lower():
        qd_exp += "\n\nThe flagship hard application of a deque is the monotonic sliding-window technique. To find the maximum in a sliding window of size k: keep a deque of indices; before reading the front, pop it if it's outside the window (`front <= i - k`); before pushing i, pop from the back while the back's value < arr[i] so the deque stays decreasing; the front is always the window max."
    files['queue-and-deque']['explanation'] = qd_exp

    # VALID PARENTHESES P3
    vp_exp = files['valid-parentheses'].get('explanation', '')
    vp_exp += "\n\nIn compiler theory, checking nested brackets requires a memory of what was opened. A left-to-right scan can't count nesting depth; a stack gives it the memory to keep track of this state. This is exactly how a pushdown automaton (a machine with a stack) parses context-free grammars.\n\nFor advanced problems like finding the 'Longest Valid Parentheses', we use an index-stack with a sentinel value. We seed the stack with -1 to represent the boundary before the string starts. We push indices of unmatched `(`, and on a match, we compute the length as `i - stack.top()`. This technique seamlessly handles contiguous valid sequences."
    # Also clean up any undefined jargon if it already existed, but we added the definitions inline.
    files['valid-parentheses']['explanation'] = vp_exp

    # MIN STACK P4
    for oa in files['min-stack'].get('oa_questions', []):
        if 'encoding' in oa.get('answer', '').lower() or 'encoding' in oa.get('question', '').lower() or 'encode' in oa.get('approach', '').lower() or 'encode' in oa.get('answer', '').lower():
            if 'recover' not in oa['answer']:
                oa['answer'] += " Decode step: if a popped value is < current min, it was an encoded flag — recover the previous min as `2*min - popped`; the real data value equals the old min."

    # min stack engineering examples replace
    for ee in files['min-stack'].get('engineering_examples', []):
        if 'State Snapshotting' in ee.get('title', ''):
            ee['title'] = 'Metrics & Observability'
            ee['problem'] = 'Maintaining a rolling-min in a metrics/observability pipeline'
            ee['why_this_algorithm'] = 'Because stacks only mutate at one boundary, historical states can be aggregated in O(1) time.'

    # min stack deepening explanation
    ms_exp = files['min-stack'].get('explanation', '')
    if 'O(1)' not in ms_exp:
        ms_exp += "\n\nA min-stack elegantly tracks the minimum value in O(1) time alongside the main data by shadowing it. You simply maintain a parallel stack (or store pairs) where each element records the minimum value present in the stack at the moment it was pushed. When you pop from the main stack, you also pop from the minimum stack, naturally reversing history and restoring the previous minimum."
    files['min-stack']['explanation'] = ms_exp

    # STACK FUNDAMENTALS P5
    for rq in files['stack-fundamentals'].get('recall_questions', []):
        if 'amortized' in rq.get('answer', '').lower() or 'O(1)' in rq.get('answer', ''):
            rq['answer'] = "O(1) (strict for linked list, amortized for dynamic arrays). POP is strict O(1). For pushes, dynamic arrays occasionally double capacity when full (that push is O(n)), but averaged over many pushes it's O(1) — 'amortized'."
        if 'cache locality' in rq.get('answer', '').lower() or 'pointer chasing' in rq.get('answer', '').lower():
            rq['answer'] = "Contiguous memory allocation provides excellent CPU cache locality. CPU cache lines fetch chunks of contiguous memory, so array neighbours arrive together; scattered linked-list nodes each cause a cache miss."

    # MONOTONIC STACK P1 & Deepening
    mon_exp = files['monotonic-stack'].get('explanation', '')
    mon_exp = "The monotonic stack is one of the most powerful and feared interview patterns. It fundamentally solves the 'next greater' or 'next smaller' query over an entire array in O(n) amortized time.\n\nThe beauty of this structure is that the *destruction* of the invariant provides the answer. Elements wait peacefully on the stack in order. The moment a contradictory element arrives, it triggers a cascade of pops. Each pop is an element realizing that its wait is over: the incoming element is exactly what it was waiting for.\n\nHere is the vital direction rule to memorize: Keep the stack DECREASING to find the next GREATER element (pop when a bigger element arrives); keep it INCREASING to find the next SMALLER element / to bound areas like histogram bars (pop when a smaller element arrives). Understanding this choice is the key to mastering the pattern. While the nested while loop looks like O(n^2), amortized analysis proves it is O(n) overall because every element is pushed exactly once and popped at most once."
    files['monotonic-stack']['explanation'] = mon_exp

    for oa in files['monotonic-stack'].get('oa_questions', []):
        if 'histogram' in oa.get('question', '').lower():
            if 'width' not in oa['answer']:
                oa['answer'] += " To compute the width, use the formula `current_index - stack.top() - 1` using the NEW top after popping as the left boundary. Use a sentinel trick: append a 0-height bar at the end of the array to flush any remaining elements from the stack."

    # NEXT GREATER ELEMENT P6 & Deepening
    nge_exp = files['next-greater-element'].get('explanation', '')
    if 'modulo' not in nge_exp.lower():
        nge_exp += "\n\nFor circular arrays, we can simulate concatenating the array to itself by iterating up to `2n-1` and using the modulo operator (`i % n`) to map back to valid bounds. This works perfectly because each real index resolves its next greater element at most once, and the stack handles the wrap-around naturally."
    files['next-greater-element']['explanation'] = nge_exp

    for k, v in files.items():
        save_json(k + '.json', v)

if __name__ == '__main__':
    process()
    print("Done")
