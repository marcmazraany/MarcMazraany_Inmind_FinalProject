import sys, re
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

def clean(s: str) -> str:
    if not s: return ""
    s = re.sub(r"\[[^\]]*\]", " ", s) 
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    
    path = Path("unit_testing/rag_tests/rag_logs.txt")
    thr = 0.70

    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    lines = [ln for ln in lines if ln]

    model = SentenceTransformer("BAAI/bge-small-en-v1.5")  

    pairs = [(clean(lines[i]), clean(lines[i+1])) for i in range(0, len(lines), 2)]
    sims = []
    for idx, (rag, mine) in enumerate(pairs, 1):
        emb = model.encode([rag, mine], normalize_embeddings=True)
        sim = float(util.cos_sim(emb[0], emb[1]))
        sims.append(sim)
        mark = "✓" if sim >= thr else "✗"
        print(f"[{mark}] {sim:.4f}  #{idx}")

    if sims:
        avg = sum(sims) / len(sims)
        acc = sum(1 for s in sims if s >= thr) / len(sims)
        print(f"Pairs: {len(sims)}")
        print(f"Avg cosine: {avg:.4f}")
        print(f"Accuracy : {thr:.2f}: {acc*100:.1f}%")

if __name__ == "__main__":
    main()
