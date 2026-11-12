# Travora – AI Trip Itinerary Planner

## 1. Project Overview

**Travora** is a full-stack, AI-powered travel planning application that generates personalized, day-by-day travel itineraries based on user preferences, including destination, travel dates, budget, number of travelers, preferred activities, and food choices.

Traditional travel planning requires users to search across multiple platforms to find tourist attractions, restaurants, activities, and other travel information. Organizing these options into a practical itinerary can be time-consuming.

Travora simplifies this process by combining **Retrieval-Augmented Generation (RAG), semantic search, vector embeddings, and Large Language Models (LLMs)** to generate context-aware travel recommendations.

The application retrieves relevant places from a curated travel database, processes user preferences, and uses a Groq LLM to generate a personalized itinerary.

### Key Features

- **Personalized Travel Planning:** Generates itineraries based on destination, dates, budget, interests, and food preferences.
- **RAG-Based Recommendations:** Uses retrieved travel information to provide context-aware AI-generated itineraries.
- **Semantic Search:** Retrieves relevant travel destinations using vector similarity rather than relying only on keyword matching.
- **User Authentication:** Supports email OTP verification and JWT-based authentication.
- **Microservices Architecture:** Separates authentication, database operations, trip validation, and AI itinerary generation into independent services.
- **Trip Management:** Allows users to access and manage their saved travel plans.
- **Containerized Deployment:** Uses Docker Compose to run the frontend and backend services.

---

## 2. System Architecture

Travora follows a microservices architecture with a React frontend and four independent FastAPI backend services.

```text
                         Browser (React)
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
        Auth Service      RAG Service      User Details
          :8001             :8002             :8003
              |                |                |
              |                |                |
              v                v                v
          DynamoDB          Pinecone         DynamoDB
              |                |
              |                v
              |          Sentence Transformers
              |                |
              |                v
              |             Groq LLM
              |                |
              |                v
              |        Generated Itinerary
              |                |
              +----------------+
                               |
                               v
                         React Frontend

                 Database Service (:8000)
                          |
                          v
                    AWS DynamoDB
```

### Backend Services

| Service | Port | Responsibility |
|---|---:|---|
| Authentication Service | 8001 | User registration, OTP verification, login, and JWT authentication |
| Database Service | 8000 | Travel data retrieval and CRUD operations |
| RAG Service | 8002 | Embedding generation, semantic retrieval, and AI itinerary generation |
| User Details Service | 8003 | Trip preference validation and retrieval of activity and food options |

Each backend service maintains its own virtual environment, `.env` configuration, and `requirements.txt` file to ensure dependency isolation.

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, REST APIs |
| Authentication | JWT, Gmail SMTP, OTP Verification |
| Database | AWS DynamoDB |
| Embedding Model | Sentence Transformers |
| Vector Database | Pinecone |
| LLM | Groq |
| Infrastructure | AWS, Docker, Docker Compose |

---

## 4. RAG Pipeline – Core AI Architecture

The central component of Travora is its Retrieval-Augmented Generation pipeline.

Instead of relying entirely on an LLM's internal knowledge, the application retrieves relevant travel information from a curated database and provides it as context to the LLM.

This helps generate more relevant and context-aware travel recommendations.

### 4.1 Data Indexing and Embedding Generation

Before generating itineraries, the travel information must be converted into vector embeddings.

The indexing workflow consists of:

1. Curated city information is loaded from JSON files into AWS DynamoDB.
2. The RAG service retrieves travel information from DynamoDB.
3. Place descriptions are processed into text documents.
4. Sentence Transformers converts the text into numerical vector embeddings.
5. Generated embeddings and associated metadata are stored in Pinecone.

### 4.2 Semantic Search and Retrieval

When a user submits a travel request:

1. The user's preferences are converted into a semantic search query.
2. Sentence Transformers generates an embedding for the query.
3. Pinecone performs vector similarity search against indexed travel information.
4. Relevant destinations, attractions, restaurants, and activities are retrieved.
5. Retrieved information is passed to the LLM as contextual information.

Semantic search helps identify relevant places based on the meaning of a query rather than requiring exact keyword matches.

### 4.3 LLM-Based Itinerary Generation

The retrieved travel information and user preferences are passed to the Groq LLM.

The LLM processes the context and generates a structured, personalized itinerary organized by day.

For example:

**User Input:**
- Destination: Goa
- Duration: 3 days
- Budget: ₹15,000
- Interests: Beaches, adventure, sightseeing
- Food Preference: Vegetarian

**Expected Output:**

- **Day 1:** Beach exploration and nearby attractions.
- **Day 2:** Historical sightseeing and adventure activities.
- **Day 3:** Local exploration and food experiences.

The generated itinerary is returned to the React frontend for display.

