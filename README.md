# E-Commerce Marketplace Database & Analytics Platform

An end-to-end data engineering and AI-powered analytics platform for an eBay-like marketplace, featuring natural language SQL generation, intelligent customer service chatbots, and comprehensive business intelligence.

## Documentation Index

Quick navigation to detailed documentation:

- **[SQL Generator](script/sql_generator/README.md)** - AI-powered natural language to SQL conversion for internal analytics
- **[Customer Chatbot](script/chatbot/README.md)** - Intelligent customer service chatbot with tool-based architecture
- **[Data Engineering & Analytics](sql/README.md)** - Database schema, SQL queries, and data validation


## What This Project Can Do

### AI-Powered SQL Generator (Internal Use)

**Natural Language to SQL Query Generation**

An intelligent SQL generation system for internal analytics use, featuring:
- **Natural Language to SQL** conversion using OpenAI GPT-4o-mini
- **Intelligent Classification** - Automatically distinguishes SQL queries from conversational questions
- **Error Handling & Retry Logic** - Automatic query correction with LangGraph state machine
- **Result Validation** - Ensures generated queries answer the user's question
- **AI-Powered Analysis** - Generates insights and business implications from query results

![System Architecture](result/image/core_flow.png)

📖 **[Read the complete SQL Generator documentation →](script/sql_generator/README.md)**

### Customer Service Chatbot

**Intelligent Customer Support System**

A tool-based chatbot powered by OpenAI GPT-4o-mini, featuring:
- **Multi-Tool Architecture** - FAQ, order lookup, product reviews, policy search
- **RAG Integration** - Semantic search of return/shipping policy documents using ChromaDB
- **Multi-Turn Conversations** - Context-aware conversations with conversation history
- **Database Integration** - Direct SQL queries for order and product data
- **LangChain Integration** - Full LangSmith tracing and monitoring

#### Chatbot Tool-Call Flow

User prompt -> Tool calls (RAG, SQL execute) -> Response 

![Chatbot Tool-Call Flow Diagram](result/image/chatbot_tool_call_flow.png)

📖 **[Read the complete Customer Chatbot documentation →](script/chatbot/README.md)**

### Data Engineering & Analytics

**Comprehensive SQL Analytics & Data Engineering**

This project includes a complete data engineering implementation with:
- **17-table normalized database schema** (PostgreSQL)
- **Revenue, Customer, Product, and Operational Analytics** - Advanced SQL queries for business intelligence
- **Data Quality & Validation** - Automated quality checks and validation queries
- **Business Intelligence Metrics** - CLV, RFM analysis, cohort retention, and more

📖 **[Read the complete Data Engineering documentation →](sql/README.md)**

📖 **[SQL Analysis Report →](../result/report.md)**

### RESTful API

**FastAPI-Based API Server**
- `/analyze` - Natural language to SQL analysis endpoint
- `/chat` - Customer service chatbot endpoint
- `/health` - System health monitoring
- `/profile` - User profile management
- JWT-based authentication and authorization
- CORS support for frontend integration
- Interactive API documentation

### RAG (Retrieval-Augmented Generation) System

**Document Intelligence**
- PDF document processing (return policies, shipping policies)
- Semantic search using vector embeddings
- ChromaDB for persistent vector storage
- OpenAI embeddings for semantic similarity
- Context-aware document retrieval for chatbot responses

## Database Architecture

**17-Table Normalized Schema:**
- **Core Entities**: Customer, Seller, Product, Staff, Department
- **Transactions**: Order_Header, Payment, Bid, Shipping
- **Analytics**: Customer_Review, Seller_Review, Order_History
- **Logistics**: Import_Distribution, Export_Distribution, Customer/Seller Service
- **App Users**: App_User for authentication and access control

![ERD Diagram](/result/image/conceptual%20diagram%20-%20Physical%20Model.png)

📖 For detailed database schema, analytics queries, and data engineering documentation, see [sql/README.md](sql/README.md)

## System Architecture

**AI Agent Workflow:**
- LangGraph-based state machine for SQL agent
- Intelligent error handling and retry mechanisms
- Multi-step query generation and validation
- Result analysis and insight generation

## Tech Stack

**Backend:**
- **Database**: PostgreSQL
- **Languages**: Python, SQL
- **AI/ML**: OpenAI GPT-4o-mini, LangChain, LangGraph
- **Vector Database**: ChromaDB
- **API Framework**: FastAPI
- **Authentication**: JWT (JSON Web Tokens)


### What's in Each Guide

**SQL Generator Documentation** includes:
- LangGraph workflow architecture
- Question classification and SQL generation
- Error handling and retry logic
- Result validation and AI-powered analysis
- Usage examples and API integration

**Customer Chatbot Documentation** includes:
- Tool-based function calling architecture
- All 4 available tools (FAQ, Orders, Reviews, Policies)
- Multi-turn conversation support
- RAG integration for policy documents
- Security features and testing

**Data Engineering Documentation** includes:
- Complete 17-table database schema
- Revenue, Customer, Product, and Operational analytics
- Data quality validation queries
- Business intelligence metrics (CLV, RFM, cohorts)
- SQL best practices and examples