# Product Overview

SaaS Contabil Converter is a document processing service that converts PDF files to CSV format. The application provides both REST API and Telegram bot interfaces for document conversion.

## Key Features

- **PDF to CSV Conversion**: Core functionality to extract and convert PDF content to structured CSV format
- **Authentication**: JWT-based authentication for API access
- **Telegram Integration**: Bot interface with payment processing for document conversion services
- **Asynchronous Processing**: Background task processing using Celery for document conversion
- **File Validation**: PDF validation against a registered database before processing

## Business Model

The service operates on a pay-per-conversion model through Telegram, charging R$50 per PDF conversion. Users can upload documents via Telegram, make payments, and receive converted CSV files.

## Target Users

Accounting professionals and businesses needing to convert PDF documents (likely financial statements, invoices, or reports) into structured CSV format for further processing or analysis.