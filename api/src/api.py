import os
import json
import uuid
import logging
import io

from typing import Tuple, List, Optional
from google.cloud import vision

from pydantic import BaseModel, Field

from langchain.chains import RetrievalQA
from langchain.agents import AgentExecutor, create_openai_tools_agent

from langchain_core.runnables import (
  RunnableBranch,
  RunnableLambda,
  RunnableParallel,
  RunnablePassthrough,
)
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts.prompt import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
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
from fastapi.responses import JSONResponse

from database import postgres_db, get_pg_conn
from upload import UploadManager
from embedding import EmbeddingManager
from pdf import PDF, PDFStore

model_name = os.environ["MODEL_NAME"]
# remapping for langchain neo4j integration
os.environ["NEO4J_URL"] = os.environ["NEO4J_URI"]


service_account_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
print(f"service account key: {service_account_key}")

# Initialize the Google Cloud Vision client
print("Initializing Google Cloud Vision client...")
vision_client = vision.ImageAnnotatorClient.from_service_account_json('/app/credentials/credentials.json')


llm = ChatOpenAI(model_name=model_name)

# TODO: make all the neo4j async
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
{"- Document ". join(unstructured_data)}
  """
  return final_data

###########
### API ###
###########

# configure logging -> TODO refactor to other file for universal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# configure file uploads, top-level dir of /uploads
upload_manager = UploadManager(upload_dir="/uploads")

# configure embedding management
embedding_manager = EmbeddingManager()

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

class DocumentInput(BaseModel):
  question: str = Field(description="question for retrieval chain")

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
  if pdf.handle is None:
    raise HTTPException(status_code=400, detail="Invalid PDF, please reupload")

  pdf_store = await embedding_manager.get_embeddings(pdf)

  tools = [
    Tool(
      args_schema=DocumentInput,
      name="knowledge_base",
      description=f"useful for comparing against documents",
      func=retriever,
    ),
    Tool(
      args_schema=DocumentInput,
      name="uploaded_document",
      description=f"useful when you want to answer questions about the current document",
      func=RetrievalQA.from_chain_type(llm=llm, retriever=pdf_store.embeddings),
    )
  ]

  prompt = ChatPromptTemplate.from_messages(
    [
      ("system", "You are a helpful assistant"),
      MessagesPlaceholder("chat_history", optional=True),
      ("human", "{input}"),
      MessagesPlaceholder("agent_scratchpad"),
    ]
  )
  agent = create_openai_tools_agent(llm, tools, prompt)
  agent_executor = AgentExecutor(agent=agent, tools=tools)

  def convert_to_chat_history(pairs):
    if pairs is None:
      return []
    chat_history = []
    for pair in pairs:
      human_msg = HumanMessage(content=pair[0])
      ai_msg = AIMessage(content=pair[1])
      chat_history.extend([human_msg, ai_msg])
    return chat_history

  response = await agent_executor.ainvoke(
    {
      "input": request.question,
      "chat_history": convert_to_chat_history(request.chat_history),
    }
  )

  logger.info(f"Received request: {response}")

  return {"response": response["output"]}

# OCR function to extract text from PDF
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as image_file:
        content = image_file.read()
    logging.info("Sending file to google vision API for text detection.")
    image = vision.Image(content=content)
    response = vision_client.document_text_detection(image=image)
    texts = response.full_text_annotations

    logging.info(f"Google vision API response: {response}")

    extracted_text = ""
    for text in texts:
        extracted_text += text.description + "\n"

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(response.error.message))

    return extracted_text

class AnalysisRequest(BaseModel):
  text: str = Field(..., description="The text to be analyzed")
  modes: List[str] = Field(..., description="List of analysis modes to apply")


@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")
    
    try:
        logger.info(f"Received file: {file.filename}")
        contents = await file.read()
        text = extract_text_from_pdf(contents)
        response = {
            "uuid": str(file.filename),
            "text": text
        }
        logger.info(f"Extracted text: {text}")  # Log extracted text for debugging
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    # pdf = PDF(uuid.uuid4(), file.filename)
    # response = await upload_manager.upload(conn, pdf, contents)
    # extracted_text = extract_text_from_pdf(response)
    # return JSONResponse(content={'uuid': pdf_uuid, 'text': extracted_text}, status_code=200)
  # return {"uuid": response}


# @app.post("/analyze/")
# async def analyze_text(request: AnalysisRequest):
#   text= request.text
#   modes = request.modes

#   prompts = {
#       "Analyze": "Analyze the following text and provide suggestions for improvement. Consider gaps, relevant considerations and implications of the policies.",
#       "Compare": "Compare the following text with industry standards, governmental policies, and other relevant sources.",
#       "Clarify": "Identify ambiguities and inconsistencies in the text.",
#   }

#   results = []

#   for mode in modes:
#       if mode in prompts:
#           prompt_template = PromptTemplate(template=prompts[mode] + "\n\n{text}", input_variables=["text"])
#           chain = load_qa_chain(llm, prompt_template)
#           response = chain.run({"text": text})
#           suggestions = response.strip()
#           results.append({"mode": mode, "suggestions": suggestions})

#   return JSONResponse(content={"results": results}, status_code=200)

@app.on_event("startup")
async def on_startup():
  await postgres_db.connect()

@app.on_event("shutdown")
async def on_shutdown():
  await postgres_db.disconnect()