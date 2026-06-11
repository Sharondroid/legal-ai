import pandas as pd
import numpy as np
import faiss
import torch

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("ghana_cases_ghalii.csv")
df = df.dropna(subset=["full_text"])

texts = (df["case_name"].fillna("") + ". " + df["full_text"]).tolist()
sources = df["source"].tolist()
case_names = df["case_name"].tolist()

print(f"Loaded {len(texts)} cases")

# =========================
# EMBEDDINGS + INDEX
# =========================
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = embedding_model.encode(texts, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

print("FAISS index ready")

# =========================
# LOAD LLM (LIGHTWEIGHT)
# =========================
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    device_map="cpu"
)

model.eval()

print("Model loaded")

# =========================
# INTENT DETECTION
# =========================
def detect_mode(query):
    q = query.lower()

    if " v " in q or " vs " in q:
        return "case"

    if any(w in q for w in ["explain", "discuss", "analysis", "in detail"]):
        return "detailed"

    if any(w in q for w in ["what is", "define", "meaning"]):
        return "definition"

    return "simple"

# =========================
# RETRIEVAL
# =========================
def retrieve_cases(query, k=5):
    query_vec = embedding_model.encode([query]).astype("float32")
    distances, indices = index.search(query_vec, k)

    results = []

    for i, dist in zip(indices[0], distances[0]):
        if dist > 1.3:
            continue

        results.append({
            "case_name": case_names[i],
            "text": texts[i],
            "source": sources[i],
            "score": float(dist)
        })

    results.sort(key=lambda x: x["score"])
    return results

# =========================
# TEXT GENERATION CORE
# =========================
def generate_text(prompt):

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.3,
        top_p=0.9,
        do_sample=True
    )

    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

    if "ANSWER:" in full_output:
        return full_output.split("ANSWER:")[-1].strip()

    return full_output.strip()

# =========================
# CASE MODE
# =========================
def case_mode(cases):

    if not cases:
        return "No matching case found."

    c = cases[0]

    prompt = f"""
You are a legal assistant.

Summarize this case clearly and simply.

Focus on:
- Facts
- Issue
- Decision
- Key reasoning

CASE:
{c['text'][:1500]}

ANSWER:
"""

    return generate_text(prompt)

# =========================
# SIMPLE ANSWER (DEFAULT)
# =========================
def simple_answer(question, cases):

    context = ""
    for c in cases:
        context += f"{c['case_name']}: {c['text'][:500]}\n\n"

    prompt = f"""
You are a Ghanaian legal assistant.

Give a SHORT and DIRECT answer.

Do not be verbose.

QUESTION:
{question}

CASES:
{context}

ANSWER:
"""

    return generate_text(prompt)

# =========================
# DETAILED LEGAL ANSWER
# =========================
def detailed_answer(question, cases):

    context = ""
    for c in cases:
        context += f"{c['case_name']}: {c['text'][:1000]}\n\n"

    prompt = f"""
You are a Ghanaian legal assistant.

Answer in this format:

1. Issue
2. Rule
3. Application
4. Conclusion

QUESTION:
{question}

CASES:
{context}

ANSWER:
"""

    return generate_text(prompt)

# =========================
# DEFINITION MODE
# =========================
def definition_mode(question):

    prompt = f"""
You are a legal assistant.

Give a SIMPLE and CLEAR definition.

QUESTION:
{question}

ANSWER:
"""

    return generate_text(prompt)

# =========================
# MAIN LOOP
# =========================
print("\n⚖️ Ghana Legal AI Assistant Ready ⚖️")
print("Type 'exit' to stop")

while True:

    query = input("\nAsk a legal question: ")

    if query.lower() == "exit":
        print("Goodbye.")
        break

    mode = detect_mode(query)
    cases = retrieve_cases(query)

    print(f"\n🧠 Mode: {mode.upper()}\n")

    if mode == "case":
        answer = case_mode(cases)

    elif mode == "detailed":
        answer = detailed_answer(query, cases)

    elif mode == "definition":
        answer = definition_mode(query)

    else:
        answer = simple_answer(query, cases)

    print("="*60)
    print(answer)

    if cases:
        print("\n📌 Sources:")
        for c in cases[:3]:
            print(f"- {c['source']}")