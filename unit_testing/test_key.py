from openai import OpenAI

client = OpenAI(
  api_key="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"
)

response = client.responses.create(
  model="gpt-4o-mini",
  input="write a haiku about ai",
  store=True,
)

print(response.output_text)