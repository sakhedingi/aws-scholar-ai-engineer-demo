"""
Optimized RAG with CAG and Memory Integration
Combines pre-vectorization, cache-augmented generation, and memory layer
"""
import json
from typing import Dict, List, Optional
from botocore.exceptions import ClientError
from .bedrock_runtime import get_bedrock_runtime
from .vector_store_manager import VectorStoreManager
from .prompt_cache import PromptCache
from .context_memory import ContextMemoryStore
from .system_prompt import load_system_prompt

class OptimizedRAG:
    """Integrated RAG system with vectorization, caching, and memory"""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.prompt_cache = PromptCache()
        self.memory_store = ContextMemoryStore()
    
    def initialize_knowledge_base(self, folder_path: str, embed_model_id: str) -> Dict:
        """Initialize pre-vectorized knowledge base"""
        print("[*] Initializing optimized knowledge base...")
        store = self.vector_store_manager.build_from_folder(folder_path, embed_model_id)
        stats = self.vector_store_manager.get_cache_stats()
        print(f"[OK] Knowledge base ready: {stats['num_vectors']} documents cached")
        return stats
    
    def answer_with_optimization(self, model_id: str, user_question: str, 
                                 embed_model_id: str, message_history: List[Dict] = None,
                                 temperature: float = 0.7, top_p: float = 0.9,
                                 use_cache: bool = True, store_memory: bool = True,
                                 retrieve_past_contexts: bool = True) -> Dict:
        """Answer question with full optimization (RAG + CAG + Memory)"""
        stats = {
            "cache_hit": False,
            "memory_reused": False,
            "contexts_retrieved": 0,
            "tokens_saved": 0,
            "optimization_source": []
        }
        
        if use_cache:
            cached_response = self.prompt_cache.get_cached_response(user_question)
            if cached_response:
                print(f"[CACHE] Cache hit! (saved {cached_response['tokens_saved']} tokens)")
                stats["cache_hit"] = True
                stats["tokens_saved"] = cached_response['tokens_saved']
                stats["optimization_source"].append("prompt_cache")
                return {
                    "response": cached_response['response'],
                    "stats": stats,
                    "from_cache": True
                }
        
        past_contexts = []
        if retrieve_past_contexts:
            past_contexts = self.memory_store.retrieve_similar_contexts(user_question, limit=3)
            if past_contexts:
                print(f"[MEM] Found {len(past_contexts)} similar contexts from memory")
                stats["memory_reused"] = True
                stats["optimization_source"].append("context_memory")
        
        retrieved_results = self.vector_store_manager.semantic_search(
            user_question, embed_model_id, top_k=3
        )
        stats["contexts_retrieved"] = len(retrieved_results)
        print(f"[SEARCH] Retrieved {len(retrieved_results)} relevant documents")
        
        context_parts = []
        
        for past_ctx in past_contexts:
            context_parts.append(f"[Memory - Confidence: {past_ctx.confidence_score:.2%}]")
            context_parts.append(past_ctx.response)
            context_parts.append("")
        
        for filename, score, content in retrieved_results:
            context_parts.append(f"[Document: {filename}]")
            # retrieved entries are now document chunks; include full chunk
            context_parts.append(content)
            context_parts.append("")
        
        combined_context = "\n".join(context_parts)
        
        for filename, score, content in retrieved_results:
            self.prompt_cache.cache_context_chunk(
                content, 
                {"source": filename, "score": score}
            )
        
        response = self._invoke_model_with_context(
            model_id, user_question, combined_context, message_history, 
            temperature, top_p
        )
        
        if response is None:
            return {
                "response": "Error generating response",
                "stats": stats,
                "error": True
            }
        
        if use_cache:
            estimated_tokens_saved = len(combined_context.split()) // 4
            self.prompt_cache.cache_response(
                user_question, combined_context, response, model_id, 
                tokens_saved=estimated_tokens_saved
            )
            stats["tokens_saved"] = estimated_tokens_saved
            stats["optimization_source"].append("newly_cached")
        
        if store_memory:
            confidence_score = 0.85 if len(retrieved_results) > 0 else 0.5
            tags = self._extract_tags(user_question)
            
            context_id = self.memory_store.store_context(
                query=user_question,
                context=combined_context,
                response=response,
                metadata={
                    "source": "optimized_rag",
                    "retrieved_docs": len(retrieved_results),
                    "past_contexts_used": len(past_contexts)
                },
                tags=tags,
                confidence_score=confidence_score,
                model_id=model_id
            )
            print(f"[SAVED] Stored in memory (ID: {context_id})")
            stats["optimization_source"].append("memory_stored")
        
        return {
            "response": response,
            "stats": stats,
            "from_cache": False
        }
    
    def _invoke_model_with_context(self, model_id: str, user_question: str, 
                                   context: str, message_history: List[Dict] = None,
                                   temperature: float = 0.7, top_p: float = 0.9) -> Optional[str]:
        """Invoke Bedrock model with context"""
        bedrock_runtime = get_bedrock_runtime()
        
        if message_history is None:
            message_history = []
        
        try:
            if 'claude' in model_id.lower():
                system_prompt = load_system_prompt()
                if 'claude-3' in model_id.lower() or 'claude-3-5' in model_id.lower():
                    prompt_text = f"Context:\n{context}\n\nQuestion:\n{user_question}"
                    message_history.append({
                        "role": "user",
                        "content": prompt_text
                    })
                    body = json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 1000,
                        "messages": message_history,
                        "system": system_prompt,
                        "temperature": temperature
                    })
                else:
                    prompt_text = f"Context:\n{context}\n\nQuestion:\n{user_question}"
                    body = json.dumps({
                        "prompt": f"{system_prompt}\n\nHuman: {prompt_text}\n\nAssistant:",
                        "max_tokens_to_sample": 1000,
                        "temperature": temperature
                    })
            elif 'titan' in model_id.lower():
                body = json.dumps({
                    "inputText": f"Context: {context}\n\nQuestion: {user_question}",
                    "textGenerationConfig": {
                        "maxTokenCount": 1000,
                        "temperature": temperature
                    }
                })
            elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
                body = json.dumps({
                    "prompt": f"Context: {context}\n\nQuestion: {user_question}",
                    "max_tokens": 1000,
                    "temperature": temperature
                })
            else:
                print(f"Model not supported: {model_id}")
                return None
            
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=body,
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'claude' in model_id.lower():
                if 'claude-3' in model_id.lower():
                    reply = response_body['content'][0]['text']
                    message_history.append({"role": "assistant", "content": reply})
                    return reply
                else:
                    return response_body.get('completion', 'No response')
            elif 'titan' in model_id.lower():
                return response_body['results'][0]['outputText']
            elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
                return response_body.get('generation', response_body.get('outputs', [{}])[0].get('text', 'No response'))
            
            return str(response_body)
        
        except ClientError as e:
            print(f"Error invoking model: {e}")
            return None
    
    def _extract_tags(self, question: str) -> List[str]:
        """Extract tags from question for categorization"""
        tags = []
        keywords = {
            "implementation": ["how", "build", "create", "develop"],
            "explanation": ["what", "explain", "describe", "why"],
            "troubleshooting": ["error", "bug", "fix", "issue", "problem"],
            "design": ["architecture", "design", "pattern", "structure"]
        }
        
        question_lower = question.lower()
        for category, words in keywords.items():
            if any(word in question_lower for word in words):
                tags.append(category)
        
        return tags[:3]  # Limit to 3 tags
    
    def get_optimization_stats(self) -> Dict:
        """Get statistics about all optimization systems"""
        return {
            "vector_store": self.vector_store_manager.get_cache_stats(),
            "prompt_cache": self.prompt_cache.get_cache_stats(),
            "memory_store": self.memory_store.get_memory_stats()
        }
    
    def clear_all_caches(self):
        """Clear all caches and memory"""
        self.vector_store_manager.clear_cache()
        self.prompt_cache.clear_cache()
        self.memory_store.cleanup_old_contexts(days=0)
        print("[OK] All caches cleared")
    
    def answer_with_optimization_stream(self, model_id: str, user_question: str, 
                                        embed_model_id: str, message_history: List[Dict] = None,
                                        temperature: float = 0.7, top_p: float = 0.9,
                                        use_cache: bool = True, store_memory: bool = True,
                                        retrieve_past_contexts: bool = True):
        """Answer question with full optimization and stream tokens in real-time.
        
        Yields tuples of (token, stats_dict) where token is a text chunk 
        and stats_dict contains optimization metadata.
        """
        stats = {
            "cache_hit": False,
            "memory_reused": False,
            "contexts_retrieved": 0,
            "tokens_saved": 0,
            "optimization_source": [],
            "streaming": True
        }
        
        # Check cache first
        if use_cache:
            cached_response = self.prompt_cache.get_cached_response(user_question)
            if cached_response:
                print(f"[CACHE] Cache hit! (saved {cached_response['tokens_saved']} tokens)")
                stats["cache_hit"] = True
                stats["tokens_saved"] = cached_response['tokens_saved']
                stats["optimization_source"].append("prompt_cache")
                # Yield cached response token by token for consistency
                for token in cached_response['response'].split():
                    yield token + " ", stats.copy()
                return
        
        # Retrieve past contexts
        past_contexts = []
        if retrieve_past_contexts:
            past_contexts = self.memory_store.retrieve_similar_contexts(user_question, limit=3)
            if past_contexts:
                print(f"[MEM] Found {len(past_contexts)} similar contexts from memory")
                stats["memory_reused"] = True
                stats["optimization_source"].append("context_memory")
        
        # Retrieve from vector store
        retrieved_results = self.vector_store_manager.semantic_search(
            user_question, embed_model_id, top_k=3
        )
        stats["contexts_retrieved"] = len(retrieved_results)
        print(f"[SEARCH] Retrieved {len(retrieved_results)} relevant documents")
        
        # Build combined context
        context_parts = []
        for past_ctx in past_contexts:
            context_parts.append(f"[Memory - Confidence: {past_ctx.confidence_score:.2%}]")
            context_parts.append(past_ctx.response)
            context_parts.append("")
        
        for filename, score, content in retrieved_results:
            context_parts.append(f"[Document: {filename}]")
            context_parts.append(content)
            context_parts.append("")
        
        combined_context = "\n".join(context_parts)
        
        # Cache context chunks
        for filename, score, content in retrieved_results:
            self.prompt_cache.cache_context_chunk(
                content, 
                {"source": filename, "score": score}
            )
        
        # Stream response from model
        full_response = ""
        for token in self._invoke_model_with_context_stream(
            model_id, user_question, combined_context, message_history, 
            temperature, top_p
        ):
            full_response += token
            yield token, stats.copy()
        
        # Cache the response for future use
        if use_cache:
            estimated_tokens_saved = len(combined_context.split()) // 4
            self.prompt_cache.cache_response(
                user_question, combined_context, full_response, model_id, 
                tokens_saved=estimated_tokens_saved
            )
            stats["tokens_saved"] = estimated_tokens_saved
            stats["optimization_source"].append("newly_cached")
        
        # Store in memory
        if store_memory:
            confidence_score = 0.85 if len(retrieved_results) > 0 else 0.5
            tags = self._extract_tags(user_question)
            
            context_id = self.memory_store.store_context(
                query=user_question,
                context=combined_context,
                response=full_response,
                metadata={
                    "source": "optimized_rag_stream",
                    "retrieved_docs": len(retrieved_results),
                    "past_contexts_used": len(past_contexts)
                },
                tags=tags,
                confidence_score=confidence_score,
                model_id=model_id
            )
            print(f"[SAVED] Stored in memory (ID: {context_id})")
            stats["optimization_source"].append("memory_stored")
    
    def _invoke_model_with_context_stream(self, model_id: str, user_question: str, 
                                         context: str, message_history: List[Dict] = None,
                                         temperature: float = 0.7, top_p: float = 0.9):
        """Stream response tokens from Bedrock model with context.
        
        Yields:
            Text tokens from the model response
        """
        from .chat import invoke_model_stream
        
        bedrock_runtime = get_bedrock_runtime()
        system_prompt = load_system_prompt()
        
        if message_history is None:
            message_history = []
        
        try:
            if 'claude' in model_id.lower():
                if 'claude-3' in model_id.lower() or 'claude-3-5' in model_id.lower():
                    prompt_text = f"Context:\n{context}\n\nQuestion:\n{user_question}"
                    temp_messages = message_history.copy()
                    temp_messages.append({
                        "role": "user",
                        "content": prompt_text
                    })
                    body_dict = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 1000,
                        "messages": temp_messages,
                        "system": system_prompt,
                        "temperature": temperature
                    }
                else:
                    prompt_text = f"Context:\n{context}\n\nQuestion:\n{user_question}"
                    body_dict = {
                        "prompt": f"{system_prompt}\n\nHuman: {prompt_text}\n\nAssistant:",
                        "max_tokens_to_sample": 1000,
                        "temperature": temperature
                    }
            elif 'titan' in model_id.lower():
                body_dict = {
                    "inputText": f"Context: {context}\n\nQuestion: {user_question}",
                    "textGenerationConfig": {
                        "maxTokenCount": 1000,
                        "temperature": temperature
                    }
                }
            elif 'llama' in model_id.lower() or 'mistral' in model_id.lower():
                body_dict = {
                    "prompt": f"Context: {context}\n\nQuestion: {user_question}",
                    "max_tokens": 1000,
                    "temperature": temperature
                }
            else:
                print(f"Model not supported: {model_id}")
                yield "Model not supported."
                return
            
            # Use streaming invoke
            for token in invoke_model_stream(model_id, body_dict):
                yield token
        
        except Exception as e:
            print(f"Error streaming from model: {e}")
            yield f"Error: {str(e)}"

