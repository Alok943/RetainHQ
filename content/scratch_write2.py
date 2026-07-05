import json
import os

ROADMAP_DIR = r"c:\Users\aloks\Desktop\RetainHQ\content\roadmaps\python-backend"

the_gil = {
  "slug": "the-gil",
  "title": "The GIL (Global Interpreter Lock)",
  "roadmap": "python-backend",
  "kind": "engineering",
  "tier": "tier1",
  "metadata": {
    "difficulty": "medium",
    "estimated_minutes": 15,
    "importance": 10,
    "interview_frequency": "high",
    "prerequisites": ["concurrency-vs-parallelism"],
    "unlocks": ["threading-vs-multiprocessing"]
  },
  "hook": {
    "scenario": "You spin up 4 threads on your 4-core server to process a massive dataset, expecting it to be 4x faster. But it actually takes slightly longer than using 1 thread. Why?"
  },
  "mental_model": {
    "intuition": "The GIL is a speaking baton. Even if there are 10 people in the room (threads), only the person holding the baton is allowed to speak (execute Python code).",
    "description": "The Global Interpreter Lock (GIL) is a mutex in CPython that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once. This means no matter how many threads or CPU cores you have, only one thread can execute Python code at any given time."
  },
  "sections": [
    {
      "body": "Python's memory management uses reference counting. If two threads increase a variable's reference count at the exact same nanosecond, the count might only go up by 1 instead of 2. The variable would eventually be deleted while a thread was still using it, causing a crash. The GIL was introduced as a simple, foolproof lock to prevent these race conditions at the interpreter level.",
      "recap": "The GIL exists to make Python's memory management (reference counting) thread-safe."
    },
    {
      "body": "The massive consequence: Python threads CANNOT run in parallel. A multi-threaded Python program is strictly concurrent. If you have CPU-bound work (like crunching numbers), threads will fight over the GIL, and the overhead of switching the lock will actually make the program slower than a single thread.",
      "recap": "The GIL prevents true parallelism for Python threads."
    },
    {
      "body": "However, the GIL is released when a thread does I/O (like network requests, reading a file, or waiting for a database). During that time, another thread can acquire the GIL and execute Python code. This means threading IS useful in Python, but only for I/O-bound tasks.",
      "recap": "The GIL is dropped during I/O, allowing other threads to run."
    }
  ],
  "code_snippets": [
    {
      "title": "CPU-Bound: Threads fight for the GIL (Slower)",
      "language": "python",
      "code": "import threading\n\ndef count_down(n):\n    while n > 0:\n        n -= 1\n\n# Using 2 threads to do CPU-heavy math\nt1 = threading.Thread(target=count_down, args=(50_000_000,))\nt2 = threading.Thread(target=count_down, args=(50_000_000,))\n\nt1.start(); t2.start()\nt1.join(); t2.join()\n\n# This takes LONGER than running count_down(100_000_000) sequentially!\n# Both threads are fighting for the single GIL.",
      "explanation": "Because of the GIL, `t1` and `t2` cannot execute their `while` loops simultaneously. They rapidly pass the GIL back and forth, and that context-switching overhead makes it slower than doing the math in one thread."
    },
    {
      "title": "I/O-Bound: The GIL is released (Faster)",
      "language": "python",
      "code": "import threading\nimport time\n\ndef simulated_network_call():\n    # The GIL is RELEASED during time.sleep() (or any I/O)\n    time.sleep(1)\n\nt1 = threading.Thread(target=simulated_network_call)\nt2 = threading.Thread(target=simulated_network_call)\n\nstart = time.time()\nt1.start(); t2.start()\nt1.join(); t2.join()\n\n# This takes ~1 second, not 2 seconds.\nprint(f\"Took {time.time() - start:.2f}s\")",
      "explanation": "When `t1` hits the blocking I/O (simulated by `sleep`), it drops the GIL. `t2` grabs the GIL and also starts waiting. They wait concurrently, finishing in 1 second total."
    }
  ],
  "common_mistakes": [
    {
      "title": "Using threads for CPU-intensive tasks",
      "explanation": "Believing that threading in Python will speed up math, image processing, or data crunching. Because of the GIL, the threads will run sequentially, but slower due to lock-switching overhead."
    }
  ],
  "recall_questions": [
    {
      "q": "What does the GIL stand for, and what does it do?",
      "answer": "Global Interpreter Lock. It prevents multiple native threads from executing Python bytecodes at once."
    },
    {
      "q": "Why was the GIL introduced in Python?",
      "answer": "To make CPython's memory management (specifically reference counting) thread-safe without needing to add locks to every single object."
    },
    {
      "q": "Does the GIL prevent concurrency or parallelism?",
      "answer": "It prevents parallelism (simultaneous execution on multiple cores) for Python threads. It still allows concurrency."
    }
  ],
  "oa_questions": [
    {
      "question": "What is the GIL and how does it affect threads?",
      "company": "Backend Engineer interview",
      "answer": "The Global Interpreter Lock ensures only one thread executes Python code at a time. It prevents CPU-bound threads from running in parallel, making them useless for performance gains. However, I/O-bound threads drop the GIL while waiting, so multithreading is still highly effective for network or disk operations.",
      "approach": "Define it, explain WHY it restricts parallelism (CPU-bound bottleneck), and ALWAYS mention the I/O-bound exception where it's released."
    }
  ],
  "sources": [
    "https://wiki.python.org/moin/GlobalInterpreterLock"
  ]
}

