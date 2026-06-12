# Legal Research AI

🚧 Work in Progress

This project is currently under active development.

The goal is to build an AI-powered legal research assistant capable of crawling  case law sites, creating a searchable legal knowledge base, and answering legal research questions using retrieval-augmented generation (RAG).

Current functionality includes:
- Case law crawling and dataset generation
- Semantic search using FAISS
- Retrieval-based legal question answering
- Local LLM integration
- Streamlit web interface

Planned improvements:
- Improved answer quality and legal reasoning
- Better case extraction and document chunking
- Advanced citation handling
- Conversational memory
- Multi-jurisdiction support
- Cloud deployment
- Production-grade legal research workflows

⚠️ This project is a research and educational tool. It does not constitute legal advice.

## Setup

1. Clone the repository
2. Install requirements
3. Run crawler.py
4. Generate ghana_cases_ghalii.csv
5. Run legal_bot.py

## Dataset

The dataset is not included in this repository.

Generate it by running:

python crawler.py