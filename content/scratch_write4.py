import os

todo_path = r"c:\Users\aloks\Desktop\RetainHQ\content\_TODO-backend.md"
with open(todo_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "| Concurrency vs parallelism |" in line:
        line = line.replace("| Concurrency vs parallelism |", "| [x] Concurrency vs parallelism |")
    elif "| The GIL |" in line:
        line = line.replace("| The GIL |", "| [x] The GIL |")
    elif "| Threading vs multiprocessing |" in line:
        line = line.replace("| Threading vs multiprocessing |", "| [x] Threading vs multiprocessing |")
    elif "| Blocking calls in async code |" in line:
        line = line.replace("| Blocking calls in async code |", "| [x] Blocking calls in async code |")
    new_lines.append(line)

with open(todo_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Updated _TODO-backend.md")