threading = {
  "slug": "threading-vs-multiprocessing",
  "title": "Threading vs Multiprocessing",
  "roadmap": "python-backend",
  "kind": "engineering",
  "tier": "tier1",
  "metadata": {
    "difficulty": "medium",
    "estimated_minutes": 15,
    "importance": 9,
    "interview_frequency": "high",
    "prerequisites": ["the-gil"],
    "unlocks": []
  },
  "hook": {
    "scenario": "You need to scale a Python script. Should you use `threading` or `multiprocessing`? Pick wrong, and your script might crash your server with out-of-memory errors, or run slower than it did on one core."
  },
  "mental_model": {
    "intuition": "Threads are workers sharing the same desk and tools. Processes are workers in completely separate rooms, each with their own copy of the tools.",
    "description": "Threads run in the same memory space, making them lightweight and easy to share data, but they are limited by the GIL. Processes spawn an entirely new Python interpreter with its own memory space and its own GIL, allowing true parallelism across CPU cores."
  },
  "sections": [
    {
      "body": "Threading is lightweight. Because all threads share the same memory, starting a thread is fast, and they can easily read the same variables. The massive downside is the GIL: only one thread can execute Python code at a time. This makes threads perfect for I/O-bound tasks (waiting on the network or DB), because they drop the GIL while waiting.",
      "recap": "Threading: Shared memory, blocked by the GIL, perfect for I/O-bound work."
    },
    {
      "body": "Multiprocessing bypasses the GIL entirely. It spawns a brand new OS process, which gets its own memory and its own Python interpreter (meaning its own GIL). If you have 4 cores, 4 processes can run Python code at the exact same time. The downside is heavy overhead: creating processes is slow, they use 4x the RAM, and sharing data between them requires serialising it (Pickle) and sending it over pipes/queues.",
      "recap": "Multiprocessing: Separate memory, bypasses the GIL, required for CPU-bound work."
    }
  ],
  "code_snippets": [
    {
      "title": "Threading (I/O-Bound)",
      "language": "python",
      "code": "import threading\nimport requests\n\ndef fetch_url(url):\n    # Drops the GIL while waiting for the network\n    response = requests.get(url)\n    print(f\"Fetched {url}\")\n\nurls = [\"https://example.com\"] * 10\nthreads = []\n\nfor url in urls:\n    t = threading.Thread(target=fetch_url, args=(url,))\n    threads.append(t)\n    t.start()\n\nfor t in threads:\n    t.join()",
      "explanation": "Since `requests.get` is I/O-bound, the GIL is released. All 10 threads can wait for their HTTP responses concurrently in the same memory space. Fast and memory-efficient."
    },
    {
      "title": "Multiprocessing (CPU-Bound)",
      "language": "python",
      "code": "from multiprocessing import Pool\nimport math\n\ndef heavy_computation(num):\n    # CPU-bound: pure math\n    return math.factorial(num)\n\nif __name__ == '__main__':\n    numbers = [50000, 50001, 50002, 50003]\n    \n    # Spawns 4 separate Python processes, utilising 4 CPU cores\n    with Pool(processes=4) as pool:\n        results = pool.map(heavy_computation, numbers)\n        \n    print(\"Done\")",
      "explanation": "If we used threads here, the GIL would force them to run sequentially. By using a Process Pool, the OS distributes the 4 isolated processes across 4 physical cores, achieving true parallelism."
    }
  ],
  "common_mistakes": [
    {
      "title": "Sharing complex objects in multiprocessing",
      "explanation": "In threads, modifying a global list is easy (though you need locks to prevent race conditions). In multiprocessing, variables aren't shared. If Process A modifies a list, Process B won't see the change. You must use `multiprocessing.Queue` or shared memory arrays to communicate between processes, which has serialization overhead."
    }
  ],
  "recall_questions": [
    {
      "q": "Which approach (threading or multiprocessing) shares the same memory space?",
      "answer": "Threading. Multiprocessing spawns entirely separate memory spaces."
    },
    {
      "q": "Which approach is required to bypass the GIL in Python?",
      "answer": "Multiprocessing. Each process gets its own GIL, allowing true parallelism."
    },
    {
      "q": "Why shouldn't you use multiprocessing for a simple script that downloads 100 images?",
      "answer": "Downloading images is I/O-bound. Multiprocessing adds massive memory and startup overhead. Threading (or asyncio) can handle I/O concurrently within a single process much more efficiently."
    }
  ],
  "oa_questions": [
    {
      "question": "Threading vs multiprocessing \u2014 which for CPU-bound work?",
      "company": "Backend Engineer interview",
      "answer": "Multiprocessing. CPU-bound work (like data processing or image resizing) requires the CPU to constantly execute instructions. In Python, the GIL prevents threads from running in parallel, meaning threads would just fight for execution time and run slower. Multiprocessing bypasses the GIL by creating isolated processes, allowing true parallel execution across multiple cores.",
      "approach": "Always link CPU-bound to Multiprocessing, and explicitly mention the GIL as the reason why Threading fails for this use case."
    }
  ],
  "sources": [
    "https://docs.python.org/3/library/multiprocessing.html",
    "https://docs.python.org/3/library/threading.html"
  ]
}

