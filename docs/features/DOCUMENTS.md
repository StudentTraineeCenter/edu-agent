# Documents

Documents are the foundation of the learning system. Users upload documents that are processed, indexed, and made searchable for use in chat, quiz generation, and flashcard creation.

## Document Upload

### Supported File Types

- **PDF & Images**
  - `.pdf`
  - `.tiff`
  - `.jpg`, `.jpeg`, `.jpe`
  - `.png`
  - `.bmp`
  - `.heif`, `.heic`
- **Office Documents**
  - `.docx`
  - `.xlsx`
  - `.pptx`
- **Text / Markup**
  - `.txt`
  - `.html`
  - `.md`
  - `.rtf`
  - `.xml`
- **Email**
  - `.eml`
  - `.msg`

### Upload Process

1. User uploads one or more files.
2. The API (`DocumentUploadService`) creates a `documents` row with status `UPLOADED`, infers `file_type`, and writes basic metadata (size, owner, project).
3. The raw file is uploaded to the **input** Azure Blob container under `<project_id>/<document_id>.<ext>`.
4. Background processing begins automatically via the worker:
   - Text extraction & summary generation using Azure Content Understanding.
   - Original blob is copied to the **output** container and a `<document_id>.contents.txt` blob is written with processed markdown.
   - Document segmentation into chunks.
   - Embedding generation with Azure OpenAI embeddings.
   - Vector indexing in PostgreSQL with pgvector.

### Batch Upload

Multiple documents can be uploaded simultaneously. Each file is processed independently in the background.

## Document Processing

Documents are processed asynchronously using Azure Content Understanding:

1. **Text Extraction**: The document is analyzed to extract structured markdown content.
2. **Summary Generation**: An automatic summary is generated from the document content.
3. **Segmentation**: Content is split into chunks using:
   - Page breaks (marked with `<!-- PageBreak -->`)
   - Markdown headers (H1, H2, H3)
   - Recursive text splitting with overlap
4. **Embedding Generation**: Each segment gets a 3072-dimensional vector embedding.
5. **Vector Storage**: Embeddings are stored in PostgreSQL with pgvector extension.

### Runtime Implementation (API + Worker)

- The API (`src/edu-api`) uploads the raw file to Azure Blob Storage and creates a `documents` row with status `UPLOADED`.
- It enqueues a message to an Azure Storage Queue (`ai-generation-tasks`) with document metadata.
- The worker service (`src/edu-worker`) consumes queue messages and performs:
  - Azure Content Understanding / Document Intelligence extraction and summarization.
  - Segmentation and embedding generation using the `text-embedding-3-large` model.
- The worker updates the document status (`UPLOADED` → `PROCESSING` → `PROCESSED` → `INDEXED` / `FAILED`) and writes segments + embeddings via the shared data layer in `src/edu-shared`.

## Document Search

Documents are searchable using semantic similarity search:

- **Vector Search**: Uses cosine similarity on embeddings to find relevant content.
- **Project Scoping**: Searches are limited to documents within a specific project.
- **Top-K Results**: Returns the most relevant document segments.
- **Score Ranking**: Results include relevance scores.

## Document Features

- **List Documents**: View all documents in a project.
- **Get Document**: Retrieve document metadata and status.
- **Preview Document**: Stream document content for viewing in browser.
- **Delete Document**: Remove document and all associated data (blobs, segments, embeddings).

## Document Status

Documents have the following statuses:

- `UPLOADED`: File uploaded, processing not started.
- `PROCESSING`: Text extraction in progress.
- `PROCESSED`: Text extracted, awaiting indexing.
- `INDEXED`: Fully processed and searchable.
- `FAILED`: Processing encountered an error.

## Document Segments

Each document is split into multiple segments for better search granularity:

- Segments preserve document structure (headers, page breaks).
- Each segment has its own embedding vector.
- Segments are searchable independently.
- Segments maintain references to their parent document.


