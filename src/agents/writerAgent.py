from agent import Agent
import re


class Writer(Agent):
    def write(self, draft):
        pass


class TitleWriter(Writer):
    def write(self, draft):
        system_message = "You are an experienced patent attorney, skilled in crafting clear, precise, and legally sound patent titles. You can efficiently transform technical concepts into concise and impactful patent titles that accurately reflect the invention, ensuring they meet all patent office requirements. Your expertise ensures that each title is coherent, captures the essence of the invention, and demonstrates a deep understanding of both legal and technical aspects."
        user_message = f"""{draft}\nBased on the above patent draft, please generate a patent title that complies with legal and patent regulations, and follows the format below:\n<Title> the title of patent </Title>"""
        title = self.chat(user_message=user_message, system_message=system_message)
        title_pattern = rf"(?<=<Title>).*?(?=</Title>)"
        title = re.findall(title_pattern, title, re.DOTALL)[0]
        return title


class AbstractWriter(Writer):
    def write(self, draft):
        system_message = "You are an experienced patent attorney, skilled in crafting clear, precise, and legally sound patent abstract. You can efficiently transform technical concepts into concise and impactful patent titles that accurately reflect the invention, ensuring they meet all patent office requirements. Your expertise ensures that each title is coherent, captures the essence of the invention, and demonstrates a deep understanding of both legal and technical aspects."
        user_message = f"{draft}\nBased on the provided patent draft, please generate a patent abstract that complies with legal and patent regulations, following the format below:\n<Abstract> the abstract of patent </Abstract>"
        abstract = self.chat(user_message=user_message, system_message=system_message)
        abstract_pattern = rf"(?<=<Abstract>).*?(?=</Abstract>)"
        abstract = re.findall(abstract_pattern, abstract, re.DOTALL)[0]
        return abstract


class ClaimsWriter(Writer):
    def write(self, draft):
        system_message = "You are an experienced patent attorney, skilled in drafting clear, precise, and legally sound patent claims. You can efficiently transform technical concepts into well-structured patent claims that accurately define the scope of the invention, ensuring they meet all patent office requirements. Your expertise ensures that each claim is coherent, captures the key technical features of the invention, and demonstrates a deep understanding of both legal and technical aspects."
        user_message = f"""{draft}\nBased on the above patent draft, please generate patent claims that comply with legal and patent regulations.\nThe claims should be written in clear language, avoiding ambiguity or vague descriptions.\nThe independent claims should cover the core technical features of the invention and should not rely on other claims.\nThe dependent claims should supplement or limit the independent claims, referencing the relevant independent claims.\nThe claims must focus on a single invention, ensuring the unity of the invention, and must be consistent with the content of the draft.\nEnsure that the described invention possesses novelty, inventive step, and industrial applicability.\nThe claims should clearly define the scope of the invention's protection through specific technical features (such as components, steps, or systems).\nEach claim should end with a complete sentence, be numbered sequentially, and have an appropriate scope—neither too narrow nor too broad.\nPlease strictly adhere to these guidelines when generating the patent claims and following the format below:\n<Claims> the claims of patent </Claims>"""
        claims = self.chat(user_message=user_message, system_message=system_message)
        claims_pattern = rf"(?<=<Claims>).*?(?=</Claims>)"
        claims = re.findall(claims_pattern, claims, re.DOTALL)[0]
        return claims


class BackgroundWriter(Writer):
    def write(self, draft):
        system_message = "You are an experienced patent attorney, skilled in drafting clear, well-structured, and legally compliant patent background information. You can efficiently transform technical concepts into background content that meets patent standards, specifically including the definition of the technical field, an objective introduction to existing technology, identification of deficiencies in existing technology, and the purpose and motivation of the invention. Your expertise ensures that the background information is coherent, concise, and highlights key technical elements, demonstrating a deep understanding of both legal and technical aspects."
        user_message = f"""{draft}\nPlease generate the detailed background information for the patent application based on the above patent draft. The background information should include the technical field of the patent, provide an objective introduction to the existing technology relevant to the invention, and point out any deficiencies or issues in the existing technology. Additionally, summarize the purpose or motivation of the invention without disclosing specific details. Please avoid negative comments about the existing technology or others' patents. The content should be clear and concise, avoiding unnecessary complexity.\nPlease output in the following format:\n<Background> the background information of patent </Background>"""
        background = self.chat(user_message=user_message, system_message=system_message)
        background_pattern = rf"(?<=<Background>).*?(?=</Background>)"
        background = re.findall(background_pattern, background, re.DOTALL)[0]
        return background


