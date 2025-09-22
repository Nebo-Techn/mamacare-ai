import json

def convert_txt_to_jsonl(txt_path, jsonl_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    dataset = []
    question, answer = None, None
    for line in lines:
        line = line.strip()
        if line.startswith("Q:"):
            question = line[2:].strip()
        elif line.startswith("A:"):
            answer = line[2:].strip()
            if question and answer:
                dataset.append({"question": question, "answer": answer})
                question, answer = None, None

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    convert_txt_to_jsonl("fine-tune-dataset-maternal-mother-v0.txt", "maternal_qa_train.jsonl")