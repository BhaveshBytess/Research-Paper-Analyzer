# scripts/repair_summary_anchor_semantic.py
import json, sys
from sentence_transformers import SentenceTransformer
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt', quiet=True)

MODEL_NAME = 'all-MiniLM-L6-v2'
EMBED_SIM_THRESHOLD = 0.72

model = SentenceTransformer(MODEL_NAME)

def gather_evidence(paper):
    ev = []
    evidence = paper.get('evidence', {})
    for k, items in evidence.items():
        for it in items:
            snippet = it.get('snippet')
            if snippet:
                ev.append({'text': snippet, 'page': it.get('page'), 'section': k})
    # optional: include pages if present in _meta
    pages = paper.get('_meta', {}).get('pages', [])
    for p in pages:
        txt = p.get('clean_text') or p.get('raw_text')
        if txt:
            for s in sent_tokenize(txt):
                ev.append({'text': s, 'page': p.get('page_no'), 'section': 'page_text'})
    return ev

def embed_texts(texts):
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

def repair(paper_path, out_path=None):
    paper = json.load(open(paper_path, 'r', encoding='utf-8'))
    summary = paper.get('summary','').strip()
    sentences = [s.strip() for s in sent_tokenize(summary) if s.strip()]
    evidence = gather_evidence(paper)
    if not evidence:
        print("No evidence found. Aborting repair.")
        return
    ev_texts = [e['text'] for e in evidence]
    sent_embs = embed_texts(sentences)
    ev_embs = embed_texts(ev_texts)
    repaired_sentences = []
    for i, s in enumerate(sentences):
        # Ignore short, non-substantive sentences
        if len(s.split()) < 3:
            continue
        sims = (ev_embs @ sent_embs[i]).tolist()
        max_idx = int(np.argmax(sims))
        best_sim = sims[max_idx]
        best_ev = evidence[max_idx]
        if best_sim >= EMBED_SIM_THRESHOLD:
            # keep sentence but append anchor
            anchor = f"{s} (see p{best_ev.get('page')}: \"{best_ev.get('text')[:80]}...\")"
            repaired_sentences.append(anchor)
        else:
            # cannot find direct evidence; replace sentence with a concise evidence-based statement using top-1 evidence
            anchor = best_ev.get('text')
            replacement = f"{anchor} (p{best_ev.get('page')})"
            repaired_sentences.append(replacement)
    new_summary = " ".join(repaired_sentences)
    paper['summary'] = new_summary
    if out_path:
        json.dump(paper, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print("Wrote repaired summary to", out_path)
    else:
        json.dump(paper, open(paper_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print("Rewrote summary in", paper_path)
    return paper

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/repair_summary_anchor_semantic.py path/to/paper.clean.json [out.json]")
        sys.exit(1)
    inpath = sys.argv[1]
    outpath = sys.argv[2] if len(sys.argv)>2 else None
    repair(inpath, outpath)