blocking = {
  "slug": "blocking-calls-in-async",
  "title": "Blocking Calls in Async Code",
  "roadmap": "python-backend",
  "kind": "engineering",
  "tier": "tier1",
  "metadata": {
    "difficulty": "medium",
    "estimated_minutes": 15,
    "importance": 10,
    "interview_frequency": "high",
    "prerequisites": ["coroutines-async-await", "the-event-loop"],
    "unlocks": []
  },
  "hook": {
    "scenario": "Your FastAPI app handles 500 req/sec effortlessly. You add one endpoint that uses the standard `requests` library to fetch a 3rd-party API. Suddenly, your entire server freezes for 2 seconds every time someone hits that endpoint. All 500 users timeout."
  },
  "mental_model": {
    "intuition": "The event loop is a single waiter serving 100 tables. If the waiter goes to the kitchen and waits 10 minutes staring at the chef (a blocking call), no other table gets served.",
    "description": "Async Python runs on a single thread\u2014the event loop. When you `await`, you tell the loop 'I am pausing, go serve someone else.' But if you make a synchronous, blocking call (like `time.sleep` or `requests.get`), the loop doesn't know you paused. It literally freezes the entire thread until the call finishes, halting all other concurrent tasks."
  },
  "sections": [
    {
      "body": "Async code achieves high concurrency by never waiting. When it hits an `await` (like `await db.fetch()`), it registers a callback and the event loop instantly switches to another request. The golden rule of async is: you must never block the event loop thread.",
      "recap": "`await` yields control back to the event loop. Synchronous calls do not."
    },
    {
      "body": "Standard libraries like `requests`, `time.sleep`, or `psycopg2` are synchronous. They do not yield control. If you put `requests.get()` inside an `async def` function, the event loop stops dead. It cannot process new HTTP requests, it cannot respond to open websockets, it is completely frozen until that network call returns.",
      "recap": "A single synchronous call in an `async def` freezes the entire server for all users."
    },
    {
      "body": "To fix this, you must either use an async-compatible library (like `httpx.AsyncClient` or `asyncpg`) and `await` it, OR, in FastAPI, declare the endpoint as a standard `def` (not `async def`). FastAPI will automatically run standard `def` endpoints in a separate background threadpool, keeping the main event loop unblocked.",
      "recap": "Fix: Use async libraries, or let FastAPI run it in a threadpool using a standard `def`."
    }
  ],
  "code_snippets": [
    {
      "title": "The Bug: Freezing the Event Loop",
      "language": "python",
      "code": "from fastapi import FastAPI\nimport time, requests\n\napp = FastAPI()\n\n@app.get(\"/fast\")\nasync def fast_endpoint():\n    return {\"msg\": \"I am fast!\"}\n\n@app.get(\"/slow\")\nasync def slow_endpoint():\n    # FATAL MISTAKE: Sync call inside `async def`\n    # The entire server freezes for 2 seconds. \n    # Nobody can access /fast while this is running.\n    time.sleep(2)  \n    \n    # Same issue: requests.get is blocking\n    # resp = requests.get(\"https://api.example.com\")\n    \n    return {\"msg\": \"Done\"}",
      "explanation": "Because it's an `async def`, FastAPI runs it directly on the event loop. `time.sleep` (or `requests.get`) blocks the thread. The event loop is stuck, meaning all other incoming requests queue up and hang."
    },
    {
      "title": "Fix 1: Use an Async Library",
      "language": "python",
      "code": "import asyncio\nimport httpx\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/slow-fixed-async\")\nasync def slow_endpoint_async():\n    # Async sleep yields control to the loop\n    await asyncio.sleep(2)  \n    \n    # Async network call yields control\n    async with httpx.AsyncClient() as client:\n        resp = await client.get(\"https://api.example.com\")\n        \n    return {\"msg\": \"Done, and server stayed responsive!\"}",
      "explanation": "By using `await asyncio.sleep(2)` and `httpx.AsyncClient`, control is yielded back to the event loop. Other endpoints like `/fast` continue to be served instantly while this request waits."
    },
    {
      "title": "Fix 2: Let FastAPI Threadpool It",
      "language": "python",
      "code": "from fastapi import FastAPI\nimport requests, time\n\napp = FastAPI()\n\n# Notice: `def`, NOT `async def`\n@app.get(\"/slow-fixed-sync\")\ndef slow_endpoint_sync():\n    # This is safe! FastAPI runs standard `def` endpoints \n    # in an external threadpool.\n    time.sleep(2)\n    resp = requests.get(\"https://api.example.com\")\n    \n    return {\"msg\": \"Done, threadpool absorbed the block.\"}",
      "explanation": "If you MUST use a blocking library (like boto3, or an older database driver), drop the `async` keyword. FastAPI detects this and runs the function in a threadpool, preventing the main event loop from freezing."
    }
  ],
  "common_mistakes": [
    {
      "title": "Using `time.sleep` or sync `requests` inside `async def`",
      "explanation": "This is the classic production bug. `time.sleep` / sync `requests` / sync DB driver inside `async def` freezes the whole event loop \u2014 every request, not just this one. Fix = `asyncio.sleep`, async clients, or `def` endpoint (FastAPI threadpools it)."
    }
  ],
  "recall_questions": [
    {
      "q": "What happens to a FastAPI server if you run `requests.get()` inside an `async def` endpoint?",
      "answer": "The event loop freezes completely until the request finishes. The server will not accept or process any other requests during that time."
    },
    {
      "q": "How does FastAPI handle standard `def` endpoints (without `async`) differently?",
      "answer": "It runs them in an external threadpool. This allows the blocking code to run without freezing the main async event loop."
    },
    {
      "q": "If you are writing an `async def` endpoint, how should you make an HTTP request to a 3rd-party API?",
      "answer": "You must use an async-compatible HTTP client, such as `httpx.AsyncClient` or `aiohttp`, and `await` the request."
    }
  ],
  "oa_questions": [
    {
      "question": "A FastAPI endpoint marked with `async def` performs a slow synchronous database query using psycopg2. What is the impact on the application under load?",
      "company": "Backend Engineer interview",
      "answer": "The application will completely lock up under load. An `async def` function runs directly on the single event loop thread. A synchronous blocking call (like psycopg2) will freeze the loop, meaning the server cannot process any other requests for any endpoint until the query returns.",
      "approach": "Identify that the event loop gets blocked. State the blast radius (affects ALL requests, not just the slow one)."
    }
  ],
  "sources": [
    "https://fastapi.tiangolo.com/async/",
    "https://docs.python.org/3/library/asyncio-task.html#sleeping"
  ]
}

with open(os.path.join(ROADMAP_DIR, "the-gil.json"), "w") as f:
    json.dump(the_gil, f, indent=2)

with open(os.path.join(ROADMAP_DIR, "threading-vs-multiprocessing.json"), "w") as f:
    json.dump(threading, f, indent=2)

with open(os.path.join(ROADMAP_DIR, "blocking-calls-in-async.json"), "w") as f:
    json.dump(blocking, f, indent=2)

print("Created remaining 3 JSON files.")
