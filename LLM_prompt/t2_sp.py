# -*- coding: utf-8 -*-
# @Time : 10/21/24 3:52 PM
# @Author : Florence
# @File : t2_sp.py
# @Project : Assignment1

import openai
import sympy as sp
import time
from evaluation import extract_ans_from_response, delete_extra_zero
import re
import json

# 初始化
# 优化问题的示例
sp_que = [
    (
        'Original Question: Monica is a teacher. She has 6 classes per day. The first class has 20 students. The second and third classes have 25 students. Her fourth class has half as many as her first class. Her fifth and sixth classes have 28 students. How many students does Monica see each day?',
        'New Question: Monica is a teacher with 6 classes per day. Her first class has 20 students, her second and third classes have 25 students, and her fourth class has 10 students. Her fifth and sixth classes have 28 students. How many students does Monica see each day in all of her classes?'
    ),
    (
        'Original Question: Emily went to the store and bought art supplies for $20 and 2 skirts that cost the same amount of money. She spent a total of $50. How much did Emily pay for each of the skirts?',
        'New Question: Emily went to the store and bought art supplies for $20 and 2 skirts for a total of $50. How much did Emily pay for each of the skirts?'
    ),
    (
        'Original Question: John’s neighbor tells him to walk his dog for 1 hour each day for a total of $10. He does this for April, save for the 4 Sundays in April. He later spent $50 on books and gave his sister Kaylee the same amount. How much money did John have left?',
        'New Question: John’s neighbor tells him to walk his dog for April (30 days excluding 4 Sundays) for a total of $10 each day. He later spent $50 on books and gave his sister Kaylee the same amount. How much money did John have left after these expenses?'
    ),
    (
        'Original Question: Three years ago, Bethany was twice the age of her younger sister. In 5 years, her younger sister will be 16. How old is Bethany now?',
        'New Question: Three years ago, Bethany was twice the age of her younger sister, who is currently 11 years old. How old is Bethany now?'
    ),
    (
        'Original Question: At the bookstore, Sarah bought 6 paperback books and 4 hardback books. Her brother bought one-third as many paperback books as Sarah bought, and two times the number of hardback books that she bought. How many books did her brother buy in total?',
        'New Question: At the bookstore, Sarah bought 6 paperback books and 4 hardback books. Her brother bought 2 paperback books and 8 hardback books. How many books did her brother buy in total?'
    ),
    (
        'Original Question: Sandra had 2 different bags of candy. Each of her bags had 6 pieces of candy left. Her brother, Roger, also had 2 bags of candy. One of his bags of candy had 11 pieces left and the other had 3 pieces left. How much more candy did Roger have?',
        'New Question: Sandra had 2 bags of candy, each with 6 pieces left. Her brother, Roger, had 2 bags of candy, one with 11 pieces left and the other with 3 pieces left. How many more pieces of candy did Roger have than Sandra?'
    ),
    (
        'Original Question: Joan wants to visit her family who live 480 miles away. If she drives at a rate of 60 mph and takes a lunch break taking 30 minutes, and 2 bathroom breaks taking 15 minutes each, how many hours did it take her to get there?',
        'New Question: Joan wants to visit her family who live 480 miles away. If she drives at a rate of 60 mph and takes a lunch break of 30 minutes, and 2 bathroom breaks of 15 minutes each, how many hours(60 minutes = 1 hour) does it take her to get there?'
    )
]
# 解决问题的示例
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
    )
]

