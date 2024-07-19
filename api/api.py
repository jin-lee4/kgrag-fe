import os
import json
import uuid
import logging

from typing import Tuple, List, Optional

from pydantic import BaseModel

from langchain_core.runnables import (
  RunnableBranch,
  RunnableLambda,
  RunnableParallel,
  RunnablePassthrough,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from database import postgres_db, get_pg_conn

from upload import UploadManager
from embedding import EmbeddingManager
from pdf import PDF, PDFStore

model_name = os.environ["MODEL_NAME"]
# remapping for langchain neo4j integration
os.environ["NEO4J_URL"] = os.environ["NEO4J_URI"]

llm = ChatOpenAI(model_name=model_name)

graph = Neo4jGraph()

vector_index = Neo4jVector.from_existing_graph(
  OpenAIEmbeddings(),
  search_type="hybrid",
  node_label="Document",
  text_node_properties=["text"],
  embedding_node_property="embedding"
)

graph.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")

# Extract entities from text
class Entities(BaseModel):
  """Identifying information about entities."""

  names: List[str] = Field(
    ...,
    description="All the person, organization, or business entities that "
    "appear in the text",
  )

prompt = ChatPromptTemplate.from_messages(
  [
    (
      "system",
      "You are extracting organization and person entities from the text.",
    ),
    (
      "human",
      "Use the given format to extract information from the following "
      "input: {question}",
    ),
  ]
)

entity_chain = prompt | llm.with_structured_output(Entities)

def generate_full_text_query(input: str) -> str:
  """
  Generate a full-text search query for a given input string.

  This function constructs a query string suitable for a full-text search.
  It processes the input string by splitting it into words and appending a
  similarity threshold (~2 changed characters) to each word, then combines
  them using the AND operator. Useful for mapping entities from user questions
  to database values, and allows for some misspelings.
  """
  full_text_query = ""
  words = [el for el in remove_lucene_chars(input).split() if el]
  for word in words[:-1]:
    full_text_query += f" {word}~2 AND"
  full_text_query += f" {words[-1]}~2"
  return full_text_query.strip()

# Fulltext index query
def structured_retriever(question: str) -> str:
  """
  Collects the neighborhood of entities mentioned
  in the question
  """
  result = ""
  entities = entity_chain.invoke({"question": question})
  for entity in entities.names:
    response = graph.query(
      """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
      YIELD node,score
      CALL {
        WITH node
        MATCH (node)-[r:!MENTIONS]->(neighbor)
        RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
        UNION ALL
        WITH node
        MATCH (node)<-[r:!MENTIONS]-(neighbor)
        RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
      }
      RETURN output LIMIT 50
      """,
      {"query": generate_full_text_query(entity)},
    )
    result += "\n".join([el['output'] for el in response])
  return result

def retriever(question: str):
  #print(f"Search query: {question}")
  structured_data = structured_retriever(question)
  unstructured_data = [el.page_content for el in vector_index.similarity_search(question)]
  final_data = f"""Structured data:
{structured_data}
Unstructured data:
{"#Document ". join(unstructured_data)}
  """
  return final_data

# Condense a chat history and follow-up question into a standalone question
_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question,
in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""  # noqa: E501
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
  buffer = []
  for human, ai in chat_history:
    buffer.append(HumanMessage(content=human))
    buffer.append(AIMessage(content=ai))
  return buffer

_search_query = RunnableBranch(
  # If input includes chat_history, we condense it with the follow-up question
  (
    RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
      run_name="HasChatHistoryCheck"
    ),  # Condense follow-up question and chat into a standalone_question
    RunnablePassthrough.assign(
      chat_history=lambda x: _format_chat_history(x["chat_history"])
    )
    | CONDENSE_QUESTION_PROMPT
    | ChatOpenAI(temperature=0)
    | StrOutputParser(),
  ),
  # Else, we have no chat history, so just pass through the question
  RunnableLambda(lambda x : x["question"]),
)

template = """Answer the question based only on the following context:
{context}

Question: {question}
Use natural language and be concise.
Answer:"""
prompt = ChatPromptTemplate.from_template(template)

chain = (
  RunnableParallel(
    {
      "context": _search_query | retriever,
      "question": RunnablePassthrough(),
    }
  )
  | prompt
  | llm
  | StrOutputParser()
)

result = chain.invoke(
  {
    "question": "When was she born?",
    "chat_history": [("Which house did Elizabeth I belong to?", "House Of Tudor")],
  }
)
print("result is: " + result)

###########
### API ###
###########

# configure logging -> TODO refactor to other file for universal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# configure file uploads, top-level dir of /uploads
upload_manager = UploadManager(upload_dir="/uploads")

# configure app
app = FastAPI(root_path="/api/v1")
origins = ["*"]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/")
async def root():
  return {"message": "Hello World"}

class QueryRequest(BaseModel):
  uuid: str
  question: str
  chat_history: Optional[List[Tuple[str, str]]] = None

@app.get("/query/")
async def query(request: QueryRequest = Depends(), conn = Depends(get_pg_conn)):
  logger.info(f"Received request: {request.json()}")

  try:
    query_uuid = uuid.UUID(request.uuid)
  except ValueError:
    raise HTTPException(status_code=400, detail="Invalid UUID")

  pdf = await upload_manager.fetch(conn, query_uuid)

  """
  if request.chat_history is None:
    response = chain.invoke({
      "question": request.question,
    })
  else:
    response = chain.invoke({
      "question": request.question,
      "chat_history": request.chat_history,
    })
  """

  if pdf.handle is None:
    raise HTTPException(status_code=400, detail="Invalid Handle")
  
  return {"response": pdf.handle}

@app.post("/upload/")
async def upload(file: UploadFile = File(...), conn = Depends(get_pg_conn)):
  if file.content_type != "application/pdf":
    raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")

  contents = file.file.read()
  if len(contents) > 10 * 1024 * 1024:  # 10MB
    raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

  pdf = PDF(uuid=uuid.uuid4(), name=file.filename)
  uuid = await upload_manager.upload(conn, pdf, contents)

  return {"uuid": uuid}

@app.on_event("startup")
async def on_startup():
  await postgres_db.connect()

@app.on_event("shutdown")
async def on_shutdown():
  await postgres_db.disconnect()