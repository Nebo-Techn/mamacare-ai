import json
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from transformers import DataCollatorForLanguageModeling, DataCollatorForSeq2Seq
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

# Load Hugging Face token from secret.json
with open("c:/Users/User/Documents/mamacare_project/Afyamama_AI/secret.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)
hf_token = secrets["HUGGING_API"]

model_name = "microsoft/phi-2"  # or another valid model
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=hf_token)

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

def preprocess(examples):
    prompt = [f"Swali: {q}\nJibu: {a}" for q, a in zip(examples["question"], examples["answer"])]
    tokenized = tokenizer(prompt, truncation=True, padding="max_length", max_length=512)
    return tokenized

tokenized = dataset["train"].map(preprocess, batched=True)

training_args = TrainingArguments(
    output_dir="./lora_results",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=500,
    logging_steps=100,
    save_total_limit=2,
)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator,
)

trainer.train()
model.save_pretrained("./lora_maternal_model")
tokenizer.save_pretrained("./lora_maternal_model")