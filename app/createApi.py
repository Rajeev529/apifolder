import os
import uuid
import asyncio
import json

from project.settings import llm
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from app.models import API, user_data
from langchain_core.prompts import PromptTemplate
from openai import OpenAI

from dotenv import load_dotenv
from .models import API, Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# ✅ Replace this line
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# ✅ With the new import
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ✅ Replace this line
# embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
# ✅ With the new embedding object, specifying a Hugging Face model
# embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")


load_dotenv()
client = OpenAI(
    api_key=os.getenv("ppxapi"),
    base_url="https://api.perplexity.ai"
)

# 🔹 Choose model here
model = "sonar-pro"   # sonar, sonar-pro, sonar-reasoning, etc.

# Pricing table (USD per 1M tokens)
prices = {
    "sonar": {"in": 1, "out": 1},
    "sonar-pro": {"in": 3, "out": 15},
    "sonar-reasoning": {"in": 1, "out": 5},
    "sonar-reasoning-pro": {"in": 2, "out": 8},
    "sonar-deep-research": {"in": 2, "out": 8},  # citations/reasoning need extra handling
}



def create_api(request):
    if request.method == 'POST':
        name = request.POST['name']
        desc = request.POST['desc']
        key1 = request.POST['key1']
        val1 = request.POST['val1']
        key2 = request.POST['key2']
        val2 = request.POST['val2']
        key3 = request.POST['key3']
        val3 = request.POST['val3']

        files = request.FILES.getlist('files')

        # create api key
        api_key = str(uuid.uuid4())
        retr_path = os.path.join("vectorstores", api_key)
        os.makedirs(retr_path, exist_ok=True)

        # ✅ ensure uploads folder exists
        uploads_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        docs = []
        for f in files:
            file_path = os.path.join(uploads_dir, f.name)
            with open(file_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            docs.append({
                "filename": f.name,
                "file_path": file_path,
                "file_type": f.content_type,
            })

        # Load documents
        lang_docs = []
        for d in docs:
            if d["file_type"].endswith("pdf"):
                lang_docs.extend(PyPDFLoader(d["file_path"]).load())
            elif d["file_type"].endswith("docx"):
                lang_docs.extend(Docx2txtLoader(d["file_path"]).load())

        if not lang_docs:
            return JsonResponse({"error": "No documents loaded"}, status=400)

        # Split
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(lang_docs)

        if not chunks:
            return JsonResponse({"error": "No chunks created"}, status=400)

        # Fix asyncio loop issue
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        # Build FAISS
        # ✅ Use the global `embedding` object initialized with Hugging Face
        db = FAISS.from_documents(chunks, embedding)
        db.save_local(retr_path)

        # ✅ create API object (needs actual logged-in user)
        # Replace this with your actual user instance
        username=request.session.get('username')
        print(username)
        user_instance = user_data.objects.get(username=username)  # ⚠️ just an example
        api = API.objects.create(
            user=user_instance,
            name=name,
            desc=desc,
            api_key=api_key,
            retriever_path=retr_path,
            key1=key1, val1=val1,
            key2=key2, val2=val2,
            key3=key3, val3=val3
        )

        # ✅ save Document objects properly
        for d in docs:
            Document.objects.create(
                api=api,
                filename=d["filename"],
                file_path=d["file_path"],
                file_type=d["file_type"]
            )

        return JsonResponse({"apikey": api_key})

    return JsonResponse({"message": "internal fault"})


@csrf_exempt
def answer(request, apiKey):
    api={}
    key=API.objects.get(api_key=apiKey)
    user=user_data.objects.get(id=key.user_id)
    # user= user_data.objects.get(username=request.session.get('username'))
    if( user.balance<=0):
        return JsonResponse({"error": "recharge your balance"})
    if request.method == 'POST':
        try:
            api = API.objects.get(api_key=apiKey)
            print(api)
        except API.DoesNotExist:
            return JsonResponse({"error": "Invalid API key"}, status=404)

        try:
            data = json.loads(request.body)
            q = data.get("query")
            res = analyze(q, api, user)
            return JsonResponse(res, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)

def analyze(q, api, user):
    # ✅ Use the global `embedding` object initialized with Hugging Face
    db = FAISS.load_local(api.retriever_path, embedding, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()

    prompt = PromptTemplate(
        template="""
        You are an AI assistant specialized in analyzing provided context.
        Answer based ONLY on the given context. If the user asks out of context,
        reply: "Sorry, I can't answer it. Please ask an appropriate question."

        {desc}

        Format your final response as JSON:
        {{
            "{key1}": "{val1}",
            "{key2}": "{val2}",
            "{key3}": "{val3}",
        }}

        <context>
        {context}
        </context>

        User's Query: {input}
        """,
        input_variables=["context", "input", "desc", "key1", "val1", "key2", "val2", "key3", "val3"],
    )

    parser = JsonOutputParser()

    rag_chain = (
        {
            "context": retriever | (lambda docs: "\n\n".join([d.page_content for d in docs])),
            "input": RunnablePassthrough(),
            "desc": lambda _: api.desc,
            "key1": lambda _: api.key1,
            "val1": lambda _: api.val1,
            "key2": lambda _: api.key2,
            "val2": lambda _: api.val2,
            "key3": lambda _: api.key3,
            "val3": lambda _: api.val3,
        }
        | prompt
        | llm
        | parser
    )

    ans = rag_chain.invoke(q)

    # Call Perplexity only if you want *their* model to refine answer
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": json.dumps(ans)}
        ]
    )

    usage = response.usage
    prompt_tokens, completion_tokens = usage.prompt_tokens, usage.completion_tokens

    # Cost calculation
    model_price = prices.get(model, {"in": 0, "out": 0})
    cost = ((prompt_tokens * model_price["in"] + completion_tokens * model_price["out"]) / 1_000_000) * 88

    # Update balance
    newbal = float(user.balance) - cost
    user.balance = newbal
    user.save()

    return ans
