import json
import os

data = {
  "slug": "functools-wraps",
  "title": "functools.wraps and preserving metadata",
  "roadmap": "python-swe",
  "kind": "concept",
  "tier": "tier2",
  "metadata": {
    "difficulty": "medium",
    "estimated_minutes": 30,
    "importance": 8,
    "interview_frequency": "medium",
    "prerequisites": ["decorators", "closures"],
    "unlocks": ["decorator-factories"],
    "project_usage": ["FastAPI", "Flask"]
  },
  "overview": {
    "what": "When you write a decorator, the returned wrapper function replaces the original function. By default, this wrapper hides the original function's metadata (like its `__name__` and `__doc__`). Using `@functools.wraps(func)` on the wrapper copies the original function's metadata to the wrapper. Think of it like wearing a costume: without `@wraps`, people see the costume and forget who is inside; with `@wraps`, you wear a name tag over the costume so your real identity is preserved.",
    "why": "Web frameworks and documentation generators rely on function metadata to register routes and build docs. If decorators obscure this, frameworks fail to map URLs correctly.",
    "where_used": ["FastAPI routes", "Flask views", "Celery tasks"]
  },
  "why_learning_this": [
    "Ensuring your decorators don't break web frameworks that inspect function names.",
    "Generating accurate documentation for decorated functions."
  ],
  "common_mistakes": [
    {
      "title": "Missing @wraps on decorators",
      "explanation": "Forgetting to decorate the inner wrapper with `@wraps(func)`. This causes the decorated function's `__name__` to become `'wrapper'`, breaking reflection."
    }
  ],
  "recall_questions": [
    {
      "q": "What happens to a function's `__name__` attribute if you decorate it with a custom decorator that doesn't use `functools.wraps`?",
      "answer": "It changes to the name of the inner wrapper function defined inside the decorator.",
      "tier": "tier1"
    },
    {
      "q": "Why do frameworks like FastAPI or Flask require decorators to use `functools.wraps`?",
      "answer": "They rely on the original function's metadata to properly register routes and generate documentation.",
      "tier": "tier2"
    }
  ],
  "practice_tasks": [
    {
      "title": "Fix a broken decorator",
      "prompt": "The provided `log_calls` decorator loses the original function's name. Fix it using `functools.wraps`.",
      "starter_code": "def log_calls(func):\n  def wrapper(*args, **kwargs):\n    print('Calling function')\n    return func(*args, **kwargs)\n  return wrapper\n\n@log_calls\ndef calculate_tax(amount):\n  '''Calculates tax for an amount.'''\n  return amount * 0.2",
      "solution": "import functools\n\ndef log_calls(func):\n  @functools.wraps(func)\n  def wrapper(*args, **kwargs):\n    print('Calling function')\n    return func(*args, **kwargs)\n  return wrapper\n\n@log_calls\ndef calculate_tax(amount):\n  '''Calculates tax for an amount.'''\n  return amount * 0.2"
    }
  ],
  "code_walkthrough": {
    "code": "import functools\n\ndef my_decorator(func):\n  @functools.wraps(func)\n  def wrapper():\n    return func()\n  return wrapper\n\n@my_decorator\ndef real_function():\n  pass\n\nprint(real_function.__name__)",
    "focus": "print(real_function.__name__)"
  },
  "aha_moment": {
    "code": "def naive_decorator(func):\n  def wrapper():\n    return func()\n  return wrapper\n\n@naive_decorator\ndef greet():\n  '''Says hello'''\n  pass\n\nprint(greet.__name__)",
    "prediction": "What does this script print?",
    "common_guess": "'greet'",
    "why": "Because `greet` is replaced by `wrapper`, its `__name__` becomes `'wrapper'`. Without `@wraps`, the original identity is lost."
  },
  "challenge": {
    "title": "Create a well-behaved timing decorator",
    "prompt": "Write a `time_it` decorator that measures execution time and prints it. It must use `functools.wraps` so the decorated function retains its `__doc__` and `__name__`. Test it on a function named `process_data`.",
    "solution": "import functools\nimport time\n\ndef time_it(func):\n  @functools.wraps(func)\n  def wrapper(*args, **kwargs):\n    start = time.time()\n    result = func(*args, **kwargs)\n    print(f'Took {time.time() - start}s')\n    return result\n  return wrapper\n\n@time_it\ndef process_data():\n  '''Processes a bunch of data.'''\n  pass"
  },
  "sources": [
    "https://docs.python.org/3/library/functools.html#functools.wraps"
  ]
}

target_dir = r"c:\Users\aloks\Desktop\RetainHQ\content\roadmaps\python-swe"
os.makedirs(target_dir, exist_ok=True)

with open(os.path.join(target_dir, "functools-wraps.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Generated functools-wraps.json successfully!")