### RAG Workflow

```text
User Travel Preferences
          |
          v
    Query Processing
          |
          v
  Sentence Transformers
          |
          v
    Query Embedding
          |
          v
       Pinecone
          |
          v
  Semantic Similarity Search
          |
          v
   Retrieved Travel Context
          |
          v
       Groq LLM
          |
          v
  Personalized Itinerary
          |
          v
     React Frontend
```

---

## 5. Application Workflow

### Step 1: User Registration

Users register by entering their name, email, and password.

The authentication service sends a six-digit OTP to the registered email address using Gmail SMTP.

### Step 2: Email Verification

Users enter the OTP to verify their email address and activate their account.

### Step 3: Authentication

After successful login, the authentication service generates a JWT that is used for authenticated requests.

### Step 4: Travel Preference Selection

Users select:

- Destination
- Travel dates
- Number of travelers
- Budget
- Preferred activities
- Food preferences

### Step 5: Preference Validation

The User Details Service validates the submitted travel preferences and provides available activity tags and food categories for the selected city.

### Step 6: AI Itinerary Generation

The RAG service retrieves relevant places from Pinecone and provides the retrieved information to the Groq LLM.

The LLM generates a personalized day-by-day itinerary.

### Step 7: Trip Management

The generated travel plans can be accessed through the My Trips page.

---

## 6. Challenges and Solutions

During the development of Travora, several important engineering challenges were addressed.

### Challenge 1: Generating Context-Aware Travel Recommendations

**Problem:**

Directly prompting an LLM to generate travel itineraries can result in irrelevant recommendations or places that are not present in the application's travel dataset.

**Solution:**

Implemented a RAG pipeline that retrieves relevant travel information from Pinecone before generating the final response.

The retrieved context is passed to the Groq LLM to generate more relevant and grounded itineraries.

### Challenge 2: Implementing Semantic Search

**Problem:**

Traditional keyword-based searches may fail to identify relevant places when users express preferences using different words or descriptions.

**Solution:**

Integrated Sentence Transformers to generate vector embeddings and Pinecone to perform semantic similarity search.

This allows the application to retrieve relevant places based on the meaning of user queries.

### Challenge 3: Synchronizing Structured Data and Vector Embeddings

**Problem:**

Travel information is maintained in DynamoDB, while its vector representations are stored separately in Pinecone.

Changes to the source travel data require corresponding updates to the vector index.

**Solution:**

Separated data loading and vector indexing into dedicated API operations:

- `/admin/load-data` – Loads curated travel information into DynamoDB.
- `/index` – Generates embeddings and upserts them into Pinecone.

This provides a structured approach to initial data setup and re-indexing.

### Challenge 4: Managing Multiple Backend Services

**Problem:**

Combining authentication, database operations, user preference validation, and AI processing into a single backend would increase coupling and make maintenance more difficult.

**Solution:**

Designed four independent FastAPI microservices, each with its own dependencies, environment configuration, and API endpoints.

This improves separation of responsibilities and makes individual services easier to maintain and debug.

### Challenge 5: Integrating External Services

**Problem:**

The application depends on multiple external systems, including AWS DynamoDB, Pinecone, Groq, and Gmail SMTP, each requiring separate credentials and configurations.

**Solution:**

Maintained service-specific environment configurations using `.env` files and used Docker Compose to simplify application setup and execution.

### Challenge 6: Implementing Authentication

**Problem:**

The application requires a mechanism to verify users during registration and authenticate them during subsequent requests.

**Solution:**

Implemented email OTP verification during registration and JWT-based authentication for login and protected profile retrieval.

---

## 7. API Reference

### Authentication Service – Port 8001

| Method | Endpoint | Description |
|---|---|---|
| POST | `/signup` | Initiate registration and send OTP |
| POST | `/verify-otp` | Verify OTP and create account |
| POST | `/login` | Authenticate user and return JWT |
| GET | `/me` | Retrieve authenticated user profile |
| GET | `/health` | Health check |

### Database Service – Port 8000

| Method | Endpoint | Description |
|---|---|---|
| GET | `/explore?city=goa` | Retrieve all places for a city |
| GET | `/places?city=goa&category=restaurant` | Retrieve places by category |
| POST | `/admin/load-data` | Load curated city JSON files into DynamoDB |
| GET | `/health` | Health check |

### RAG Service – Port 8002

| Method | Endpoint | Description |
|---|---|---|
| POST | `/itinerary` | Generate a complete AI itinerary |
| POST | `/search` | Perform semantic vector search |
| POST | `/index` | Index travel information from DynamoDB into Pinecone |
| GET | `/health` | Health check |

### User Details Service – Port 8003

