import os
import json
import logging
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model
from datasets import load_from_disk
import config

logging.basicConfig(filename='finetuning_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def count_feedback_entries(feedback_path: str) -> int:
    count = 0
    with open(feedback_path, 'r', encoding='utf-8') as f:
        for _ in f:
            count += 1
    return count

def finetune_model(dataset_path: str, output_dir: str, base_model: str = "Nerys/BERTic-zero-shot"):
    if not os.path.exists(dataset_path):
        logging.warning(f"Dataset not found at {dataset_path}")
        return

    dataset = load_from_disk(dataset_path)
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForSequenceClassification.from_pretrained(base_model, num_labels=len(config.METADATA_CATEGORIES))

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["query", "value"],
        lora_dropout=0.05,
        bias="none"
    )
    model = get_peft_model(model, lora_config)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        learning_rate=2e-4,
        fp16=True if config.DEFAULT_DEVICE == 'cuda' else False,
        save_steps=500,
        logging_steps=100
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        tokenizer=tokenizer
    )

    trainer.train()
    model.save_pretrained(output_dir)
    logging.info(f"Model fine-tuned and saved to {output_dir}")

if __name__ == '__main__':
    feedback_count = count_feedback_entries(config.FEEDBACK_LOG_PATH)
    if feedback_count >= 10:  # Automatsko pokretanje posle N feedback-a, npr. 10
        os.system("python generate_lora_dataset.py {} data/lora_dataset".format(config.FEEDBACK_LOG_PATH))
        finetune_model("data/lora_dataset", "models/drveni_advokat_lora")
    else:
        logging.info(f"Insufficient feedback entries ({feedback_count}). Need at least 10.")
