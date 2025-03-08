# -*- coding: utf-8 -*-
# @Time : 10/17/24 11:03 AM
# @Author : Florence
# @File : test.py
# @Project : Assignment1
import os
import time
import re
import openai
import json
from baseline import nshot_chats
from evaluation import extract_ans_from_response, delete_extra_zero


def load_data(path):
    test_data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # 确保行不为空
                test_data.append(json.loads(line))
    return test_data


def test_acc(test_data, output_path):
    correct_num = 0
    total_num = len(test_data)
    total_tokens = 0
    total_time = 0

    results = []
    for item in test_data:
        que = item["question"]
        ans = item["answer"]
        ans = extract_ans_from_response(ans)
        zero_shot_prompt = nshot_chats(n=0, question=que)

        while True:
            try:

                response = client.chat.completions.create(
                    model='Meta-Llama-3.1-8B-Instruct',
                    messages=zero_shot_prompt,
                    temperature=0.8,
                    top_p=0.8
                )
                # 计算时间
                time_cost = response.usage.total_latency
                total_time += time_cost
                # 计算token
                num_tokens = response.usage.total_tokens
                total_tokens += num_tokens
                # 处理回答格式
                res_ans = response.choices[0].message.content

                res_ans = extract_ans_from_response(res_ans)
                if isinstance(res_ans, str):
                    res_ans = re.findall('-?\d+(?:\.\d+)?(?:/\d+)?', res_ans)[0]
                res_ans = delete_extra_zero(res_ans)

                # 记录正确个数
                if res_ans == ans:
                    correct_num += 1
                print("correct_ans:", ans, "output:", res_ans, "correct_num:", correct_num)
                # 记录输入、输出
                result = {
                    "input": que,
                    "prompt": zero_shot_prompt,
                    "output": res_ans
                }
                results.append(result)
                break

            except openai.RateLimitError:
                print("please wait...")
                time.sleep(10)

    # 输出总结果
    accuracy = 100 * correct_num / total_num
    average_time = total_time / total_num
    average_tokens = total_tokens / total_num

    print(f"准确率: {accuracy:.2f}%")
    print(f"平均推理时间: {average_time:.2f}秒")
    print(f"每个问题花费的平均 tokens 数量: {average_tokens:.2f}")
    # 存储输入输出
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    client = openai.OpenAI(
        api_key="b9e3bf38-cc50-4a19-a301-e8f05776c863",
        base_url="https://api.sambanova.ai/v1",
    )
    test_data_path = "data/GSM8K/test.jsonl"
    output_data_path = "data/output/t1_zero.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)

