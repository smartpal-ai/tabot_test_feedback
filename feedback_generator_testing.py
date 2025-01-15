from template_detail import AutomatedFeedbackTemplate 
from utils import OpenAIChatResponse
from pprint import pprint
import pandas as pd
from datetime import datetime

class QuizFeedbackGenerator():
    def __init__(self, course_id, user_id, readonly: bool = False):
        """
        Initializes the QuizFeedbackGenerator with a database connection and course ID.
        
        :param course_id: The ID of the course to fetch data for.
        :param readonly: Boolean flag to set the database connection to read-only mode.
        """
        super().__init__()
        self.course_id = course_id
        self.user_id = user_id
        
        self.openai = OpenAIChatResponse()
        
        self.file_name = 'data/feedback_generator.xlsx'
        self.load_file()

        self.to_update_feedback_quizzes = None
        self.quiz_questions = None
        self.to_update_quiz_details = None
        self.users_past_performance = None
    
    def save_data(self):
        try:
            with pd.ExcelWriter(path=self.file_name, engine='openpyxl') as writer:
                self.df_quiz.to_excel(writer, sheet_name='quiz_to_update', index=False)
                self.df_question_answer.to_excel(writer, sheet_name='quiz_question_answers', index=False)
                self.df_user_answer.to_excel(writer, sheet_name='quiz_user_answer', index=False)
                self.df_past_performance.to_excel(writer, sheet_name='quiz_user_past_performance', index=False)
        except Exception as e:
            print(f"Error occured when saving data to file: {self.file_name}")
            print(f"Error {e}")

    def __del__(self):
        self.save_data()

    def load_file(self):
        self.df_quiz = pd.read_excel(self.file_name, sheet_name="quiz_to_update", engine='openpyxl')
        self.df_question_answer = pd.read_excel(self.file_name, sheet_name="quiz_question_answers", engine='openpyxl')
        self.df_user_answer = pd.read_excel(self.file_name, sheet_name="quiz_user_answer",  engine='openpyxl')
        self.df_past_performance = pd.read_excel(self.file_name, sheet_name="quiz_user_past_performance",  engine='openpyxl')

    def update_feedback(self, submission_id, feedback):
        self.df_quiz.loc[self.df_quiz['submission_id'] == submission_id, 'feedback'] = feedback
        curr = self.df_quiz[self.df_quiz['submission_id'] == submission_id]
        curr_user_id = curr['user_id'].iloc[0]
        curr_quiz_id = curr['quiz_id'].iloc[0]
        condition = (
                        (self.df_past_performance['quiz_id'] == curr_quiz_id) & 
                        (self.df_past_performance['user_id'] == curr_user_id)
                    )
        self.df_past_performance.loc[condition,'feedback'] = feedback

    def get_quiz_to_update_query(self, limit: int = None) -> dict:
        """
            :param limit: Optional limit for the number of quizzes to fetch.
            :return: Filtered DataFrame
        """
        df = self.df_quiz

        condition = (
            df['submission_id'].notna()  # Use .notna() to check for non-null values
            & (df['attempt'] == 1)
            & (df['submission_dropped'] == 0)
            & (df['quiz_dropped'] == 0)
            & (df['visible_to_everyone'] == 1)
            & (df['feedback'].isnull())
            & (df['course_id'] == self.course_id)
            & (df['user_id'] == self.user_id)
            & (df['due_date'] < datetime.now())
        )

        filtered_data = df[condition] 

        if limit:
            filtered_data = filtered_data[:limit]
    
        return filtered_data.to_dict(orient='records')

    def get_question_answer_of_quiz_query(self, quiz_id: int) -> dict:
        """
        :param quiz_id: The ID of the quiz.
        :return: Filtered DataFrame
        """
        df = self.df_question_answer

        condition = (
            (df['course_id'] == self.course_id)  
          & (df['quiz_id'] == quiz_id)
        )

        return df[condition].to_dict(orient='records')

    def get_user_answer_of_quiz_query(self, submission_id: int) -> dict:
        """
        :param submission_id: The ID of the quiz submission.
        :return: SQL query string.
        """
        df = self.df_user_answer
        
        condition = (   
                    df['submission_id'] == submission_id
                )
                
        return df[condition].to_dict(orient='records')
    
    def get_past_performance_query(self, user_id: int, quiz_date: datetime, limit:int = 3) -> dict:
        """
        :param user_id: The ID of the user.
        :param quiz_date: The date of the current quiz.
        :return: Filtered Data is returned
        """

        df = self.df_past_performance

        condition = (
                (df['attempt'] == 1)
                & (df['published'] == 1)
                & (df['visible_to_everyone'] == 1)
                & (df['submission_dropped'] == 0)
                & (df['quiz_dropped'] == 0)
                & (df['course_id'] == self.course_id)
                & (df['user_id'] == self.user_id)
                & (df['due_date'] < quiz_date)
                & (df['feedback'].notna())
            )
        
        filtered_data = df[condition]

        filtered_data = filtered_data.sort_values(by="due_date", ascending = False) ## Past quizzes should be descending in due date

        if limit:
            filtered_data = filtered_data[:limit]

        return filtered_data.to_dict(orient='records')

    def combine_questions_and_answers(self, question_answers: list, user_answers: list) -> list:
        """
        Combines question and answer data with user answers.

        :param question_answers: List of question and answer details.
        :param user_answers: List of user answers.
        :return: Combined list of questions with user answers.
        """
        combined_data = {}

        for item in question_answers:
            q_id = item['question_id']
            if q_id not in combined_data:
                combined_data[q_id] = {
                    'question_id': q_id,
                    'question_name': item['question_name'],
                    'question_type': item['question_type'],
                    'question_text': item['question_text'],
                    'answer_choices': []
                }
            combined_data[q_id]['answer_choices'].append({
                'answer_id': item['answer_id'],
                'answer_text': item['answer_text'],
                'weight': item['weight']
            })
        
        for answer in user_answers:
            q_id = answer['question_id']
            if combined_data.get(q_id):
                combined_data[q_id].update(answer)
        result = list(combined_data.values())

        return result

    def get_quiz_to_update(self, limit: int = 1):
        """
        Fetches quizzes that need feedback and stores them in an instance variable.

        :param limit: The number of quizzes to fetch.
        """

        self.to_update_feedback_quizzes = self.get_quiz_to_update_query(limit=limit)
    
    def get_details_to_generate_feedback(self):
        """
        Fetches details of quizzes and user past performance to generate feedback.
        """
        if not self.to_update_feedback_quizzes:
            self.get_quiz_to_update()

        self.quiz_questions = {}
        self.to_update_quiz_details = {}
        self.users_past_performance = {}

        for quiz in self.to_update_feedback_quizzes:
            quiz_id = quiz['quiz_id']
            submission_id = quiz['submission_id']
            user_id = quiz['user_id']
            quiz_date = quiz['due_date']

            if not self.quiz_questions.get((self.course_id, quiz_id), False):
                self.quiz_questions[(self.course_id, quiz_id)] = self.get_question_answer_of_quiz_query(quiz_id)

            user_answers = self.get_user_answer_of_quiz_query(submission_id)

            self.to_update_quiz_details[submission_id] = self.combine_questions_and_answers(
                                                            self.quiz_questions[(self.course_id, quiz_id)], 
                                                            user_answers)

            history_feedback_quizzes = self.get_past_performance_query(user_id, quiz_date)

            self.users_past_performance[submission_id] = history_feedback_quizzes

    def generate_past_performance_template(self, data: dict, id: int) -> str:
        """
        Generates a template for past performance feedback.

        :param data: Dictionary containing past performance data.
        :param id: The submission ID.
        :return: Formatted past performance string.
        """
        if not data.get(id, False):
            return "Past Performance: Not Available."
        
        past_performance_template = """ 
                Past Performance: 
            """ 
        for index, quiz in enumerate(data[id]):
            quiz_id = quiz['quiz_id']
            quiz_date = str(quiz['due_date']) if quiz['due_date'] else "N/A"
            score = quiz['final_score'] if quiz['final_score'] else "N/A"
            total_score = quiz['total_score'] if quiz['total_score'] else "N/A"
            feedback = quiz['feedback']
            
            past_quiz_template = f""" 
                                    Quiz {index + 1}
                                    Past Quiz Date: {quiz_date}
                                    Past Score: {score} / {total_score}
                                    Past Feedback: {feedback}
                                """
            past_performance_template += past_quiz_template
        
        return past_performance_template
    
    def generate_current_quiz_template(self, quiz: dict, quiz_details: dict) -> str:
        """
        Generates a template for current quiz feedback.

        :param quiz: Dictionary containing current quiz data.
        :param quiz_details: Dictionary containing current quiz details.
        :return: Formatted current quiz string.
        """
        quiz_date = str(quiz['due_date']) if quiz['due_date'] else "N/A"
        quiz_id = quiz['quiz_id']
        submission_id = quiz['submission_id']
        score = quiz['final_score']
        total_score = quiz['total_score']

        Current_Quiz_Template = f"""
            Current Quiz Details: \
            Quiz Date: {quiz_date} \
            Quiz Id: {quiz_id} \
            Score: {score} / {total_score} \
            """
        
        for question in quiz_details[submission_id]:
            question_id = question['question_id']
            question_name = question['question_name']
            question_text = question['question_text']

            question_template = f""" 
            {question_id} | {question_name} : {question_text} \
            """

            Current_Quiz_Template += question_template

            for index, answer in enumerate(question['answer_choices']):
                answer_id = answer['answer_id']
                answer_text = answer['answer_text']
                weight = answer['weight']

                answer_template = f""" 
                    {index + 1} | Id: {answer_id} | Text: {answer_text} | Weight: {weight} \
                """

                Current_Quiz_Template += answer_template
        
            student_choice_template = f"""
                Student's Choice Id : {question.get('user_answer', 'Not Attempted')}
            """
            Current_Quiz_Template += student_choice_template

        return Current_Quiz_Template
    
    def generate_feedback(self) -> dict:
        """
        Generates feedback for quizzes and updates the database.

        :return: Dictionary containing the number of quizzes updated.
        """
        if not self.to_update_feedback_quizzes or not self.to_update_quiz_details:
            self.get_details_to_generate_feedback()
        
        updated = 0

        for quiz in self.to_update_feedback_quizzes:
            submission_id = quiz['submission_id']
            print(f"**************** - updated_submission_id {submission_id} - *****************")
            Current_Quiz_Template = self.generate_current_quiz_template(quiz, self.to_update_quiz_details)
            Past_Performance_Template = self.generate_past_performance_template(self.users_past_performance, submission_id)

            feedback_template = AutomatedFeedbackTemplate()
            prompt, _, _ = feedback_template.build()
            input = {
                    'current_quiz' : Current_Quiz_Template, 
                    'past_performance' : Past_Performance_Template
                }
            feedback = self.openai.generate_response(query=prompt.format(**input))

            # print(Current_Quiz_Template)
            # print(Past_Performance_Template)
            print(feedback)
            
            self.update_feedback(submission_id,feedback)
            updated += 1
        
        return feedback


# if __name__ == "__main__":
#     course_id = 395298
#     user_id = 1280512
#     qfg = QuizFeedbackGenerator(course_id=course_id)
#     qfg.get_quiz_to_update()
#     pprint(qfg.to_update_feedback_quizzes)

#     qfg.generate_feedback()
#     qfg.save_data()
