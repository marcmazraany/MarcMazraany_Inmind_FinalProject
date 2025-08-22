from fastapi import FastAPI
from pydantic import BaseModel
from a2a_seg.final_step.agent import ADK_Run  
from server import rag_tool
import torch

app = FastAPI()

class Prompt(BaseModel):
    text: str

@app.post("/full_workflow")
async def run_agent_endpoint(prompt: Prompt):
    return  await ADK_Run(prompt.text)

@app.post("/rag_tool")
def run_rag_tool_endpoint(prompt: Prompt):
    return rag_tool(prompt.text)











# @app.post("/finetuned")
# async def run_finetuned_model(prompt: Prompt):
    # model_dir = "finetuned/model"
    # tokenizer = AutoTokenizer.from_pretrained(model_dir)
    # model = AutoModelForCausalLM.from_pretrained(model_dir)
    # device = "cuda"
    # model = model.to(device)
    # model.eval()
    # if tokenizer.pad_token is None:
    #     tokenizer.pad_token = tokenizer.eos_token or ""
    #     model.config.pad_token_id = tokenizer.pad_token_id
    # inputs = tokenizer(prompt, return_tensors="pt").to(device)
    # with torch.no_grad():
    #     out = model.generate(
    #         **inputs,
    #         max_new_tokens= 5,
    #         do_sample=False,         
    #         num_beams=4,            
    #         early_stopping=True,
    #         pad_token_id=tokenizer.pad_token_id,
    #         repetition_penalty=1.2, 
    #     )
    # text = tokenizer.decode(out[0], skip_special_tokens=True)
    # if "Answer:" in text:
    #     answer =  text.split("Answer:")[-1].strip()
    # answer = text.strip()
    # return {"answer": answer}

@app.get("/health")
async def health():
    return {"ok": True}