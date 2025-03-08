import os
import time
import re
import openai
import json
from evaluation import extract_ans_from_response, delete_extra_zero
import random

gsm8k_nshots = [

    (
        "What is fifteen more than a quarter of 48?",
        "A quarter of 48 is 48/4=12. The number is 12+15=27. The answer is 27. #### 27"),
    (
        "Twice Angie's age, plus 4, is 20. How old is Angie?",
        "Twice Angie's age is 20-4=16. Angie is 16/2=8. The answer is 8. #### 8"),
    (
        "Steve is 5'6\". He grows 6 inches. How tall is he in inches?",
        "He is 5*12+6=66 inches tall before the growth spurt. After growing he is now 66+6=72 inches. The answer is 72. #### 72"),
    (
        "If 12 bags of oranges weigh 24 pounds, how much do 8 bags weigh?",
        "Each bag of oranges weighs 24 pounds / 12 = 2 pounds. 8 bags of oranges would weigh 8 * 2 pounds = 16 pounds. The answer is 16. #### 16"),
    (
        "A roll of 25 m wire weighs 5 kg. How much does a 75 m roll weigh?",
        "We know that the 75 m roll is three times bigger than the 25 m roll because 75 m / 25 m = 3. This means the 75 m roll weighs 3 times more than the 25 m roll: 5 kg * 3 = 15 Kg. The answer is 15. #### 15"),
    (
        "Fifteen more than a quarter of a number is 27. What is the number?",
        "A quarter of the number is 27-15=12. The number is 12*4=48. The answer is 48. #### 48"),
    (
        "198 passengers fit into 9 buses. How many passengers fit in 5 buses?",
        "198 passengers / 9 buses = 22 passengers fit in one bus. 22 passengers/bus * 5 buses = 110 passengers fit in 5 buses. The answer is 110. #### 110"),
    (
        "John takes a pill every 6 hours. How many pills does he take a week?",
        "He takes 24/6=4 pills a day. So he takes 4*7=28 pills a week. The answer is 28. #### 28")
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
    output_data_path = "output/short.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)
