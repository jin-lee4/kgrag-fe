import os
import uuid
import shutil

import asyncpg

from fastapi import HTTPException

class UploadManager:
  def __init__(self, upload_dir: str):
    self.upload_dir = upload_dir
    os.makedirs(self.upload_dir, exist_ok=True)

  def save_file(self, file_content, filename):
    file_uuid = uuid.uuid4()
    new_filename = f"{file_uuid}_{filename}"
    file_path = os.path.join(self.upload_dir, new_filename)

    with open(file_path, "wb") as buffer:
      buffer.write(file_content)

    return file_uuid, file_path

  async def insert_file_record(self, conn, file_uuid: uuid.UUID, filename: str, file_handle: str):
    async with conn.transaction():
      record = await conn.fetchrow(
        "INSERT INTO uploaded_pdfs (id, filename, file_handle) VALUES ($1, $2, $3) RETURNING *",
        file_uuid, filename, file_handle
      )
    return record

  async def upload_file(self, conn, file):
    if file.content_type != "application/pdf":
      raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")

    contents = file.file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB
      raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

    file_uuid, file_path = self.save_file(contents, file.filename)
    file_record = await self.insert_file_record(conn, file_uuid, file.filename, file_path)

    return file_record

  async def get_file(self, conn, file_id: uuid.UUID):
    file_record = await conn.fetchrow("SELECT * FROM uploaded_pdfs WHERE id = $1", file_id)
    if not file_record:
      raise HTTPException(status_code=404, detail="File not found")
    file_path = file_record['file_handle']
    with open(file_path, "rb") as file:
      file_content = file.read()
    return file_content, file_record['filename']

  async def delete_file(self, conn, file_id: uuid.UUID):
    file_record = await self.get_file(conn, file_id)
    if not file_record:
      raise HTTPException(status_code=404, detail="File not found")

    if os.path.exists(file_record['file_handle']):
      os.remove(file_record['file_handle'])

    async with conn.transaction():
      await conn.execute("DELETE FROM uploaded_pdfs WHERE id = $1", file_id)
