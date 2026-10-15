import json
import csv
from typing import Iterator, Dict, Any, List

class DataParser:
    """Parses raw files into unified string formats."""

    @staticmethod
    def parse_jsonl(file_path: str, text_key: str = "text") -> Iterator[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if text_key in data:
                            yield data[text_key]
                    except json.JSONDecodeError:
                        continue
    
    @staticmethod
    def parse_json(file_path: str, text_key: str = "text") -> Iterator[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if text_key in item:
                            yield item[text_key]
            except:
                pass

    @staticmethod
    def parse_text(file_path: str) -> Iterator[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            yield f.read()

    @staticmethod
    def parse_csv(file_path: str, text_col: str = "text") -> Iterator[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if text_col in row:
                    yield row[text_col]

    @staticmethod
    def parse_conversation(file_path: str) -> Iterator[str]:
        # conversation format: {"messages": [{"role": "user", "content": "..."}]}
        for data in DataParser._parse_json_or_jsonl_objects(file_path):
            if "messages" in data:
                messages = data["messages"]
                valid = True
                formatted_msgs = []
                for msg in messages:
                    if "role" not in msg or "content" not in msg:
                        valid = False
                        break
                    formatted_msgs.append(f"{msg['role'].upper()}\n \u2193\n{msg['content']}")
                if valid:
                    yield "\n \u2193\n".join(formatted_msgs)
    
    @staticmethod
    def parse_instruction(file_path: str) -> Iterator[str]:
        # instruction format: {"instruction": "...", "input": "...", "output": "..."}
        for data in DataParser._parse_json_or_jsonl_objects(file_path):
            if "instruction" in data and "output" in data:
                res = f"INSTRUCTION: {data['instruction']}\n"
                if "input" in data and data["input"]:
                    res += f"INPUT: {data['input']}\n"
                res += f"OUTPUT: {data['output']}"
                yield res

    @staticmethod
    def parse_tool_calling(file_path: str) -> Iterator[str]:
        for data in DataParser._parse_json_or_jsonl_objects(file_path):
            # assume list of steps or messages
            yield json.dumps(data)
            
    @staticmethod
    def _parse_json_or_jsonl_objects(file_path: str) -> Iterator[Dict[Any, Any]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        yield item
                else:
                    yield data
            except:
                f.seek(0)
                for line in f:
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except:
                            pass
