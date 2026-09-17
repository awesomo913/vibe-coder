"""Multi-agent pipeline: Planner -> Coder -> Reviewer. All local via Ollama."""
import requests
import json
import time
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api"

# Agent system prompts define each agent's role and behavior
AGENT_PROMPTS = {
    "planner": """You are a Senior Software Architect. Your job is to design a clear,
step-by-step architecture plan for the requested application.

Rules:
- Output a numbered list of components/functions needed
- Specify what each function does, its inputs and outputs
- Note any external libraries needed
- Keep the design lightweight and efficient
- Consider memory and CPU constraints (this may run on limited hardware)
- Do NOT write code - only the architecture plan""",

    "coder": """You are a Lead Python Developer. You receive an architecture plan and
write the complete, working Python code.

Rules:
- Follow the plan EXACTLY - implement every component listed
- Write clean, well-structured Python code
- Include all necessary imports
- Add brief comments for complex logic only
- Use efficient patterns (generators over lists for large data, etc.)
- Output ONLY the raw Python code, no explanations
- Make sure the code is complete and runnable""",

    "reviewer": """You are a System Safety Engineer. You review Python code for bugs,
security issues, and hardware safety.

Rules:
- Check for infinite loops or unbounded recursion
- Check for memory leaks (unclosed files, growing lists, etc.)
- Check for missing error handling on I/O operations
- Check for hardcoded secrets or unsafe practices
- Fix any issues you find
- Output the FINAL corrected code only
- If no issues found, output the code unchanged with a brief "REVIEW PASSED" header""",
}


def get_available_models():
    """Fetch models from local Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/tags", timeout=5)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except requests.RequestException:
        return []


def pick_model(available, preference_keywords):
    """Pick the best model matching preference keywords.

    Filters out 70b+ models to avoid VRAM issues on consumer hardware.
    """
    # Filter out huge models that will likely OOM
    safe_models = [m for m in available if "70b" not in m.lower() and "65b" not in m.lower()]
    if not safe_models:
        safe_models = available  # fallback if ALL models are huge

    for kw in preference_keywords:
        for model in safe_models:
            if kw in model.lower():
                return model
    return safe_models[0] if safe_models else None


def run_agent(agent_name, model, prompt, context=""):
    """Run a single agent: send prompt to Ollama with the agent's system prompt."""
    system = AGENT_PROMPTS[agent_name]
    full_prompt = f"{context}\n\n{prompt}" if context else prompt

    payload = {
        "model": model,
        "prompt": full_prompt,
        "system": system,
        "stream": False,
    }

    try:
        resp = requests.post(f"{OLLAMA_URL}/generate", json=payload, timeout=600)
        resp.raise_for_status()
        return resp.json().get("response", "Error: Empty response.")
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot connect to Ollama. Is it running?"
    except requests.exceptions.Timeout:
        return "ERROR: Agent timed out (10 min limit)."
    except requests.RequestException as e:
        return f"ERROR: {e}"


def run_pipeline(user_request, progress_callback=None):
    """Run the full 3-agent pipeline sequentially.

    progress_callback(agent_name, status, output) is called at each step.
    """
    available = get_available_models()
    if not available:
        return {"error": "No Ollama models found. Run `ollama pull mistral` first."}

    # Pick models for each agent role
    planner_model = pick_model(available, ["dolphin", "mistral", "llama"])
    coder_model = pick_model(available, ["qwen", "coder", "codestral", "deepseek", "dolphin", "mistral"])
    reviewer_model = pick_model(available, ["dolphin", "mistral", "llama"])

    results = {
        "request": user_request,
        "timestamp": datetime.now().isoformat(),
        "agents": {},
    }

    # ── Step 1: Planner ──
    if progress_callback:
        progress_callback("planner", "running", None)

    start = time.time()
    plan = run_agent("planner", planner_model, user_request)
    plan_time = time.time() - start

    results["agents"]["planner"] = {
        "model": planner_model,
        "output": plan,
        "time_seconds": round(plan_time, 1),
    }
    if progress_callback:
        progress_callback("planner", "done", plan)

    if plan.startswith("ERROR"):
        return results

    # ── Step 2: Coder ──
    if progress_callback:
        progress_callback("coder", "running", None)

    start = time.time()
    code = run_agent("coder", coder_model, "Implement this architecture plan:", context=plan)
    code_time = time.time() - start

    results["agents"]["coder"] = {
        "model": coder_model,
        "output": code,
        "time_seconds": round(code_time, 1),
    }
    if progress_callback:
        progress_callback("coder", "done", code)

    if code.startswith("ERROR"):
        return results

    # ── Step 3: Reviewer ──
    if progress_callback:
        progress_callback("reviewer", "running", None)

    start = time.time()
    reviewed = run_agent("reviewer", reviewer_model, "Review this code for safety and correctness:", context=code)
    review_time = time.time() - start

    results["agents"]["reviewer"] = {
        "model": reviewer_model,
        "output": reviewed,
        "time_seconds": round(review_time, 1),
    }
    if progress_callback:
        progress_callback("reviewer", "done", reviewed)

    results["total_time"] = round(plan_time + code_time + review_time, 1)
    return results


def save_results(results, output_dir="outputs"):
    """Save pipeline results to a timestamped file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"vibe_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return filepath
