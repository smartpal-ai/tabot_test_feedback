from pinecone import Pinecone
import pandas as pd
from openai import OpenAI
import os
from langchain_openai import OpenAIEmbeddings
# from lib.templates import QueryResponseTemplate

class OpenAIChatResponse:
    def __init__(self, **kwargs):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI()
    
    def generate_response(self, query:str, model:str = "gpt-4o", max_token:int = 4000):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                model=model,
                max_tokens=max_token,
            )
            return chat_completion.choices[0].message.content
        except:
            print('Error generating response')
            return None
    
    def generate_summary(self, text:str, model:str = "gpt-4o", max_token:int = 4000):
        query = f"""
                    Please generate a detailed summary of the following text: {text}
                """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                model=model,
                max_tokens=max_token,
            )
            return chat_completion.choices[0].message.content
        except:
            print('Error generating response')
            return None

class OpenAIEmbedder:
    def __init__(self, model:str='text-embedding-ada-002', **kwargs):
        self.model = model  # can also be text-embedding-3-large        
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

        self.embedder = OpenAIEmbeddings(
            model=self.model,  #'text-embedding-ada-002'
            openai_api_key=self.openai_api_key,
            **kwargs
        )
        
    def get_embedder(self):
        return self.embedder
    
    def embed_query(self, query_text:str):
        return self.embedder.embed_query(query_text)
    
    def embed_documents(self, docs:list[str]):
        return self.embedder.embed_documents(docs)
    
class PineConeAPI:
    def __init__(self, logger):
        self.logger = logger
        self.pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        if self.pinecone_api_key is None:
            raise ValueError("PINECONE_API_KEY is not set in the environ")            
        
        self.index_name = os.environ.get("PINECONE_INDEX")       
        if self.index_name is None:
            raise ValueError("PINECONE_INDEX is not set in the environ")            
        
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pc.Index(self.index_name)
    
    def fetch_relevant_results(self, course_id:str, query:str,embedder = None, openai = None, filter:dict = {}, top_k:int = 3, summarized:bool = False, score_threshold:float = 0.5) -> pd.DataFrame:
        embedder = OpenAIEmbedder() if embedder is None else embedder
        openai = OpenAIChatResponse() if not openai else openai
        try:
            vector = embedder.embed_query(query)
            results = self.index.query(vector=vector, 
                            namespace=str(course_id),
                            filter=filter,
                            top_k=top_k,
                            include_metadata=True)

            if results['matches']:
                data = [match['metadata'] for match in results['matches'] if float(match['score']>=score_threshold)]
                df = pd.DataFrame(data)
                if 'Text' in df.columns:
                    # this command combines Text and text in the best way possible
                    df['text'] = df['Text'].combine_first(df['text'])
                    
                if summarized:
                    df['text'] = df['text'].apply(lambda x: openai.generate_summary(text=x))
                return df
            else:
                return None 
        except Exception as e:
            self.logger.error(f"Error occured during fetch relevant records during 'fetch_relevant_results': {e}")

    def fetch_response(self, course_id:str, query:str, embedder = None, openai = None,filter:dict = {}, top_k:int = 3, evidence:bool = True) -> str:      
        openai = OpenAIChatResponse() if not openai else openai
        df = self.fetch_relevant_results(course_id=course_id,query=query, embedder=embedder, filter=filter, top_k=top_k)

        self.logger.info("fetch_response was called.")

        try:
            if df is not None and len(df) > 0:
                relevant_info = '\n'.join(df['text'].to_list())
                query_response_template = QueryResponseTemplate()
                prompt, _, _ = query_response_template.build()
                input = {
                        'query' : query, 
                        'text' : relevant_info
                    }
                response = openai.generate_response(query=prompt.format(**input))

                if evidence:
                    return df.to_dict(orient='records'), response
                return response
            else:
                if evidence:
                    return None, None
                return None
            
        except Exception as e:
            self.logger.error(f"Error occured during generating response in fetch response: {e}")
            