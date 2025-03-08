# -*- coding: utf-8 -*-
# @Time : 10/23/24 7:56 PM
# @Author : Florence
# @File : rag_prompt.py
# @Project : Assignment1
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# 假设你的数据集以 JSON 字符串格式存储在一个列表中
def load_data(path):
    test_data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # 确保行不为空
                test_data.append(json.loads(line))
    test_data = test_data[0:1000]
    return test_data


path = "data/GSM8K/train.jsonl"
data = load_data(path)




def rag(question):
    # 提取问题列表
    questions = [item["question"] for item in data]
    answers = [item["answer"] for item in data]
    # 输入问题
    que = question

    # 计算相似度
    vectorizer = TfidfVectorizer().fit_transform(questions + [que])
    vectors = vectorizer.toarray()

    # 计算余弦相似度
    cosine_sim = cosine_similarity(vectors[-1:], vectors[:-1])
    similar_indices = cosine_sim[0].argsort()[-6:][::-1]  # 获取最相似的 6 个问题

    def question_prompt(s):
        return f'Question: {s}'

    def answer_prompt(s):
        return f"Answer:\nLet's think step by step.\n{s}"

    # 构建 Prompt，包括问题和对应的答案
    chats = [
        {"role": "system",
         "content": "Your task is to solve a series of math word problems by providing the final answer. "
                    "Important: Use the format #### [value] to highlight your answer. For example, if the final answer is 560, "
                    "you should write #### 560."}
    ]


    for i in similar_indices:
        chats.append(
            {"role": "user", "content": question_prompt(questions[i])})
        chats.append(
            {"role": "assistant", "content": answer_prompt(answers[i])})

    chats.append({"role": "user", "content": question_prompt(question)})

    return chats

#
# print(rag("How much did Natalia sell in total over two months?"))
