import os
import time
import re
import openai
import json

from evaluation import extract_ans_from_response, delete_extra_zero

gsm8k_nshots = [
('Q: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?',
 'A: There are 15 trees originally. Then there were 21 trees after the Grove workers planted some more. Now 15 + 21 = 36. Since there were 6 workers in the grove, so the grove workers planted 36 / 6 = 6 trees today. The answer is 6. #### 6'),

('Q: If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?',
 'A: There are originally 3 cars. Then 2 more cars arrive. Now 3 * 2 = 6 cars come. So 6 - 1 = 5 cars are in the parking lot. The answer is 5. #### 5'),

('Q: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?',
 'A: Originally, Leah had 32 chocolates and her sister had 42. So her sister had 42 - 32 = 10 chocolates more than Leah has. After eating 35, since 10 + 35 = 45, they had 45 - 6 = 39 pieces left in total. The answer is 39. #### 39'),

('Q: Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?',
 'A: Jason had 20 lollipops originally. Then he had 12 after giving some to Denny. Now 20 + 12 = 32. Jason has 4 times what Denny has, so he gave Denny 32 / 4 = 8 lollipops. The answer is 8. #### 8'),

('Q: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?',
 'A: Shawn started with 5 toys. He then got 2 toys each from his mom and dad. Now 5 - 2 = 3. So he has 3 * 3 = 9 toys now for Christmas. The answer is 9. #### 9'),

('Q: There were nine computers in the server room. Five more computers were installed each day, from Monday to Thursday. How many computers are now in the server room?',
 'A: There were originally 9 computers. For each day from Monday to Thursday, 5 more computers were installed. Now 9 * 5 = 45 computers. Since 4 * 4 = 16, now 45 - 16 = 29 computers are now in the server room. The answer is 29. #### 29'),

('Q: Michael had 58 golf balls. On Tuesday, he lost 23 golf balls. On Wednesday, he lost 2 more. How many golf balls did he have at the end of Wednesday?',
 'A: Michael started with 58 golf balls. He lost 23 on Tuesday, and lost 2 more on Wednesday. So compared with Wednesday, he lost 23 - 2 = 21 more balls on Tuesday. So he had 58 - 21 = 37 golf balls at the end of Wednesday. The answer is 37. #### 37'),

('Q: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?',
 'A: Olivia had 23 dollars. She bought 5 bagels for 3 dollars each. So she spent 5 * 3 = 15 dollars. Now 23 - 15 = 8 dollars left. The answer is 8. #### 8')
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
        n_shot_prompt = nshot_chats( question=que)

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
                print("correct_ans:", ans, "output:", res_ans, "correct_num:", correct_num)
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
        api_key="b60711d4-3d78-4080-8bdf-b8825d106f77",
        base_url="https://api.sambanova.ai/v1",
    )
    test_data_path = "/Users/florence/Desktop/hku/nlp/COMP7607-2024-master/Assignment1/data/GSM8K/test.jsonl"
    output_data_path = "output/invalid.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)
