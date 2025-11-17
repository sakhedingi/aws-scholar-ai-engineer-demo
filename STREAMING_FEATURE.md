# Token-by-Token Streaming Feature

## Overview

The SDQA AI Assistant now supports **token-by-token streaming** for real-time response display. This enhancement significantly improves user experience by:

- ✨ **Real-time feedback**: Users see responses appear character-by-character as the model generates them
- ⚡ **Improved responsiveness**: No more waiting for the full response to complete
- 🎯 **Better engagement**: Streaming creates a more interactive and modern feel
- 📊 **Transparency**: Users can see tokens arriving in real-time

## How It Works

### Architecture Components

#### 1. **Streaming Helper** (`bedrock_app/chat.py::invoke_model_stream`)
- Calls Bedrock's `invoke_model_with_response_stream` API
- Parses event-based responses from different model families (Claude, Titan, Llama, Mistral)
- Supports configurable character-level streaming for smoother UI updates
- Breaks large chunks into smaller pieces (10 chars at a time for Titan models) for more responsive display

#### 2. **RAG Streaming Integration** (`bedrock_app/optimized_rag.py::answer_with_optimization_stream`)
- New method that streams RAG responses with full optimization pipeline:
  - Checks prompt cache first
  - Retrieves context from memory and vector store
  - Streams tokens from the model while maintaining optimization stats
  - Caches final response for future use
  - Stores conversation in memory
- Yields tuples of `(token, stats_dict)` for real-time updates with metadata

#### 3. **Streaming Display** (`app.py`)
- In RAG mode (Intelligent Document Querying), responses now use `response_placeholder.markdown()` with real-time updates
- Each token arrival triggers a UI update
- Optimization stats are displayed after streaming completes
- Cache hits still display the full cached response instantly

### Model-Specific Behavior

| Model Family | Streaming Granularity | Chunk Size | Notes |
|---|---|---|---|
| **Claude** | Character-by-character | 1 char | Finest granularity, very responsive |
| **Titan** | Sub-token chunks | ~10 chars | Good responsiveness, batched updates |
| **Llama/Mistral** | Sub-token chunks | ~10 chars | Similar to Titan, model-dependent |

## Usage

### Basic RAG with Streaming

```python
from bedrock_app.optimized_rag import OptimizedRAG

rag = OptimizedRAG()
rag.initialize_knowledge_base("./knowledge_base", embed_model_id)

# Stream responses token-by-token
for token, stats in rag.answer_with_optimization_stream(
    model_id="anthropic.claude-3-sonnet",
    user_question="What is RAG?",
    embed_model_id="amazon.titan-embed-v2",
    use_cache=True,
    store_memory=True
):
    print(token, end="", flush=True)  # Display each token as it arrives
    # stats contains: cache_hit, contexts_retrieved, tokens_saved, etc.
```

### Direct Model Streaming

```python
from bedrock_app.chat import invoke_model_stream

body = {
    "prompt": "Your question here",
    "max_tokens": 200
}

for chunk in invoke_model_stream("amazon.titan-tg1-large", body, character_stream=True):
    print(chunk, end="", flush=True)
```

## Configuration

### Streaming Granularity

Adjust chunk size in `bedrock_app/chat.py::invoke_model_stream()`:

```python
# For finer control: stream by character
for char in text:
    yield char

# For batched updates: stream by N-character chunks
for i in range(0, len(text), 10):  # 10 chars at a time
    yield text[i:i+10]
```

### Disabling Character-Level Streaming

To return full chunks without breaking them into smaller pieces:

```python
for chunk in invoke_model_stream(model_id, body, character_stream=False):
    # Receives full chunks from model
    print(chunk, end="", flush=True)
```

## Testing

### Test Streaming Directly

```bash
python test_stream_tokens.py
```

Shows token-by-token output from a simple question with metrics:
- Total chunks received
- Response length
- Average chunk size

### Test RAG with Streaming

```bash
python test_streaming.py
```

Tests the full RAG pipeline with streaming, including:
- Knowledge base initialization
- Cache loading
- Streaming response generation
- Memory storage
- Optimization stats

### Run the Streamlit App

```bash
streamlit run app.py
```

Then:
1. Select "Intelligent Document Querying Mode (RAG)"
2. Ask a question
3. Watch the response appear token-by-token in real-time

## Performance Characteristics

### Latency Improvements
- **First token latency**: Typically 2-5 seconds (Bedrock model inference time)
- **Subsequent tokens**: 50-200ms between updates (model-dependent)
- **Cache hits**: Instant display of full response

### Response Throughput
- Character-level streaming: ~20-50 characters per second depending on model
- Full chunk streaming: Variable (1-10 chunks per response)
- Network latency: Minimal impact due to streaming protocol

## Error Handling

The implementation gracefully handles:
- **Model unavailable**: Returns error message
- **Stream timeout**: Displays partial response received so far
- **Invalid request**: Returns descriptive error
- **Cache miss**: Falls back to fresh streaming

```python
# Errors during streaming are caught and yielded as text
for token, stats in rag.answer_with_optimization_stream(...):
    # token may contain error text if streaming fails mid-response
    print(token, end="", flush=True)
```

## Future Enhancements

1. **Streamed response validation**: Detect and handle mid-stream response cuts
2. **User interrupt handling**: Allow users to stop streaming mid-response
3. **Token counting**: Real-time token count display during streaming
4. **Streaming to file**: Save streaming responses to file as they arrive
5. **WebSocket support**: For scalable concurrent streaming sessions

## Troubleshooting

### Streaming Not Appearing

**Check**: Model supports `invoke_model_with_response_stream` API
- Claude 3+ ✅
- Titan Text ✅
- Llama 2 ✅
- Mistral ✅

**Issue**: Streamlit UI not updating fast enough
- **Solution**: Reduce chunk size in `invoke_model_stream` (decrease from 10 to 5 chars)

### Streaming Very Slow

**Issue**: Network latency or model is slow
- **Solution**: Ensure you're using latest model versions (e.g., Claude 3.5 Sonnet)

### Cache Hits Not Streaming

**Expected**: Cache hits show full response instantly (not streamed)
- This is intentional for performance. Remove `use_cache=False` to disable caching

## Example Output

```
🚀 Starting streaming response test...

Response tokens (streaming):
--------------------------------------------------
Retrieval-Augmented Generation (RAG) is a technique that combines the
 power of pre-trained large language models with external knowledge ret
rieval. It allows AI systems to fetch relevant information from a knowl
edge base or documents and use that context to provide more accurate, g
rounded, and factual responses. This approach significantly improves the
 quality of generated content by grounding it in verified information s
ources.
--------------------------------------------------

✅ Streaming test completed!
📊 Total tokens: 45
📝 Response length: 356 characters
📈 Avg chunk size: 7.9 chars/chunk
```

## References

- [AWS Bedrock Streaming Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Streamlit write_stream API](https://docs.streamlit.io/develop/api-reference/write-stream-magic/write_stream)
- [LLM Streaming Best Practices](https://llm.datasette.io/)
