# active_learning/sampler.py
"""
Active learning sampler utilities.

Provides:
 - least_confidence_sampling
 - margin_sampling
 - entropy_sampling

Input:
 - items: list of dicts, each must include 'item_id' and optional 'probs' or 'score'
 - probs: either provided per item (list of floats summing to 1) or computed externally

Output:
 - ordered list of item_ids by decreasing sampling priority
"""
from typing import List, Dict, Tuple
import math
import numpy as np

def _entropy(probs: List[float]) -> float:
    e = 0.0
    for p in probs:
        if p > 0:
            e -= p * math.log(p + 1e-12)
    return e

def least_confidence_score(probs: List[float]) -> float:
    # 1 - max_prob (higher = more uncertain)
    if not probs:
        return 1.0
    return 1.0 - max(probs)

def margin_score(probs: List[float]) -> float:
    # difference between top two probs; smaller margin = more uncertain -> we return 1 - margin
    if not probs or len(probs) == 1:
        return 1.0
    sorted_probs = sorted(probs, reverse=True)
    margin = sorted_probs[0] - sorted_probs[1]
    return 1.0 - margin

def entropy_score(probs: List[float]) -> float:
    return _entropy(probs)

def rank_items_by_uncertainty(items: List[Dict], method: str = "least_confidence") -> List[Tuple[str, float]]:
    """
    items: list of dicts, each with:
        - item_id: unique id
        - probs: optional list of probabilities [p1,p2,...] (if not present, item must have 'score' already)
    method: 'least_confidence', 'margin', 'entropy'
    returns list of (item_id, score) sorted by descending score (most uncertain first)
    """
    if method not in {"least_confidence", "margin", "entropy"}:
        raise ValueError("method must be one of least_confidence, margin, entropy")
    scored = []
    for it in items:
        item_id = it.get("item_id")
        probs = it.get("probs")
        if probs is None:
            # if the item has a precomputed 'score', use inverted value to treat larger as more uncertain
            sc = float(it.get("score", 0.0))
        else:
            if method == "least_confidence":
                sc = least_confidence_score(probs)
            elif method == "margin":
                sc = margin_score(probs)
            else:
                sc = entropy_score(probs)
        scored.append((item_id, float(sc)))
    # sort by score desc
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

# convenience to pick top-k
def select_top_k(items: List[Dict], k: int = 10, method: str = "least_confidence") -> List[Dict]:
    ranked = rank_items_by_uncertainty(items, method=method)
    topk = [r[0] for r in ranked[:k]]
    lookup = {it["item_id"]: it for it in items}
    return [lookup[i] for i in topk if i in lookup]