| Method | Endpoint | Description |
|---|---|---|
| GET | `/plan?city=goa` | Retrieve available activity tags and food types |
| POST | `/plan` | Validate and submit trip preferences |
| GET | `/health` | Health check |

---

## 8. Project Structure

```text
Travora/
│
├── docker-compose.yml
├── .env.example
│
├── data/
│   └── curated city JSON files
│
├── frontend/
│   ├── src/
│   │   ├── context/
│   │   │   └── AuthContext.tsx
│   │   ├── pages/
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   └── Dockerfile
│
└── backend/
    │
    ├── auth-service/
    │   ├── app/
    │   ├── requirements.txt
    │   └── .env
    │
    ├── database/
    │   ├── app/
    │   ├── requirements.txt
    │   └── .env
    │
    ├── rag/
    │   ├── app/
    │   ├── requirements.txt
    │   └── .env
    │
    └── user_details/
        ├── app/
        ├── requirements.txt
        └── .env
```

---

## 9. Installation and Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11+
- AWS account with DynamoDB access in `ap-south-1`
- Pinecone account with a serverless index
- Groq API key
- Gmail account with an App Password

### Environment Configuration

Each backend service requires its own `.env` file.

**Database Service – `backend/database/.env`**

```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

**Authentication Service – `backend/auth-service/.env`**

```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
JWT_SECRET_KEY=your_secret_key
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

**RAG Service – `backend/rag/.env`**

```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=voyonata-travel
GROQ_API_KEY=your_groq_api_key
```

**User Details Service – `backend/user_details/.env`**

```env
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

Use `.env.example` as a reference for the required configuration.

Never commit actual credentials or API keys to version control.

---

## 10. Running with Docker Compose

Docker Compose is the recommended way to run the complete application.

### Step 1: Configure Environment Variables

Create and configure the four `.env` files with the required credentials.

### Step 2: Build and Start Services

```bash
docker compose up --build
```

### Step 3: Access the Application

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Database Service | http://localhost:8000 |
| Authentication Service | http://localhost:8001 |
| RAG Service | http://localhost:8002 |
| User Details Service | http://localhost:8003 |

### Step 4: Load Travel Data

Run this command for the initial data setup:

```bash
curl -X POST http://localhost:8000/admin/load-data
```

This loads curated city JSON files into DynamoDB.

### Step 5: Index Travel Places

Run:

```bash
curl -X POST http://localhost:8002/index
```

This generates vector embeddings from the travel data and stores them in Pinecone.

After completing these initial setup steps, the application is ready to generate itineraries.

---

## 11. Running Locally Without Docker

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

To override backend URLs, create `frontend/.env.local`:

```env
VITE_AUTH_URL=http://localhost:8001
VITE_RAG_URL=http://localhost:8002
VITE_USER_DETAILS_URL=http://localhost:8003
VITE_DATABASE_URL=http://localhost:8000
```

### Backend Setup

Each backend service must be started separately.

**Database Service**

```bash
cd backend/database

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

**Authentication Service**

```bash
cd backend/auth-service

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8001
```

**RAG Service**

```bash
cd backend/rag

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8002
```

**User Details Service**

```bash
cd backend/user_details

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8003
```

---

## 12. Future Enhancements

Potential improvements to Travora include:

- **Real-Time Travel Information:** Integrate external APIs for weather, events, attraction timings, and travel updates.
- **Route Optimization:** Arrange recommended destinations based on geographical distance and estimated travel time.
- **Advanced Recommendation System:** Incorporate user feedback, ratings, and historical preferences.
- **Cost Estimation:** Improve budget planning by estimating transportation, accommodation, and food expenses.
- **Improved RAG Retrieval:** Introduce metadata filtering, reranking, and relevance evaluation.
- **Performance Optimization:** Add caching and asynchronous processing for improved response times.
- **Monitoring and Reliability:** Implement structured logging, health monitoring, retries, and error tracking.

---

## 13. Learning Outcomes

Through Travora, I gained practical experience in:

- Building full-stack applications using React and FastAPI.
- Designing and implementing microservices architectures.
- Implementing Retrieval-Augmented Generation pipelines.
- Generating and managing vector embeddings.
- Performing semantic search using Pinecone.
- Integrating LLMs using Groq.
- Working with AWS DynamoDB.
- Implementing JWT-based authentication and email OTP verification.
- Building REST APIs and integrating independent services.
- Containerizing applications using Docker Compose.

---

## 14. Conclusion

Travora demonstrates how Generative AI and modern backend technologies can be combined to build an intelligent travel planning application.

By integrating RAG, semantic search, Pinecone, Groq LLM, AWS DynamoDB, and FastAPI microservices, the application transforms user travel preferences into personalized day-by-day itineraries.

The project provides practical experience in AI application development, vector databases, cloud integration, backend engineering, and full-stack system design.
