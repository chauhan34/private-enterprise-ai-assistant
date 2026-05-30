import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

st.title("Compliance AI Assistant")

st.write(
    "Private enterprise compliance knowledge assistant"
)

uploaded_file = st.file_uploader(
    "Upload a policy PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    st.success(
        f"Uploaded file: {uploaded_file.name}"
    )

    # Read PDF
    document_text = ""

    pdf_reader = PdfReader(uploaded_file)

    for page in pdf_reader.pages:

        extracted = page.extract_text()

        if extracted:

            document_text += extracted

    # Create chunks
    chunk_size = 1000

    chunks = []

    for i in range(
        0,
        len(document_text),
        chunk_size
    ):

        chunk = document_text[i:i+chunk_size]

        chunks.append(chunk)

    st.write(
        f"Created {len(chunks)} chunks"
    )

    # Load embedding model
    model = SentenceTransformer(
        'all-MiniLM-L6-v2'
    )

    embeddings = model.encode(chunks)

    # Create vector DB
    client = chromadb.Client()

    collection = client.get_or_create_collection(
        name="compliance_docs"
    )

    # Clear previous data
    try:

        existing = collection.get()

        if existing['ids']:

            collection.delete(
                ids=existing['ids']
            )

    except:

        pass

    # Store chunks
    for i, chunk in enumerate(chunks):

        collection.add(
            documents=[chunk],
            embeddings=[embeddings[i].tolist()],
            ids=[str(i)]
        )

    question = st.text_input(
        "Ask a compliance question"
    )

    if st.button("Submit Question"):

        # Semantic retrieval
        results = collection.query(
            query_texts=[question],
            n_results=5
        )

        context = "\n".join(
            results['documents'][0]
        )

        # Build AI prompt
        prompt = f"""
        You are a compliance AI assistant.

        Answer ONLY using the provided context.

        Context:
        {context}

        Question:
        {question}
        """

        # Call local LLM
        response = ollama.chat(
            model='llama3',
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )

        st.subheader("AI Answer")

        st.write(
            response['message']['content']
        )

        st.subheader("Retrieved Context")

        st.write(context)

else:

    st.info(
        "Please upload a PDF document."
    )