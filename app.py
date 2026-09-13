import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.chat_models import ChatOpenAI
# from langchain.embeddings import HuggingfaceInstructEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css,bot_template,user_template
import requests


ESCALATION_KEYWORDS = [
    "still not working", "tried twice", "already tried", "not resolved",
    "keeps happening", "still broken", "won't reset", "doesn't work", "escalate"
]

# def is_escalation(text):
#     text = text.lower()
#     return any(kw in text for kw in ESCALATION_KEYWORDS)
def is_escalation(user_question):
    classifier_llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    prompt = (
        "A maintenance technician sent this message. Does it indicate an "
        "unresolved issue that needs to be escalated as a ticket (e.g. they "
        "already tried the fix and it didn't work)? Answer with exactly one "
        "word: YES or NO.\n\n"
        f"Message: \"{user_question}\"\n"
        "Answer:"
    )
    response = classifier_llm.invoke(prompt)
    return response.content.strip().upper().startswith("YES")

def log_ticket(issue, urgency="HIGH"):
    try:
        response = requests.post(
            "http://localhost:5000/tickets",
            json={"issue": issue, "urgency": urgency},
            timeout=5
        )
        return response.json()
    except requests.RequestException as e:
        return {"status": "error", "detail": str(e)}

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader=PdfReader(pdf)
        for page in pdf_reader.pages:
            text+= page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter= CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks=text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks):
    # embeddings= HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore= FAISS.from_texts(texts=text_chunks,embedding=embeddings)
    return vectorstore
    
def get_conversation_chain(vectorstore):
    llm= ChatGoogleGenerativeAI(model="gemini-flash-latest",temperature=0.7)
    memory = ConversationBufferMemory(memory_key='chat_history',return_messages=True)
    conversation_chain= ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
         
    )
    return conversation_chain

# def handle_userinput(user_question):
#      response = st.session_state.conversation({'question':user_question})
#      st.session_state.chat_history = response['chat_history']

#      for i, message in enumerate(st.session_state.chat_history):
#         if i%2==0:
#             st.write(user_template.replace("{{MSG}}",message.content),unsafe_allow_html=True)
#         else:
#              st.write(bot_template.replace("{{MSG}}",message.content),unsafe_allow_html=True)


def handle_userinput(user_question):
    if st.session_state.conversation is None:
        st.warning("Please upload and process your documents first.")
        return

    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)

    if is_escalation(user_question):
        result = log_ticket(issue=user_question, urgency="HIGH")
        if result.get("status") == "logged":
            st.success(f"🎫 Ticket {result['ticket']['ticket_id']} logged (urgency: HIGH)")
        else:
            st.error("Could not reach ticket API — is ticket_api.py running?")
def main(): 
    load_dotenv()
    st.set_page_config(page_title="MaintAI",page_icon="🔧")


    st.write(css,unsafe_allow_html=True)
    if "conversation" not in st.session_state:
        st.session_state.conversation=None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history=None


    st.header("Chat with sources 🔧")
    user_question=st.text_input("Ask a question about your documents: ")
    if user_question:
        handle_userinput(user_question)

    # st.write(user_template.replace("{{MSG}}","Hello Robot"),unsafe_allow_html=True)
    # st.write(bot_template.replace("{{MSG}}","Hello Human"),unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Your Documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on Process", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text

                raw_text = get_pdf_text(pdf_docs)

                #get the text chunks
                text_chunks = get_text_chunks(raw_text)
            

               #create a vector store
                vectorstore= get_vectorstore(text_chunks)

               #create conversation chain
                st.session_state.conversation= get_conversation_chain(vectorstore)

               



                
            
if __name__ == '__main__':
    main()