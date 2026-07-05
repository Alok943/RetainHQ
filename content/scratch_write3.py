import json
import os

ROADMAP_DIR = r"c:\Users\aloks\Desktop\RetainHQ\content\roadmaps\python-backend"

# Fix the-gil.json
with open(os.path.join(ROADMAP_DIR, "the-gil.json"), "r") as f:
    gil = json.load(f)
gil["oa_questions"] = [
    {
      "question": "What is the GIL and how does it affect threads?",
      "company": "Backend Engineer interview",
      "answer": "The Global Interpreter Lock ensures only one thread executes Python code at a time. It prevents CPU-bound threads from running in parallel, making them useless for performance gains. However, I/O-bound threads drop the GIL while waiting, so multithreading is still highly effective for network or disk operations.",
      "approach": "Define it, explain WHY it restricts parallelism (CPU-bound bottleneck), and ALWAYS mention the I/O-bound exception where it's released."
    },
    {
      "question": "If you have a 16-core machine, how can you bypass the GIL to fully utilise the CPU for a heavy data-processing script?",
      "company": "Data Engineering",
      "answer": "You must use multiprocessing instead of threading. The `multiprocessing` module spawns separate OS processes, each with its own memory space and its own Python interpreter/GIL, allowing them to run truly in parallel across the 16 cores.",
      "approach": "State that threading cannot bypass the GIL, but multiprocessing can because it isolates the interpreters."
    }
]
with open(os.path.join(ROADMAP_DIR, "the-gil.json"), "w") as f:
    json.dump(gil, f, indent=2)

# Fix threading-vs-multiprocessing.json
with open(os.path.join(ROADMAP_DIR, "threading-vs-multiprocessing.json"), "r") as f:
    thm = json.load(f)
thm["oa_questions"] = [
    {
      "question": "Threading vs multiprocessing \u2014 which for CPU-bound work?",
      "company": "Backend Engineer interview",
      "answer": "Multiprocessing. CPU-bound work (like data processing or image resizing) requires the CPU to constantly execute instructions. In Python, the GIL prevents threads from running in parallel, meaning threads would just fight for execution time and run slower. Multiprocessing bypasses the GIL by creating isolated processes, allowing true parallel execution across multiple cores.",
      "approach": "Always link CPU-bound to Multiprocessing, and explicitly mention the GIL as the reason why Threading fails for this use case."
    },
    {
      "question": "Why is threading often preferred for web scraping or making thousands of API calls?",
      "company": "System Design",
      "answer": "Web scraping is heavily I/O-bound. The script spends 99% of its time waiting for the network to respond. Threads drop the GIL during I/O, allowing concurrent execution. Since threads share memory, they are much lighter to spawn and use vastly less RAM than spawning thousands of full OS processes.",
      "approach": "Contrast the low memory footprint of threads with the heavy footprint of processes, and explain that the GIL isn't a bottleneck for I/O."
    }
]
with open(os.path.join(ROADMAP_DIR, "threading-vs-multiprocessing.json"), "w") as f:
    json.dump(thm, f, indent=2)

# Fix blocking-calls-in-async.json
with open(os.path.join(ROADMAP_DIR, "blocking-calls-in-async.json"), "r") as f:
    bla = json.load(f)
bla["oa_questions"] = [
    {
      "question": "A FastAPI endpoint marked with `async def` performs a slow synchronous database query using psycopg2. What is the impact on the application under load?",
      "company": "Backend Engineer interview",
      "answer": "The application will completely lock up under load. An `async def` function runs directly on the single event loop thread. A synchronous blocking call (like psycopg2) will freeze the loop, meaning the server cannot process any other requests for any endpoint until the query returns.",
      "approach": "Identify that the event loop gets blocked. State the blast radius (affects ALL requests, not just the slow one)."
    },
    {
      "question": "If you absolutely must use a synchronous library like boto3 in FastAPI, how do you prevent it from blocking the event loop?",
      "company": "API Design interview",
      "answer": "You define the endpoint function as a standard `def` (instead of `async def`), or you explicitly run the blocking code in a threadpool using `run_in_executor`. FastAPI automatically detects standard `def` endpoints and executes them in an external threadpool, keeping the main event loop free.",
      "approach": "Give the practical framework-specific solution (dropping the async keyword) or the pure Python solution (run_in_executor)."
    }
]
with open(os.path.join(ROADMAP_DIR, "blocking-calls-in-async.json"), "w") as f:
    json.dump(bla, f, indent=2)

# Fix middleware-and-cors.json
mid_path = os.path.join(ROADMAP_DIR, "middleware-and-cors.json")
if os.path.exists(mid_path):
    with open(mid_path, "r") as f:
        mid = json.load(f)
    if "sources" not in mid:
        mid["sources"] = ["https://fastapi.tiangolo.com/tutorial/cors/"]
    with open(mid_path, "w") as f:
        json.dump(mid, f, indent=2)

print("Fixed JSON files.")
