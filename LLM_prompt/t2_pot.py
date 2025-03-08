# -*- coding: utf-8 -*-
# @Time : 10/21/24 10:16 AM
# @Author : Florence
# @File : t2.py
# @Project : Assignment1

import openai
import sympy as sp
import time
from evaluation import extract_ans_from_response, delete_extra_zero
import re
import json

# 初始化
gsm8k_nshots = [
    (
        'A robe takes 2 bolts of blue fiber and half that much white fiber. How many bolts in total does it take?',
        'bolts_of_blue_fiber = 2\nbolts_of_white_fiber = num_of_blue_fiber / 2\nans = bolts_of_blue_fiber + bolts_of_white_fiber'
    ),
    (
        'Janet’s ducks lay 15 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four.She sells the remainder at the farmers market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers market?',
        'total_eggs = 15\neaten_eggs = 3\nbaked_eggs = 4\nsold_eggs = total_eggs - eaten_eggs - baked_eggs\ndollars_per_egg = 2\nans = sold_eggs * dollars_per_egg'
    ),
    (
        'Josh decides to try flipping a house. He buys a house for $80,000 and then puts in $50,000 in repairs. This increased the value of the house by 150%. How much profit did he make?',
        'cost_of_original_house = 80000\nincrease_rate = 150 / 100\nvalue_of_house = (1 + increase_rate) * cost_of_original_house\ncost_of_repair = 50000\nans = value_of_house - cost_of_repair - cost_of_original_house'
    ),
    (
        'When Freda cooks canned tomatoes into sauce, they lose half their volume. Each 16 ounce can of tomatoes that she uses contains three tomatoes. Freda’s last batch of tomato sauce made 32 ounces of sauce. How many tomatoes did Freda use?',
        'lose_rate = 0.5\nnum_tomato_contained_in_per_ounce_sauce = 3 / 16\nounce_sauce_in_last_batch = 32\nnum_tomato_in_last_batch = ounce_sauce_in_last_batch * num_tomato_contained_in_per_ounce_sauce\nans = num_tomato_in_last_batch / (1 - lose_rate)'
    )
]
client = openai.OpenAI(
    api_key="b9e3bf38-cc50-4a19-a301-e8f05776c863",
    base_url="https://api.sambanova.ai/v1",
)


# 加载测试集
def load_data(path):
    test_data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # 确保行不为空
                test_data.append(json.loads(line))
    # test_data = test_data[0:100]
    return test_data


def nshot_prompt(question: str) -> dict:
    def question_prompt(s):
        return f'Question: {s}'

    def answer_prompt(s):
        return f"\n{s}"

    chats = [
        {"role": "system",
         "content": "Your task is to solve a series of math word problems by providing the python program."
                    "Important: you don't need to generate other content except python code."
                    "Use variable 'ans' to store the final answer. "}
    ]

    for q, a in gsm8k_nshots:
        chats.append(
            {"role": "user", "content": question_prompt(q)})
        chats.append(
            {"role": "assistant", "content": answer_prompt(a)})

    chats.append({"role": "user", "content": question_prompt(question)})
    return chats


# 生成程序，并执行
def generate_program_of_thoughts(question):
    prompt = nshot_prompt(question)  # 生成python程序需要的提示词
    client = openai.OpenAI(
        api_key="b60711d4-3d78-4080-8bdf-b8825d106f77",
        base_url="https://api.sambanova.ai/v1",
    )
    num_tokens = 0
    time_cost = 0
    for i in range(5):  # 尝试5次，生成正确代码
        # execute the model to generate an answer
        response = client.chat.completions.create(
            model='Meta-Llama-3.1-8B-Instruct',
            messages=prompt,
            temperature=0.8,
            top_p=0.1
        )  # assume this is where you get the response from the model
        program = response.choices[0].message.content
        time_cost = response.usage.total_latency
        num_tokens = response.usage.total_tokens
        exec_globals = {}
        try:
            exec(program, exec_globals)
        except SyntaxError as e:  # 出错处理
            print(f"SyntaxError: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        if 'ans' in exec_globals:  # 检查是否有'ans'变量
            return exec_globals['ans'], prompt, num_tokens, time_cost

        # if 'ans' is not present, re-execute the program
        print("Model response does not include 'ans', re-executing...")

    return 0, prompt, num_tokens, time_cost  # 未能成功输出正确的代码


def test_acc(test_data):
    correct_num = 0
    total_num = len(test_data)
    total_time = 0
    total_tokens = 0
    # results = []
    with open(output_data_path, 'w', encoding='utf-8') as f:
        for item in test_data:
            que = item["question"]
            ans = item["answer"]
            ans = extract_ans_from_response(ans)

            while True:
                try:

                    result_ans, prompt, n_token, time_cost = generate_program_of_thoughts(que)

                    total_time += time_cost
                    total_tokens += n_token
                    # 记录正确个数
                    if result_ans == ans:
                        correct_num += 1
                    print("correct_ans:", ans, "output:", result_ans, "correct_num:", correct_num)
                    # 记录输入、输出
                    # 尝试将 result_ans 转换为 float
                    try:
                        output_value = float(result_ans)
                    except (ValueError, TypeError):
                        output_value = str(result_ans)  # 转换为字符串
                    result = {
                        "input": que,
                        "prompt": prompt,
                        "output": output_value
                    }

                    # 将结果写入文件
                    json.dump(result, f, ensure_ascii=False, indent=4)
                    break

                except openai.RateLimitError:
                    print("please wait...")
                    time.sleep(5)

        # 输出总结果
        accuracy = 100 * correct_num / total_num
        average_time = total_time / total_num
        average_tokens = total_tokens / total_num

        print(f"准确率: {accuracy:.2f}%")
        print(f"平均推理时间: {average_time:.2f}秒")
        print(f"每个问题花费的平均 tokens 数量: {average_tokens:.2f}")


if __name__ == "__main__":
    test_data_path = "data/GSM8K/test.jsonl"
    output_data_path = "data/output/t2_pot.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data)
