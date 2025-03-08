# -*- coding: utf-8 -*-
# @Time : 11/30/24 7:45 PM
# @Author : Florence
# @File : simple.py
# @Project : assign2
import os
import time
import re
import openai
import json
from evaluation import extract_ans_from_response, delete_extra_zero
import random

gsm8k_nshots = [
    (
        "Ivan has a bird feeder in his yard that holds two cups of birdseed. Every week, he has to refill the emptied feeder. Each cup of birdseed can feed fourteen birds, but Ivan is constantly chasing away a hungry squirrel that steals half a cup of birdseed from the feeder every week. How many birds does Ivan’s bird feeder feed weekly? ",
        "The squirrel steals 1/2 cup of birdseed every week, so the birds eat 2 - 1/2 = 1 1/2 cups of birdseed. Each cup feeds 14 birds, so Ivan’s bird feeder feeds 14 * 1 1/2 = 21 birds weekly. The answer is 21. #### 21"),
    (
        "Samuel took 30 minutes to finish his homework while Sarah took 1.3 hours to finish it. How many minutes faster did Samuel finish his homework than Sarah?",
        "Since there are 60 minutes in 1 hour, then 1.3 hours is equal to 1.3 x 60 = 78 minutes. Thus, Samuel is 78 – 30 = 48 minutes faster than Sarah. The answer is 48. #### 48"),
    (
        "Julia bought 3 packs of red balls, 10 packs of yellow balls, and 8 packs of green balls. There were 19 balls in each package. How many balls did Julia buy in all? ",
        "The total number of packages is 3 + 10 + 8 = 21. Julia bought 21 × 19 = 399 balls. The answer is 399. #### 399"),
    (
        "Lexi wants to run a total of three and one-fourth miles. One lap on a particular outdoor track measures a quarter of a mile around. How many complete laps must she run?",
        "There are 3/ 1/4 = 12 one-fourth miles in 3 miles. So, Lexi will have to run 12 (from 3 miles) + 1 (from 1/4 mile) = 13 complete laps. The answer is 13 #### 13"),
    (
        "Asia bought a homecoming dress on sale for $140. It was originally priced at $350. What percentage off did she get at the sale?",
        "Asia saved $350 - $140 = $210 on the dress. That means she saved $210 / $350 = 0.60 or 60% off on the dress. The answer is 60 ####60"),
    (
        "As a special treat, Georgia makes muffins and brings them to her students on the first day of every month.  Her muffin recipe only makes 6 muffins and she has 24 students.  How many batches of muffins does Georgia make in 9 months?",
        "She has 24 students and her muffin recipe only makes 6 muffins so she needs to bake 24/6 = 4 batches of muffins. She brings muffins on the 1st of the month for 9 months and it takes 4 batches to feed all of her students so she bakes 9*4 = 36 batches of muffins. The answer is 36 #### 36"),
    (
        "Jorge bought 24 tickets for $7 each. For purchasing so many, he is given a discount of 50%. How much, in dollars, did he spend on tickets?",
        "Jorge spent 24 tickets * $7 per ticket = $168 total. After applying the discount, Jorge spent $168 * 0.50 = $84. The answer is 84. #### 84"),
    (
        "OpenAI runs a robotics competition that limits the weight of each robot. Each robot can be no more than twice the minimum weight and no less than 5 pounds heavier than the standard robot. The standard robot weighs 100 pounds. What is the maximum weight of a robot in the competition?",
        "the minimum is 5 more than 100 so 100+5=105. the maximum weight of a robot is twice the minimum 105*2=210. The answer is 210. #### 210")
]


def nshot_chats(question: str) -> dict:
    def question_prompt(s):
        return f'Question: {s}'

    def answer_prompt(s):
        return f"Answer:\nLet's think step by step.\n{s}"

    chats = [
        {"role": "system",
         "content": "Your task is to solve a series of math word problems by providing the final answer. "
                    "Important: Use the format #### [value] to highlight your answer. For example, if the final answer is 560, "
                    "you should write #### 560."}
    ]

    for q, a in gsm8k_nshots:
        chats.append(
            {"role": "user", "content": question_prompt(q)})
        chats.append(
            {"role": "assistant", "content": answer_prompt(a)})

    chats.append({"role": "user", "content": question_prompt(question)})

    return chats


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
    results = []
    total_time = 0
    total_tokens = 0
    for item in test_data:
        que = item["question"]
        ans = item["answer"]
        ans = extract_ans_from_response(ans)
        n_shot_prompt = nshot_chats(question=que)

        while True:
            try:
                response = client.chat.completions.create(
                    model='Meta-Llama-3.1-8B-Instruct',
                    messages=n_shot_prompt,
                    temperature=0.7,
                    top_p=0.7
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
                print("correct_answer:", ans, "output:", res_ans, "correct_num:", correct_num)
                # 记录输入、输出
                result = {
                    "input": que,
                    "prompt": n_shot_prompt,
                    "output": res_ans
                }
                results.append(result)
                break

            except openai.RateLimitError:
                print("please wait...")
                time.sleep(20)
            except openai.APIConnectionError:
                print("Connection error, retrying in 10 seconds...")
                time.sleep(10)  # Wait before retrying
            except Exception as e:
                print(f"An error occurred: {e}. Retrying in 5 seconds...")
                time.sleep(5)  # Wait before retrying

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
    test_data_path = "/Users/florence/Desktop/hku/nlp/COMP7607-2024-master/Assignment1/data/GSM8K/test.jsonl"
    output_data_path = "output/simple.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)
