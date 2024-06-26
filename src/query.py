import os
from dotenv import load_dotenv
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_mongodb import MongoDBAtlasVectorSearch
from src.utils import get_mongo_collection


def vector_search(ticker, query):
    '''
    Performs vector search on MongoDB Atlas vector store to retrieve relevant embeddings
    while filtering results based on ticker specified.
    Uses OpenAI's gpt-3.5-turbo to generate a response given the retrieved embeddings.

    Args:
        ticker (str): The stock ticker (e.g. AAPL) specified for filtering.
        query (str): The question inputted by the user.

    Returns:
        retriever_output (str): The chatbot's answer.
    '''
    load_dotenv()
    ATLAS_VECTOR_SEARCH_INDEX_NAME = os.getenv("ATLAS_VECTOR_SEARCH_INDEX_NAME")
    collection = get_mongo_collection()

    # Define the filter based on the metadata field and value
    vector_search = MongoDBAtlasVectorSearch(
        embedding=OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY")),
        collection=collection,
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    )

    llm = OpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )
    
    retriever = vector_search.as_retriever()
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
    )
    
    # Inject ticker into query to filter documents
    retriever_output = qa.invoke({"query": ticker + ": " + query})["result"]
    return retriever_output.replace("$", "\$") # Escape dollar signs to prevent LaTeX rendering issues
    
if __name__ == "__main__":
    print(vector_search("AAPL", "How much did Americas net sales decrease in 2023 compared to Europe?"))