import json
import os
import re
import argparse
from time import sleep
from types import SimpleNamespace

from tqdm import tqdm
from openai import OpenAI


args = argparse.ArgumentParser()
args.add_argument('--result_path', type=str, default='results/misinformation_detection', help='Path to the result files')
args.add_argument('--output_path', type=str, default='scores/misinformation_detection', help='Path to the output files')
args.add_argument('--setting_path', type=str, default='eval_scripts/settings.json', help='Path to the setting file')
args.add_argument('--api_retry', type=int, default=3, help='Retry times for extraction API failures')
args = args.parse_args()

settings = SimpleNamespace(**json.load(open(args.setting_path, 'r')))
os.makedirs(args.output_path, exist_ok=True)

def remove_think_tags(text):
    # 使用正则表达式匹配<think>到</think>之间的内容，并将其替换为空字符串
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

def class_projection(category: str):
    if category in ["pants-fire", "false"]:
        return "false"
    elif category in ["barely-true", "half-true"]:
        return "half"
    elif category in ["mostly-true", "true"]:
        return "true"
    else:
        return "error"


def try_rule_extract(raw_text: str) -> str:
    text = remove_think_tags(raw_text).lower()
    # Prefer longer labels first to avoid substring conflicts.
    ordered_labels = ["pants-fire", "mostly-true", "barely-true", "half-true", "false", "true"]
    for label in ordered_labels:
        if re.search(rf"\b{re.escape(label)}\b", text):
            return label
    return "error"

en_prompt = '''
    Please read the provided text carefully and extract the final verdict indicating whether the given tweet contains any misinformation. The result must be one of the following: "pants-fire", "false", "barely-true", "half-true", "mostly-true", or "true". Do not provide any explanations or additional content.
    You must explicitly extract and output the final verdict from the text.
    Output format requirements:
    - If the verdict is pants-fire, output: "pants-fire".
    - If the verdict is false, output: "false".
    - If the verdict is barely-true, output: "barely-true".
    - If the verdict is half-true, output: "half-true".
    - If the verdict is mostly-true, output: "mostly-true".
    - If the verdict is true, output: "true".
    - If the verdict is indeterminate or unclear, output: "error".
    You should always reponse to the user in English.
    Note: Strictly follow the above output rules.
    Example input:
    -"Based on the retrieved documents, the statement \"Building a wall on the U.S.-Mexico border will take literally years\" is accurate. Multiple sources indicate that constructing a border wall is a lengthy process, often taking several years due to logistical, financial, and political challenges. For instance, Document 1 mentions it could take more than three years, while Document 3 highlights experts' skepticism about completing it quickly. \n\nTherefore, the statement is **mostly-true**."
    Example output:
    - "mostly-true"
'''
client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
        )

    
for file_path in tqdm(os.listdir(args.result_path)):
    print(file_path)
    json_path = os.path.join(args.result_path, file_path)
    raw_data = json.load(open(json_path))

    output_file = os.path.join(args.output_path, file_path)

    if os.path.exists(output_file):
        results = json.load(open(output_file))
    else:
        results = {}
        
    for json_name, samples in tqdm(raw_data.items()):
        if json_name in results:
            continue
        if samples in ["pants-fire", "false", "barely-true", "half-true", "mostly-true", "true", "error"]:
            results[json_name] = class_projection(samples)
            continue
        rule_answer = try_rule_extract(samples)
        if rule_answer != "error":
            results[json_name] = class_projection(rule_answer)
            continue
        
        query = f"the provided text is “{samples}”"
        success = False
        for _ in range(args.api_retry):
            try:
                chat_response = client.chat.completions.create(
                            model=settings.model,
                            messages=[
                                {"role": "system", "content": en_prompt},
                                {"role": "user", "content": query},
                            ],
                        )
                response = chat_response.choices[0].message.content
                print(f"{samples}\n{response}\n")
                answer = remove_think_tags(response).strip().strip('"').lower()
                if answer in ["pants-fire", "false", "barely-true", "half-true", "mostly-true", "true", "error"]:
                    results[json_name] = class_projection(answer)
                    success = True
                    break
            except Exception as e:
                print(f"API extraction failed for {json_name}: {e}")
                sleep(2)
        if not success:
            results[json_name] = "error"
        
    # Persist one output file per model after finishing all samples.
    with open(output_file, "w", encoding="utf8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)