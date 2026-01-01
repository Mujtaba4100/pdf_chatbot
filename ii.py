from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import google.generativeai as genai
import PyPDF2

genai.configure(api_key="AIzaSyDDPSmnK_ybvO63uLkF8GMWqu0CNAUXzTI")
model_gemini=genai.GenerativeModel("gemini-2.5-flash")

def chunk_text_overlap(text,chunk_size=200,overlap_size=50):
  words=text.split()
  chunks=[]
  start=0
  while start<len(words):
    end=start+chunk_size
    chunk=" ".join(words[start:end])
    chunks.append(chunk)
    start+=chunk_size-overlap_size
  return chunks

def extract_chunk_from_pdfs(pdf_paths,chunk_size=200,overlap_size=50):
  all_chunks=[]
  for path in pdf_paths:
    with open(path,"rb") as f:
      reader=PyPDF2.PdfReader(f)
      for page_num,page in enumerate(reader.pages):
        text=page.extract_text()
        if not text:
          continue
        page_chunks=chunk_text_overlap(text,chunk_size,overlap_size)
        for chunk in page_chunks:
          all_chunks.append(
              {
                  "text":chunk,
                  "page":page_num+1,
                  "source":path
              }
          )
  return all_chunks

pdf_paths=["./04072213019_Ass1.pdf","./AI_DMS.pdf","./FYP_PROPOSAL.pdf","./installGuideWindows.pdf"]
chunks = extract_chunk_from_pdfs(pdf_paths)

texts=[c["text"] for c in chunks]
metadata=chunks

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embed_model.encode(texts)

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings).astype("float32"))

print("FAISS index ready for multiple PDFs!")


def ask_multi_pdf(query,top_k=2):
  query_embedding=embed_model.encode([query]).astype("float32")
  distances,indices=index.search(query_embedding,k=top_k)
  context=""
  sources=[]
  for i in indices[0]:
    context+=texts[i]+"\n"
    sources.append(f"{metadata[i]['source']} (page {metadata[i]['page']})")

  prompt= f"""
You are an assistant. Use ONLY the context below to answer the question.
Do not invent any information that is not in the context.
You may summarize, reformat, or combine information from the context to make your answer clear.

Context:
{context}

Question:
{query}

Answer:
"""
  responce=model_gemini.generate_content(prompt)
  return responce.text,list(set(sources))


print("Type 'exit' to quit")
while True:
    q = input("Ask PDFs: ")
    if q.lower() == "exit":
        break
    answer, sources = ask_multi_pdf(q)
    print("Answer:", answer)
    print("Sources:", sources)
