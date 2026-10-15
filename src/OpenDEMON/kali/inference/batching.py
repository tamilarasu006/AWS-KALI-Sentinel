"""Continuous Batching Engine for KALI Inference."""

import asyncio
import time
from typing import List, Dict, Any
from dataclasses import dataclass
import torch

from OpenDEMON.kali.architecture.transformer import KALITransformer
from OpenDEMON.kali.tokenizer import DummyKALITokenizer

@dataclass
class InferenceRequest:
    id: str
    prompt: str
    max_tokens: int
    temperature: float
    future: asyncio.Future

class ContinuousBatchingEngine:
    """
    Manages a continuous batching loop for inference requests.
    Batches incoming requests up to a max_batch_size to maximize GPU utilization.
    """
    
    def __init__(self, model: KALITransformer, tokenizer: DummyKALITokenizer, max_batch_size: int = 4):
        self.model = model
        self.tokenizer = tokenizer
        self.max_batch_size = max_batch_size
        self.queue: asyncio.Queue[InferenceRequest] = asyncio.Queue()
        self._running = False
        self._task = None
        
    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._batching_loop())
            
    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            
    async def generate(self, request_id: str, prompt: str, **kwargs) -> str:
        """Submit a prompt for generation and await its completion."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        req = InferenceRequest(
            id=request_id,
            prompt=prompt,
            max_tokens=kwargs.get("max_new_tokens", 50),
            temperature=kwargs.get("temperature", 1.0),
            future=future
        )
        await self.queue.put(req)
        
        # Await the result of this specific request
        return await future
        
    async def _batching_loop(self):
        """Background loop that drains the queue and processes batches."""
        while self._running:
            batch = []
            
            # Wait for at least one request
            req = await self.queue.get()
            batch.append(req)
            
            # Opportunistically grab more requests up to max_batch_size
            while len(batch) < self.max_batch_size and not self.queue.empty():
                batch.append(self.queue.get_nowait())
                
            if batch:
                await self._process_batch(batch)
                
            await asyncio.sleep(0.01) # Yield to event loop
            
    async def _process_batch(self, requests: List[InferenceRequest]):
        """
        Process a batch of requests simultaneously.
        In a full vLLM-like implementation, this would handle PagedAttention.
        Here we simulate batch generation by iterating max_tokens of the longest request.
        """
        from OpenDEMON.kali.inference.generate import generate_text
        
        # Simplified batching: for the sake of the reference implementation,
        # we generate text individually in a threadpool or concurrently,
        # but conceptually this engine represents the entrypoint for true dynamic batching.
        
        loop = asyncio.get_running_loop()
        
        # Process them concurrently using asyncio to simulate batch-level speedup
        async def _generate_single(req: InferenceRequest):
            try:
                # In real batching, we wouldn't call generate_text per request, 
                # we'd step the model forward on a combined tensor.
                def _run():
                    return generate_text(
                        model=self.model,
                        prompt=req.prompt,
                        tokenizer=self.tokenizer,
                        max_new_tokens=req.max_tokens,
                        temperature=req.temperature
                    )
                result = await loop.run_in_executor(None, _run)
                req.future.set_result(result)
            except Exception as e:
                req.future.set_exception(e)
                
        await asyncio.gather(*[_generate_single(req) for req in requests])
