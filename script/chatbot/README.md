# Customer Service Chatbot

An AI-powered customer service chatbot including conversations, tool-based function calling, and RAG (Retrieval-Augmented Generation) for policy document search.

## Overview

The customer service chatbot provides automated, intelligent support for e-commerce customers, which brings following benefits to businesses:
- reducing support workload  
- improving customer satisfaction through instant, accurate responses to common inquiries
- Example chat: ![Chatbot Tool-Call Flow Diagram](../../result/image/chat.png)



## Business Value

### Customer Experience

- **24/7 Availability** + **Reduced Wait Times**: Instant responses to customer inquiries at any time
- **Reduced Wait Times** + **Consistent Service**: Standardized, accurate answers to common questions

## Core Capabilities


### 1. FAQ Support

**Business Function**: Answers frequently asked questions from a curated knowledge base

**Value**: Reduces repetitive inquiries and ensures consistent, accurate information delivery

### 2. Order History Retrieval

**Business Function**: Provides customers with instant access to their complete order history

**Value**:

- Customers can track orders without contacting support
- Includes order details, payment information, and shipping status
- Supports up to 50 orders per query for comprehensive history


### 3. Product Review Lookup

**Business Function**: Retrieves and presents product reviews and ratings to help customers make informed decisions

**Value**:

- Enables customers to research products independently
- Builds trust through transparent review access
- Supports purchase decision-making


### 4. Policy Document Search

**Business Function**: Semantic search across return and shipping policy documents using advanced RAG technology

**Value**:

- Customers get precise answers from official policy documents
- Reduces policy-related support tickets
- Ensures compliance with official terms and conditions

## How It Works


### Chatbot Workflow
![Chatbot Tool-Call Flow Diagram](../../result/image/chatbot_tool_call_flow.png)

### Intelligent Tool Selection

The chatbot automatically determines which capabilities to use based on customer questions, enabling it to:

- Answer simple questions directly
- Retrieve data from the database when needed
- Search policy documents for specific information
- Combine multiple tools for complex inquiries

### Sequential Tool Execution

For complex questions, the chatbot can:

- Execute multiple tools in sequence
- Synthesize information from different sources
- Provide comprehensive answers that combine data from orders, policies, and FAQs

## Key Features

### Context Awareness

- Remembers conversation history across multiple turns
- Understands references to previous messages
- Maintains customer context throughout the session


### Security & Reliability

- Parameterized queries prevent SQL injection
- Input validation and sanitization
- Type-safe data handling
- Error handling for robust operation

## Additional Resources

- [Main Project README](../../README.md)
- [SQL Generator Documentation](../sql_generator/README.md)
- [Data Engineering Documentation](../../sql/README.md)

---
