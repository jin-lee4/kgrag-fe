import uuid

from typing import Optional

class PDF:
  """
    A PDF is a fancy UUID that stores extra information 
    and can generate its own embeddings
  """
  
  def __init__(self, uuid: uuid.UUID, name: str, handle: Optional[str] = None):
    self.uuid = uuid
    self.name = name
    self.handle = handle

  def generate_embeddings(self):
    pass

class PDFStore:
  def __init__(self, embeddings):
    self.embeddings = embeddings