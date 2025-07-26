import json
import argparse
import logging
from datasets import Dataset

logging.basicConfig(filename='dataset_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_dataset(feedback_path: str, output_path: str, balance_ratio=0.5, min_samples=10):
    """Generiše kvalitetan dataset za LoRA fine-tuning iz feedback loga."""
    metadata_pairs = []
    chunking_pairs = []
    seen = set()  # Za filtriranje duplikata

    with open(feedback_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                feedback = json.loads(line)
                if feedback.get('rating') == 'Bad':
                    original_text = ' '.join(feedback['chunks'])  # Kombinuj chunks u jedan tekst
                    corrected = feedback.get('corrected', '')

                    # Kreiraj par za metadata (pretpostavljamo da corrected sadrži ispravljene metadata ili chunks)
                    if 'metadata' in corrected.lower():
                        pair = {"input": original_text, "output": corrected}
                        pair_hash = hash(pair['input'] + pair['output'])
                        if pair_hash not in seen:
                            metadata_pairs.append(pair)
                            seen.add(pair_hash)

                    # Kreiraj par za chunking
                    else:
                        pair = {"input": original_text, "output": corrected}
                        pair_hash = hash(pair['input'] + pair['output'])
                        if pair_hash not in seen:
                            chunking_pairs.append(pair)
                            seen.add(pair_hash)
            except json.JSONDecodeError:
                logging.warning("Invalid JSON line skipped.")

    total_samples = len(metadata_pairs) + len(chunking_pairs)
    if total_samples < min_samples:
        logging.info(f"Insufficient data ({total_samples} samples). Minimum {min_samples} required.")
        return

    # Balansiraj dataset
    target_per_class = min(len(metadata_pairs), len(chunking_pairs))
    metadata_pairs = metadata_pairs[:target_per_class]
    chunking_pairs = chunking_pairs[:target_per_class]

    data = metadata_pairs + chunking_pairs

    dataset = Dataset.from_list(data)
    dataset = dataset.train_test_split(test_size=0.2)  # Za cross-validation

    dataset.save_to_disk(output_path)
    logging.info(f"Dataset saved to {output_path} with {len(data)} examples (balanced 50/50).")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate LoRA dataset from feedback.")
    parser.add_argument("feedback_path", type=str, help="Path to feedback_log.jsonl")
    parser.add_argument("output_path", type=str, help="Output path for dataset")
    args = parser.parse_args()
    generate_dataset(args.feedback_path, args.output_path)
