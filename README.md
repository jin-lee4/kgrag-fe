# kg-rag
KG-RAG Backend


#### Bugs
- Neo4j/Postgres need permissions for the .gitignore in the /data directory, must be given with
  - `sudo chown 1000:1000 ./neo4j/data/.gitignore` (replacing neo4j with postgres)
