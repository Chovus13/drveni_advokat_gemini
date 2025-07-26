import json
import argparse
import logging
from datasets import Dataset

logging.basicConfig(filename='dataset_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_dataset(feedback_path: str, output_path: str):
    """Generiše dataset za LoRA fine-tuning iz feedback loga."""
    data = []
    with open(feedback_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                feedback = json.loads(line)
                # Pretpostavimo da feedback ima 'input_text' i 'corrected_metadata' ili slično
                # Adaptiraj prema stvarnom formatu feedback-a
                if 'chunks' in feedback and 'rating' in feedback and feedback['rating'] == 'negative':
                    for chunk in feedback['chunks']:
                        data.append({
                            "instruction": "Extract metadata from this legal text chunk.",
                            "input": chunk,
                            "output": feedback.get('corrected_metadata', '')  # Pretpostavka
                        })
            except json.JSONDecodeError:
                logging.warning("Invalid JSON line skipped.")

    if not data:
        logging.info("No data for dataset generation.")
        return

    dataset = Dataset.from_list(data)
    dataset.save_to_disk(output_path)
    logging.info(f"Dataset saved to {output_path} with {len(data)} examples.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate LoRA dataset from feedback.")
    parser.add_argument("feedback_path", type=str, help="Path to feedback_log.jsonl")
    parser.add_argument("output_path", type=str, help="Output path for dataset")
    args = parser.parse_args()
    generate_dataset(args.feedback_path, args.output_path)
