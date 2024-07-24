import os
import uuid
import asyncpg

from fastapi import HTTPException

from pdf import PDF

def save_file(upload_dir: str, pdf: PDF, pdf_binary_data: bytes) -> str:
  new_filename = f"{pdf.uuid}_{os.path.splitext(pdf.name)[0]}.pdf"
  file_path = os.path.join(upload_dir, new_filename)

  with open(file_path, "wb") as buffer:
    buffer.write(pdf_binary_data)

  return file_path

async def insert_file_record(conn, pdf: PDF, file_handle: str):
  async with conn.transaction():
    await conn.fetchrow(
      "INSERT INTO uploaded_pdfs (id, filename, file_handle) VALUES ($1, $2, $3)",
      pdf.uuid, pdf.name, file_handle,
    )

class UploadManager:
  def __init__(self, upload_dir: str):
    self.upload_dir = upload_dir
    os.makedirs(self.upload_dir, exist_ok=True)

  async def upload(self, conn, pdf: PDF, pdf_binary_data: bytes) -> uuid.UUID:
    file_handle = save_file(self.upload_dir, pdf, pdf_binary_data)
    await insert_file_record(conn, pdf, file_handle)
    return pdf.uuid

  async def fetch(self, conn, pdf_uuid: uuid.UUID) -> PDF:
    async with conn.transaction():
      row = await conn.fetchrow('SELECT * FROM uploaded_pdfs WHERE id = $1', pdf_uuid)
      if not row:
        raise HTTPException(status_code=404, detail="PDF not found")
      pdf = PDF(uuid=row['id'], name=row['filename'], handle=row['file_handle'])
      return pdf