import os
import time
import re
import openai
import json

from evaluation import extract_ans_from_response, delete_extra_zero

gsm8k_nshots = [
    (
        'There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?',
        'There are 15 trees originally. Then there were 21 trees after the Grove workers planted some more. So there must have been 21 - 15 = <<21-15=6>>6 trees that were planted.\n#### 6'
    ),
    (
        'If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?',
        'There are originally 3 cars. Then 2 more cars arrive. Now 3 + 2 = <<3+2=5>>5 cars are in the parking lot.\n#### 5'
    ),
    (
        'Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?',
        'Originally, Leah had 32 chocolates and her sister had 42. So in total they had 32 + 42 = <<32+42=74>>74. After eating 35, they had 74 - 35 = <<74-35=39>>39 pieces left in total.\n#### 39'
    ),
    (
        'Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?',
        'Jason had 20 lollipops originally. Then he had 12 after giving some to Denny. So he gave Denny 20 - 12 = <<20-12=8>>8 lollipops.\n#### 8'
    ),
    (
        'Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?',
        'Shawn started with 5 toys. He then got 2 toys each from his mom and dad. So he got 2 * 2 = <<2*2=4>>4 more toys. Now he has 5 + 4 = <<5+4=9>>9 toys.\n#### 9'
    ),
    (
        'There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?',
        'There were originally 9 computers. For each day from monday to thursday, 5 more computers were installed. So 4 * 5 = <<4*5=20>>20 computers were added. Now 9 + 20 = <<9+20=29>>29 computers are now in the server room.\n#### 29'
    ),
    (
        'Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?',
        'Michael started with 58 golf balls. He lost 23 on Tuesday, and lost 2 more on wednesday. So he had 58 - 23 = <<58-23=35>>35 at the end of Tuesday, and 35 - 2 = <<35-2=33>>33 at the end of wednesday.\n#### 33'
    ),
    (
        'Olivia has $23. She bought five bagels for $3 each. How much money does she have left?',
        'Olivia had 23 dollars. She bought 5 bagels for 3 dollars each. So she spent 5 * 3 = <<5*3=15>>15 dollars. Now she has 23 - 15 = <<23-15=8>>8 dollars left.\n#### 8'
    ),
    ("In 5 years, Heath will be 3 times as old as Jude.  If Heath is 16 years old today, how old is Jude today?",
     "In 5 years, Heath will be 16 + 5 = 21 years old. In 5 years, Jude will be 21 / 3 = 7 years old. The difference in their ages is 21 - 7 = 14 years. Today, Jude will be 16 - 14 = 2 years old. The answer is 2. #### 2"),

    (
        "Mancino is tending 3 gardens that each measure 16 feet by 5 feet. His sister, Marquita, is tilling the soil for two gardens that each measure 8 feet by 4 feet. How many square feet combined are in all their gardens?",
        "3 * (16 * 5) = 240 square feet. 2 * (8 * 4) = 64 square feet. 240 + 64 = 304 square feet. The gardens have a total of 304 square feet. The answer is 304. #### 304")
]


def nshot_chats(n: int, question: str) -> dict:
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

    for q, a in gsm8k_nshots[:n]:
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
    test_data = test_data[:100]
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
        n_shot_prompt = nshot_chats(n=0, question=que)

        while True:
            try:
                response = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=n_shot_prompt,
                    temperature=0.7,
                    top_p=0.7
                )
                # 计算时间
                # time_cost = response.usage.total_latency
                # total_time += time_cost
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
    # average_time = total_time / total_num
    average_tokens = total_tokens / total_num

    print(f"Accuracy: {accuracy:.2f}%")
    # print(f"Average Inference Time: {average_time:.2f}秒")
    print(f"Average number of token: {average_tokens:.2f}")
    # 存储输入输出
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    client = openai.OpenAI(
        api_key="sk-NV51c58fKzcyLM6tAanoETOmzzkcx4j9nuyMK5t6RvSV9qcL",
        base_url="https://api.chatanywhere.tech/v1"
    )

    test_data_path = "/Users/florence/Desktop/hku/nlp/COMP7607-2024-master/Assignment1/data/GSM8K/test.jsonl"
    output_data_path = "output/gpt.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)
