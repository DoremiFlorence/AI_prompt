import os
import time
import re
import openai
import json
from evaluation import extract_ans_from_response, delete_extra_zero
import random

gsm8k_nshots = [
    (
        "Angelo and Melanie want to plan how many hours over the next week they should study together for their test next week. They have 2 chapters of their textbook to study and 4 worksheets to memorize. They figure out that they should dedicate 3 hours to each chapter of their textbook and 1.5 hours for each worksheet. If they plan to study no more than 4 hours each day, how many days should they plan to study total over the next week if they take a 10-minute break every hour, include 3 10-minute snack breaks each day, and 30 minutes for lunch each day?",
        "Angelo and Melanie think they should dedicate 3 hours to each of the 2 chapters, 3 hours x 2 chapters = 6 hours total. For the worksheets they plan to dedicate 1.5 hours for each worksheet, 1.5 hours x 4 worksheets = 6 hours total. Angelo and Melanie need to start with planning 12 hours to study, at 4 hours a day, 12 / 4 = 3 days. However, they need to include time for breaks and lunch. Every hour they want to include a 10-minute break, so 12 total hours x 10 minutes = 120 extra minutes for breaks. They also want to include 3 10-minute snack breaks, 3 x 10 minutes = 30 minutes. And they want to include 30 minutes for lunch each day, so 120 minutes for breaks + 30 minutes for snack breaks + 30 minutes for lunch = 180 minutes, or 180 / 60 minutes per hour = 3 extra hours. So Angelo and Melanie want to plan 12 hours to study + 3 hours of breaks = 15 hours total. They want to study no more than 4 hours each day, 15 hours / 4 hours each day = 3.75 They will need to plan to study 4 days to allow for all the time they need. The answer is 4. #### 4"),
    (
        "Mark's basketball team scores 25 2 pointers, 8 3 pointers and 10 free throws.  Their opponents score double the 2 pointers but half the 3 pointers and free throws.  What's the total number of points scored by both teams added together?",
        " Mark's team scores 25 2 pointers, meaning they scored 25*2= 50 points in 2 pointers. His team also scores 6 3 pointers, meaning they scored 8*3= 24 points in 3 pointers They scored 10 free throws, and free throws count as one point so they scored 10*1=10 points in free throws. All together his team scored 50+24+10= 84 points Mark's opponents scored double his team's number of 2 pointers, meaning they scored 50*2=100 points in 2 pointers. His opponents scored half his team's number of 3 pointers, meaning they scored 24/2= 12 points in 3 pointers. They also scored half Mark's team's points in free throws, meaning they scored 10/2=5 points in free throws. All together Mark's opponents scored 100+12+5=117 points. The total score for the game is both team's scores added together, so it is 84+117=201 points The answer is 201. ####201"),
    (
        "Bella has two times as many marbles as frisbees. She also has 20 more frisbees than deck cards. If she buys 2/5 times more of each item, what would be the total number of the items she will have if she currently has 60 marbles? ",
        "When Bella buys 2/5 times more marbles, she'll have increased the number of marbles by 2/560 = 24. The total number of marbles she'll have is 60+24 = 84. If Bella currently has 60 marbles, and she has two times as many marbles as frisbees, she has 60/2 = 30 frisbees. If Bella buys 2/5 times more frisbees, she'll have 2/530 = 12 more frisbees. The total number of frisbees she'll have will increase to 30+12 = 42. Bella also has 20 more frisbees than deck cards, meaning she has 30-20 = 10 deck cards. If she buys 2/5 times more deck cards, she'll have 2/5*10 = 4 more deck cards. The total number of deck cards she'll have is 10+4 = 14. Together, Bella will have a total of 14+42+84 = 140 items. The answer is 140. #### 140"),
    (
        "A group of 4 fruit baskets contains 9 apples, 15 oranges, and 14 bananas in the first three baskets and 2 less of each fruit in the fourth basket. How many fruits are there? ",
        "For the first three baskets, the number of apples and oranges in one basket is 9+15=24. In total, together with bananas, the number of fruits in one basket is 24+14=38 for the first three baskets. Since there are three baskets each having 38 fruits, there are 3*38=114 fruits in the first three baskets. The number of apples in the fourth basket is 9-2=7. There are also 15-2=13 oranges in the fourth basket. The combined number of oranges and apples in the fourth basket is 13+7=20. The fourth basket also contains 14-2=12 bananas. In total, the fourth basket has 20+12=32 fruits. The four baskets together have 32+114=146 fruits. The answer is 146. #### 146"),
    (
        "You can buy 4 apples or 1 watermelon for the same price. You bought 36 fruits evenly split between oranges, apples and watermelons, and the price of 1 orange is $0.50. How much does 1 apple cost if your total bill was $66? ",
        "If 36 fruits were evenly split between 3 types of fruits, then I bought 36/3 = 12 units of each fruit. If 1 orange costs $0.50 then 12 oranges will cost $0.50 * 12 = $6. If my total bill was $66 and I spent $6 on oranges then I spent $66 - $6 = $60 on the other 2 fruit types. Assuming the price of watermelon is W, and knowing that you can buy 4 apples for the same price and that the price of one apple is A, then 1W=4A. If we know we bought 12 watermelons and 12 apples for $60, then we know that $60 = 12W + 12A. Knowing that 1W=4A, then we can convert the above to $60 = 12(4A) + 12A. $60 = 48A + 12A. $60 = 60A. Then we know the price of one apple (A) is $60/60= $1. The answer is 1. ####1"),
    (
        "Susy goes to a large school with 800 students, while Sarah goes to a smaller school with only 300 students. At the start of the school year, Susy had 100 social media followers. She gained 40 new followers in the first week of the school year, half that in the second week, and half of that in the third week. Sarah only had 50 social media followers at the start of the year, but she gained 90 new followers the first week, a third of that in the second week, and a third of that in the third week. After three weeks, how many social media followers did the girl with the most total followers have?",
        "Let's think step by step. After one week, Susy has 100+40 = 140 followers. In the second week, Susy gains 40/2 = 20 new followers. In the third week, Susy gains 20/2 = 10 new followers. In total, Susy finishes the three weeks with 140+20+10 = 170 total followers. After one week, Sarah has 50+90 = 140 followers. After the second week, Sarah gains 90/3 = 30 followers. After the third week, Sarah gains 30/3 = 10 followers. So, Sarah finishes the three weeks with 140+30+10 = 180 total followers. Thus, Sarah is the girl with the most total followers with a total of 180. The answer is 180. #### 180"),
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
    output_data_path = "output/complexity.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)
