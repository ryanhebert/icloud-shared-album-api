# iCloud Shared Album API

A FastAPI-based API to programmatically fetch and serve content from an iCloud Shared Album. Built using Playwright for browser automation to scrape and process album data from Apple's iCloud.

## Features

- Fetches and caches images and metadata from a public iCloud Shared Album.
- Provides endpoints to retrieve:
  - Recent posts (`/recent`)
  - Posts by date (`/posts/{post_date}`)
  - Random post (`/random`)
- Automatically parses and organizes image data and album metadata.

## Tech Stack

- **FastAPI**: High-performance, easy-to-use Python API framework.
- **Playwright**: Headless browser automation to handle dynamic content.
- **Uvicorn**: ASGI server to serve the API.

## Installation

### Prerequisites

Ensure Python 3.8+ and pip are installed.

### Setup

Clone the repository:

```sh
git clone https://github.com/your-username/icloud-shared-album-api.git
cd icloud-shared-album-api
```

Install dependencies:

```sh
pip install -r requirements.txt
```

Install Playwright browser (Chromium):

```sh
playwright install chromium
```

## Usage

Run the API locally using Uvicorn:

```sh
uvicorn main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

## Endpoints

- **Get recent posts:**  
`GET /recent?limit=5`

- **Get posts by date:**  
`GET /posts/{YYYY-MM-DD}`

- **Get a random post:**  
`GET /random`

## Example Requests

Fetch recent posts:
```sh
curl http://127.0.0.1:8000/recent?limit=3
```

Fetch posts by specific date:
```sh
curl http://127.0.0.1:8000/posts/2025-03-07
```

Fetch a random post:
```sh
curl http://127.0.0.1:8000/random
```

## Contributing

Contributions and pull requests are welcome. For major changes, please open an issue first to discuss the changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

