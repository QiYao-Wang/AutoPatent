class ExaminerAgent:
    def __init__(self, client, model_name, temperature=0.5, max_tokens=16384):
        self.client = client
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, user_message, system_message=None):
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content

    def reviewDraft(self, answer, i):
        system_message = "You are a patent agent responsible for reviewing users' technical drafts, skilled at assessing whether the drafts meet quality standards based on relevant requirements."
        # for question i
        prompt1 = f"""# Draft: {answer}
# Requirements: The text of this draft section must include the technical problem solved by the invention. If it is included, just return <Result> Pass </Result>; if it is not included, return <Result> Fail </Result>, and provide a detailed explanation in <Reason> waiting for filling </Reason>.
Please tell me if this section of the draft meets the quality standards."""
        prompt2 = f"""# Draft: {answer}
# Requirements: The text of this draft section must include the background of the technology, the existing technical solutions, the shortcomings of the existing technology, and the advantages of the present invention. If it is included, just return <Result> Pass </Result>; if it is not included, return <Result> Fail </Result>, and provide a detailed explanation in <Reason> waiting for filling </Reason>.
Please tell me if this section of the draft meets the quality standards."""
        prompt3 = f"""# Draft: {answer}
# Requirements: The text of this draft section must include a detailed technical solution, which should describe the specific technical means for implementing the invention. If it is included, just return <Result> Pass </Result>; if it is not included, return <Result> Fail </Result>, and provide a detailed explanation in <Reason> waiting for filling </Reason>.
Please tell me if this section of the draft meets the quality standards."""
        prompt4 = f"""# Draft: {answer}
# Requirements: The text of this draft section must include the key points and protection points of the invention, so that the critical innovations of the technical solution can be distilled and listed in bullet points, such as 1, 2, 3, etc. If it is included, just return <Result> Pass </Result>; if it is not included, return <Result> Fail </Result>, and provide a detailed explanation in <Reason> waiting for filling </Reason>.
Please tell me if this section of the draft meets the quality standards."""
        prompt5 = f"""# Draft: {answer}
# Requirements: The text of this draft section must include the description of the drawings for the invention, where each figure must correspond to its respective drawing description one by one. If it is included, just return <Result> Pass </Result>; if it is not included, return <Result> Fail </Result>, and provide a detailed explanation in <Reason> waiting for filling </Reason>.
Please tell me if this section of the draft meets the quality standards."""
        prompts = [prompt1, prompt2, prompt3, prompt4, prompt5]
        user_message = prompts[i - 1]
        # st.write(user_message)
        response = self.chat(user_message=user_message, system_message=system_message)
        # st.write(response)
        result_pattern = rf"(?<=<Result>).*?(?=</Result>)"
        result = re.findall(result_pattern, response, re.DOTALL)[0].strip()
        reason_pattern = rf"(?<=<Reason>).*?(?=</Reason>)"
        reason = re.findall(reason_pattern, response, re.DOTALL)
        if len(reason) == 0:
            reason = ""
        else:
            reason = reason[0]
        return result, reason

    def reviewSubsection(self, sub_plan, subsection, book):
        draft = book["draft"]
        result_pattern = r"<Result>(.*?)</Result>"
        reason_pattern = r"<Advice>(.*?)</Advice>"
        prompt = f"""{draft}
        <WritingGuideline>{sub_plan}</WritingGuideline>
        <Content>{subsection}</Content>
        <Requirement> Accuracy should ensure that technical details are clear and precise, aligning with law and technical standards. Logic should follow a natural progression with a clear structure. Comprehensiveness should fully disclose all necessary information required by the writing guideline. Clarity should feature concise and easily understandable language, balancing technical and legal descriptions. Coherence should ensure smooth expression, avoiding any ambiguity or uncertainty. Consistency should maintain uniform terminology, align fully with the draft, and avoid any contradictions.</Requirement>
        Refer to draft and evaluate whether the content meets the requirement provided, based on the given writing guideline.
        If it complies with the requirement and writing guideline, return <Result>Pass</Result>; if it does not comply, return <Result>Fail</Result>. And you must provide helpful and detailed advice in <Advice>waiting for filling</Advice> regardless of whether the result is Pass or Fail.
        """
        try_times = 0
        while True:
            try_times += 1
            ref = self.chat(user_message=prompt, system_message="You are an experienced patent examiner.")
            match = re.search(result_pattern, ref, re.DOTALL)
            match1 = re.search(reason_pattern, ref, re.DOTALL)
            if try_times > 1:
                return "Fail", None
            if match is None or match1 is None:
                continue
            else:
                result = match.group(1).strip()
                advice = match1.group(1)
                if result == "Pass":
                    return "Pass", advice
                else:
                    return "Fail", advice
