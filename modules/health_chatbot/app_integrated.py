# modules/health_chatbot/app_integrated.py
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

load_dotenv()

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# Global variables
rag_chain = None
fallback_llm = None
memory = None

def initialize_chatbot():
    global rag_chain, fallback_llm, memory
    
    try:
        print("🤖 Initializing Health Chatbot...")
        
        # Get API keys
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        
        if not PINECONE_API_KEY or not GROQ_API_KEY:
            raise ValueError("Missing API keys")
        
        os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
        
        # Initialize embeddings
        print("📚 Loading embeddings...")
        embeddings = download_hugging_face_embeddings()
        
        # Connect to Pinecone
        index_name = "medical-chatbot"
        print(f"🔌 Connecting to Pinecone...")
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=index_name,
            embedding=embeddings
        )
        
        # Initialize LLM (same for both)
        print("🧠 Initializing Groq LLM...")
        llm = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            openai_api_key=GROQ_API_KEY,
            openai_api_base="https://api.groq.com/openai/v1",
            temperature=0.3,
            max_tokens=1000  # Increased for more detailed responses
        )
        
        # Store LLM for fallback
        fallback_llm = llm
        
        # RAG Prompt (for when we have context)
        rag_prompt = PromptTemplate(
            template="""You are an expert medical assistant with access to medical literature.
            Use the following context to answer the question thoroughly and accurately.
            
            Context from medical literature:
            {context}
            
            Question: {question}
            
            Provide a comprehensive answer based on the context. Include:
            1. Main answer with explanation
            2. Key points to remember
            3. Any precautions or warnings
            4. When to consult a doctor
            
            If the context doesn't fully answer the question, supplement with your medical knowledge
            but clearly indicate what comes from the context vs general knowledge.
            
            Answer:""",
            input_variables=["context", "question"]
        )
        
        # Create RAG chain that returns source documents
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type_kwargs={"prompt": rag_prompt},
            return_source_documents=True
        )
        
        print("✅ Chatbot ready with fallback capability!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def has_relevant_context(result):
    """Check if the RAG result actually used meaningful context"""
    # If no source documents were returned
    if not result.get('source_documents') or len(result['source_documents']) == 0:
        return False
    
    # Check if the answer indicates no information
    answer = result['result'].lower()
    no_info_phrases = [
        "don't have enough information",
        "doesn't contain",
        "no information",
        "not provided in the context",
        "context does not",
        "does not provide"
    ]
    
    for phrase in no_info_phrases:
        if phrase in answer:
            return False
    
    # Check if the answer is substantial (more than 2 sentences)
    sentences = answer.split('.')
    if len(sentences) < 3:
        return False
    
    return True

def get_fallback_answer(question):
    """Get answer directly from LLM with no context"""
    fallback_prompt = PromptTemplate(
        template="""You are a knowledgeable medical assistant. Answer the following question based on your general medical knowledge.
        Provide a detailed, helpful response while being careful to include appropriate disclaimers.
        
        Question: {question}
        
        Please provide:
        1. A comprehensive answer to the question
        2. Important facts and considerations
        3. When to seek professional medical help
        4. Any relevant precautions
        
        Note: This is general information. Always consult a healthcare provider for personal medical advice.
        
        Answer:""",
        input_variables=["question"]
    )
    
    response = fallback_llm.invoke(fallback_prompt.format(question=question))
    return response.content

initialized = initialize_chatbot()

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    if not initialized or rag_chain is None:
        return jsonify({'success': False, 'error': 'Chatbot not initialized'}), 500
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'No message'}), 400
        
        print(f"\n👤 User: {user_message}")
        print("🔍 Trying RAG with Pinecone...")
        
        # Try RAG first
        rag_result = rag_chain.invoke({"query": user_message})
        
        # Check if RAG gave a good answer
        if has_relevant_context(rag_result):
            print("✅ Using RAG answer (from medical PDFs)")
            response = rag_result['result']
            source_count = len(rag_result.get('source_documents', []))
            response += f"\n\n[Answer based on {source_count} medical sources from your PDF library]"
        else:
            print("⚠️ No good context in PDFs, using general medical knowledge")
            response = get_fallback_answer(user_message)
            response += "\n\n[Answer based on general medical knowledge - not found in your specific PDFs]"
        
        print(f"🤖 Response: {response[:150]}...")
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'initialized': initialized})

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(chatbot_bp)
    print("🚀 Server starting on port 5002...")
    app.run(host="0.0.0.0", port=5002, debug=True)