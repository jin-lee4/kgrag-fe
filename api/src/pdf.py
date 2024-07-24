import uuid

from typing import Optional

from langchain.text_splitter import TokenTextSplitter

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader

from langchain_openai import OpenAIEmbeddings

class PDF:
  """
    A PDF is a fancy UUID that stores extra information 
    and can generate its own embeddings
  """

  def __init__(self, uuid: uuid.UUID, name: str, handle: Optional[str] = None):
    self.uuid = uuid
    self.name = name
    self.handle = handle

  async def generate_embeddings(self):
    raw_documents = await PyPDFLoader(self.handle).aload()

    # chunk and split
    text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
    documents = text_splitter.split_documents(raw_documents)

    # generate in memory representation
    chroma = await Chroma.afrom_documents(
      documents,
      OpenAIEmbeddings(),
    )

    retriever = chroma.as_retriever(
      search_type="similarity_score_threshold",
      search_kwargs={
        "k": 4,
        "score_threshold": 0.4,
      },
    )

    return retriever

class PDFStore:
  def __init__(self, embeddings):
    self.embeddings = embeddings