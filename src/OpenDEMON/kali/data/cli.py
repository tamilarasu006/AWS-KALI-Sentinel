import argparse
import sys
import os
import json
from .pipeline import DatasetPipeline
from .splits import DatasetSplitter
from .manifest import ManifestGenerator

def main():
    parser = argparse.ArgumentParser(description="KALI Dataset Engineering CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("file")
    
    process_parser = subparsers.add_parser("process")
    process_parser.add_argument("--input", required=True)
    process_parser.add_argument("--format", default="text")
    process_parser.add_argument("--category", default="general")
    process_parser.add_argument("--output-dir", required=True)
    
    args = parser.parse_args()
    
    if args.command == "inspect":
        print(f"Inspecting {args.file}...")
        
    elif args.command == "process":
        config = {"format": args.format, "category": args.category}
        pipeline = DatasetPipeline(config)
        
        processed_data = pipeline.process_file(
            args.input, 
            args.format, 
            args.category, 
            preserve_code=(args.category=="code")
        )
        
        os.makedirs(args.output_dir, exist_ok=True)
        splitter = DatasetSplitter()
        train, val, test = splitter.split(processed_data)
        
        pipeline.stats["splits"] = {"train": len(train), "val": len(val), "test": len(test)}
        
        with open(os.path.join(args.output_dir, "train.jsonl"), "w") as f:
            for item in train: f.write(json.dumps({"text": item}) + "\n")
        with open(os.path.join(args.output_dir, "val.jsonl"), "w") as f:
            for item in val: f.write(json.dumps({"text": item}) + "\n")
        with open(os.path.join(args.output_dir, "test.jsonl"), "w") as f:
            for item in test: f.write(json.dumps({"text": item}) + "\n")
            
        ManifestGenerator.generate(
            "ds-001", "processed_dataset", "1.0", args.category, "MIT",
            pipeline.stats["output_samples"], pipeline.stats["token_count"], 3,
            "1.0", "1.0", "Passed", os.path.join(args.output_dir, "manifest.json")
        )
        pipeline.generate_report(os.path.join(args.output_dir, "dataset_quality_report.json"))
        print(f"Processed {len(processed_data)} samples successfully.")

if __name__ == "__main__":
    main()
