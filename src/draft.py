import pandas


answer1 = input("Answer for Question 1: ")
answer2 = input("Answer for Question 2: ")
answer3 = input("Answer for Question 3: ")
answer4 = input("Answer for Question 4: ")
answer5 = input("Answer for Question 5: ")

df = pandas.DataFrame([
    {"q": "What is the technical problem that this invention aims to solve?", "a": answer1},
    {"q": "What is the technical background of this invention? What are the existing solutions most similar to this invention? What are the shortcomings of the existing technologies, and what are the advantages of this invention?", "a": answer2},
    {"q": "Please provide a detailed explanation of the technical solution of this invention.", "a": answer3},
    {"q": "What are the key points and the aspects intended for protection in this invention?", "a": answer4},
    {"q": "Please provide the description of the drawings for this invention.", "a": answer5}
])

df.to_json("../data/draft.json", orient="records", force_ascii=False)
