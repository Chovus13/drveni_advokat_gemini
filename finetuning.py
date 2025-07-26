import os
import json
import logging
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, Trainer, TrainingArguments
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
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)

    def preprocess_function(examples):
        inputs = [f"Extract and correct metadata: {inp}" for inp in examples["input"]]
        targets = examples["output"]
        model_inputs = tokenizer(inputs, max_length=512, truncation=True)
        labels = tokenizer(targets, max_length=512, truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q", "v"],
        lora_dropout=0.05,
        bias="none"
    )
    model = get_peft_model(model, lora_config)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        learning_rate=2e-4,
        fp16=True if config.DEFAULT_DEVICE == 'cuda' else False,
        save_steps=500,
        logging_steps=100,
        evaluation_strategy="steps",
        eval_steps=500,
        load_best_model_at_end=True
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["test"],
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
