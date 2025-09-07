# views.py
import os
import uuid
import asyncio
import json
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from dotenv import load_dotenv
from django.core.files.storage import FileSystemStorage

from app.models import user_data, chats, Document2
from project.settings import llm
from googletrans import Translator

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")


def embed(request):
    if request.method == 'POST':
        lang = request.POST['language']
        files = request.FILES.getlist('files')
        name = request.POST['name']

        # create api key
        api_key = str(uuid.uuid4())
        retr_path = os.path.join("vectorstores", api_key)
        os.makedirs(retr_path, exist_ok=True)

        # ensure uploads folder exists
        uploads_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        fs = FileSystemStorage(location=uploads_dir)

        docs = []
        for f in files:
            file_path = fs.save(f.name, f)
            full_path = fs.path(file_path)

            docs.append({
                "filename": f.name,
                "file_path": full_path,
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

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(lang_docs)
        if not chunks:
            return JsonResponse({"error": "No chunks created"}, status=400)

        # Fix asyncio loop issue
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        # Build FAISS index
        db = FAISS.from_documents(chunks, embedding)
        db.save_local(retr_path)

        # get current logged-in user from session
        username = request.session.get('username')
        user_instance = user_data.objects.get(username=username)

        # create chat object
        chat = chats.objects.create(
            user=user_instance,
            retriever_path=retr_path,
            lang=lang,
            name=name,   # ✅ fixed typo
            data={
                'q': [],
                'a': []   # ✅ lowercase for consistency
            },
            api_key=api_key
        )

        # save uploaded document entries
        for d in docs:
            Document2.objects.create(
                api=chat,
                filename=d["filename"],
                file_path=d["file_path"],
                file_type=d["file_type"]
            )

        return redirect(f'/advocate/{api_key}/')

    return JsonResponse({"message": "Invalid request"}, status=400)


from django.http import JsonResponse
from deep_translator import GoogleTranslator

def chatbot(request):
    if request.method == "GET":
        key = request.GET['api']
        q = request.GET['q']

        api = chats.objects.get(api_key=key)
        data = api.data
        print(data)
        db = FAISS.load_local(api.retriever_path, embedding, allow_dangerous_deserialization=True)
        retriever = db.as_retriever()

        prompt = PromptTemplate(
            template="""
            You are a senior contracts lawyer. When given a legal document or a user question about it, produce:
            return find keys from user query ans each keys return 3 key value pair with json response

            <context>
            {context}
            </context>

            User's Query: {input}
            """,
            input_variables=["context", "input"],
        )

        parser = JsonOutputParser()

        rag_chain = (
            {
                "context": retriever,
                "input": RunnablePassthrough()
            }
            | prompt
            | llm
            | parser
        )

        # get language from DB
        lang = api.lang
        print("Language:", lang)

        # get JSON answer
        ans = rag_chain.invoke(q)
        
        data['q'].append(q)
        data['a'].append(ans)
        # save history if needed
        api.data = data
        api.save(update_fields=["data"])
        
        print("Original:", ans)
        if lang=='en':
            return JsonResponse(ans, safe=False)
        # ✅ recursive translation
        def translate_json(data, lang):
            if isinstance(data, dict):
                return {k: translate_json(v, lang) for k, v in data.items()}
            elif isinstance(data, list):
                return [translate_json(i, lang) for i in data]
            elif isinstance(data, str):
                return GoogleTranslator(source="auto", target=lang).translate(data)
            else:
                return data

        translated = translate_json(ans, lang)
        print("Translated:", translated)


        return JsonResponse(translated, safe=False)

    return JsonResponse({"error": "Invalid request"}, status=400)

