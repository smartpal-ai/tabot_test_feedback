from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from typing import Dict, List, Optional, Tuple, Union
from pprint import pprint

class BaseTemplate:
    
    def __init__(self, 
                 template_text: Optional[str] = None, 
                 response_schemas: Optional[Dict[str, str]] = None, 
                 input_vars: Optional[List[str]] = None):
        """
        Initialize the BaseTemplate with optional template text, response schemas, and input variables.

        :param template_text: The template text for the prompt.
        :param response_schemas: A dictionary of response schemas with name as key and description as value.
        :param input_vars: A list of input variable names to be used in the template.
        """
        self.template_text = template_text
        self.response_schemas = response_schemas
        self.input_vars = input_vars

        self.prompt = None
        self.output_parser = None
        self.format_instructions = None

    def build(self) -> Tuple[ChatPromptTemplate, Optional[str], Union[StructuredOutputParser, StrOutputParser]]:
        """
        Build the prompt and output parser based on the provided template text and response schemas.

        :return: A tuple containing the prompt, format instructions, and output parser.
        """
        if not self.template_text:
            raise ValueError("Template text must be provided.")
        
        # Ensure input_vars are passed correctly
        if self.input_vars:
            self.prompt = ChatPromptTemplate.from_template(template=self.template_text, input_variables=self.input_vars)
        else:
            self.prompt = ChatPromptTemplate.from_template(template=self.template_text)

        if self.response_schemas:
            schemas = [ResponseSchema(name=name, description=desc) for name, desc in self.response_schemas.items()]
            self.output_parser = StructuredOutputParser.from_response_schemas(schemas)
            self.format_instructions = self.output_parser.get_format_instructions()
        else:
            self.output_parser = StrOutputParser()
            self.format_instructions = None
            
        return self.prompt, self.format_instructions, self.output_parser

    def set_template_text(self, template_text: str) -> None:
        """
        Set the template text for the prompt.

        :param template_text: The template text for the prompt.
        """
        self.template_text = template_text

    def set_response_schemas(self, response_schemas: Dict[str, str]) -> None:
        """
        Set the response schemas.

        :param response_schemas: A dictionary of response schemas with name as key and description as value.
        """
        self.response_schemas = response_schemas

    def set_input_vars(self, input_vars: List[str]) -> None:
        """
        Set the input variables for the template.

        :param input_vars: A list of input variable names to be used in the template.
        """
        self.input_vars = input_vars

class AutomatedFeedbackTemplate(BaseTemplate):
    
    def __init__(self, 
                 template_text: Optional[str] = None, 
                 response_schemas: Optional[Dict[str, str]] = None, 
                 input_vars: Optional[List[str]] = None):
        """
        Initialize the AutomatedFeedbackTemplate with default or provided template text, response schemas, and input variables.

        :param template_text: The template text for the prompt.
        :param response_schemas: A dictionary of response schemas with name as key and description as value.
        :param input_vars: A list of input variable names to be used in the template.
        """
        if template_text is None:
            template_text = """
            You are a university teacher. You will be provided with detailed information about a student's recent quiz performance, including past performance data if available. \
            Use this information to analyze the student's current performance and generate personalized feedback. If past performance data is available, compare the current performance with past performance. \
            Your feedback should be specific to the text of questions/answers where the student made mistakes. \

            {current_quiz} \

            {past_performance} \ 

            Instructions:

            - Analyze Current Performance:

            Analyze the texts of questions, correct answers, and the student's answers. 
            Compare the chosen answers with the correct answers (weight == 100) and incorrect answers (weight == 0).
            Calculate the accuracy and identify all the areas where the student made mistakes.
            For all the questions where the student made mistakes, please show the reasoning and explanations for the correct answer (as detailed as possible).

            - Compare with Past Performance (if available):

            If past performance data is available, examine the student's past performance details.
            Compare current quiz results with past results to identify improvement or decline.
            
            - Generate Personalized Feedback:

            Provide a summary of the student's performance in the current quiz.
            Highlight areas of strength and areas needing improvement.
            If past performance data is available, compare current performance with past performance to show progress or areas of concern.
            
            - Suggest Ways to Improve:

            Provide actionable and specific suggestions for the student to improve in future quizzes.
            Include study tips, resources, and strategies tailored to the student's needs.

            Example Feedback Structure:

            Feedback: [Feedback]
            Strengths: [List areas where the student performed well]
            Areas for Improvement: [List all the areas where the student made mistakes and show the reasoning for correct answers]
            Progress: [Highlight improvements or decline compared to the past quiz]
            Suggestions for Improvement: [Provide suggestions for the student to improve in future quizzes]
            
            Please ensure that the feedback is not too general and focuses on the specific context of the question text and answer text of the current quiz.
            For all the questions where the student made mistakes, please show the reasoning and explanations for the correct answer (as detailed as possible). 
            """

            # Ensure that the feedback is positive, constructive, and encouraging. Focus on helping the student understand their mistakes and provide clear guidance on how to improve.
        
        if response_schemas is None:
            response_schemas = {
                "feedback" : "Personalised feedback generated based on student performace",
                "strengths": "Areas where the student performed well",
                "areas_for_improvement": "Areas where the student needs improvement",
                "progress": "A brief summary of the student's performance",
                "suggestions": "Suggestions for the student to improve in future quizzes"
            }
        
        super().__init__(template_text, response_schemas, input_vars)

    def build(self) -> Tuple[ChatPromptTemplate, Optional[str], Union[StructuredOutputParser, StrOutputParser]]:
        """
        Build the prompt and output parser for the automated feedback generation.

        :return: A tuple containing the prompt, format instructions, and output parser.
        """
        return super().build()
    
if __name__ == "__main__":
    feedback_template = AutomatedFeedbackTemplate()
    prompt, format_instructions, output_parser = feedback_template.build()
    pprint(prompt)
