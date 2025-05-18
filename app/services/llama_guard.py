from transformers import AutoProcessor, Llama4ForConditionalGeneration
import torch

model_id = "meta-llama/Llama-Guard-4-12B"

processor = AutoProcessor.from_pretrained(model_id)
model = Llama4ForConditionalGeneration.from_pretrained(
    model_id,
    device_map="cuda",
    torch_dtype=torch.bfloat16
)

def is_safe_text(text: str) -> tuple[bool, list[str]]:
    """Check if the given text is safe using Llama Guard 4"""
    messages = [
        {"role": "user", "content": [{"type": "text", "text": text}]}
    ]

    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=10,
        do_sample=False
    )

    response = processor.batch_decode(outputs[:, inputs["input_ids"].shape[-1]:])[0]

    if response.startswith("safe"):
        return True, []
    elif response.startswith("unsafe"):
        categories = response.split("\n")[1].split(",")
        return False, categories
    else:
        return False, ["Unknown"]
