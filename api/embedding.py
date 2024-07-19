from lru import LRU

from pdf import PDF, PDFStore

class EmbeddingManager:
  def __init__(self):
    self.cache = LRU(100)  # LRU cache with capacity of 100

  def get_embeddings(self, pdf: PDF) -> PDFStore:
    # do embeddings already exist?
    if pdf.uuid in self.cache:
      return self.cache[pdf.uuid]
    
    # construct embeddings since they dont exist yet
    embeddings = pdf.generate_embeddings()

    # create, cache, and return new PDFStore
    pdf_store = PDFStore(embeddings)
    self.cache[pdf.uuid] = pdf_store
    return pdf_store

