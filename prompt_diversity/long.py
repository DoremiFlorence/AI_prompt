import os
import time
import re
import openai
import json
from evaluation import extract_ans_from_response, delete_extra_zero
import random

gsm8k_nshots = [

    (
        "Jo-Bob hopped into the hot air balloon, released the anchor rope, and pulled on the lift chain, which ignited the flame and provided the warm air that caused the balloon to rise. When the lift chain was pulled, the balloon would rise at a rate of 50 feet per minute. But when the chain was not being pulled, the balloon would slowly descend at a rate of 10 feet per minute. During his balloon ride, he pulled the chain for 15 minutes, then released the rope for 10 minutes, then pulled the chain for another 15 minutes, and finally released the chain and allowed the balloon to slowly descend back to the earth. During his balloon ride, what was the highest elevation reached by the balloon?",
        "The first 15-minute chain pull caused the balloon to rise 50*15=750 feet. Releasing the chain for 10 minutes caused the balloon to descend 10*10=100 feet. The second 15-minute chain pull caused the balloon to rise another 50*15=750 feet. Thus, at the end of the second chain pull, when the balloon was at its highest elevation, the balloon had risen to an elevation of 750-100+750=1400 feet above the earth's surface. The answer is 1400. #### 1400"),

    (
        "At the beginning of the day, Principal Kumar instructed Harold to raise the flag up the flagpole. The flagpole is 60 feet long, and when fully raised, the flag sits on the very top of the flagpole. Later that morning, Vice-principal Zizi instructed Harold to lower the flag to half-mast. So, Harold lowered the flag halfway down the pole. Later, Principal Kumar told Harold to raise the flag to the top of the pole once again, and Harold did just that. At the end of the day, Vice-principal Zizi instructed Harold to completely lower the flag, take it off of the pole, and put it away for the evening. Over the course of the day, how far, in feet, had the flag moved up and down the pole?",
        "Half of the distance up the flagpole is 60/2 = 30 feet. Thus, Harold moved the flag 60 up + 30 down + 30 up + 60 down = 180 feet. The answer is 180. #### 180"),

    (
        "Sam works at the Widget Factory, assembling Widgets. He can assemble 1 widget every 10 minutes. Jack from the loading dock can help assemble widgets when he doesn't have anything else to do. When he helps, they put together 2 complete widgets every 15 minutes. Recently the factory hired Tony to help assemble widgets. Being new to the job, he doesn't work as fast as Sam or Jack. Yesterday Sam worked for 6 hours before he had to leave work early for a dentist appointment. Jack was able to help out for 4 hours before he had to go back to the loading dock to unload a new shipment of widget materials. Tony worked the entire 8-hour shift. At the end of the day, they had completed 68 widgets. How long does it take Tony to assemble a Widget, in minutes?",
        "Sam completes a widget every 10 minutes. When Jack helps they finish 2 in 15 minutes. Sam has finished 1 widget and has begun working on another one, and Jack finishes the second one at 15 minutes. So it takes Jack 15 minutes to complete a widget. Sam worked for 6 hours yesterday, so he was able to complete 6 hours * 60 minutes per hour / 10 minutes per widget = 36 widgets. Jack worked for 4 hours, so he was able to complete 4 hours * 60 minutes per hour / 15 minutes per widget = 16 widgets. Sam, Jack, and Tony were able to complete 68 widgets together. So of those, Tony personally completed 68 widgets - 36 widgets - 16 widgets = 16 widgets. It took Tony 8 hours to complete those 16 widgets, so he takes 8 hours * 60 minutes per hour / 16 widgets = 30 minutes per widget. The answer is 30. #### 30"),

    (
        "Tina is working on her homework when she realizes she's having a hard time typing out her answers on her laptop because a lot of the keys are sticky. She is trying to get her homework done before dinner, though, so she needs to decide if she has time to clean her keyboard first. Tina knows her assignment will only take 10 minutes to complete. Dinner will be ready at 5:30 p.m. Tina decides to time how long it takes to remove and clean one key and will then multiply that time by how many keys she needs to fix. She counts 15 keys that are sticky and times it to take 3 minutes to clean one. After Tina has cleaned one key, there are 14 left to clean. How many minutes total will it take for Tina to both clean the remaining keys and finish her assignment?",
        "Tina has already cleaned one key so she has 14 left which take 3 minutes each to clean, 14 x 3 = 42 minutes to clean all the keyboard keys. Her assignment will take 10 minutes to complete, so she needs 42 minutes + 10 minutes = 52 minutes total before dinner. The answer is 52. #### 52"),

    (
        "Ellie went to visit a circus with Sarah and they both got lost in the house of mirrors. They have to travel through the house of mirrors a few times before they finally get out and when they leave, they discuss how many times they've seen their own reflections. Sarah says that every time they were in the room with tall mirrors, she saw her reflection 10 times and every time they were in the room with wide mirrors, she saw her reflection 5 times. Ellie says that every time they were in the room with tall mirrors, she saw her reflection 6 times and every time they were in the room with wide mirrors she saw her reflection 3 times. They both passed through the room with tall mirrors 3 times each and they both passed through the room with wide mirrors 5 times each. In total, how many times did Sarah and Ellie see their reflections?",
        "In the rooms with tall mirrors, Sarah saw her reflection a total of 10 reflections * 3 passes = 30 times. In the rooms with wide mirrors, Sarah saw her reflection a total of 5 reflections * 5 passes = 25 reflections. So Sarah saw her reflection a total of 30 + 25 = 55 times. In the rooms with tall mirrors, Ellie saw her reflection a total of 6 reflections * 3 passes = 18 times. In the rooms with wide mirrors, Ellie saw her reflection a total of 3 reflections * 5 passes = 15 times. So Ellie saw her reflection a total of 18 + 15 = 33 times. Therefore, Sarah and Ellie saw their reflections a total of 55 + 33 = 88 times. The answer is 88"),

    (
        "A curry house sells curries that have varying levels of spice. Recently, a lot of the customers have been ordering very mild curries and the chefs have been having to throw away some wasted ingredients. To reduce cost and food wastage, the curry house starts monitoring how many ingredients are actually being used and changes their spending accordingly. The curry house needs 3 peppers for very spicy curries, 2 peppers for spicy curries, and only 1 pepper for mild curries. After adjusting their purchasing, the curry house now buys the exact amount of peppers they need. Previously, the curry house was buying enough peppers for 30 very spicy curries, 30 spicy curries, and 10 mild curries. They now buy enough peppers for 15 spicy curries and 90 mild curries. They no longer sell very spicy curries. How many fewer peppers does the curry house now buy?",
        "The curry house previously bought 3 peppers per very spicy curry * 30 very spicy curries = 90 peppers for very spicy curries. They also bought 2 peppers per spicy curry * 30 spicy curries = 60 peppers for spicy curries. They also bought 1 pepper per mild curry * 10 mild curries = 10 peppers for mild curries. So they were previously buying 90 + 60 + 10 = 160 peppers. They now buy 2 peppers per spicy curry * 15 spicy curries = 30 peppers for spicy curries. They also now buy 1 pepper per mild curry * 90 mild curries = 90 peppers for mild curries. So they now buy 30 + 90 = 120 peppers. This is a difference of 160 peppers bought originally - 120 peppers bought now = 40 peppers. The answer is 40"),

    (
        "A man is trying to maximize the amount of money he saves each month. In particular, he is trying to decide between two different apartments. The first apartment costs $800 per month in rent and will cost an additional $260 per month in utilities. The second apartment costs $900 per month and will cost an additional $200 per month in utilities. The first apartment is slightly further from the man's work, and the man would have to drive 31 miles per day to get to work. The second apartment is closer, and the man would only have to drive 21 miles to get to work. According to the IRS, each mile a person drives has an average cost of 58 cents. If the man must drive to work 20 days each month, what is the difference between the total monthly costs of these two apartments after factoring in utility and driving-related costs (to the nearest whole dollar)?",
        "The mileage cost for the first apartment will be 31*20*0.58 = $359.60. This makes the total monthly cost of the first apartment 359.60 + 800 + 260 = $1419.60. Similarly, the mileage cost for the second apartment will be 21*20*0.58 = $243.60. Thus, the total monthly cost of the second apartment is 243.60 + 900 + 200 = 1343.60. Therefore, the difference in total monthly costs is 1419.60 - 1343.60 = $76. The answer is 76"),
    (
        "Hasan is packing up his apartment because he’s moving across the country for a new job. He needs to ship several boxes to his new home. The movers have asked that Hasan avoid putting more than a certain weight in pounds in any cardboard box. The moving company has helpfully provided Hasan with a digital scale that will alert him if a package is too heavy. Hasan is in the kitchen, and he fills a cardboard box with 38 dinner plates. When he checks the box, the scale reports his box is too heavy. Hasan knows each of his plates weighs 10 ounces. He removes a single plate from the box and checks the movers’ scale again. The scale reports his box is still too heavy. Hasan repeats the process again and again. When he has removed enough plates, the movers’ scale shows the box is now an acceptable weight for shipping. Hasan deduces that each shipping box can hold 20 pounds before the scale says the box is too heavy. How many plates did Hasan need to remove from the shipping box?",
        "Let x be the number of plates removed from the box. Hasan figured out the movers' weight limit was 20 pounds. Since a pound is equal to 16 ounces, each box can hold 20 * 16, or 320 ounces. Each plate weighs 10 ounces, so the weight of the plates in the box after Hasan removes enough plates to satisfy the movers' weight limit is (38 - x) * 10 ounces. Since these two values are equal, we can write the equation (38 - x) * 10 = 320. Dividing both sides by 10 leaves 38-x = 32. Adding x to both sides gives 38 – x + x = 32 +x, or, 38 = 32 +x. Subtracting 32 from both sides gives the value of x, which is the number of plates removed from the box, 38 -32 = 32 + x – 32, or, 6 = x. The answer is 6. #### ")

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
        api_key="b60711d4-3d78-4080-8bdf-b8825d106f77",
        base_url="https://api.sambanova.ai/v1",
    )
    test_data_path = "/Users/florence/Desktop/hku/nlp/COMP7607-2024-master/Assignment1/data/GSM8K/test.jsonl"
    output_data_path = "output/long.jsonl"
    test_data = load_data(test_data_path)
    test_acc(test_data, output_data_path)
