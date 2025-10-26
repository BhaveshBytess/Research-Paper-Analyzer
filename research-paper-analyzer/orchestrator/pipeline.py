# orchestrator/pipeline.py
import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Callable
from datetime import datetime, timezone
from orchestrator.heads import HeadRunner, LLMGenerationError
from orchestrator.merge import merge_heads_to_paper

CACHE_DIR = Path(".cache")

def _hash_key(head_name: str, context_text: str) -> str:
    h = hashlib.sha256()
    h.update(head_name.encode("utf-8"))
    h.update(b"\0")
    h.update(context_text.encode("utf-8"))
    return h.hexdigest()

def _cache_path_for_key(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"

class Pipeline:
    def __init__(self, head_runner: HeadRunner = None, cache_dir: str = ".cache"):
        self.head_runner = head_runner or HeadRunner()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def _run_head_cached(self, head_name: str, call_fn: Callable[[str], Any], context: str) -> Any:
        """
        Run a head function with caching. call_fn is a synchronous function taking context and returning a Pydantic model.
        We'll run it in a thread and await the result.
        """
        key = _hash_key(head_name, context)
        cache_path = _cache_path_for_key(key)
        if cache_path.exists():
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
            # Return the raw dict; caller may parse into model or may already have Pydantic model
            return raw

        # Run call_fn in a thread to keep event loop free
        result = await asyncio.to_thread(call_fn, context)
        # result may be a Pydantic model; convert to dict for caching
        try:
            if hasattr(result, "dict"):
                payload = result.dict()
            else:
                # might be a list or dict
                payload = result
        except Exception:
            payload = result

        # Save to cache
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "_cached_at": datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        # Return the payload (not wrapped)
        return {"payload": payload}

    async def run_heads(self, contexts: Dict[str, str]) -> Dict[str, Any]:
        """
        contexts: mapping of head_name -> context_text
        head_name must match runner methods: metadata, methods, results, limitations, summary
        Returns dict head_name -> parsed object (prefer Pydantic models where possible, otherwise raw dict)
        """
        # Map head_name to runner functions
        runner = self.head_runner
        mapping = {
            "metadata": runner.run_metadata_head,
            "methods": runner.run_methods_head,
            "results": runner.run_results_head,
            "limitations": runner.run_limitations_head,
            "summary": runner.run_summary_head
        }

        tasks = {}
        for head_name, ctx in contexts.items():
            if head_name not in mapping:
                continue
            call_fn = mapping[head_name]
            # Wrap in async cached task
            tasks[head_name] = asyncio.create_task(self._run_head_cached(head_name, call_fn, ctx))

        # Await all
        results = {}
        errors = {}
        for head_name, task in tasks.items():
            try:
                res = await task
                # If cached file format used, unwrap
                if isinstance(res, dict) and "payload" in res and len(res) == 1:
                    res_obj = res["payload"]
                else:
                    # result may already be Pydantic model (if not cached path)
                    res_obj = res
                results[head_name] = res_obj
            except Exception as e:
                results[head_name] = None
                errors[head_name] = e
        if errors:
            messages = []
            for head, err in errors.items():
                messages.append(f"{head}: {err}")
            summary = "; ".join(messages)
            raise LLMGenerationError(f"Head failures detected: {summary}") from next(iter(errors.values()))
        return results

    def run(self, contexts: Dict[str, str]) -> Dict[str, Any]:
        """
        Synchronous wrapper for convenience in tests and CLI.
        """
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            head_outputs = loop.run_until_complete(self.run_heads(contexts))
        finally:
            try:
                loop.close()
            except Exception:
                pass

        # At this point head_outputs contains raw dicts (from cache) or Pydantic models (if not cached).
        # Normalize: if dict contains {"_cached_at","payload"}, unwrap to payload
        normalized = {}
        for k, v in head_outputs.items():
            if isinstance(v, dict) and "_cached_at" in v and "payload" in v:
                normalized[k] = v["payload"]
            else:
                normalized[k] = v

        # If values are plain dicts, optionally we might want to parse back into Pydantic models
        # But merge function expects either Pydantic models or dicts with appropriate shape; handle both.
        # For now, try to leave as-is if it's Pydantic, else if dict, create simple namespace-like object with attributes for access.
        head_objs = {}
        for k, v in normalized.items():
            head_objs[k] = v  # merge module handles dicts as necessary

        # The merge function (merge_heads_to_paper) expects Pydantic-like objects (attributes) for metadata, methods, etc.
        # If head_objs values are dicts (from cache), wrap minimal adapter that exposes .dict() and attributes via keys.
        class DictWrapper:
            def __init__(self, d):
                self._d = d
            def dict(self):
                return self._d
            def __getattr__(self, item):
                # return key or None
                val = self._d.get(item)
                # if the val is a list of dicts (methods or results), keep as is
                return val

        head_for_merge = {}
        for name, val in head_objs.items():
            # If it's already a Pydantic model (has dict() and attrs), keep it.
            if hasattr(val, "dict") and not isinstance(val, dict):
                head_for_merge[name] = val
            else:
                # val may be {"payload": ...} or raw dict; unpack
                if isinstance(val, dict) and "payload" in val and isinstance(val["payload"], dict):
                    raw = val["payload"]
                else:
                    raw = val if isinstance(val, dict) else {}
                head_for_merge[name] = DictWrapper(raw)

        # Merge into final paper JSON (may raise ValidationError)
        merged = merge_heads_to_paper(head_for_merge)
        return merged
