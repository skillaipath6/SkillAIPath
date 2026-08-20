# RAG Pipeline Architecture
## Document Processing | Vector Search | LLM Generation

Production RAG system with document ingestion, embedding, and retrieval-augmented generation.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE ARCHITECTURE                         │
└──────────────────────────────────────────────────────────────────────────┘

          INDEXING PIPELINE                      QUERY PIPELINE

     Documents (PDF, HTML, MD)                   User Query
              │                                      │
              ↓                                      ↓
       Text Extraction                        Top-K Retrieval
              │                                      │
              ↓                                      │
   Smart Chunking (512 tokens)                    │
              │                                      │
              ↓                                      │
    Embedding Generation                          │
              │                                      │
              ↓                                      │
   Databricks Vector Search ────────────────────┘
              (Index)                               │
                                                    ↓
                                            Context Assembly
                                                    │
                                                    ↓
                                             LLM Generation
                                            (GPT-4/Claude)
                                                    │
                                                    ↓
                                            Generated Answer
```

Components: Document parsing, chunking, embedding, vector indexing, retrieval, LLM generation
Models: OpenAI GPT-4, Anthropic Claude, Databricks DBRX
Module: 3_AI_Platform/2_Rag_Pipeline
