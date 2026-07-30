"""
Query Parser
=============
Takes a complex user query and splits it into 2-4 focused sub-questions
using DeepSeek Flash. Each sub-question is later fetched from all 3
sources independently.

Example:
  "How does quantum computing affect cryptography?"
  -> ["What is the current state of quantum computing?",
      "What are the fundamentals of modern cryptography?",
      "How does quantum computing impact cryptographic security?"]
"""

import json
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

SYSTEM_PROMPT = """You are a query decomposition engine for a research pipeline.
Given a complex research question, split it into 2-4 focused, self-contained
sub-questions that together cover what's needed to fully answer the original
question. Each sub-question should be searchable on its own (Wikipedia, web
search, or academic papers).

Respond with ONLY a JSON array of strings, nothing else. No markdown, no
explanation. Example output:
["What is the current state of quantum computing?", "What are the fundamentals of modern cryptography?", "How does quantum computing impact cryptographic security?"]
"""


def parse_query(query: str) -> list:
    """Returns a list of sub-question strings. Falls back to the original
    query as a single-item list if the LLM call fails, so the pipeline
    can still continue with a degraded (but non-empty) result."""

    if not DEEPSEEK_API_KEY:
        print("[query_parser] WARNING: DEEPSEEK_API_KEY not set — falling back to using the raw query as-is.")
        return [query]

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()

        # Strip accidental markdown code fences if the model adds them
        if content.startswith("```"):
            content = content.strip("`")
            content = content.replace("json", "", 1).strip()

        sub_queries = json.loads(content)

        if not isinstance(sub_queries, list) or not sub_queries:
            raise ValueError("Model did not return a valid non-empty list")

        return [str(q).strip() for q in sub_queries]

    except Exception as e:
        print(f"[query_parser] WARNING: parsing failed ({e}) — falling back to using the raw query as-is.")
        return [query]


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "How does quantum computing affect cryptography?"
    sub_queries = parse_query(query)
    print(f"\nOriginal query: {query}")
    print(f"Sub-questions ({len(sub_queries)}):")
    for i, sq in enumerate(sub_queries, 1):
        print(f"  {i}. {sq}")
