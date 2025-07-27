from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain

def summarize_manifest(data, api_key):
    prompt = PromptTemplate(
        input_variables=["data"],
        template="""You are a logistics assistant. Summarise this manifest dataset with a short overview:
{data}
Give:
- Total number of shipments
- How many are delayed or in transit
- Breakdown of carriers
- Any useful trends or anomalies"""
    )
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=api_key)
    chain = prompt | llm
    result = chain.invoke({"data": data})
    return result.content if hasattr(result, "content") else str(result)

def answer_question(documents, question, api_key):
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=api_key)
    chain = load_qa_chain(llm, chain_type="stuff")
    return chain.run(input_documents=documents, question=question)
