## Problem statement
A university student throughout the year receives 100's of pages of notes and lecture slides. Usually they would dump them into folders and then when prepping for exams they have to start digging through those folders just to find answers.
RAG retrieves only the relevant chunks from across the entire document library and grounds the answer in cited sources — so the student gets accurate answers tied directly to their own material, not a general LLM response.

## Competitive Analysis

### Notebook LM
- Notebook LM is good at creating audio files and taking information from uploaded files and creating good responses to user questions
- But it does not cater for true power users limiting a notebook to 50 sources
- With my RAG knowledge Assistant, I will remove this limit. It is also limited to Gemini, while I plan on allowing Ollama which will keep your information private. and this can be swapped out at any time to a hosted AI Agent

### ChatPDF
- ChatPDF responds very quickly and is simple to use
- But it only loads one document at a time and it is limited to PDFs
- With my RAG knowledge Assistant, I will be allowing more doc types. Compared to the proprietary soft, my knowledge assistant will be open source

### Perplexity Spaces
- Perplexity Spaces uses the internet to help increase the depth in the response it gives
- This can sometimes create a bias in its response, with more information coming from the internet.
- I would implement web search but only as a validator to the current information or as an option to get more in depth of an answer if the user requires it.

## Tech bets with reasoning

### pgvector
Pgvector works best for me as this is a small scale project and will integrate well with my Postgres db.
Pinecone works well, but I don't need a large scale solution, but will keep this in mind as a potential improvement down the line.

### LangGraph
LangGraph would allow me more options down the line, especially if I make more complex agent workflows.
LangGraph supports stateful, cyclical graphs. The agent can loop, branch, and call tools with memory across steps. Raw LangChain chains are linear pipelines.

### FastAPI
FastAPI allows asynchronous API calls and has good performance.
Flask is older and does not have as many built in features, which creates more dependencies on other libraries

### Ollama
Ollama is more developer orientated and is easier to use with APIs.
Ollama exposes an OpenAI-compatible REST API, which means the same LangChain abstraction works for both Ollama and OpenAI

## Risks and Unknowns
- Embedding dimension mismatch if you swap providers mid-project (the 768-dim ADR addresses this)
- LangGraph agent loops that don't terminate (need a max-steps guard)
- Ollama RAM footprint on constrained dev machines

