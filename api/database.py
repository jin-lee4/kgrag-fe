import os

import asyncpg

user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]
host = os.environ["POSTGRES_HOST"]
port = os.environ["POSTGRES_PORT"]
db_name = os.environ["POSTGRES_DB"]

POSTGRES_URI = f"postgres://{user}:{password}@{host}:{port}/{db_name}"

class PgDatabase:
  def __init__(self):
    self.pool = None

  async def connect(self):
    self.pool = await asyncpg.create_pool(POSTGRES_URI)

  async def disconnect(self):
    if self.pool:
      await self.pool.close()

  async def get_connection(self):
    if not self.pool:
      raise ConnectionError("Connection pool is not initialized")
    return await self.pool.acquire()

  async def release_connection(self, conn):
    if self.pool:
      await self.pool.release(conn)

postgres_db = PgDatabase()

async def get_pg_conn():
  conn = await postgres_db.get_connection()
  try:
    yield conn
  finally:
    await postgres_db.release_connection(conn)