# scripts/validate_summary_semantic.py
import json, sys
from sentence_transformers import SentenceTransformer
import numpy as np
from rapidfuzz import fuzz
import nltk
nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize

# configurable thresholds
EMBED_SIM_THRESHOLD = 0.72   # start here, tune 0.65-0.78
FUZZY_THRESHOLD = 65        # fallback

model = SentenceTransformer('all-MiniLM-L6-v2')  # small, CPU-friendly

def load_paper(path):
    return json.load(open(path, 'r', encoding='utf-8'))

def gather_evidence(paper):
    ev = []
    # include title, methods, results, summary (but not summary as evidence), abstract, conclusion if present
    EKS = ['title', 'methods', 'results', 'limitations', 'tasks', 'datasets']
    # methods and results are lists of dicts with snippet fields in paper['evidence']
    # aggregate all evidence snippets available in paper['evidence']
    evidence = paper.get('evidence', {})
    for k, items in evidence.items():
        for it in items:
            snippet = it.get('snippet')
            if snippet:
                ev.append({'text': snippet, 'page': it.get('page'), 'section': k})
    # also add full text pages if available in _meta.pages_text (optional)
    # include a small context window (if pages included)
    # If your pipeline saved parsed pages: include them here by checking paper.get('_meta','').get('pages',[])
    pages = paper.get('_meta', {}).get('pages', [])
    for p in pages:
        txt = p.get('clean_text') or p.get('raw_text')
        if txt:
            # split into sentences and add short ones
            sents = sent_tokenize(txt)
            for s in sents:
                if len(s.split()) <= 200:
                    ev.append({'text': s, 'page': p.get('page_no')})
    return ev

def embed_texts(texts):
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

def cosine_sim(a,b):
    return float(np.dot(a,b))

def validate(paper_path):
    paper = load_paper(paper_path)
    summary = paper.get('summary','').strip()
    if not summary:
        print("No summary present.")
        return
    sentences = [s.strip() for s in sent_tokenize(summary) if s.strip()]
    evidence = gather_evidence(paper)
    if not evidence:
        print("No evidence snippets found.")
        return
    ev_texts = [e['text'] for e in evidence]
    # compute embeddings
    sent_embs = embed_texts(sentences)
    ev_embs = embed_texts(ev_texts)
    matches = []
    for i, s in enumerate(sentences):
        sim_scores = (ev_embs @ sent_embs[i]).tolist()  # cosine because we normalized
        max_idx = int(np.argmax(sim_scores))
        best_sim = sim_scores[max_idx]
        # fallback fuzzy matching
        fuzzy_best = 0
        for j, et in enumerate(ev_texts):
            fuzzy = fuzz.partial_ratio(s.lower(), et.lower())
            if fuzzy > fuzzy_best:
                fuzzy_best = fuzzy
        matched = best_sim >= EMBED_SIM_THRESHOLD or fuzzy_best >= FUZZY_THRESHOLD
        matches.append({
            'sentence': s,
            'matched': bool(matched),
            'best_sim': best_sim,
            'fuzzy_best': fuzzy_best,
            'best_evidence': evidence[max_idx] if matched else (evidence[max_idx] if len(evidence)>0 else None)
        })
    # compute alignment score = fraction of sentences matched
    matched_count = sum(1 for m in matches if m['matched'])
    alignment_score = matched_count / len(matches) if matches else 0.0
    print("Alignment score:", alignment_score)
    # print per-sentence diagnosis
    for m in matches:
        print("----")
        print("SENT:", m['sentence'][:200])
        print("MATCHED:", m['matched'], " best_sim:", round(m['best_sim'],3), " fuzzy:", m['fuzzy_best'])
        if m['best_evidence']:
            print("BEST EVIDENCE (p{}):".format(m['best_evidence'].get('page')), m['best_evidence']['text'][:200])
    return alignment_score, matches

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_summary_semantic.py path/to/paper.json")
        sys.exit(1)
    validate(sys.argv[1])
