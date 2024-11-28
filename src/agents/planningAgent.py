class PlanningAgent:
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

    def plan(self, draft):
        system_message = "You are a patent drafting assistant. Your task is to analyze the provided patent description and organize it into a structured format."
        user_message = f"""{draft}\nBased on the provided patent draft, I need you to help me write the most detailed writing guide for the patent description. This guide should consist of multiple sections, with each section providing guidance for writing a specific part of the patent description and including the key points that need to be covered for that section. Please output in the following format:\n<Section-1>\nOverview: Describe the main purpose of this section and its role in the patent application.\n<Subsection-1>\nThe main content and drafting points for this subsection.\n</Subsection-1>\n<Subsection-2>\nThe main content and drafting points for this subsection.\n</Subsection-2>\n<Subsection-3>\nThe main content and drafting points for this subsection.\n</Subsection-3>\n...\n<Subsection-m>\nThe main content and drafting points for this subsection.\n</Subsection-m>\n</Section-1>\n<Section-2>\nOverview: Describe the main purpose of this section and its role in the patent application.\n<Subsection-1>\nThe main content and drafting points for this subsection.\n</Subsection-1>\n<Subsection-2>\nThe main content and drafting points for this subsection.\n</Subsection-2>\n...\n<Subsection-m>\nThe main content and drafting points for this subsection.\n</Subsection-m>\n</Section-2>\n...\n<Section-n>\nOverview: Describe the main purpose of this section and its role in the patent application.\n<Subsection-1>\nThe main content and drafting points for this subsection.\n</Subsection-1>\n<Subsection-2>\nThe main content and drafting points for this subsection.\n</Subsection-2>\n...\n<Subsection-m>\nThe main content and drafting points for this subsection.\n</Subsection-m>\n</Section-n>\nEach Section in this guide should describe the main role of this part in the patent and the goals it should achieve. Each Subsection in this guide should be a complete paragraph that clearly outlines the main content and drafting points while ensuring a balance between the clarity of the technical description and legal enforceability."""
        plan = self.chat(user_message=user_message, system_message=system_message)
        return plan
