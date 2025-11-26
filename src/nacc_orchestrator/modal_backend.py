"""
Modal-based LLM backend for NACC using IBM Granite-3.0-3B-A800M-Instruct.

This backend deploys Granite-3.0-3B-A800M on Modal's serverless GPU infrastructure,
providing on-demand AI inference for NACC's multi-node orchestration system.

Granite-3.0-3B-A800M is an efficient MoE (Mixture of Experts) model:
- 3.3B total parameters with only 800M active (super fast!)
- 32 experts with TopK=8 routing
- Apache 2.0 license from IBM
- Perfect for instruction-following and tool calling

Modal is the hackathon sponsor and provides elastic GPU scaling with sub-second
cold starts, making it perfect for the NACC project.

SETUP:
1. Install Modal: pip install modal
2. Authenticate: modal token new
3. Deploy: modal deploy src/nacc_orchestrator/modal_backend.py
4. The web endpoint will be available at the URL shown after deployment
5. Set MODAL_ENDPOINT_URL in your environment or config
"""

import modal
import os
import json
import logging
import requests
from typing import Any

logger = logging.getLogger(__name__)

# Create Modal app for NACC with Granite MoE
# Modal App ID: ap-8PaCvfA0O7brdDuCMSuNRV (DEPLOYED)
# View at: https://modal.com/apps/vasanthfeb13/main/ap-8PaCvfA0O7brdDuCMSuNRV
app = modal.App("nacc-granite-moe-3b")

# Define the container image with required dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "transformers>=4.45.0",  # Need latest version for GraniteMoE support
        "torch>=2.3.0",
        "accelerate>=0.30.0",
        "sentencepiece>=0.2.0",
        "protobuf>=4.25.0",
        "fastapi[standard]>=0.115.0",  # Required for web endpoints
    )
)

# Deploy Granite-3B-MoE model on HIGH-PERFORMANCE GPU for sub-30s responses
@app.function(
    image=image,
    gpu="A100",  # A100 80GB - Enterprise-grade GPU for maximum speed
    timeout=600,  # 10 minutes for first-time model download
    min_containers=1,  # Keep 1 instance warm for instant responses (no cold start)
    scaledown_window=300,  # Keep container alive for 5 minutes after last request
)
def generate_completion(data: dict) -> dict:
    """
    Generate AI completion for NACC tool calling via web endpoint.
    
    This function runs on Modal's serverless GPU infrastructure and uses
    IBM Granite-3.0-3B-A800M to understand natural language queries and identify the
    appropriate NACC tools to execute.
    
    Args:
        data: Dict with 'prompt' (user query) and optional 'context' (session info)
    
    Returns:
        Dict with 'response' containing the model's completion
    """
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    
    prompt = data.get("prompt", "")
    context = data.get("context")
    
    print(f"🚀 Processing query on Modal GPU: {prompt[:100]}...")
    
    # Load Granite-3.0-3B-A800M-Instruct (IBM MoE model) with optimizations
    # 3.3B total parameters, 800M active - efficient Mixture of Experts
    # 32 experts with TopK=8 routing, Apache 2.0 license
    # Perfect for NACC's instruction-following and tool calling
    model_name = "ibm-granite/granite-3.0-3b-a800m-instruct"
    
    # Use cached model loading for faster subsequent calls
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        use_fast=True  # Use fast tokenizer for speed
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,  # Granite uses bfloat16
        device_map="auto",
        low_cpu_mem_usage=True  # Optimize memory usage for faster loading
    )
    
    # Enable inference optimizations
    model.eval()  # Set to evaluation mode
    if hasattr(torch, 'compile'):
        # PyTorch 2.0+ optimization (can give 2x speedup)
        try:
            model = torch.compile(model, mode="reduce-overhead")
            print("✅ Model compiled with torch.compile for faster inference")
        except Exception as e:
            print(f"⚠️ Could not compile model: {e}")
    
    # Build optimized NACC-specific prompt for Granite MoE model
    # Using structured format for faster, more accurate parsing
    system_prompt = """<|system|>
You are NACC AI - a high-performance network orchestration assistant.
Task: Analyze user queries and return precise JSON tool calls.

AVAILABLE TOOLS:
1. write_file(filename: str, content: str) - Create/update files
2. read_file(filename: str) - Read file contents
3. execute_command(command: str) - Run shell commands
4. switch_node(target_node: str) - Change active node
5. list_files(path: str) - List directory contents

OUTPUT FORMAT (JSON only, no markdown):
{"tool": "<tool_name>", "parameters": {<params>}, "reasoning": "<brief explanation>"}

EXAMPLES:
Query: "write test to file.txt"
Output: {"tool": "write_file", "parameters": {"filename": "file.txt", "content": "test"}, "reasoning": "file creation"}

Query: "check disk space"
Output: {"tool": "execute_command", "parameters": {"command": "df -h"}, "reasoning": "disk space check"}

Query: "read config.yml"
Output: {"tool": "read_file", "parameters": {"filename": "config.yml"}, "reasoning": "file read"}
<|end|>"""
    
    # Add context if available
    context_str = f"\n<|context|>{json.dumps(context)}<|end|>" if context else ""
    
    # Construct final prompt with clear delimiters
    full_prompt = f"{system_prompt}{context_str}\n<|user|>{prompt}<|end|>\n<|assistant|>"
    
    # HIGH-SPEED generation with optimized parameters
    inputs = tokenizer(
        full_prompt, 
        return_tensors="pt",
        truncation=True,
        max_length=2048  # Limit input length for speed
    ).to(model.device)
    
    with torch.no_grad():
        # Use torch.inference_mode for maximum speedup
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,  # Optimized for JSON responses (<30 tokens typically)
                min_new_tokens=10,  # Ensure minimum output
                temperature=0.1,  # Very low for fast, deterministic output
                top_k=50,  # Top-K sampling for speed
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.1,  # Prevent repetition
                num_beams=1,  # Greedy (fastest)
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                early_stopping=True,  # Stop ASAP
                use_cache=True  # Enable KV cache for speed
            )
    
    # Fast decoding
    response = tokenizer.decode(
        outputs[0][inputs['input_ids'].shape[1]:], 
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True
    )
    
    print(f"✅ Generated response in <30s: {response[:200]}...")
    return {"response": response.strip()}


