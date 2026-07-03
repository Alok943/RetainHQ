import json
import os

backfill_data = {
    "in-place-operations": {
        "steps": [
            {"id": "init", "label": "left = 0, right = end"},
            {"id": "swap", "label": "swap(arr[left], arr[right])"},
            {"id": "move", "label": "left++, right--"},
            {"id": "done", "label": "if left >= right: return"}
        ],
        "predictions": [
            {
                "at_step": "swap",
                "occurrence": "first",
                "level": "easy",
                "prompt": "The pointers are set. Which two elements swap next?",
                "derive": "next_swap_pair"
            }
        ]
    },
    "prefix-sums": {
        "steps": [
            {"id": "build", "label": "P[i] = P[i-1] + arr[i]"},
            {"id": "query", "label": "sum = P[R] - P[L-1]"},
            {"id": "done", "label": "queries complete"}
        ],
        "predictions": [
            {
                "at_step": "build",
                "occurrence": "first",
                "level": "easy",
                "prompt": "Building the prefix array. What value is written first?",
                "derive": "next_write"
            }
        ]
    },
    "frequency-counting": {
        "steps": [
            {"id": "count", "label": "freq[val] += 1"},
            {"id": "done", "label": "tally complete"}
        ],
        "predictions": [
            {
                "at_step": "count",
                "occurrence": "first",
                "level": "easy",
                "prompt": "Counting the first element. What happens next?",
                "derive": "next_op"
            }
        ]
    },
    "palindromes": {
        "steps": [
            {"id": "init", "label": "left = 0, right = end"},
            {"id": "match", "label": "if str[left] == str[right]"},
            {"id": "mismatch", "label": "if str[left] != str[right]: break"},
            {"id": "move", "label": "left++, right--"},
            {"id": "done", "label": "return result"}
        ],
        "predictions": [
            {
                "at_step": "match",
                "occurrence": "first",
                "level": "easy",
                "prompt": "Checking the first pair. What is the next operation?",
                "derive": "next_op"
            }
        ]
    },
    "two-pointers-on-strings": {
        "steps": [
            {"id": "init", "label": "left = 0, right = end"},
            {"id": "swap", "label": "swap(str[left], str[right])"},
            {"id": "move", "label": "left++, right--"},
            {"id": "done", "label": "return result"}
        ],
        "predictions": [
            {
                "at_step": "swap",
                "occurrence": "first",
                "level": "easy",
                "prompt": "Which two characters swap next?",
                "derive": "next_swap_pair"
            }
        ]
    },
    "frequency-arrays": {
        "steps": [
            {"id": "count", "label": "arr[val] += 1"},
            {"id": "done", "label": "tally complete"}
        ],
        "predictions": [
            {
                "at_step": "count",
                "occurrence": "first",
                "level": "easy",
                "prompt": "Counting the first element. What happens next?",
                "derive": "next_op"
            }
        ]
    },
    "bubble-sort": {
        "steps": [
            {"id": "compare", "label": "if arr[i] > arr[i+1]"},
            {"id": "swap", "label": "swap(arr[i], arr[i+1])"},
            {"id": "placed", "label": "largest element placed"},
            {"id": "done", "label": "array sorted"}
        ],
        "predictions": [
            {
                "at_step": "compare",
                "occurrence": "first",
                "level": "easy",
                "prompt": "Comparing the first pair. Which two elements swap next?",
                "derive": "next_swap_pair"
            }
        ]
    },
    "selection-sort": {
        "steps": [
            {"id": "scan", "label": "find min in remaining"},
            {"id": "compare", "label": "if arr[curr] < arr[min]"},
            {"id": "newmin", "label": "min = curr"},
            {"id": "swap", "label": "swap(arr[first], arr[min])"},
            {"id": "placed", "label": "minimum element placed"},
            {"id": "done", "label": "array sorted"}
        ],
        "predictions": [
            {
                "at_step": "compare",
                "occurrence": "first",
                "level": "medium",
                "prompt": "Comparing elements. Which two elements swap next?",
                "derive": "next_swap_pair"
            }
        ]
    },
    "insertion-sort": {
        "steps": [
            {"id": "pick", "label": "pick next element to insert"},
            {"id": "compare", "label": "compare with previous"},
            {"id": "swap", "label": "swap backwards if smaller"},
            {"id": "inplace", "label": "element in correct place"},
            {"id": "done", "label": "array sorted"}
        ],
        "predictions": [
            {
                "at_step": "compare",
                "occurrence": "first",
                "level": "medium",
                "prompt": "Comparing with previous. Which two elements swap next?",
                "derive": "next_swap_pair"
            }
        ]
    },
    "linear-search": {
        "steps": [
            {"id": "start", "label": "i = 0"},
            {"id": "compare", "label": "if arr[i] == target"},
            {"id": "found", "label": "return i"},
            {"id": "done", "label": "return -1"}
        ],
        "predictions": [
            {
                "at_step": "compare",
                "occurrence": "first",
                "level": "easy",
                "prompt": "Comparing first element. What is the next operation?",
                "derive": "next_op"
            }
        ]
    },
    "binary-search": {
        "steps": [
            {"id": "start", "label": "lo = 0, hi = end"},
            {"id": "window", "label": "while lo <= hi"},
            {"id": "probe", "label": "mid = (lo+hi)/2"},
            {"id": "found", "label": "if arr[mid] == target: return"},
            {"id": "discard", "label": "discard left or right half"},
            {"id": "done", "label": "return -1"}
        ],
        "predictions": [
            {
                "at_op": "WINDOW",
                "occurrence": "first",
                "level": "medium",
                "prompt": "First probe checked. Does the search go left or right?",
                "derive": "branch_binary"
            }
        ]
    }
}

base_dir = r"c:\Users\aloks\Desktop\RetainHQ\content\roadmaps\dsa"

for slug, payload in backfill_data.items():
    path = os.path.join(base_dir, f"{slug}.json")
    if not os.path.exists(path):
        print(f"Skipping {path} (not found)")
        continue
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if "viz" not in data:
        data["viz"] = {}
        
    data["viz"]["steps"] = payload["steps"]
    data["viz"]["predictions"] = payload["predictions"]
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        
print("Backfill completed.")
