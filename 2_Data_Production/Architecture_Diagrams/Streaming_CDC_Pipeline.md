# Streaming CDC Pipeline Architecture
## Real-Time Change Data Capture | Auto Loader | Checkpointing

Real-time CDC implementation with structured streaming and Delta Lake checkpointing.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                STREAMING CDC PIPELINE ARCHITECTURE                          │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  STREAMING SOURCES                                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│  Kafka Topics (Change Events) | AWS Kinesis (Data Streams)                  │
│  Cloud Storage (New Files)                                                   │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────┴───────────────────────────────────────┐
│  AUTO LOADER (Ingestion)                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│  Schema Inference & Evolution ─> Checkpoint Management                      │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────┴───────────────────────────────────────┐
│  STRUCTURED STREAMING (Processing)                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Bronze (Raw Append)                                                         │
│      ↓                                                                       │
│  Watermarking (Late Data Handling - 10 min)                                  │
│      ↓                                                                       │
│  MERGE INTO (Upsert Logic - INSERT/UPDATE/DELETE)                           │
│      ↓                                                                       │
│  Silver (Change Tracking & SCD Type 2)                                       │
│                                                                              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────┴───────────────────────────────────────┐
│  FAULT TOLERANCE (Exactly-Once Semantics)                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Delta Lake Checkpoints ─> Auto Recovery on Failure ─> Stream Monitoring   │
│  (Write-Ahead Logs, Incremental Updates)                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Components

### Auto Loader Configuration
* cloudFiles.format = "json" or "parquet"
* cloudFiles.schemaLocation = checkpoint path
* cloudFiles.inferColumnTypes = true
* cloudFiles.schemaEvolutionMode = "rescue"

### Structured Streaming
* readStream from Kafka/Kinesis/CloudFiles
* Watermarking: withWatermark("timestamp", "10 minutes")
* Trigger: processingTime='30 seconds' or Trigger.Once()
* Output mode: append (Bronze) or complete (Silver)

### Change Data Capture
* Operation types: INSERT, UPDATE, DELETE
* Timestamp-based ordering
* Deduplication logic on business keys
* SCD Type 2 implementation for dimensions

### Checkpointing Strategy
* Checkpoint location: dbfs:/checkpoints/pipeline_name
* Write-ahead logs for exactly-once semantics
* Incremental checkpoint updates
* Auto-recovery on stream restart

### Performance Tuning
* maxFilesPerTrigger = 1000 (control micro-batch size)
* maxBytesPerTrigger = "10g" (memory management)
* Partition pruning on timestamp column
* Optimize file compaction frequency

Module: 2_Data_Production/02_Medallion_Architecture/03_Streaming_Cdc
Pattern: Streaming CDC with checkpointing
Latency: Under 1 minute end-to-end
Last Updated: January 2025
