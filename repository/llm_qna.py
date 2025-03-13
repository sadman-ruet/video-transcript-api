from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch  # Updated import
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document
import time
import os
from dotenv import load_dotenv
load_dotenv()

# Function to split the input document(s) into chunks
def split_text(docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500)
    return text_splitter.split_documents([Document(page_content=doc) for doc in docs])

# Define the embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Function to create a retrieval chain for Q&A
def create_qa_chain(docs, num_questions=3):
    # Split documents into chunks
    split_docs = split_text(docs)

    # Create a vectorstore from the documents and their embeddings
    vectorstore = DocArrayInMemorySearch.from_documents(
        split_docs,
        embedding=embeddings  # Use the correct embedding model
    )

    # Create a retriever to fetch relevant documents based on a query
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={'k': 5})

    # Initialize the LLM (Chat model)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.3, max_tokens=768)

    # System prompt template for the Q&A process
    system_prompt = (
        "You are a Question and Answer Making Assistant. "
        "Use the retrieved context along with your own knowledge to create {num_questions} questions and answers. "
        "If unsure about context, say you can't provide question and answer. Keep responses concise, organized, and clean."
        "\n\n"
        "{context}"
    )

    # Create the prompt template for Q&A with dynamic num_questions
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Create {num_questions} questions with answers from the following context: {input}"),
    ])

    # Create a chain to handle documents and question generation
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # Generate the specified number of questions and answers
    results = rag_chain.invoke({"input": "Create questions and answers", "num_questions": num_questions})

    # Extract only the answer part from the results
    answer = results.get('answer', '')  # Get the answer from the results

    return answer

# Example usage
# docs = [
#     " If you work in tech or in anything adjacent to tech, you've probably heard the abbreviation  API being thrown around. So let's talk about APIs. What are they and why do we need them?  Let's start with what is an API? API stands for Application Programming Interface.  Fancy words, so let's break it down. Application in this context just means any software that has  a specific functionality or purpose. Interface refers to a contract or a protocol that dictates  how two applications talk to each other using requests and responses. So put together, an API  is simply a way for different systems or applications to communicate with each other.  Okay, cool in theory. So why do we need APIs? Let's start with a non-technical analogy first.  Let's say you have a dinner reservation for tonight for three people, but you want to change  it to six because some friends decided to join you at the last minute. So you call the restaurant,  ask them if it's possible to do that, and the customer service person puts you on hold.  It takes a minute, but they finally come back and they say, yes, simple. You called someone,  made a request, and you got a response, yes or no. Now let's say that there was no customer service  person and that it was up to you to figure out how many people have made reservations for the same  time at this restaurant. How many tables do they have free at that time? What's their kitchen  capacity? What's their waitstaff capacity? All to figure out whether you can add three more people  to your reservation. That's a lot of unnecessary work on your part, work that you, the customer,  have no expertise in. And it means that the restaurant has to reveal a lot of data to you,  maybe even private data about who's eating there that night and who works there, etc.  In this analogy, the restaurant is an application that provides a specific service or function,  which is to feed you. You are an application that is trying to get fed with a group of friends.  The customer service rep from the restaurant is the restaurants API. That is the interface through  which you can communicate with the restaurant and make requests like changing the number on a  reservation. And you can do that without having to dive into the messy details about how restaurant  reservations work or anything like that. For a more technical example now, think about Apple's  weather app. Do we think that Apple decided to set up weather monitoring stations around the  world? That's a really expensive endeavor. And if it was super critical to Apple's business model,  then maybe sure, we could we could see that happening. But there are already services out  there that meticulously collect global weather data services like weather.com. So if weather.com  creates an API through which anybody can access their data, but only in the ways that weather.com  allows, then Apple could just use that API to populate their weather app. So how do APIs  actually work? Let's use the example of web APIs, which are the type of APIs that deliver client  requests and return responses via JSON or XML, usually over the internet. Each request and  response cycle is an API call. A request typically consists of a server endpoint URL and a request  method, usually through HTTP or hypertext transfer protocol. The request method indicates  the desired API action. The HTTP response contains a status code, a header and a response body. The  response body varies depending on the request and it could be the server resource a client needs to  access or any application specific messages. One status code you might be familiar with when you've  tried to visit a website that might be down or doesn't exist anymore is the error 404 code URL  not found. And that's it request response. To get more in depth about APIs and the various different  types that exist, I encourage you to check out the exponent article linked in the description below.  Good luck with your interviews and thanks for watching."
#     ]
#
# # Generate 3 questions and answers
# output = create_qa_chain(docs, num_questions=3)
# print(output)
