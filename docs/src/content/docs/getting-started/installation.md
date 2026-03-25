---
title: Installation
description: Set up and run Gilial
---

## Prerequisites

- Python 3.8 or higher
- Pinecone account with an active index
- Pinecone API key

## Set Up Gilial

Clone the Gilial repository and install dependencies:

```bash
git clone https://github.com/aadyantmaity/Gilial.git
cd Gilial
pip install -r requirements.txt
```

## Configure Your Credentials

Set your Pinecone credentials as environment variables:

```bash
export PINECONE_API_KEY="your-api-key-here"
export PINECONE_INDEX_NAME="your-index-name"
export PINECONE_ENVIRONMENT="us-west-1"  # or your region
```

## Start the Server

Start the Gilial backend:

```bash
python backend/main.py
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The API is now ready to accept requests!

## Verify Setup

Test the connection:

```bash
curl http://localhost:8000/status
```

If you get a JSON response with your index info, you're ready to go.

## Next Steps

- Read the [Quick Start Guide](./quick-start.md)
- Learn about [Compression Strategies](../guides/strategies.md)
- Check the [REST API Reference](../api/rest-api.md)
