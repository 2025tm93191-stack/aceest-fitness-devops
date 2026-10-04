# ACEest Fitness & Gym — Flask App with CI/CD

A Flask web application for ACEest Fitness & Gym, built from the baseline `Aceestver` Tkinter scripts, with automated quality gates in **GitHub Actions** and **Jenkins**.

[![CI Pipeline](https://github.com/2025tm93191-stack/aceest-fitness-devops/actions/workflows/main.yml/badge.svg)](https://github.com/2025tm93191-stack/aceest-fitness-devops/actions/workflows/main.yml)

## Features

- Program catalogue (Fat Loss, Muscle Gain, Beginner) with workout and diet plans
- Calorie estimator (body weight × program factor) and BMI calculator
- Client management with membership status and expiry detection
- Weekly adherence tracking with averages, and workout logging
- SQLite storage, JSON REST API, and an HTML home page

## Project Structure

```
aceest-fitness-devops/
├── app.py                    # Flask app factory and routes
├── fitness/
│   ├── programs.py           # Program catalogue and lookups
│   ├── calculations.py       # Calorie, BMI and adherence logic (pure functions)
│   └── db.py                 # SQLite connection and schema
├── templates/index.html      # Home page
├── tests/                    # Pytest suite (unit + API tests)
├── Dockerfile                # Multi-stage build: test + slim runtime
├── Jenkinsfile               # Jenkins BUILD pipeline
├── .github/workflows/main.yml
├── requirements.txt          # Runtime dependencies
└── requirements-dev.txt      # Test and lint tools
```

## Local Setup

Requires Python 3.12+.

```bash
git clone https://github.com/2025tm93191-stack/aceest-fitness-devops.git
cd aceest-fitness-devops
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py
```

Open http://localhost:5000. The SQLite database is created in `instance/aceest.db`; set `ACEEST_DB` to use another path.

## Running Tests Manually

```bash
pytest                                              # run all tests
pytest tests/test_api.py                            # one file
pytest tests/test_api.py::test_bmi_endpoint         # one test
pytest --cov=fitness --cov=app --cov-report=term-missing   # with coverage
flake8 .                                            # lint
```

The suite has 55 tests: unit tests for the pure logic in `fitness/` (calories, BMI, adherence, program lookups) and API tests that drive every endpoint through Flask's test client, including validation errors, 404s and duplicate-client 409s. Each test gets its own temporary SQLite database, so tests never touch `instance/aceest.db` or each other. Coverage is 99%.

## Running with Docker

```bash
docker build -t aceest-fitness .                    # runtime image (default target)
docker run -p 5000:5000 aceest-fitness

docker build --target test -t aceest-fitness:test . # test image
docker run --rm aceest-fitness:test                 # runs Pytest inside the container
```

The Dockerfile uses `python:3.12-slim`, a multi-stage build so test tools never reach the runtime image, a non-root user, no pip cache, a `.dockerignore`, and a health check. The app runs under Gunicorn instead of the Flask dev server.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/programs` | List programs |
| GET | `/api/programs/<code>` | Program detail (`FL`, `MG`, `BG`) |
| POST | `/api/calories` | `{"weight_kg": 70, "program": "FL"}` |
| POST | `/api/bmi` | `{"height_cm": 175, "weight_kg": 70}` |
| GET / POST | `/api/clients` | List or create clients |
| GET | `/api/clients/<name>` | Client detail |
| GET | `/api/clients/<name>/membership` | Membership status |
| GET / POST | `/api/clients/<name>/progress` | `{"week": "W1", "adherence": 85}` |
| GET / POST | `/api/clients/<name>/workouts` | `{"workout_type": "Strength", "duration_min": 45}` |

Example:

```bash
curl -X POST localhost:5000/api/clients -H "Content-Type: application/json" \
     -d '{"name": "Arjun", "weight": 80, "program": "FL"}'
```

## CI/CD Integration Overview

```
 git push / pull request
          │
          ├──────────────► GitHub Actions (.github/workflows/main.yml)
          │                  1. Build & Lint   – compileall + flake8
          │                  2. Docker build   – test image and runtime image
          │                  3. Tests          – Pytest inside the container
          │                  4. Smoke test     – run container, hit /health
          │
          └──────────────► Jenkins (Jenkinsfile, polls GitHub)
                             Checkout → clean venv → lint → unit tests (JUnit report)
                             → Docker build → container tests
```

**GitHub Actions** runs on every push and every pull request, on any branch. Linting runs first; the Docker job depends on it, so a syntax error stops the pipeline before any image is built. Tests run inside the container, which proves the image itself works, not just the developer's machine.

**Jenkins** is the secondary build and quality gate in a controlled environment. It pulls the latest code from GitHub, rebuilds a fresh virtual environment every run (a clean build), publishes JUnit test results, and builds a Docker image tagged with the build number.

### Jenkins Setup

1. Install Jenkins with the **Git**, **Pipeline**, and **JUnit** plugins, and make sure the Jenkins agent has Python 3 and Docker (add the `jenkins` user to the `docker` group).
2. Create a **Pipeline** job → *Pipeline script from SCM* → Git → your repository URL → branch `*/main` → script path `Jenkinsfile`.
3. Run *Build Now* once. After that, Jenkins polls GitHub every 5 minutes. For instant builds, add a GitHub webhook to `http://<jenkins-host>/github-webhook/` and switch the trigger to `githubPush()`.

## Branching Strategy

- `main` — always releasable, protected; changes arrive through pull requests
- `feature/<name>` — new functionality
- `fix/<name>` — bug fixes
- `test/<name>` — test suite work
- `ci/<name>` — pipeline and infrastructure changes (Docker, GitHub Actions, Jenkins)
- `docs/<name>` — documentation

Feature branches are merged into `main` with `--no-ff`, so each feature remains visible as a merge commit in `git log --graph`.

Commit messages follow the `type: summary` style, e.g. `feat: add BMI endpoint`, `test: cover membership expiry`, `ci: run pytest inside docker`.
