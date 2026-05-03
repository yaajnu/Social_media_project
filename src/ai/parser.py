import json
import re

from pydantic import BaseModel


def _parse_llm_response(raw: str, model_cls: type[BaseModel]) -> BaseModel:
    """
    Parse and validate a raw LLM JSON string into a Pydantic model.

    Handles markdown code fences in the following forms:
        ```json\n...\n```
        ```\n...\n```
        ```json...```
        ```...```

    Raises:
        ValueError: If JSON is malformed or input is empty.
        ValidationError: If the parsed dict does not match the schema.
    """
    if not raw or not raw.strip():
        raise ValueError("Empty input string")

    cleaned = raw.strip()

    # Strip markdown code fences: ```json ... ``` or ``` ... ```
    # Handles both inline and multiline variants
    fence_pattern = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
    match = fence_pattern.match(cleaned)
    if match:
        cleaned = match.group(1).strip()

    data = json.loads(cleaned)  # raises ValueError (JSONDecodeError) on bad JSON
    return model_cls.model_validate(data)  # raises ValidationError on schema mismatch
