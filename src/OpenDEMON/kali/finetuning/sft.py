import json
import torch
import os
from .config import KALISFTConfig
from OpenDEMON.kali.architecture.transformer import KALITransformer
from OpenDEMON.kali.model.config import KALIModelConfig
from OpenDEMON.kali.tokenizer.tokenizer import DummyKALITokenizer
from .chat_template import KALIChatTemplate
from .dataset import SFTDataset
from torch.utils.data import DataLoader

class SFTTrainer:
    def __init__(self, config: KALISFTConfig, output_dir: str):
        self.config = config
        self.output_dir = output_dir
        self.tokenizer = DummyKALITokenizer()
        self.chat_template = KALIChatTemplate(self.tokenizer)
        
        # instantiate model
        self.model_config = KALIModelConfig(model_name="kali-mini", model_path="kali-mini-checkpoint", vocab_size=self.tokenizer.vocab_size())
        self.model = KALITransformer(self.model_config)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.config.learning_rate)

    def evaluate(self, dataloader) -> dict:
        self.model.eval()
        total_loss = 0.0
        with torch.no_grad():
            for batch in dataloader:
                logits = self.model(input_ids=batch["input_ids"])
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = batch["labels"][..., 1:].contiguous()
                loss_fct = torch.nn.CrossEntropyLoss(ignore_index=-100)
                loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                if loss is not None:
                    total_loss += loss.item()
        avg_loss = total_loss / max(1, len(dataloader))
        return {"loss": avg_loss, "perplexity": torch.exp(torch.tensor(avg_loss)).item()}
        
    def train(self, train_data, val_data):
        train_ds = SFTDataset(train_data, self.chat_template, self.config.max_sequence_length)
        val_ds = SFTDataset(val_data, self.chat_template, self.config.max_sequence_length)
        
        train_loader = DataLoader(train_ds, batch_size=self.config.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.config.batch_size)
        
        baseline_metrics = self.evaluate(val_loader)
        with open(os.path.join(self.output_dir, "baseline_results.json"), "w") as f:
            json.dump(baseline_metrics, f)
            
        self.model.train()
        step = 0
        for epoch in range(self.config.epochs):
            for batch in train_loader:
                self.optimizer.zero_grad()
                logits = self.model(input_ids=batch["input_ids"])
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = batch["labels"][..., 1:].contiguous()
                loss_fct = torch.nn.CrossEntropyLoss(ignore_index=-100)
                loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                
                if loss is not None:
                    loss.backward()
                    self.optimizer.step()
                step += 1
                
        sft_metrics = self.evaluate(val_loader)
        with open(os.path.join(self.output_dir, "sft_results.json"), "w") as f:
            json.dump(sft_metrics, f)
            
        self.save_checkpoint()
        return baseline_metrics, sft_metrics

    def save_checkpoint(self):
        os.makedirs(self.output_dir, exist_ok=True)
        torch.save(self.model.state_dict(), os.path.join(self.output_dir, "pytorch_model.bin"))
        with open(os.path.join(self.output_dir, "sft_config.json"), "w") as f:
            json.dump(self.config.__dict__, f)
        
    def generate_tests(self, prompts: list):
        self.model.eval()
        results = {}
        with torch.no_grad():
            for p in prompts:
                input_ids = torch.tensor([self.tokenizer.encode(p)]).to(next(self.model.parameters()).device)
                outputs = self.model.generate(input_ids, max_length=100)
                results[p] = self.tokenizer.decode(outputs[0].tolist())
        return results
