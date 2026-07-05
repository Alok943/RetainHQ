import json
import os

files = {
    "pytest-basics-and-fixtures": {
        "slug": "pytest-basics-and-fixtures",
        "title": "Pytest Basics and Fixtures",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "medium",
            "estimated_minutes": 25,
            "importance": 9,
            "interview_frequency": "high",
            "prerequisites": [],
            "unlocks": ["parametrized-tests", "mocking-and-patching"],
            "project_usage": ["Writing backend unit tests", "Database session fixture setup"]
        },
        "hook": {
            "scenario": "You have a massive test file with 100 lines of setup (database connection, user creation) copied and pasted at the top of every single test function. It's brittle and slow."
        },
        "mental_model": {
            "intuition": "Fixtures are dependency injection for your tests. Just like FastAPI's `Depends`, a test simply declares what it needs, and pytest figures out how to build it, pass it in, and clean it up."
        },
        "sections": [
            {
                "body": "Pytest is the standard testing framework for Python. Instead of subclassing `unittest.TestCase`, you write plain `assert` statements. Pytest introspects the assertions to provide rich failure diffs."
            },
            {
                "body": "A `fixture` is a setup function decorated with `@pytest.fixture`. When a test function includes the fixture's name in its arguments, pytest executes the fixture first and injects the returned value."
            },
            {
                "body": "Fixtures use `yield` instead of `return` to handle teardown. Everything before `yield` is setup; everything after `yield` runs after the test finishes, ensuring resources like database connections are closed even if the test fails."
            }
        ],
        "code_snippets": [
            {
                "title": "With Pytest Fixtures (Clean)",
                "language": "python",
                "code": "import pytest\n\n@pytest.fixture\ndef db_session():\n    # Setup: runs before test\n    db = setup_test_db()\n    yield db\n    # Teardown: runs after test\n    teardown_test_db(db)\n\ndef test_create_user(db_session):\n    # db_session is injected automatically\n    user = create_user(db_session, 'alice')\n    assert user.name == 'alice'",
                "explanation": "The fixture handles the lifecycle. The test only contains the actual logic. Pytest guarantees the code after `yield` runs."
            }
        ],
        "common_mistakes": [
            {
                "title": "Forgetting to yield",
                "explanation": "Using `return` instead of `yield` in a fixture means you cannot write teardown code. The fixture will just exit, leaving database connections or files open."
            }
        ],
        "recall_questions": [
            {
                "q": "How does pytest know to pass a fixture into a test?",
                "answer": "By matching the argument name of the test function with the name of the fixture."
            },
            {
                "q": "How do you execute teardown code in a pytest fixture?",
                "answer": "Use `yield` to return the resource. Any code placed after the `yield` statement will run as teardown."
            },
            {
                "q": "What happens if a test fails when using a generator (yield) fixture?",
                "answer": "The teardown code after the `yield` in the fixture will still execute."
            }
        ],
        "oa_questions": [
            {
                "question": "How would you share a database connection fixture across hundreds of tests without recreating the engine every time?",
                "answer": "Use a fixture with `scope='session'` to create the engine once. Then, use a `scope='function'` fixture that connects to the engine, starts a transaction, `yield`s the session, and rolls back the transaction in the teardown so tests don't see each other's data."
            },
            {
                "question": "If test A and test B both require a `user` fixture, does test B get the exact same user object?",
                "answer": "By default, fixtures are function-scoped. Pytest will execute the fixture twice, so test B gets a freshly created user object, preventing test pollution."
            }
        ],
        "sources": [
            "https://docs.pytest.org/en/7.1.x/fixture.html"
        ]
    },
    
    "parametrized-tests": {
        "slug": "parametrized-tests",
        "title": "Parametrized Tests",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "easy",
            "estimated_minutes": 15,
            "importance": 8,
            "interview_frequency": "medium",
            "prerequisites": ["pytest-basics-and-fixtures"],
            "unlocks": [],
            "project_usage": ["Testing edge cases", "Reducing boilerplate"]
        },
        "hook": {
            "scenario": "You need to test an email validator with 10 different valid emails and 10 invalid ones. You copy-paste the test 20 times."
        },
        "mental_model": {
            "intuition": "Parametrization is a loop for your tests. Instead of writing one test per scenario, you write the test logic once and feed it a table of inputs and expected outputs."
        },
        "sections": [
            {
                "body": "Pytest's `@pytest.mark.parametrize` decorator allows you to define multiple sets of arguments for a single test function."
            },
            {
                "body": "When pytest runs, it treats each parameter set as an independent, standalone test. If one input fails, the others will still run."
            }
        ],
        "code_snippets": [
            {
                "title": "Repetitive testing",
                "language": "python",
                "code": "def test_is_valid_email_1():\n    assert is_valid('test@example.com') is True\n\ndef test_is_valid_email_2():\n    assert is_valid('invalid') is False",
                "explanation": "This approach scales poorly as the number of test cases increases."
            },
            {
                "title": "Parametrized test",
                "language": "python",
                "code": "import pytest\n\n@pytest.mark.parametrize(\"email, expected\", [\n    ('test@example.com', True),\n    ('invalid', False),\n    ('user@sub.domain.com', True),\n])\ndef test_is_valid_email(email, expected):\n    assert is_valid(email) == expected",
                "explanation": "The decorator unpacks each tuple into the test function arguments. Pytest reports this as 3 separate test cases."
            }
        ],
        "common_mistakes": [
            {
                "title": "Looping inside a test",
                "explanation": "If you write a `for` loop inside a single test, the test halts on the first failure, so you won't know if the remaining inputs in the loop would have passed."
            }
        ],
        "recall_questions": [
            {
                "q": "Why is `@pytest.mark.parametrize` better than a `for` loop inside a test?",
                "answer": "Parametrize creates independent test cases. A failure in one parameter set doesn't stop pytest from testing the others, whereas a loop stops at the first `assert` failure."
            },
            {
                "q": "How do you specify the argument names for a parametrized test?",
                "answer": "They are provided as a comma-separated string in the first argument to the decorator, e.g. `@pytest.mark.parametrize('input,expected', [...])`."
            },
            {
                "q": "Can you parametrize over fixtures?",
                "answer": "You cannot directly pass fixture results into the parametrize decorator's data, but you can use `indirect=True` or use fixture parametrization via the `params` argument in `@pytest.fixture`."
            }
        ],
        "oa_questions": [
            {
                "question": "How would you test an API endpoint that filters by status, ensuring it works for 'active', 'pending', and 'archived'?",
                "answer": "I would write a single test function that makes a request to the endpoint, decorated with `@pytest.mark.parametrize('status', ['active', 'pending', 'archived'])`."
            },
            {
                "question": "What happens if we stack two `@pytest.mark.parametrize` decorators on a single test?",
                "answer": "Pytest will generate the cartesian product (all combinations) of both parameter sets."
            }
        ],
        "sources": [
            "https://docs.pytest.org/en/7.1.x/how-to/parametrize.html"
        ]
    },

    "mocking-and-patching": {
        "slug": "mocking-and-patching",
        "title": "Mocking and Patching",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "hard",
            "estimated_minutes": 35,
            "importance": 9,
            "interview_frequency": "high",
            "prerequisites": ["pytest-basics-and-fixtures"],
            "unlocks": [],
            "project_usage": ["Testing third-party APIs", "Isolating unit tests"]
        },
        "hook": {
            "scenario": "Your CI pipeline is failing randomly because an external payment API (Stripe) is rate-limiting your test runner. Tests shouldn't hit real external APIs."
        },
        "mental_model": {
            "intuition": "Mocking is like a movie set. Instead of using a real bank vault (an external API), you build a wooden prop that looks like a vault. The actors (your code) interact with the prop, and you control exactly what the prop does."
        },
        "sections": [
            {
                "body": "In Python, `unittest.mock.patch` temporarily replaces a real object (like a function or a class) with a `MagicMock` during a test. A mock records how it was called and can be configured to return specific values."
            },
            {
                "body": "FastAPI provides a superior alternative to `patch` for APIs: `app.dependency_overrides`. Instead of monkey-patching Python's internals, you tell the framework to inject a fake dependency when running tests."
            }
        ],
        "code_snippets": [
            {
                "title": "Bad: Patching internals",
                "language": "python",
                "code": "from unittest.mock import patch\n\n@patch('app.services.payment.charge_stripe')\ndef test_payment(mock_charge):\n    mock_charge.return_value = True\n    # Brittle: if the import path changes, the mock breaks\n    res = process_order() \n    mock_charge.assert_called_once()",
                "explanation": "Patching requires knowing exactly where the module is imported. It is highly brittle and can cause weird side effects if not cleaned up."
            },
            {
                "title": "Good: FastAPI Dependency Overrides",
                "language": "python",
                "code": "from fastapi.testclient import TestClient\nfrom app.main import app\nfrom app.dependencies import get_payment_gateway\n\nclass FakeGateway:\n    def charge(self, amount):\n        return True\n\n# Override the dependency\napp.dependency_overrides[get_payment_gateway] = FakeGateway\n\nclient = TestClient(app)\n\ndef test_payment_endpoint():\n    res = client.post('/checkout')\n    assert res.status_code == 200\n    # Clean up override after test\n    app.dependency_overrides = {}",
                "explanation": "Instead of `patch`, we override the FastAPI dependency. This is typesafe, refactor-friendly, and respects the framework's lifecycle."
            }
        ],
        "common_mistakes": [
            {
                "title": "Patching the wrong path",
                "explanation": "You must patch the object where it is *used* (imported into), not where it is *defined*. If module `A` imports `foo` from `B`, you patch `A.foo`, not `B.foo`."
            },
            {
                "title": "Using patch instead of dependency_overrides",
                "explanation": "In FastAPI, patching internal functions that are meant to be injected is an anti-pattern. Always use `app.dependency_overrides` instead."
            }
        ],
        "recall_questions": [
            {
                "q": "What is the primary rule for the string path passed to `@patch()`?",
                "answer": "Patch where the object is looked up/used (the namespace it's imported into), not where it is defined."
            },
            {
                "q": "How do you check if a mocked function was executed exactly once?",
                "answer": "Use `mock_obj.assert_called_once()` or `mock_obj.assert_called_once_with(*args, **kwargs)`."
            },
            {
                "q": "In FastAPI, what is the preferred way to mock a database session or external service?",
                "answer": "Using `app.dependency_overrides[original_dependency] = mock_dependency`."
            }
        ],
        "oa_questions": [
            {
                "question": "How do you test an endpoint that sends an email without actually sending an email?",
                "answer": "If the email sender is injected via FastAPI `Depends`, I would use `app.dependency_overrides` to inject a `FakeEmailSender` that just appends the email to an in-memory list. Then I can assert the list length."
            },
            {
                "question": "Why is FastAPI's dependency overriding superior to `unittest.mock.patch`?",
                "answer": "`patch` relies on string paths which break during refactoring and can cause state leakage if not torn down. Dependency overrides are strongly typed, robust against refactoring, and explicitly supported by the framework."
            }
        ],
        "sources": [
            "https://fastapi.tiangolo.com/advanced/testing-dependencies/",
            "https://docs.python.org/3/library/unittest.mock.html"
        ]
    },

    "async-tests": {
        "slug": "async-tests",
        "title": "Async Tests",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "medium",
            "estimated_minutes": 20,
            "importance": 9,
            "interview_frequency": "medium",
            "prerequisites": ["pytest-basics-and-fixtures"],
            "unlocks": [],
            "project_usage": ["Testing async endpoints", "Async database tests"]
        },
        "hook": {
            "scenario": "You write an `async def test_my_func():` and pytest skips it, or gives a warning about an un-awaited coroutine."
        },
        "mental_model": {
            "intuition": "Pytest is a synchronous runner by default. If a test is a coroutine (`async def`), pytest just calls it (which returns a coroutine object) and immediately moves on without running it on an event loop. You need a plugin to provide the event loop."
        },
        "sections": [
            {
                "body": "To test `async` functions, you must install `pytest-asyncio`. This plugin automatically provisions an event loop for your tests."
            },
            {
                "body": "Any test defined as `async def` must be decorated with `@pytest.mark.asyncio`, or you must set `asyncio_mode = auto` in your `pytest.ini` so it detects them automatically."
            }
        ],
        "code_snippets": [
            {
                "title": "Failing: un-awaited coroutine",
                "language": "python",
                "code": "async def test_fetch_data():\n    data = await fetch_data()\n    assert data is not None\n# Pytest will warn: coroutine 'test_fetch_data' was never awaited",
                "explanation": "Standard pytest doesn't know how to run an event loop to execute the coroutine."
            },
            {
                "title": "Working Async Test",
                "language": "python",
                "code": "import pytest\n\n@pytest.mark.asyncio\nasync def test_fetch_data():\n    data = await fetch_data()\n    assert data['status'] == 'ok'",
                "explanation": "With `pytest-asyncio`, the decorator tells pytest to spin up an event loop, run the coroutine to completion, and tear down the loop."
            }
        ],
        "common_mistakes": [
            {
                "title": "Mixing sync test client with async code",
                "explanation": "If your application relies heavily on async features, testing it with the synchronous `TestClient` can mask async blocking bugs. Use `httpx.AsyncClient` instead."
            },
            {
                "title": "Async fixtures without pytest-asyncio",
                "explanation": "Just like tests, if you define an `async def` fixture, `pytest-asyncio` is required to evaluate it properly."
            }
        ],
        "recall_questions": [
            {
                "q": "Why does a standard pytest run fail to execute `async def` tests?",
                "answer": "Because it calls the function, which returns a coroutine object, but it does not run it on an asyncio event loop."
            },
            {
                "q": "What plugin is standard for running async tests in pytest?",
                "answer": "`pytest-asyncio`."
            },
            {
                "q": "How can you avoid decorating every async test with `@pytest.mark.asyncio`?",
                "answer": "By configuring `pytest.ini` with `asyncio_mode = auto`."
            }
        ],
        "oa_questions": [
            {
                "question": "If you have an `async` database driver, how must you write your test fixture to provide a session?",
                "answer": "The fixture must be an `async def` function, yielding the async session. The tests consuming it must also be `async def` and marked with `@pytest.mark.asyncio`."
            },
            {
                "question": "What happens if an `async` test hangs indefinitely?",
                "answer": "Usually it means a task was left awaiting a lock or a network call that never resolved, or there is a sync blocking call starving the test's event loop."
            }
        ],
        "sources": [
            "https://pytest-asyncio.readthedocs.io/en/latest/"
        ]
    },

    "api-tests-httpx-testclient": {
        "slug": "api-tests-httpx-testclient",
        "title": "API Tests: TestClient vs HTTPX",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "medium",
            "estimated_minutes": 25,
            "importance": 9,
            "interview_frequency": "high",
            "prerequisites": ["async-tests", "pytest-basics-and-fixtures"],
            "unlocks": [],
            "project_usage": ["End-to-end API testing", "Integration testing"]
        },
        "hook": {
            "scenario": "You're testing a FastAPI app using `TestClient`. The test passes, but in production, the exact same endpoint raises a `RuntimeError: Timeout context manager should be used inside a task`."
        },
        "mental_model": {
            "intuition": "Testing a server requires a client. `TestClient` is a synchronous caller that bypasses the network. `httpx.AsyncClient` + ASGI transport actually executes the request in a true asynchronous event loop, perfectly mimicking production."
        },
        "sections": [
            {
                "body": "FastAPI's `TestClient` (built on `requests` and `starlette`) is synchronous. It's great for simple apps, but it runs your async endpoints in a simulated synchronous thread pool."
            },
            {
                "body": "If your app uses `asyncio` deeply (like async database drivers or HTTP clients), `TestClient` can hide concurrency bugs. In these cases, you must use `httpx.AsyncClient` with an `ASGITransport` to test asynchronously."
            }
        ],
        "code_snippets": [
            {
                "title": "Sync TestClient",
                "language": "python",
                "code": "from fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_read_main():\n    response = client.get(\"/\")\n    assert response.status_code == 200",
                "explanation": "This is simple but entirely synchronous. If the endpoint `await`s something that relies on a specific event loop state, it might behave differently here than in prod."
            },
            {
                "title": "AsyncClient (Ground Truth)",
                "language": "python",
                "code": "import pytest\nfrom httpx import AsyncClient, ASGITransport\nfrom app.main import app\n\n@pytest.mark.asyncio\nasync def test_async_endpoint():\n    transport = ASGITransport(app=app)\n    async with AsyncClient(transport=transport, base_url=\"http://test\") as client:\n        response = await client.get(\"/\")\n        assert response.status_code == 200",
                "explanation": "This runs the FastAPI app entirely asynchronously, ensuring the event loop behavior matches the real `uvicorn` production server."
            }
        ],
        "common_mistakes": [
            {
                "title": "Using TestClient for fully async apps",
                "explanation": "If your app uses `asyncpg` or `httpx` internally, `TestClient` can mask deadlocks or trigger event-loop mismatch errors. Always use `AsyncClient` for async apps."
            }
        ],
        "recall_questions": [
            {
                "q": "What library is `FastAPI(TestClient)` built on top of?",
                "answer": "It is provided by Starlette and built on top of `requests` and `httpx` synchronously."
            },
            {
                "q": "Why is `httpx.AsyncClient` preferred over `TestClient` for heavily async applications?",
                "answer": "It tests the application in a true asyncio event loop, matching the production environment and exposing concurrency bugs."
            },
            {
                "q": "What transport is needed for `httpx.AsyncClient` to directly test a FastAPI app without a real network server?",
                "answer": "`ASGITransport(app=app)`."
            }
        ],
        "oa_questions": [
            {
                "question": "How do you structure your pytest fixtures to provide an `AsyncClient`?",
                "answer": "I would create an `async def` fixture using `pytest-asyncio` that yields an `httpx.AsyncClient` configured with `ASGITransport(app=app)` so every test gets an isolated async client."
            },
            {
                "question": "A test passes with `TestClient` but the app fails in production under uvicorn. What's the likely difference?",
                "answer": "`TestClient` runs your app synchronously. If your app has blocking I/O inside an `async def` endpoint, `TestClient` might survive it, but uvicorn will freeze the event loop."
            }
        ],
        "sources": [
            "https://fastapi.tiangolo.com/advanced/async-tests/"
        ]
    },
    
    "coverage-and-ci": {
        "slug": "coverage-and-ci",
        "title": "Coverage and CI",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier2",
        "metadata": {
            "difficulty": "medium",
            "estimated_minutes": 15,
            "importance": 7,
            "interview_frequency": "medium",
            "prerequisites": ["pytest-basics-and-fixtures"],
            "unlocks": [],
            "project_usage": ["Setting up GitHub Actions", "Enforcing code quality"]
        },
        "hook": {
            "scenario": "A developer pushes a PR that passes all tests, but it completely missed a new `except` block. In production, that block executes and crashes due to a typo."
        },
        "mental_model": {
            "intuition": "Coverage is a highlighter. It runs your tests while watching which lines of your source code actually execute. CI (Continuous Integration) is the bouncer that rejects PRs if the highlighted lines fall below a certain percentage."
        },
        "sections": [
            {
                "body": "`pytest-cov` is a pytest plugin that measures code coverage. It generates reports showing exactly which lines of code were executed and which were missed by your test suite."
            },
            {
                "body": "Continuous Integration (like GitHub Actions) runs these tests automatically on every push. You can configure it to fail the build if the total coverage drops below a threshold."
            }
        ],
        "code_snippets": [
            {
                "title": "Running tests with coverage",
                "language": "bash",
                "code": "pytest --cov=app --cov-report=term-missing --cov-fail-under=90",
                "explanation": "This tells pytest to measure coverage for the `app` package, print the exact lines missed, and exit with an error code if coverage is below 90%."
            },
            {
                "title": "GitHub Actions CI Workflow",
                "language": "yaml",
                "code": "name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: actions/setup-python@v4\n        with:\n          python-version: '3.11'\n      - run: pip install -r requirements.txt pytest pytest-cov\n      - run: pytest --cov=app --cov-fail-under=90",
                "explanation": "This standard CI pipeline ensures that no un-tested or poorly-tested code is merged into the main branch."
            }
        ],
        "common_mistakes": [
            {
                "title": "Chasing 100% coverage blindly",
                "explanation": "100% line coverage means every line ran, not that every logical state was verified. Focus on testing edge cases and business logic rather than writing trivial tests just to hit 100%."
            }
        ],
        "recall_questions": [
            {
                "q": "What command line flag makes `pytest-cov` exit with an error if coverage is too low?",
                "answer": "`--cov-fail-under=<percentage>`."
            },
            {
                "q": "What does `--cov-report=term-missing` do?",
                "answer": "It prints a terminal report that includes the specific line numbers that were not executed during the tests."
            },
            {
                "q": "Why run coverage checks in a CI pipeline?",
                "answer": "To automatically prevent code from being merged if it doesn't meet the project's testing standards."
            }
        ],
        "oa_questions": [
            {
                "question": "If a line of code is covered by tests, does it mean the code is bug-free?",
                "answer": "No, it just means the line executed. The test might not have asserted the correct outcome, or it might have missed specific data permutations that cause a bug."
            },
            {
                "question": "How do you exclude certain files (like database migrations) from the coverage report?",
                "answer": "You can configure an `.coveragerc` file and use the `omit` directive to ignore specific directories or files."
            }
        ],
        "sources": [
            "https://pytest-cov.readthedocs.io/en/latest/"
        ]
    },

    "env-vars-and-secrets": {
        "slug": "env-vars-and-secrets",
        "title": "Env Vars and Secrets",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "easy",
            "estimated_minutes": 25,
            "importance": 10,
            "interview_frequency": "high",
            "prerequisites": [],
            "unlocks": [],
            "project_usage": ["Configuration management", "Security"]
        },
        "hook": {
            "scenario": "You accidentally hardcoded a database password in your code. You pushed it to GitHub. Within 5 minutes, an automated bot scrapes it and drops your production database."
        },
        "mental_model": {
            "intuition": "The '12-Factor App' rule: Configuration should be strictly separated from code. Code lives in Git; secrets live in the environment."
        },
        "sections": [
            {
                "body": "Environment variables are key-value pairs managed by the operating system. They allow you to change an application's behavior (e.g., pointing to a staging DB vs a prod DB) without changing the code."
            },
            {
                "body": "In FastAPI and Pydantic v2, `pydantic-settings` is the standard way to read and validate environment variables. It automatically loads variables and converts them to the correct Python types."
            },
            {
                "body": "Locally, you store secrets in a `.env` file, which is strictly added to `.gitignore`. In production, they are injected by the hosting provider (Docker, AWS, Vercel)."
            }
        ],
        "code_snippets": [
            {
                "title": "Bad: Hardcoded config",
                "language": "python",
                "code": "DB_URL = 'postgresql://user:pass@localhost:5432/db'\nSECRET_KEY = 'super_secret_key'\n\n# Do not do this. It leaks secrets and requires a code change to swap environments.",
                "explanation": "Hardcoded secrets are a critical security vulnerability."
            },
            {
                "title": "Good: Pydantic Settings (Ground Truth)",
                "language": "python",
                "code": "from pydantic_settings import BaseSettings, SettingsConfigDict\n\nclass Settings(BaseSettings):\n    database_url: str\n    secret_key: str\n    debug: bool = False\n    \n    # Automatically reads from .env file\n    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')\n\n# Instantiate once, globally or via a dependency\nsettings = Settings()",
                "explanation": "If `DATABASE_URL` is missing from the environment, Pydantic will crash the app immediately on startup, which is exactly what you want (Fail Fast)."
            }
        ],
        "common_mistakes": [
            {
                "title": "Committing the .env file",
                "explanation": "If you forget to add `.env` to `.gitignore`, you will push secrets to the repository. If this happens, you must invalidate and rotate the keys immediately; deleting the file from Git history isn't enough."
            }
        ],
        "recall_questions": [
            {
                "q": "What is the 12-Factor App principle regarding configuration?",
                "answer": "Store configuration in the environment, keeping strict separation between config and code."
            },
            {
                "q": "Why is `pydantic-settings` preferred over `os.environ.get()`?",
                "answer": "It provides type validation, fail-fast behavior if a required variable is missing, and automatic `.env` file loading."
            },
            {
                "q": "What happens if a required field in a Pydantic Settings class is missing from the environment?",
                "answer": "The application raises a `ValidationError` and crashes at startup."
            }
        ],
        "oa_questions": [
            {
                "question": "How do you handle local development secrets versus production secrets?",
                "answer": "Locally, I use a `.env` file (which is gitignored). In production, I configure the environment variables directly in the deployment platform (e.g. AWS Secrets Manager, Kubernetes Secrets, or the PaaS dashboard)."
            },
            {
                "question": "What is the problem with using `os.getenv('DEBUG', 'False')` in an `if` statement?",
                "answer": "`os.getenv` returns a string. Both `'True'` and `'False'` evaluate to truthy in Python. Pydantic settings properly coerces the string `'False'` to a boolean `False`."
            }
        ],
        "sources": [
            "https://docs.pydantic.dev/latest/concepts/pydantic_settings/",
            "https://12factor.net/config"
        ]
    },

    "structured-logging-prod": {
        "slug": "structured-logging-prod",
        "title": "Structured Logging in Prod",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier2",
        "metadata": {
            "difficulty": "medium",
            "estimated_minutes": 25,
            "importance": 8,
            "interview_frequency": "medium",
            "prerequisites": ["middleware-and-cors"],
            "unlocks": [],
            "project_usage": ["Production observability", "Debugging distributed systems"]
        },
        "hook": {
            "scenario": "A user complains that checkout failed at 3:14 PM. You search your text logs, but hundreds of concurrent requests are intermixed. You can't figure out which log lines belong to their request."
        },
        "mental_model": {
            "intuition": "Standard logs are strings designed for human eyes. Structured logs are JSON objects designed for machines (like Datadog or Splunk). By attaching a unique `request_id` to every log emitted during a request, you can instantly filter and trace a single user's journey."
        },
        "sections": [
            {
                "body": "In production, `print()` and standard Python `logging` text strings are insufficient. They cannot be easily queried or filtered in centralized log aggregators."
            },
            {
                "body": "Structured logging outputs a JSON object for every log line. Each object contains standard fields: timestamp, severity level, module, and a context payload."
            },
            {
                "body": "A critical backend pattern is injecting a correlation ID (`request_id`). A middleware generates a UUID when the request starts, stores it in context variables (`contextvars`), and the logger automatically appends it to every log emitted during that request lifecycle."
            }
        ],
        "code_snippets": [
            {
                "title": "Bad: Text logging",
                "language": "python",
                "code": "import logging\n\nlogging.info(f\"User {user_id} bought item {item_id}\")\n# Output: 2026-05-12 12:00:00 INFO User 42 bought item 99",
                "explanation": "If you want to find all purchases of item 99, you have to write a brittle regex parser."
            },
            {
                "title": "Good: Structured logging with context",
                "language": "python",
                "code": "import structlog\nfrom contextvars import ContextVar\n\nrequest_id_var = ContextVar(\"request_id\")\nlogger = structlog.get_logger()\n\n# In a FastAPI Middleware:\nrequest_id_var.set(\"uuid-1234\")\n\n# Anywhere in the app:\nlogger.info(\"item_purchased\", user_id=42, item_id=99)\n\n# Output: {\"event\": \"item_purchased\", \"user_id\": 42, \"item_id\": 99, \"request_id\": \"uuid-1234\"}",
                "explanation": "The output is JSON. Log aggregators automatically parse it, allowing you to instantly search `request_id=uuid-1234` and see everything that happened."
            }
        ],
        "common_mistakes": [
            {
                "title": "Leaking context across requests",
                "explanation": "If you use global variables or thread locals for the `request_id` in an async app, requests will overwrite each other's IDs. You MUST use Python's `contextvars`, which are natively async-safe."
            }
        ],
        "recall_questions": [
            {
                "q": "Why is JSON preferred over plain text for production logging?",
                "answer": "JSON can be automatically parsed, indexed, and queried by log management systems like Datadog or ELK."
            },
            {
                "q": "What is a correlation ID or request ID?",
                "answer": "A unique identifier generated at the start of a request and attached to all log messages related to that request, allowing you to trace the flow."
            },
            {
                "q": "Which Python module must be used to store request context safely in `async` applications?",
                "answer": "`contextvars`."
            }
        ],
        "oa_questions": [
            {
                "question": "How would you trace a request that starts in a FastAPI service, calls a microservice, and then updates a database?",
                "answer": "I would generate a `request_id` in the API gateway/middleware. I'd include it in structured logs locally, and inject it into the HTTP headers when calling the microservice so the downstream service logs with the exact same ID."
            },
            {
                "question": "Why shouldn't you use standard Python threading locals for context in FastAPI?",
                "answer": "FastAPI uses `asyncio`. Multiple concurrent requests share the same thread (the event loop). Thread locals would leak state between requests; `contextvars` natively handle async task separation."
            }
        ],
        "sources": [
            "https://www.structlog.org/en/stable/"
        ]
    },

    "httpexception-and-error-shape": {
        "slug": "httpexception-and-error-shape",
        "title": "HTTPException and Error Shape",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "easy",
            "estimated_minutes": 20,
            "importance": 9,
            "interview_frequency": "medium",
            "prerequisites": ["status-codes-and-openapi"],
            "unlocks": [],
            "project_usage": ["API Design", "Error handling"]
        },
        "hook": {
            "scenario": "Your frontend app receives a `500 Internal Server Error` with an HTML traceback instead of JSON. The frontend crashes trying to parse `response.json()`."
        },
        "mental_model": {
            "intuition": "Exceptions in Python crash the program. In a web API, you don't want to crash the server; you want to intercept the crash and return a neatly formatted JSON apology (the Error Shape) to the client."
        },
        "sections": [
            {
                "body": "When a client requests a resource that doesn't exist, or lacks permissions, you should raise an `HTTPException`."
            },
            {
                "body": "FastAPI catches `HTTPException` globally and converts it into a JSON response. The default shape is `{\"detail\": \"Error message\"}`."
            },
            {
                "body": "For robust APIs, you should override the global exception handlers to standardize a strict 'Error Shape'. Every error (validation errors, 404s, 500s) should follow the exact same JSON structure so frontend clients can parse them predictably."
            }
        ],
        "code_snippets": [
            {
                "title": "Standard HTTPException",
                "language": "python",
                "code": "from fastapi import HTTPException, status\n\ndef get_user(user_id: int):\n    user = db.query(User).get(user_id)\n    if not user:\n        # Halts execution and returns 404 JSON\n        raise HTTPException(\n            status_code=status.HTTP_404_NOT_FOUND,\n            detail=\"User not found\"\n        )\n    return user",
                "explanation": "You don't `return` an error response. You `raise` it. FastAPI catches it and converts it to `{'detail': 'User not found'}`."
            },
            {
                "title": "Custom Error Shape (Exception Handler)",
                "language": "python",
                "code": "from fastapi import FastAPI, Request\nfrom fastapi.responses import JSONResponse\n\napp = FastAPI()\n\nclass CustomError(Exception):\n    def __init__(self, message: str, code: str):\n        self.message = message\n        self.code = code\n\n@app.exception_handler(CustomError)\nasync def custom_error_handler(request: Request, exc: CustomError):\n    return JSONResponse(\n        status_code=400,\n        content={\"error\": {\"code\": exc.code, \"message\": exc.message}},\n    )",
                "explanation": "This guarantees the frontend always gets `{'error': {'code': '...', 'message': '...'}}` regardless of where `CustomError` was raised."
            }
        ],
        "common_mistakes": [
            {
                "title": "Leaking stack traces in production",
                "explanation": "If an unhandled exception occurs (e.g., `ZeroDivisionError`), it becomes a 500. Never expose the raw stack trace in the JSON payload in production, as it leaks internal system paths and logic."
            }
        ],
        "recall_questions": [
            {
                "q": "What happens when you `raise HTTPException(...)` in FastAPI?",
                "answer": "FastAPI intercepts the exception and automatically transforms it into a JSON response with the specified status code."
            },
            {
                "q": "What is the default JSON shape of a FastAPI `HTTPException`?",
                "answer": "`{\"detail\": \"Your message here\"}`."
            },
            {
                "q": "How do you catch custom domain exceptions and convert them to standard JSON errors?",
                "answer": "By registering a global exception handler using the `@app.exception_handler(MyException)` decorator."
            }
        ],
        "oa_questions": [
            {
                "question": "Why is it better to raise exceptions for missing resources rather than returning `None` up to the router?",
                "answer": "Raising an exception halts the flow immediately (Fail Fast). If you return `None`, every function up the call stack has to check `if result is None:` and handle it, creating massive boilerplate."
            },
            {
                "question": "How do you ensure the frontend doesn't crash when your API hits a 500 Internal Server Error?",
                "answer": "I register a global exception handler for the base `Exception` class. It logs the full traceback internally, but returns a clean, standardized JSON response (e.g. `{'error': 'Internal Server Error'}`) with a 500 status code."
            }
        ],
        "sources": [
            "https://fastapi.tiangolo.com/tutorial/handling-errors/"
        ]
    },

    "dockerfile-multi-stage": {
        "slug": "dockerfile-multi-stage",
        "title": "Dockerfile & Multi-stage Builds",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "medium",
            "estimated_minutes": 35,
            "importance": 10,
            "interview_frequency": "high",
            "prerequisites": [],
            "unlocks": [],
            "project_usage": ["Containerizing apps", "Deployment"]
        },
        "hook": {
            "scenario": "Your Python Docker image is 1.5GB. It takes 10 minutes to deploy, and a security scanner flags that you shipped a C++ compiler and pip caching artifacts into production."
        },
        "mental_model": {
            "intuition": "A multi-stage Dockerfile is a factory with two rooms. Room 1 (builder) has all the heavy tools needed to compile dependencies. Room 2 (runtime) is completely empty; you only copy the finished product from Room 1. Room 2 gets shipped."
        },
        "sections": [
            {
                "body": "Docker containers package an application and its dependencies into a single runnable artifact."
            },
            {
                "body": "A standard Python `Dockerfile` often includes build tools (like `gcc`) required to compile certain packages. If you ship this image, it's bloated and has a large attack surface."
            },
            {
                "body": "Multi-stage builds solve this. You use a `builder` stage to install dependencies into a virtual environment, then use a slim `runtime` stage where you simply copy the virtual environment over."
            }
        ],
        "code_snippets": [
            {
                "title": "Single-stage (Bloated)",
                "language": "dockerfile",
                "code": "FROM python:3.11\nWORKDIR /app\nCOPY requirements.txt .\n# Caches pip artifacts permanently in the layer\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\"]",
                "explanation": "This image includes the entire Debian OS, development headers, and `pip` caches. It's huge."
            },
            {
                "title": "Multi-stage Build (Ground Truth)",
                "language": "dockerfile",
                "code": "# Stage 1: Builder\nFROM python:3.11-slim AS builder\nRUN apt-get update && apt-get install -y gcc\nRUN python -m venv /opt/venv\nENV PATH=\"/opt/venv/bin:$PATH\"\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\n# Stage 2: Runtime\nFROM python:3.11-slim\n# Copy only the compiled environment, leave gcc behind\nCOPY --from=builder /opt/venv /opt/venv\nENV PATH=\"/opt/venv/bin:$PATH\"\nWORKDIR /app\nCOPY . .\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]",
                "explanation": "The final image drops the `builder` stage completely. It only contains the application code and the clean virtual environment."
            }
        ],
        "common_mistakes": [
            {
                "title": "Baking secrets into the Dockerfile",
                "explanation": "Never use `ENV SECRET_KEY=1234` in a Dockerfile. Docker caches this in a layer permanently. Anyone with the image can extract the secret. Secrets must be passed at runtime."
            }
        ],
        "recall_questions": [
            {
                "q": "What is the main advantage of a multi-stage Docker build?",
                "answer": "It reduces the final image size and attack surface by excluding build tools and caching artifacts."
            },
            {
                "q": "How do you transfer files from a previous stage in a multi-stage Dockerfile?",
                "answer": "Using the `COPY --from=<stage_name>` directive."
            },
            {
                "q": "Why should you never put API keys in a Dockerfile?",
                "answer": "Because Docker layers are readable by anyone who has the image. Secrets must be injected at runtime."
            }
        ],
        "oa_questions": [
            {
                "question": "Why do we create a Python virtual environment (`venv`) inside a Docker container when the container itself is already isolated?",
                "answer": "While isolation isn't the issue, a virtual environment makes it extremely easy to move dependencies in a multi-stage build. You can simply `COPY --from=builder /opt/venv /opt/venv` and you've transferred exactly what you need without copying system-level files."
            },
            {
                "question": "What is the order of operations in a Dockerfile for optimal caching?",
                "answer": "Copy `requirements.txt`, run `pip install`, and THEN copy the application code. This ensures that if only application code changes, the dependency installation layer is cached."
            }
        ],
        "sources": [
            "https://docs.docker.com/build/building/multi-stage/"
        ]
    },

    "uvicorn-gunicorn-workers": {
        "slug": "uvicorn-gunicorn-workers",
        "title": "Uvicorn, Gunicorn, and Workers",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "hard",
            "estimated_minutes": 30,
            "importance": 10,
            "interview_frequency": "high",
            "prerequisites": ["wsgi-vs-asgi"],
            "unlocks": [],
            "project_usage": ["Production deployment", "Performance tuning"]
        },
        "hook": {
            "scenario": "You deploy your blazing-fast async FastAPI app using `uvicorn app.main:app`. Under load, it maxes out exactly 1 CPU core at 100%, while the other 7 cores sit completely idle."
        },
        "mental_model": {
            "intuition": "Uvicorn is a chef working on a single stove (one process, one event loop). No matter how fast they juggle orders asynchronously, they only have two hands. Gunicorn is a restaurant manager that hires N chefs (worker processes) so you can utilize the whole kitchen."
        },
        "sections": [
            {
                "body": "Because of Python's Global Interpreter Lock (GIL), a single Python process can only execute on one CPU core at a time, regardless of how many async tasks or threads it spins up."
            },
            {
                "body": "Uvicorn is an ASGI server. It runs an event loop in a single process. It handles concurrent I/O brilliantly, but it cannot utilize multiple CPU cores."
            },
            {
                "body": "To scale across cores, we use Gunicorn as a process manager. Gunicorn forks the application into multiple independent worker processes, each running an instance of Uvicorn. This bypasses the GIL entirely."
            }
        ],
        "code_snippets": [
            {
                "title": "Development Server (Single Core)",
                "language": "bash",
                "code": "uvicorn app.main:app --host 0.0.0.0 --port 8000",
                "explanation": "This runs one process. Fine for development, but in production, it will bottleneck on a single CPU core."
            },
            {
                "title": "Production Server (Ground Truth)",
                "language": "bash",
                "code": "gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000",
                "explanation": "Gunicorn acts as the master process. `-w 4` creates 4 separate Python processes. `-k` tells them to use the Uvicorn ASGI worker class. 4 event loops, 4 CPU cores utilized."
            }
        ],
        "common_mistakes": [
            {
                "title": "Assuming async bypasses the GIL",
                "explanation": "`asyncio` allows concurrency for I/O bounds, but it does NOT bypass the GIL. CPU-bound work (like JSON parsing or image processing) in an async endpoint will block the event loop. Multi-processing (workers) is the only way to scale CPU in Python."
            }
        ],
        "recall_questions": [
            {
                "q": "Why does a raw `uvicorn` deployment only utilize one CPU core?",
                "answer": "Because it runs as a single Python process, which is constrained to one core by the Global Interpreter Lock (GIL)."
            },
            {
                "q": "What role does Gunicorn play when deployed with FastAPI?",
                "answer": "It acts as a process manager, spawning multiple independent Uvicorn worker processes to utilize multiple CPU cores."
            },
            {
                "q": "How do multiple worker processes bypass the GIL?",
                "answer": "The GIL is per-process. By creating entirely separate Python processes, each has its own GIL and can execute simultaneously on different cores."
            }
        ],
        "oa_questions": [
            {
                "question": "If you have N Gunicorn workers, how does memory usage scale?",
                "answer": "Memory scales linearly (N × memory). Since they are independent processes, they do not share memory space. Every worker loads the entire application and its dependencies into RAM."
            },
            {
                "question": "A request taking 2 seconds of heavy CPU calculation brings your entire API to a halt. You are using Gunicorn with 4 workers. Why did it halt, and how do you fix it?",
                "answer": "CPU-bound work blocks the asyncio event loop. With 4 workers, if 4 users make that request, all 4 event loops are blocked. The fix is to offload the CPU-bound task to a background queue (like Celery/Redis) rather than doing it in the API request lifecycle."
            }
        ],
        "sources": [
            "https://fastapi.tiangolo.com/deployment/server-workers/"
        ]
    },

    "hardening-health-rate-limit-jwt": {
        "slug": "hardening-health-rate-limit-jwt",
        "title": "Hardening, Health, and Rate Limits",
        "roadmap": "python-backend",
        "kind": "engineering",
        "tier": "tier1",
        "metadata": {
            "difficulty": "medium",
            "estimated_minutes": 30,
            "importance": 9,
            "interview_frequency": "high",
            "prerequisites": [],
            "unlocks": [],
            "project_usage": ["Securing APIs", "Production readiness"]
        },
        "hook": {
            "scenario": "A malicious user writes a script to hit your login endpoint 10,000 times a second. Your database gets overwhelmed, and the entire platform goes down for everyone."
        },
        "mental_model": {
            "intuition": "Hardening an API is like building a castle. CORS is the drawbridge (who can enter from a browser). Rate limiting is the turnstile (how fast they can enter). Health checks are the flag on the tower signaling the castle is functional."
        },
        "sections": [
            {
                "body": "Before going to production, an API needs protective boundaries."
            },
            {
                "body": "A Health Check is a simple `/health` endpoint that returns a 200 OK. Load balancers (like AWS ALB or Kubernetes) ping this constantly to know if the container is alive or needs to be restarted."
            },
            {
                "body": "Rate Limiting prevents abuse (DDoS or scraping). It tracks the number of requests per IP or user over a time window and returns a `429 Too Many Requests` if the limit is exceeded."
            }
        ],
        "code_snippets": [
            {
                "title": "Bad: Global CORS with Credentials",
                "language": "python",
                "code": "from fastapi.middleware.cors import CORSMiddleware\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=[\"*\"],\n    allow_credentials=True,\n    allow_methods=[\"*\"],\n)",
                "explanation": "This is a massive security flaw. Allowing credentials (cookies/auth) with a wildcard origin allows any malicious website to impersonate users via CSRF."
            },
            {
                "title": "Good: Specific CORS and Health Check",
                "language": "python",
                "code": "app.add_middleware(\n    CORSMiddleware,\n    allow_origins=[\"https://myapp.com\"],\n    allow_credentials=True,\n    allow_methods=[\"*\"],\n)\n\n@app.get(\"/health\")\ndef health_check():\n    # Optionally verify DB connection here\n    return {\"status\": \"ok\"}",
                "explanation": "CORS is strictly limited to the frontend domain. The health check allows the load balancer to monitor the service."
            }
        ],
        "common_mistakes": [
            {
                "title": "Doing heavy work in a health check",
                "explanation": "If your `/health` endpoint queries 5 external services, a failure in one non-critical service might cause the load balancer to kill the container, taking the whole app down. Keep health checks lightweight."
            }
        ],
        "recall_questions": [
            {
                "q": "What HTTP status code is returned when a client exceeds a rate limit?",
                "answer": "429 Too Many Requests."
            },
            {
                "q": "Why must `allow_origins` not be `[\"*\"]` when `allow_credentials=True`?",
                "answer": "It creates a Cross-Site Request Forgery (CSRF) vulnerability, allowing any website to make authenticated requests on behalf of the user."
            },
            {
                "q": "What is the purpose of a `/health` endpoint?",
                "answer": "To provide a lightweight ping for load balancers or orchestrators (like Kubernetes) to verify the service is running and ready to accept traffic."
            }
        ],
        "oa_questions": [
            {
                "question": "How do you implement rate limiting in a distributed system with multiple worker processes?",
                "answer": "You must use a centralized in-memory store like Redis. If you use local memory, each worker or container will have its own counter, allowing the user to bypass the limit."
            },
            {
                "question": "What is the difference between Authentication and Rate Limiting, and which happens first?",
                "answer": "Rate limiting (often per IP) usually happens first to prevent volumetric attacks before the server spends CPU verifying passwords or JWTs. Authentication proves identity; rate limiting restricts volume."
            }
        ],
        "sources": [
            "https://fastapi.tiangolo.com/tutorial/cors/"
        ]
    }
}

base_dir = "content/roadmaps/python-backend"
os.makedirs(base_dir, exist_ok=True)

for slug, data in files.items():
    with open(os.path.join(base_dir, f"{slug}.json"), "w") as f:
        json.dump(data, f, indent=2)

print(f"Generated {len(files)} files.")