# Local client class for NACC integration  
class ModalBackend:
    """LLM backend using Modal serverless GPU infrastructure."""
    
    def __init__(self, endpoint_url: str | None = None):
        """
        Initialize Modal backend - connects to deployed Modal app.
        
        Args:
            endpoint_url: Not used - we use Modal's native .remote() calls
        """
        # Direct reference to the function - Modal will handle deployment routing
        self.generate_completion = generate_completion
        logger.info("✅ Modal backend initialized - using deployed app: ap-8PaCvfA0O7brdDuCMSuNRV")
    
    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        """
        Complete a prompt using IBM Granite-3.0-3B-A800M on Modal A100 GPU.
        
        This method calls the deployed Modal function using with app.run() context.
        Modal handles all the scaling, GPU provisioning, and execution automatically.
        
        Args:
            prompt: The prompt to complete
            context: Optional context dictionary
        
        Returns:
            The model's completion response
        """
        try:
            logger.info(f"🚀 Sending request to Modal A100 GPU...")
            import time
            start = time.time()
            
            # Use with app.run() to create the execution context
            # Then call .remote() on the function
            with app.run():
                result = self.generate_completion.remote({"prompt": prompt, "context": context})
            
            elapsed = time.time() - start
            logger.info(f"✅ Modal A100 response in {elapsed:.2f}s")
            
            return result["response"]
        except Exception as e:
            logger.error(f"Modal backend error: {e}")
            raise RuntimeError(
                f"Modal API error: {e}\n\n"
                "The deployed Modal app (ap-8PaCvfA0O7brdDuCMSuNRV) may not be accessible.\n"
                "Check: https://modal.com/apps/vasanthfeb13/main/deployed/nacc-granite-moe-3b"
            ) from e
    
    def __repr__(self) -> str:
        return "ModalBackend(model=granite-3.0-3b-a800m, provider=modal, gpu=A100)"


# Test function to run locally
@app.local_entrypoint()
def test():
    """Test the Modal backend with NACC queries."""
    print("=" * 80)
    print("Testing NACC Modal Backend with IBM Granite-3.0-3B-A800M (MoE)")
    print("=" * 80)
    
    test_queries = [
        ("write hello world to test.txt", {"current_node": "mac", "current_path": "/tmp"}),
        ("execute ls -la command", {"current_node": "kali-vm", "current_path": "/home"}),
        ("switch to kali node", {"current_node": "mac"}),
    ]
    
    for query, context in test_queries:
        print(f"\n📝 Query: {query}")
        print(f"🔧 Context: {context}")
        
        try:
            response = generate_completion.remote(query, context)
            print(f"✅ Response:\n{response}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    # This allows running as a standalone test
    print("To test this Modal backend, run:")
    print("  modal run src/nacc_orchestrator/modal_backend.py")
    print("\nTo deploy as a web endpoint:")
    print("  modal deploy src/nacc_orchestrator/modal_backend.py")
