# 🚀 Quick Start: Token Streaming

## Try It Out in 3 Steps

### Step 1: Start the Streamlit App
```powershell
& .\venv\Scripts\Activate.ps1
streamlit run app.py
```

### Step 2: Configure Settings
- Select **"Intelligent Document Querying Mode (RAG)"**
- Choose your preferred AI model
- Adjust Temperature and Top-p if desired

### Step 3: Ask a Question
Type any question in the chat box, for example:
- "What is retrieval-augmented generation?"
- "How does RAG improve responses?"
- "Explain the caching mechanism"

**Watch the response stream in real-time!** ✨

---

## 🧪 Quick Tests

### Test 1: Simple Token Streaming
```bash
python test_stream_tokens.py
```
Shows raw token streaming with metrics.

### Test 2: Full RAG Streaming Pipeline
```bash
python test_streaming.py
```
Tests complete RAG system with caching, memory, and optimization stats.

---

## 📊 What You'll See

**Before**: Full response appears after 10-30 seconds (waiting for model)

**After with streaming**:
- ⏱️ First token: 2-5 seconds (model inference)
- 📝 Next tokens: Every 50-200ms (smooth character-by-character display)
- 📈 Final stats: Display after streaming completes

---

## 🎯 Key Features

✅ Real-time response generation
✅ Character-by-character display
✅ Works with all optimization features:
  - Cache checking (instant if found)
  - Memory retrieval
  - Vector search
  - Response caching
✅ Smooth, responsive UI

---

## 📚 Learn More

- `STREAMING_FEATURE.md` - Complete feature guide
- `STREAMING_IMPLEMENTATION.md` - Technical details
- `test_streaming.py` - See working example
- `test_stream_tokens.py` - See token-level details

---

## 🔧 Adjust Settings

### Change streaming chunk size (granularity)
Edit `bedrock_app/chat.py::invoke_model_stream()`:
- Current: 10 characters per chunk
- Decrease for smoother (more frequent updates)
- Increase for fewer UI updates

### Disable streaming for a specific model
Pass `character_stream=False` to `invoke_model_stream()`

---

## 💡 Tips

1. **For better performance**: Use Claude 3+ models (finest streaming granularity)
2. **For fastest responses**: Reduce chunk size to 5 characters
3. **For production**: Monitor response quality with streaming enabled
4. **Cache behavior**: Cached responses show full answer instantly (not streamed)

---

Ready? Start with: `streamlit run app.py` 🚀
