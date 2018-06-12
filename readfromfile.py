question_number = 0
with open('test_questions.txt', 'r') as rf:
    with open('answer_questions', 'w') as wf:
        for line in rf:
            question_number = question_number + 1
            if question_number >= 10:
                question = line[3:len(line)]
            else:
                question = line[2:len(line)]
            typeOfQuestion(question)