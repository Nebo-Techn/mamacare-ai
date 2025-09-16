from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

model_name = "phi-2"  # Change to your base model (e.g., "gemma", "llama", etc.)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Apply LoRA
lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # Adjust for your model
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# Freeze base model parameters (optional, PEFT does this by default)
for name, param in model.named_parameters():
    if "lora_" not in name:
        param.requires_grad = False

# Load your dataset
dataset = load_dataset("json", data_files={"train": "maternal_qa_train.jsonl"})

def preprocess(example):
    prompt = f"Swali: {example['question']}\nJibu:"
    input_ids = tokenizer(prompt, truncation=True, max_length=512)
    label_ids = tokenizer(example['answer'], truncation=True, max_length=512)
    input_ids["labels"] = label_ids["input_ids"]
    return input_ids

tokenized = dataset["train"].map(preprocess, batched=False)

training_args = TrainingArguments(
    output_dir="./lora_results",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=500,
    logging_steps=100,
    evaluation_strategy="no",
    save_total_limit=2,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
)

trainer.train()
model.save_pretrained("./lora_maternal_model")
tokenizer.save_pretrained("./lora_maternal_model")