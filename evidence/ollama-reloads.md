# Evidence: model reload thrash in v1

Source: the Ollama server log (`/opt/homebrew/var/log/ollama.log`) during the eval runs on 2026-11-18.
Counts come from `scripts/count_reloads.py`. Each line is one `starting llama-server` event, which means a model was
loaded into memory from scratch.

## Loads per 50-item eval run

| Run | Model loads | What loaded |
|---|---:|---|
| v1 baseline | **131** | qwen2.5:3b at num_ctx 2048 ×46, qwen2.5:3b at num_ctx 8192 ×45, nomic-embed-text ×40 |
| + fix ctx reload | **2** | qwen2.5:3b ×1, nomic-embed-text ×1 |
| + 1.5B router (rejected) | 4 | qwen2.5:1.5b ×3, qwen2.5:3b ×1 |

## What it looked like

The first few requests of the baseline run. Every request loads the 3B model twice, and the embedding model gets evicted
and reloaded in between:

```
20:47:18  starting llama-server  model=qwen2.5:3b         -c 2048   <- router call
20:47:22  starting llama-server  model=nomic-embed-text   -c 2048   <- retrieval
20:47:23  starting llama-server  model=qwen2.5:3b         -c 8192   <- answer call
20:47:46  starting llama-server  model=qwen2.5:3b         -c 2048   <- next request's router call
20:47:51  starting llama-server  model=nomic-embed-text   -c 2048
20:47:52  starting llama-server  model=qwen2.5:3b         -c 8192
20:48:27  starting llama-server  model=qwen2.5:3b         -c 2048
20:48:30  starting llama-server  model=qwen2.5:3b         -c 8192
```

## Why

The router and the answerer used the same model (`qwen2.5:3b`) with different `num_ctx` values (2048 and 8192). Ollama
treats a different context size as a different runner, so it unloads and reloads the model on every switch. On an 8 GB
machine, the second copy also pushes the embedding model out of memory.

The fix is one line: give both calls the same `num_ctx`, or use a different model for routing. Nothing in the
application logs shows this. It only shows up as slow LLM calls, and as these lines in the model server's log.
