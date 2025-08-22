import numpy as np
from transformers import GPT2Tokenizer
from transformers import GPT2ForSequenceClassification
import evaluate
from transformers import TrainingArguments, Trainer

dataset = load_dataset("mteb/tweet_sentiment_extraction")

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token
def tokenize_function(examples):
   return tokenizer(examples["text"], padding="max_length", truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)
small_train_dataset = tokenized_datasets["train"].shuffle(seed=42).select(range(1000))
small_eval_dataset = tokenized_datasets["test"].shuffle(seed=42).select(range(1000))

model = GPT2ForSequenceClassification.from_pretrained("gpt2", num_labels=3)


metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
   logits, labels = eval_pred
   predictions = np.argmax(logits, axis=-1)
   return metric.compute(predictions=predictions, references=labels)

training_args = TrainingArguments(
   output_dir="test_trainer",
   #evaluation_strategy="epoch",
   per_device_train_batch_size=1,  
   per_device_eval_batch_size=1,    
   gradient_accumulation_steps=4
   )

trainer = Trainer(
   model=model,
   args=training_args,
   train_dataset=small_train_dataset,
   eval_dataset=small_eval_dataset,
   compute_metrics=compute_metrics,

)
trainer.train()

trainer.evaluate()
trainer.save_model("outputs/gpt2-finetuned")   

tokenizer.save_pretrained("outputs/gpt2-finetuned")
from google.colab import drive
drive.mount('/content/drive')

save_dir = "/content/drive/MyDrive/Finetuning"
trainer.save_model(save_dir)
tokenizer.save_pretrained(save_dir)