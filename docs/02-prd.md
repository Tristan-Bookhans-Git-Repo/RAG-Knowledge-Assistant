# Product Requirement Document

## Overview

This PRD proposes a RAG Knowledge Assistant to help you analyse your documents and answer context based questions better.

## Goals

- Open Source so it can be enhanced by anyone.
- Works with local LLMs so users can save on cost and not be restricted to hosted LLMs, allows data to stay private as well.
- A usable product by students and everyday working people.
- Have the assistant work with no source cap.


## Non-Goals

- This is not designed to compete on the scale with the likes of Notebook LM, ChatPDF, etc. It is designed for hobbyist or people who want to keep their data totally private


## Audience

This application is designed for a software engineer studying for a certification. Each new section/chapter will have its own notes, recordings, etc. All of these files can be uploaded to the LLM and used to ask context based questions that can be raised during practice exams or be used to generate practice exam questions

## Assumptions

- Users have a internet connection to interact with the application.
- Users running Ollama have sufficient RAM to run a local model (minimum 8GB).

## Constraints

- This project is worked on by a single person, so timelines can vary greatly
- Cost of using a hosted LLM, I have no financial backing so this is coming out of my own pocket.

## Key use cases

- As a new user, I want to be able to create my own account, so that I can keep my data private from everyone else.
    - Given that I am accessing the knowledge assistant for the first time, I should be prompted to create an account before using it.
- As a registered user, I want to be able to upload documents, so that they can be added to the LLMs knowledge bank.
    - Given that I have loaded some documents during a conversation, the LLM should then use those documents to answer questions
- As a registered user, I want to be able to delete documents, so that they are no longer used by the LLM
    - Given I have uploaded document, when I want to delete them, then I can delete them from the dashboard
- As a registered user, I want to log in and log out, so that my session is secure between uses.
  - Given I have an account, when I submit valid credentials, then I receive an authenticated session and am redirected to the dashboard.
  - Given I am logged in, when I click logout, then my session is invalidated and I am redirected to the login page.
- As a registered user, I want to see a list of my uploaded documents, so that I know what is in my knowledge base.
  - Given I have uploaded documents, when I open the dashboard, then I see each document's name, upload date, and a delete option.
- As a registered user, I want to upload PDF, DOCX, TXT, and MD files, so that I am not restricted to one format.
  - Given I am on the upload screen, when I select a supported file type, then it is accepted and processed.
  - Given I select an unsupported file type, then I receive a clear error message.
- As a registered user, I want to ask a question and receive a cited answer, so that I can verify which document the information came from.
  - Given I have uploaded documents, when I submit a question, then I receive an answer with at least one source citation showing the document name and relevant excerpt.
- As a registered user, I want my documents to be invisible to other users, so that my private information stays private.
  - Given two users have each uploaded different documents, when either user asks a question, then they only receive answers from their own documents.
- As a registered user, I want to use the assistant with a local Ollama model, so that my documents never leave my machine.
  - Given Ollama is running locally and configured, when I ask a question, then the answer is generated entirely on-device with no external API calls.
- As a registered user, I want to optionally enable web search to supplement 
  my documents, so that I can get broader context when my uploaded material 
  doesn't fully answer my question.
  - Given web search is enabled, when I ask a question my documents don't 
    fully cover, then the answer includes web sources clearly labelled as 
    such, separate from document citations.
  - Given web search is disabled, when I ask a question, then the answer is 
    generated only from my uploaded documents.


## MVP scope vs later

MVP (Must be in first merge to main):

- Register / login / logout
- Upload documents (PDF, DOCX, TXT, MD)
- List and delete documents
- Ask a question, get a cited answer
- Tenant isolation (user A cannot see user B's documents)
- Works with Ollama locally or OpenAI via env var

v2 (Out of scope for now):

- Query history UI
- Streaming responses
- Usage/token tracking dashboard
- PDF page thumbnails
- Account self-deletion
- Shared workspaces


## Non-functional requirements

### Answer latency
- For ~95% of users using Ollama, ~15 seconds(Depending on the ollama model used)
- For ~95% of users using OpenAI, ~5 seconds

### Tenant isolation
- No question may return data related to another user

### Secrets
- No API keys pushed, everything should be in .env files which are git ignored

### Offline operation
- The application should work locally with Ollama and no internet connection

### File size limit
- Don't allow to large files(max 50MB per upload) which could cause memory issues when trying to load the file to the DB