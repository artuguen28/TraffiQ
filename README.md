# 🚦 TraffiQ

**AI-Powered Traffic Analysis with Natural Language Queries**

TraffiQ combines computer vision and language models to understand traffic scenes. It detects and tracks vehicles in real-time, stores the data in a structured database, and lets you query traffic patterns using natural language questions.

---

## ✨ Features

- **🎥 Real-time Vehicle Detection & Tracking**: Uses YOLOv8 to detect and track vehicles across multiple camera feeds
- **📊 Traffic Analytics**: Records lane-specific counts, timestamps, and maximum vehicles per frame
- **💬 Natural Language Queries**: Ask questions about your traffic data in plain English
- **🤖 RAG-Enabled Chatbot**: Intelligently decides when to query the database or answer conversationally
- **🗄️ PostgreSQL Database**: Structured storage for cameras and traffic summaries
- **🌐 Interactive Web UI**: Clean Gradio interface for chatting with your traffic data

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Camera Feeds   │────▶│  YOLOv8 +    │────▶│   PostgreSQL    │
│  (Video Files)  │     │  Tracking    │     │   Database      │
└─────────────────┘     └──────────────┘     └────────┬────────┘
                                                       │
                                                       │
┌─────────────────┐     ┌──────────────┐             │
│  Gradio UI      │────▶│  FastAPI     │─────────────┘
│  (Frontend)     │     │  Backend     │
└─────────────────┘     └──────────────┘
                             │
                             ▼
                        ┌──────────┐
                        │  OpenAI  │
                        │   LLM    │
                        └──────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL
- OpenAI API Key
- Docker (optional)

### 1. Clone the Repository

```bash
git clone https://github.com/artuguen28/TraffiQ.git
cd TraffiQ
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/traffiq
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o
```

### 4. Initialize the Database

Using Docker:

```bash
docker-compose up -d
```

Or manually initialize with the schema in `database/init/`.

### 5. Register a Camera

```bash
python camera_register.py --video path/to/video.mp4 --cam_id cam_001
```

### 6. Run Traffic Analysis

```bash
python traffic_counter/main.py --cam_id cam_001
```

### 7. Start the Chatbot

**Backend (FastAPI):**

```bash
cd rag
python api.py
```

**Frontend (Gradio):**

```bash
python traffiq_chatbot.py
```

Open your browser to `http://localhost:7860` 🎉

---

## 💬 Example Queries

**Database Questions:**
- "How many cameras are in the system?"
- "What's the average traffic count for cam_001?"
- "Show me the busiest time periods today"
- "Which lane has the most traffic?"

**General Questions:**
- "What is TraffiQ?"
- "How does the system work?"
- "What can you help me with?"

---

## 📁 Project Structure

```
TraffiQ/
├── database/
│   └── init/              # PostgreSQL schema initialization
├── model/                 # YOLOv8 model files
├── rag/
│   └── api.py            # FastAPI backend for chatbot
├── traffic_counter/       # Vehicle detection and tracking
├── camera_register.py     # Register new cameras
├── traffiq_chatbot.py    # Gradio frontend
├── docker-compose.yml     # PostgreSQL setup
└── requirements.txt       # Python dependencies
```

---

## 🗄️ Database Schema

### `cameras` Table
Stores camera metadata and configuration.

| Column        | Type      | Description                    |
|---------------|-----------|--------------------------------|
| id            | SERIAL    | Primary key                    |
| cam_id        | VARCHAR   | Unique camera identifier       |
| video_path    | TEXT      | Path to video file             |
| created_at    | TIMESTAMP | Registration timestamp         |
| frame_width   | INTEGER   | Video frame width              |
| frame_height  | INTEGER   | Video frame height             |
| lines         | JSONB     | Lane boundary definitions      |

### `traffic_summary` Table
Stores traffic analysis results.

| Column             | Type      | Description                    |
|--------------------|-----------|--------------------------------|
| id                 | SERIAL    | Primary key                    |
| cam_id             | VARCHAR   | Foreign key to cameras         |
| timestamp          | TIMESTAMP | Analysis timestamp             |
| lane_counts        | JSONB     | Vehicle counts per lane        |
| max_cars_in_frame  | INTEGER   | Peak simultaneous vehicles     |

---

## 🛠️ Technologies Used

- **Computer Vision**: YOLOv8, OpenCV
- **Backend**: FastAPI, PostgreSQL, psycopg2
- **Frontend**: Gradio
- **AI**: OpenAI GPT-4o
- **Deployment**: Docker

---

## 📝 How It Works

1. **Camera Registration**: Videos are registered with unique IDs and lane definitions
2. **Detection & Tracking**: YOLOv8 detects vehicles frame-by-frame and tracks them across lanes
3. **Data Storage**: Traffic counts are aggregated and stored in PostgreSQL
4. **Natural Language Queries**: Users ask questions via the chatbot
5. **Smart RAG**: The LLM decides whether to:
   - Generate SQL queries to fetch data from the database
   - Answer conversationally without database access
6. **Response Generation**: Results are formatted and returned to the user

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- OpenAI GPT models
- FastAPI and Gradio communities


---

**Built with ❤️ by [artuguen28](https://github.com/artuguen28)**
