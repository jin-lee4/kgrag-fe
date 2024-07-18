import os

from langchain.text_splitter import TokenTextSplitter

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import WikipediaLoader, PyPDFLoader
from langchain_community.graphs.neo4j_graph import Neo4jGraph

from langchain_experimental.graph_transformers import LLMGraphTransformer

from langchain_openai import ChatOpenAI

model_name = os.environ["MODEL_NAME"]
pdf_path = os.environ["PDF_PATH"]

# load the documents
print(f"Loading documents from {pdf_path}") # todo make this logger
raw_documents = WikipediaLoader(query="Elizabeth I").load()
# raw_documents = PyPDFLoader(pdf_path).load()

# chunk documents
text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
documents = text_splitter.split_documents(raw_documents[:3])

llm = ChatOpenAI(temperature=0, model_name=model_name)
llm_transformer = LLMGraphTransformer(llm=llm)

# add "Document" label to metadata
for doc in documents:
  if "metadata" not in doc:
    doc.metadata = {}
  doc.metadata["label"] = "Document"

# convert documents to graph documents
graph_documents = llm_transformer.convert_to_graph_documents(documents)

# initialize the Neo4j connection
graph = Neo4jGraph()

# add graph documents to Neo4j
graph.add_graph_documents(
  graph_documents,
  baseEntityLabel=True,
  include_source=True
)