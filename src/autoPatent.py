import tqdm
import yaml
import pandas as pd
from openai import OpenAI
import httpx
from agents.writerAgent import TitleWriter, AbstractWriter, BackgroundWriter, SummaryWriter, ClaimsWriter, \
    DescriptionWriter
from agents.planningAgent import PlanningAgent
from agents.examinerAgent import ExaminerAgent
import re
from datetime import datetime
import os


def step1(row_data):
    draft = row_data['draft']
    title = titleWriter.write(draft)
    abstract = abstractWriter.write(draft)
    background = backgroundWriter.write(draft)
    summary = summaryWriter.write(draft)
    claims = claimsWriter.write(draft)

    book = {
        "draft": draft,
        "title": title,
        "abstract": abstract,
        "claims": claims,
        "background": background,
        "summary": summary,
    }
    return book


def step2(book):
    plan = planningAgent.plan(book["draft"])

    section_pattern = re.compile(r'<Section-(\d+)>(.*?)</Section-\1>', re.DOTALL)
    section_plans = section_pattern.findall(plan)
    sections = []
    for section_plan in section_plans:
        sub_pattern = re.compile(r'<Subsection-(\d+)>(.*?)</Subsection-\1>', re.DOTALL)
        subsection_plans = sub_pattern.findall(section_plan[1])
        subsections = []
        for subsection_plan in subsection_plans:
            # For Retrieval
            referenceContent = descriptionWriter.retrieve(subsection_plan, book)
            subsection = descriptionWriter.writeSubsection(section_plan, subsection_plan, referenceContent)

            # For Examiner
            result, advice = examinerAgent.reviewSubsection(subsection_plan, subsection, book)
            subsection = descriptionWriter.writeSubsection(section_plan, subsection_plan, advice=advice,
                                                           subsection=subsection)
            result, advice = examinerAgent.reviewSubsection(subsection_plan, subsection, book)
            try_time = 0
            while result != "Pass":
                try_time += 1
                if try_time > 1:
                    break
                subsection = descriptionWriter.writeSubsection(section_plan, subsection_plan, advice=advice,
                                                               subsection=subsection)
                result, advice = examinerAgent.reviewSubsection(subsection_plan, subsection, book)

            subsections.append(subsection)
        section = "\n".join(subsections)
        sections.append(section)
    return sections


if __name__ == '__main__':

    with open('src/config.yml', 'r') as f:
        configs = yaml.safe_load(f)

    if configs["Pattern"] == "own":
        print("======Use User Pattern======")
        df = pd.read_json("data/draft.json")
        draft = "<Draft>"
        for index, row in df.iterrows():
            draft += f"<Question{index + 1}>"
            draft += row["q"]
            draft += f"</Question>{index + 1}\n"
            draft += f"<Answer{index + 1}>"
            draft += row["a"]
            draft += f"</Answer>{index + 1}\n"
        draft += "</Draft>"
        draft_list = [draft]
        df = pd.DataFrame({
            "draft": draft_list
        })

    elif configs["Pattern"] == "test":
        df = pd.read_json("data/test.json")
    else:
        raise FileExistsError("Pattern must be either own or test")

    client = None
    if "gpt" in configs["Model-series"]:
        client = OpenAI(
            base_url="https://api.lqqq.ltd/v1",
            api_key=configs["OpenAI-api-key"],
            http_client=httpx.Client(
                base_url="https://api.lqqq.ltd/v1",
                follow_redirects=True,
            ),
        )
    else:
        title_client = OpenAI(base_url=f"http://localhost:{configs['Title-port']}/v1", api_key=f"{configs['Title-api']}")
        abstract_client = OpenAI(base_url=f"http://localhost:{configs['Abstract-port']}/v1", api_key=f"{configs['Abstract-api']}")
        background_client = OpenAI(base_url=f"http://localhost:{configs['Background-port']}/v1", api_key=f"{configs['Background-api']}")
        summary_client = OpenAI(base_url=f"http://localhost:{configs['Summary-port']}/v1", api_key=f"{configs['Summary-api']}")
        claims_client = OpenAI(base_url=f"http://localhost:{configs['Claims-port']}/v1", api_key=f"{configs['Claims-api']}")
        plan_client = OpenAI(base_url=f"http://localhost:{configs['Plan-port']}/v1", api_key=f"{configs['Plan-api']}")
        description_client = OpenAI(base_url=f"http://localhost:{configs['Description-port']}/v1", api_key=f"{configs['Description-api']}")
        examiner_client = OpenAI(base_url=f"http://localhost:{configs['Examiner-port']}/v1", api_key=f"{configs['Examiner-api']}")

    print("=====Initial Agents=====")
    titleWriter = TitleWriter(client=client if "gpt" in configs["Model-series"] else title_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Title-model"])
    abstractWriter = AbstractWriter(client=client if "gpt" in configs["Model-series"] else abstract_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Abstract-model"])
    backgroundWriter = BackgroundWriter(client=client if "gpt" in configs["Model-series"] else background_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Background-model"])
    summaryWriter = SummaryWriter(client=client if "gpt" in configs["Model-series"] else summary_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Summary-model"])
    claimsWriter = ClaimsWriter(client=client if "gpt" in configs["Model-series"] else claims_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Claims-model"])
    descriptionWriter = DescriptionWriter(client=client if "gpt" in configs["Model-series"] else description_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Description-model"])
    planningAgent = PlanningAgent(client=client if "gpt" in configs["Model-series"] else plan_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Plan-model"])
    examinerAgent = ExaminerAgent(client=client if "gpt" in configs["Model-series"] else examiner_client, model_name=configs["GPT-model"] if "gpt" in configs["Model-series"] else configs["Examiner-model"])
    print("=====Successfully=====")

    df_iter = tqdm.tqdm(df.iterrows(), total=len(df))

    application_numbers = []
    model_outputs = []
    outputs = []

    for index, row in df_iter:
        # STEP1
        shortComponentBook = step1(row)
        # STEP2
        full_descriptions = step2(shortComponentBook)
        full_description = "<Description>"
        for description in full_descriptions:
            full_description += description
        full_description += "</Description>"
        if "gpt" in configs["Model-series"]:
            output = f"""<Patent>\n<Title>\n{row["Title"]}\n</Title>\n<Abstract>\n{row["Abstract"]}\n</Abstract>\n<Background>\n{row["Background"]}\n</Background>\n<Summary>\n{row["Summary"]}\n</Summary>\n<Claims>\n{row["Claims"]}\n</Claims>\n<Full Description>\n{row["Description"]}\n</Full Description>\n</Patent>"""
            outputs.append(output)
            application_numbers.append(row["application_number"])
        model_output = f"""<Patent>\n{shortComponentBook["title"]}\n{shortComponentBook["abstract"]}\n{shortComponentBook["background"]}\n{shortComponentBook["summary"]}\n{shortComponentBook["claims"]}\n{full_description}\n</Patent>"""
        model_outputs.append(model_output)

    final_df = pd.DataFrame({
        "application_number": application_numbers,
        "ground_truth": outputs,
        "model_output": model_outputs,
    })

    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")

    print("====Save the file====")

    save_path = f"AutoPatent_{len(final_df)}_{formatted_time}.json"
    save_path = os.path.join("../outputs", save_path)
    final_df.to_json(save_path, orient="records", force_ascii=False)