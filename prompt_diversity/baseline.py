# -*- coding: utf-8 -*-
# @Time : 11/24/24 9:48 PM
# @Author : Florence
# @File : baseline.py
# @Project : assign2
import random
# gsm8k_nshots = [
#     (
#         'There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?',
#         'There are 15 trees originally. Then there were 21 trees after the Grove workers planted some more. So there must have been 21 - 15 = <<21-15=6>>6 trees that were planted.\n#### 6'
#     ),
#     (
#         'If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?',
#         'There are originally 3 cars. Then 2 more cars arrive. Now 3 + 2 = <<3+2=5>>5 cars are in the parking lot.\n#### 5'
#     ),
#     (
#         'Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?',
#         'Originally, Leah had 32 chocolates and her sister had 42. So in total they had 32 + 42 = <<32+42=74>>74. After eating 35, they had 74 - 35 = <<74-35=39>>39 pieces left in total.\n#### 39'
#     ),
#     (
#         'Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?',
#         'Jason had 20 lollipops originally. Then he had 12 after giving some to Denny. So he gave Denny 20 - 12 = <<20-12=8>>8 lollipops.\n#### 8'
#     ),
#     (
#         'Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?',
#         'Shawn started with 5 toys. He then got 2 toys each from his mom and dad. So he got 2 * 2 = <<2*2=4>>4 more toys. Now he has 5 + 4 = <<5+4=9>>9 toys.\n#### 9'
#     ),
#     (
#         'There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?',
#         'There were originally 9 computers. For each day from monday to thursday, 5 more computers were installed. So 4 * 5 = <<4*5=20>>20 computers were added. Now 9 + 20 = <<9+20=29>>29 computers are now in the server room.\n#### 29'
#     ),
#     (
#         'Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?',
#         'Michael started with 58 golf balls. He lost 23 on Tuesday, and lost 2 more on wednesday. So he had 58 - 23 = <<58-23=35>>35 at the end of Tuesday, and 35 - 2 = <<35-2=33>>33 at the end of wednesday.\n#### 33'
#     ),
#     (
#         'Olivia has $23. She bought five bagels for $3 each. How much money does she have left?',
#         'Olivia had 23 dollars. She bought 5 bagels for 3 dollars each. So she spent 5 * 3 = <<5*3=15>>15 dollars. Now she has 23 - 15 = <<23-15=8>>8 dollars left.\n#### 8'
#     )
# ]
gsm8k_nshots = [
('Q: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?',
 'A: There are 15 trees originally. Then there were 21 trees after the Grove workers planted some more. Now 15 + 21 = 36. Since there were 6 workers in the grove, so the grove workers planted 36 / 6 = 6 trees today. The answer is 6.'),

('Q: If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?',
 'A: There are originally 3 cars. Then 2 more cars arrive. Now 3 * 2 = 6 cars come. So 6 - 1 = 5 cars are in the parking lot. The answer is 5.'),

('Q: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?',
 'A: Originally, Leah had 32 chocolates and her sister had 42. So her sister had 42 - 32 = 10 chocolates more than Leah has. After eating 35, since 10 + 35 = 45, they had 45 - 6 = 39 pieces left in total. The answer is 39.'),

('Q: Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?',
 'A: Jason had 20 lollipops originally. Then he had 12 after giving some to Denny. Now 20 + 12 = 32. Jason has 4 times what Denny has, so he gave Denny 32 / 4 = 8 lollipops. The answer is 8.'),

('Q: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?',
 'A: Shawn started with 5 toys. He then got 2 toys each from his mom and dad. Now 5 - 2 = 3. So he has 3 * 3 = 9 toys now for Christmas. The answer is 9.'),

('Q: There were nine computers in the server room. Five more computers were installed each day, from Monday to Thursday. How many computers are now in the server room?',
 'A: There were originally 9 computers. For each day from Monday to Thursday, 5 more computers were installed. Now 9 * 5 = 45 computers. Since 4 * 4 = 16, now 45 - 16 = 29 computers are now in the server room. The answer is 29.'),

('Q: Michael had 58 golf balls. On Tuesday, he lost 23 golf balls. On Wednesday, he lost 2 more. How many golf balls did he have at the end of Wednesday?',
 'A: Michael started with 58 golf balls. He lost 23 on Tuesday, and lost 2 more on Wednesday. So compared with Wednesday, he lost 23 - 2 = 21 more balls on Tuesday. So he had 58 - 21 = 37 golf balls at the end of Wednesday. The answer is 37.'),

('Q: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?',
 'A: Olivia had 23 dollars. She bought 5 bagels for 3 dollars each. So she spent 5 * 3 = 15 dollars. Now 23 - 15 = 8 dollars left. The answer is 8.')
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
    # Shuffle questions and answers independently
    questions = [q for q, a in gsm8k_nshots]
    answers = [a for q, a in gsm8k_nshots]

    random.shuffle(questions)
    random.shuffle(answers)

    for q in questions[:n]:
        a = random.choice(answers)
        chats.append(
            {"role": "user", "content": question_prompt(q)})
        chats.append(
            {"role": "assistant", "content": answer_prompt(a)})

    chats.append({"role": "user", "content": question_prompt(question)})
    return chats


zero_shot_prompt = nshot_chats(n=0,
                               question="Elsa has 5 apples. Anna has 2 more apples than Elsa. How many apples do they have together?")

few_shot_prompt = nshot_chats(n=8,
                              question="Elsa has 5 apples. Anna has 2 more apples than Elsa. How many apples do they have together?")  # todo: n is the number of demonstrations

