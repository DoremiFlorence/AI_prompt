## task 1
# zero shot
t1_0.py
output: zeroshot_baseline.jsonl

# few shot
t1_n.py
output: fewshot_baseline.jsonl

## task 2
# self polish
t2_sp.py
output: self_polish.jsonl

# program of thought
t2_pot.py
output: program_of_thought.jsonl

## task 3
main function: t3.py
dependent function: rag_prompt.py
output: sp_improve.jsonl