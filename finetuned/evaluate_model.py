import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from icecream import ic

base_model = "gpt2"
model_dir = "model"


tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForCausalLM.from_pretrained(model_dir)

device = "cuda"
model = model.to(device)
model.eval()

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token or ""
    model.config.pad_token_id = tokenizer.pad_token_id

def generate_answer(prompt: str, max_new_tokens: int = 12) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,         
            num_beams=4,            
            early_stopping=True,
            pad_token_id=tokenizer.pad_token_id,
            repetition_penalty=1.2, 
        )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    if "Answer:" in text:
        return text.split("Answer:")[-1].strip()
    return text.strip()

test_tweets = {
    "Absolutely love the new update — battery life improved!": "positive",
    "Ugh, my order arrived damaged. So frustrating.": "negative",
    "Not bad, could be better.": "neutral",
    "Wow, customer service was amazing 😍": "positive",
    "I can't believe they removed that feature. Why?!": "negative",
    "Just got tickets! Best day ever 🙌": "positive",
    "Totally ruined my weekend. Worst experience.": "negative",
    "It's fine, nothing special.": "neutral",
    "LOL that was actually hilarious 😂": "positive",
    "Battery dies in 2 hours — totally unacceptable.": "negative",
    "Thanks @support, fixed my issue quickly.": "positive",
    "Meh. The movie was okay, not great.": "neutral",
    "Best pizza in town! 🍕🔥": "positive",
    "This app keeps crashing after the update.": "negative",
    "Can't stop listening to this song 🎧": "positive",
    "Check out @Brand's new collection: https://t.co/abcd #fashion": "neutral",
    "Finally passed the exam!! Feels incredible 🥳": "positive",
    "I returned it — didn't fit at all.": "negative",
    "No words... just disappointed.": "negative",
    "On hold for 45 minutes. Not acceptable.": "negative"
}
count = 0
for tweet, sentiment in test_tweets.items():
    count += 1
    ic(count, tweet, sentiment)
    prompt = f"Tweet: {tweet}\nQuestion: What is the sentiment of this tweet? Answer only as a single word (positive, negative or neutral)\nAnswer:"
    answer = ic(generate_answer(prompt))