class SummaryWriter(Writer):
    def write(self, draft):
        system_message = "You are an experienced patent attorney, skilled in drafting clear, concise, and well-structured patent summaries. You excel at distilling complex technical inventions into summaries that highlight the key aspects of the invention, ensuring they are easily understood by patent examiners and meet all legal requirements. Your expertise ensures that each summary strikes a balance between technical detail and legal precision, providing a comprehensive yet focused overview of the invention while maintaining coherence and clarity."
        user_message = f"""{draft}\nPlease generate the summary for the patent application based on the above patent draft. The summary should provide a detailed overview of the invention, including the technical field, the problems in the prior art that the invention addresses, and the key technical features of the invention. The summary should explain how the invention solves the identified problems without delving into specific implementation details. Ensure the summary is clear, concise, and focused on the invention's main objectives and advantages.\nPlease output in the following format:\n<Summary>\nthe summary of the patent\n</Summary>"""
        summary = None
        try_times = 0
        while summary is None or len(summary) == 0:
            try_times += 1
            if try_times > 5:
                break
            summary = self.chat(user_message=user_message, system_message=system_message)
            summary_pattern = rf"(?<=<Summary>).*?(?=</Summary>)"
            summary = re.findall(summary_pattern, summary, re.DOTALL)
        summary = summary[0]
        return summary


class DescriptionWriter(Writer):
    def retrieve(self, sub_plan, book):
        pattern = r"(<Reference>.*?</Reference>)"
        prompt = f"""{book["draft"]}\n{book["title"]}\n{book["abstract"]}\n{book["background"]}\n{book["summary"]}\n{book["claims"]}\nWriting Plan: {sub_plan}\nAccording to the patent text writing plan, determine which of the following contents are necessary for writing this section, and copy the all relevant content without modifying or adding anything. All copied text must be placed within <Reference></Reference> tags, strictly adhering to the formatting requirements, for example:\n<Reference>\nthe needed information for writing this section\n</Reference>."""
        match = None
        try_times = 0
        while match is None and try_times < 5:
            try_times += 1
            ref = self.chat(user_message=prompt, system_message="You are an experienced patent attorney.")
            match = re.search(pattern, ref, re.DOTALL)
        if match is None:
            return None
        else:
            ref = match.group(0)
            return ref

    def writeSubsection(self, section_plan, sub_plan, ref=None, subsection=None, advice=None):
        system = "You are an experienced patent attorney, skilled in drafting clear, precise, and legally compliant patent descriptions. You can transform the provided descriptions and writing guidelines into detailed and logically structured patent descriptions, thoroughly explaining the technical principles and implementations of the invention, ensuring compliance with patent office regulations. Your expertise ensures that each description is well-organized and coherent, accurately reflecting the core technical content of the invention, while demonstrating a deep understanding of both technical details and legal requirements."

        if ref is None:
            if advice is None:
                prompt = f"""Writing Guideline Overview:{section_plan}\nSubsection Writing Guideline: {sub_plan}\nBased on the subsection writing guideline, please draft this subsection, ensuring that the description complies with legal and patent regulations."""
            else:
                prompt = f"""Writing Guideline Overview: {section_plan}\nSubsection Writing Guideline: {sub_plan}\nThe subsection already written: {subsection}\nFeedback from Patent Examiner: {advice}\nBased on the subsection writing guideline and the feedback, revise the subsection to ensure it complies with legal and patent regulations while addressing the examiner's concerns. Do not say anything else. Only output the revised subsection."""
        else:
            prompt = f"""{ref}\nWriting Guideline Overview:{section_plan}\nSubsection Writing Guideline: {sub_plan}\nBased on the content in <Reference></Reference> and the subsection writing guideline, please draft this subsection, ensuring that the description complies with legal and patent regulations."""

        content = self.chat(user_message=prompt, system_message=system)
        return content
