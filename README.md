# DataSeekAI

DataSeekAI is an AI-powered data analysis platform that enables users to upload files, extract insights, ask natural language questions, and generate visualizations using Google Gemini AI.

The application combines a FastAPI backYOUR_USERNAMEend with an interactive web frontend to provide intelligent analysis of structured and unstructured data.

---

## Features

### File Upload & Processing

Supports multiple file formats:YOUR_USERNAME

- CSV
- Excel (.xlsx, .xls)
- PDF
- DOCX
- PPTX

### AI-Powered Insights

- Natural language querying of uploaded files
- Automated data interpretation
- AI-generated summaries
- Context-aware responses using Google Gemini

### Data Visualization

Automatic chart generation including:

- Bar Charts
- Line Charts
- Pie ChartsYOUR_USERNAME
- Scatter Plots
- Tabular Views

### Interactive Frontend

- Modern chat-based interface
- File upload support
- Dynamic chart rendering using Chart.js
- Conversation-style analytics workflow

---

## Project Architecture
Bipru/dataseekai/
│
├── backend/
│   ├── main.py              # FastAPI server
│   ├── ai_engine.py         # Gemini AI integration
│   ├── file_parser.py       # Multi-format file processing
│   ├── chart_generator.py   # Chart generation logic
│   └── uploads/             # User uploaded files (ignored by Git)
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```
``text
---

## Technology Stack

### Backend

- Python
- FastAPI
- Pandas
- Google Gemini API
- Pydantic
- Python-Dotenv
``text
### Frontend

- HTML5
- CSS3
- JavaScript
- Chart.js

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Bipru/dataseekai.git
cd dataseekai
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file inside the backend directory:

```env
GEMINI_API_KEY=your_api_key_here
```

Never commit your API key to GitHub.

---

## Running the Backend

Navigate to the backend directory:

```bash
cd backend
```

Start the FastAPI server:

```bash
python main.py
```

Or:

```bash
uvicorn main:app --reload
```

---

## Running the Frontend

Open:

```text
frontend/index.html
```

in your browser.

For development, using a local web server is recommended.

Example:

```bash
python -m http.server 8000
```

---

## API Endpoints

### Health Check

```http
GET /health
```

Returns application status information.

### Upload File

```http
POST /upload
```

Uploads and processes supported files.

### Query Data

```http
POST /query
```

Allows users to ask questions about uploaded files and receive AI-generated insights.

---

## Example Workflow

1. Upload a CSV, Excel, PDF, DOCX, or PPTX file.
2. DataSeekAI extracts and parses the content.
3. Ask questions in natural language.
4. Gemini AI analyzes the data.
5. Receive:
   - Insights
   - Summaries
   - Recommendations
   - Visualizations

---

## Security Notes

Ensure the following files are excluded from version control:

```text
.env
venv/
uploads/
__pycache__/
```

Store all API keys securely using environment variables.

---

## Future Enhancements

- User authentication
- Chat history persistence
- Multi-file analysis
- Advanced dashboard analytics
- Exportable reports
- Local LLM support
- Role-based access control

---

## Author

**Bipru**

Built with FastAPI, Gemini AI, and Chart.js.