client = openai.OpenAI(
    api_key="b60711d4-3d78-4080-8bdf-b8825d106f77",
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
    return test_data


def nshot_prompt(flag: str, question: str) -> dict:
    def question_prompt(s):
        return f'{s}'

    def answer_prompt(s):
        return f"\n{s}"

    if flag == "refine":
        chats = [
            {"role": "system",
             "content": "Please rewrite new versions of the original mathematical question (including the context and the final question) "
                        "to be more understandable and easy to answer. Don’t omit any useful information, especially the numbers."
             }
        ]
        for q, a in sp_que:
            chats.append(
                {"role": "user", "content": question_prompt(q)})
            chats.append(
                {"role": "assistant", "content": answer_prompt(a)})
    else:
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


# 优化prompt。输入数学问题，输出优化后的问题
def refine_problem(problem):
    """
    提炼和优化问题
    """
    time_cost = 0
    num_tokens = 0
    refine_prompt = nshot_prompt("refine", problem)
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model='Meta-Llama-3.1-8B-Instruct',
                messages=refine_prompt,
                temperature=0.1,
                top_p=0.1,
                timeout=30  # 将超时时间设置为 30 秒
            )
            # 处理回答格式
            response_ans = response.choices[0].message.content
            time_cost = response.usage.total_latency
            num_tokens = response.usage.total_tokens
            return response_ans, time_cost, num_tokens
        except openai.APITimeoutError:
            if attempt < 2:
                print("请求超时，正在重试...")
                time.sleep(5)  # 等待 5 秒后重试
            else:
                return problem, time_cost, num_tokens


def solve_problem(problem):
    """
    解决问题
    """
    time_cost = 0
    num_tokens = 0
    solve_prompt = nshot_prompt("solve", problem)
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model='Meta-Llama-3.1-8B-Instruct',
                messages=solve_prompt,
                temperature=0.1,
                top_p=0.1,
                timeout=30  # 将超时时间设置为 30 秒
            )
            answer = response.choices[0].message.content
            time_cost = response.usage.total_latency
            num_tokens = response.usage.total_tokens
            return answer, time_cost, num_tokens
        except openai.APITimeoutError:
            if attempt < 2:
                print("请求超时，正在重试...")
                time.sleep(5)  # 等待 5 秒后重试
            else:
                return 0, time_cost, num_tokens


def self_polish(initial_problem, max_iterations=3):
    refined_problem = initial_problem
    answers = []
    num_tokens = 0
    num_ask = 0
    time_cost = 0
    for i in range(max_iterations):

        # 解决问题
        response, time_used, n_tokens = solve_problem(refined_problem)  # 第一轮用原问题提问
        num_tokens += n_tokens
        num_ask += 1
        time_cost += time_used
        answer = extract_ans_from_response(response)
        if isinstance(answer, str):
            matches = re.findall('-?\d+(?:\.\d+)?(?:/\d+)?', answer)
            if matches:  # 确保匹配结果不为空
                answer = matches[0]
            else:
                answer = "0"

        answer = delete_extra_zero(answer)
        answers.append(answer)

        # 检查是否收敛
        if len(answers) > 1 and answers[-1] == answers[-2]:
            break

        # 若未收敛，且不是最后一轮，则继续提炼问题
        if i < (max_iterations - 1):
            refined_problem, time_used, n_tokens = refine_problem(refined_problem)
            num_tokens += n_tokens
            time_cost += time_used
    return answers[-1], refined_problem, num_tokens,time_cost, num_ask


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

        while True:
            try:

                res_ans, sp_problem, n_tokens,time_cost, model_access_count = self_polish(que)
                # 计算时间
                total_time += time_cost
                # 计算token
                total_tokens += n_tokens
                # 记录正确个数
                if res_ans == ans:
                    correct_num += 1
                print("correct_answer:", ans, "output_answer:", res_ans, "correct_num:", correct_num)
                # 记录输入、输出
                result = {
                    "input": que,
                    "solve-problem's prompt": sp_problem,
                    "output": res_ans,
                    "solve_model_access_count": model_access_count,
                    "cost_time": time_cost,
                    "num_tokens": n_tokens
                }
                results.append(result)

                break

            except openai.RateLimitError:
                print("please wait...")
                time.sleep(20)

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
    test_data_path = "data/GSM8K/test.jsonl"
    output_data_path = "data/output/t2_sp.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)
