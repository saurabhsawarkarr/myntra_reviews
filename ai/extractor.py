import json
from groq import Groq
from pathlib import Path
from utils.env_loader import get_env
from utils.logger import get_logger

logger = get_logger("extractor")

def load_prompt(filename: str) -> str:
    return (Path("ai/prompts") / filename).read_text(encoding="utf-8")

def extract_signals(record: dict, client: Groq, model: str) -> dict:
    system_prompt = load_prompt("system_prompt.txt")
    user_prompt = load_prompt("extraction_prompt.txt").replace("{text}", record.get("text", ""))
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=512   # increased to handle richer schema
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if model wraps JSON in them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error for {record.get('id')}: {e}")
        return {"is_relevant": False, "error": "json_parse_error"}
    except Exception as e:
        logger.warning(f"API error for {record.get('id')}: {e}")
        return {"is_relevant": False, "error": str(e)}
