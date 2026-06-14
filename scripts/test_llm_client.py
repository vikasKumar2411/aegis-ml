from app.services.llm_client import LLMClient


def main() -> None:
    client = LLMClient()

    result = client.generate_json(
        system_prompt="You are a JSON-only ML incident reasoning assistant.",
        user_prompt="""
Create a root cause hypothesis for this alert.

Alert:
- model_id: email_identification_model
- metric: secure_email_recall
- baseline_value: 0.91
- current_value: 0.78

Evidence:
- secure_email_recall dropped significantly
- false negatives show new secure email phrasing
- feature drift detected in secure_phrase_count
- no schema drift detected
- no data-quality issue detected
- no correlated deployment found

Return JSON with:
{
  "root_cause": string,
  "confidence": number,
  "summary": string,
  "alternative_causes": [
    {
      "cause": string,
      "confidence": number,
      "reason": string
    }
  ]
}
""",
        fallback={
            "root_cause": "fallback_root_cause",
            "confidence": 0.0,
            "summary": "Fallback was used.",
            "alternative_causes": [],
        },
    )

    print(result)


if __name__ == "__main__":
    main()
