import logging
from typing import List
from OpenDEMON.kali.tokenizer.bpe_tokenizer import KALIBPETokenizer
from OpenDEMON.kali.model.kali_model import KALIModel
from OpenDEMON.kali.training.data import DataPipeline
from OpenDEMON.kali.training.trainer import KALITrainer
from OpenDEMON.kali.training.eval import EvaluationEngine

logger = logging.getLogger(__name__)

class KALITrainingPipeline:
    """Orchestrates the entire KALI training lifecycle."""
    
    def __init__(self, model: KALIModel, tokenizer: KALIBPETokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.data_pipeline = DataPipeline(tokenizer, context_length=model.config.context_length)
        self.trainer = KALITrainer(model)
        self.evaluator = EvaluationEngine(model, tokenizer)

    def run_pretraining(self, raw_data: List[str], epochs: int = 1, batch_size: int = 2):
        """Executes the pretraining pipeline."""
        logger.info("Starting Pretraining Phase...")
        dataloader = self.data_pipeline.prepare_dataloader(raw_data, batch_size=batch_size, is_sft=False)
        
        for epoch in range(epochs):
            loss = self.trainer.train_epoch(dataloader, self.tokenizer.special_tokens.pad_token_id)
            logger.info(f"Pretraining Epoch {epoch+1} - Loss: {loss:.4f}")
            
            eval_metrics = self.evaluator.evaluate(dataloader)
            logger.info(f"Evaluation - Perplexity: {eval_metrics['perplexity']:.4f}")

    def run_instruction_finetuning(self, sft_data: List[str], epochs: int = 1, batch_size: int = 2):
        """Executes the Instruction Fine-Tuning phase."""
        logger.info("Starting Instruction Fine-Tuning Phase...")
        dataloader = self.data_pipeline.prepare_dataloader(sft_data, batch_size=batch_size, is_sft=True)
        
        for epoch in range(epochs):
            loss = self.trainer.train_epoch(dataloader, self.tokenizer.special_tokens.pad_token_id)
            logger.info(f"SFT Epoch {epoch+1} - Loss: {loss:.4f}")

    def run_tool_calling_finetuning(self, tool_data: List[str], epochs: int = 1, batch_size: int = 2):
        """Executes the Tool-Calling Fine-Tuning phase."""
        logger.info("Starting Tool-Calling Fine-Tuning Phase...")
        dataloader = self.data_pipeline.prepare_dataloader(tool_data, batch_size=batch_size, is_sft=True)
        
        for epoch in range(epochs):
            loss = self.trainer.train_epoch(dataloader, self.tokenizer.special_tokens.pad_token_id)
            logger.info(f"Tool-FT Epoch {epoch+1} - Loss: {loss:.4f}")
