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
## 14. Challenges Faced and Solutions

During the development of Travora, several challenges were encountered across database integration, authentication, RAG implementation, frontend integration, and environment configuration. The following section documents the actual errors, their root causes, and the solutions implemented.

### 6.1 Database Service Challenges

#### Challenge 1: Handling Inconsistent JSON Data Structures

**Problem:**

While loading curated city data into DynamoDB, the application encountered:

```text
AttributeError: 'str' object has no attribute 'get'
```

The root cause was an inconsistent JSON structure. Most city files contained a flat list of place objects, whereas `seoul_final.json` contained nested categories such as `attractions` and `restaurants`.

The loader attempted to iterate over the dictionary directly, treating category names as place objects.

**Solution:**

Updated the data loader to detect whether the JSON root was a list or dictionary. For nested dictionaries, the loader extracts and flattens the lists before processing individual place records.

Added type validation to skip invalid records and ensure that only dictionary objects are processed.

#### Challenge 2: Stale Python Bytecode Causing Misleading Tracebacks

**Problem:**

After modifying the data loader, Python displayed incorrect traceback line numbers, pointing to code that was not responsible for the error.

The issue was caused by stale `.pyc` bytecode files stored in `__pycache__`, resulting in misleading source-line mappings during hot reload.

**Solution:**

Cleared the existing `__pycache__` directories and restarted the FastAPI server to ensure Python loaded the updated source code correctly.

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
```

#### Challenge 3: Missing AWS Dependencies in the Virtual Environment

**Problem:**

The database service failed with:

```text
ModuleNotFoundError: No module named 'boto3'
```

The dependencies had been installed before activating the virtual environment, causing them to be installed in the system Python rather than the environment used by the application.

**Solution:**

Activated the correct virtual environment before installing dependencies and verified that the packages were available to the Python interpreter running the service.

#### Challenge 4: DynamoDB Reporting Successful Writes Without Persisting Data

**Problem:**

The `/admin/load-data` endpoint reported successful writes:

```json
{"written": 275}
```

However, querying DynamoDB returned no records.

The root cause was that the `travel_data` table had not been created. Table initialization was previously performed only during FastAPI startup, which was bypassed when the loader was executed directly.

**Solution:**

Moved the table initialization check into the `load_all_cities()` function itself by calling `create_table_if_not_exists()` before writing records.

This made the loader independent of the execution method and ensured the DynamoDB table existed before data insertion.

---

### 6.2 Authentication Service Challenges

#### Challenge 5: Signup API Failing Due to CORS and SMTP Configuration

**Problem:**

The signup form displayed:

```text
Failed to fetch
```

The issue involved multiple interacting problems:

- SMTP configuration failures during OTP delivery.
- Stale Uvicorn processes running previous versions of the authentication service.
- Vite automatically switching from port `5173` to `5174` because another development server was already running.
- The CORS configuration only allowed requests from `http://localhost:5173`.

As a result, browser requests from the new frontend port were blocked.

**Solution:**

- Removed the OTP functionality from the authentication signup flow.
- Updated signup to create the user and return a JWT directly.
- Replaced the hardcoded CORS origin with a localhost port regex.
- Applied the CORS configuration consistently across all four backend services.

Updated configuration:

```python
allow_origin_regex=r"http://localhost(:\d+)?"
allow_credentials=False
```

This allowed the frontend to communicate with backend services across different localhost development ports.

#### Challenge 6: Passlib and Bcrypt Compatibility Issues

**Problem:**

The authentication service encountered:

```text
AttributeError: module 'bcrypt' has no attribute '__about__'
```

The issue occurred because `passlib==1.7.4` relied on the `bcrypt.__about__.__version__` attribute, which was removed in bcrypt 4.x.

**Solution:**

Removed the incompatible Passlib and Bcrypt dependencies and replaced the password hashing implementation with Python's built-in `hashlib` and randomly generated salts.

This eliminated the package compatibility issue and reduced external dependencies.

**Note:** The implemented SHA-256 approach was a development workaround, not a production-grade password storage solution. Production authentication should use a dedicated password hashing algorithm such as Argon2id or bcrypt with appropriate configuration.

#### Challenge 7: Frontend JSX Syntax Error After Removing OTP Verification

**Problem:**

After removing OTP verification from the signup flow, Vite reported:

```text
[plugin:vite:react-babel] Unexpected token (112:3)
```

The OTP-related JSX had been removed, but its surrounding fragment wrappers and conditional rendering syntax remained, resulting in invalid JSX.

**Solution:**

Removed the orphaned JSX fragment wrapper and unnecessary conditional closing syntax, leaving a valid and simplified component return structure.

#### Challenge 8: HTTP 500 Errors Due to Stale Processes and Incorrect Environment Setup

**Problem:**

The signup API continued returning HTTP 500 errors even after changes were made to the authentication code.

Two issues contributed to the problem:

- Multiple Uvicorn processes were running simultaneously, with older processes continuing to serve outdated code.
- The virtual environment had been recreated, leaving it without the required dependencies. Package installation through Git Bash activation was resolving to the system Python instead of the virtual environment.

**Solution:**

- Terminated stale Uvicorn processes running on port `8001`.
- Reinstalled dependencies using the absolute path to the virtual environment's `pip.exe`.
- Restarted the authentication service using the correct environment.

#### Challenge 9: Handling Duplicate User Registration in DynamoDB

**Problem:**

When an existing email address was used during signup, DynamoDB raised:

```text
ConditionalCheckFailedException
```

This happened because the user creation operation included a condition requiring the email attribute not to exist.

Although this behavior correctly prevented duplicate accounts, the exception was not initially handled properly by the API.

**Solution:**

Added explicit exception handling for DynamoDB's `ConditionalCheckFailedException` and converted it into an appropriate HTTP response.

```python
except ClientError as e:
    code = e.response["Error"]["Code"]

    if code == "ConditionalCheckFailedException":
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    raise HTTPException(
        status_code=500,
        detail=f"DB write error: {code}"
    )
```

This ensured duplicate registrations returned HTTP `409 Conflict` instead of an unhandled server error.

---

### 6.3 RAG Service Challenges

#### Challenge 10: Groq and HTTPX Dependency Incompatibility

**Problem:**

The RAG service failed when initializing the Groq client with:

```text
TypeError: Client.__init__() got an unexpected keyword argument 'proxies'
```

The root cause was a compatibility issue between the installed Groq SDK and HTTPX.

The older Groq SDK version (`0.9.0`) passed the `proxies` argument to `httpx.Client`, whereas HTTPX `0.28.0` and later removed support for that argument.

**Solution:**

Updated the Groq dependency requirement from:

```text
groq>=0.9.0
```

to:

```text
groq>=0.13.0
```

Then reinstalled the updated package inside the RAG service's virtual environment.

This resolved the client initialization incompatibility.

---

### 6.4 Environment and Dependency Management Challenges

#### Challenge 11: Windows Virtual Environment Activation Issues

**Problem:**

A recurring issue across the database, authentication, and RAG services was that packages appeared to install successfully but were unavailable when the application started.

This was particularly noticeable when using Git Bash on Windows.

The command:

```bash
source venv/Scripts/activate
pip install -r requirements.txt
```

did not consistently resolve `pip` to the virtual environment's Python installation.

As a result, dependencies were sometimes installed into the system Python rather than the service-specific environment.

**Solution:**

Used the absolute path to the virtual environment's `pip.exe` to ensure dependencies were installed into the correct environment.

Example:

```bash
# Authentication Service
"D:\ai trip itinerary planner\backend\auth-service\venv\Scripts\pip.exe" install -r requirements.txt

# RAG Service
"D:\ai trip itinerary planner\backend\rag\venv\Scripts\pip.exe" install -r requirements.txt

# Database Service
"D:\ai trip itinerary planner\backend\database\venv\Scripts\pip.exe" install -r requirements.txt
```

Alternatively, verified the active pip location before installing packages:

```bash
which pip
```

This helped prevent dependency installation into the wrong Python environment.

---

### 6.5 Summary of Challenges and Resolutions

| # | Component | Challenge | Resolution |
|---|---|---|---|
| 1 | Database | Inconsistent city JSON structures | Added dynamic JSON structure detection and flattening |
| 2 | Database | Misleading Python tracebacks | Cleared stale `__pycache__` files |
| 3 | Database | Missing `boto3` dependency | Installed dependencies in the correct virtual environment |
| 4 | Database | DynamoDB writes not persisting | Added table initialization inside the data loader |
| 5 | Authentication | Signup failures caused by SMTP, CORS, and stale processes | Simplified signup and updated CORS configuration |
| 6 | Authentication | Passlib and Bcrypt incompatibility | Replaced the dependency with a `hashlib` implementation |
| 7 | Frontend | Invalid JSX after OTP removal | Removed orphaned JSX fragments and conditional syntax |
| 8 | Authentication | HTTP 500 due to stale processes and empty virtual environment | Restarted the correct process and reinstalled dependencies |
| 9 | Authentication | Duplicate signup exception | Added explicit DynamoDB exception handling with HTTP 409 |
| 10 | RAG | Groq and HTTPX incompatibility | Updated the Groq SDK dependency |
| 11 | All Services | Windows virtual environment package installation issues | Used the virtual environment's absolute `pip.exe` path |

---

### Key Takeaways

Working through these issues provided practical experience in debugging and maintaining a multi-service application.

The development process strengthened my understanding of:

- Handling inconsistent JSON structures and building robust ETL workflows.
- Debugging Python runtime issues and stale bytecode.
- Integrating AWS DynamoDB using Boto3.
- Managing dependencies across isolated Python environments.
- Troubleshooting CORS, SMTP, and frontend-backend communication.
- Implementing exception handling for database operations.
- Resolving dependency compatibility issues in AI SDK integrations.
- Managing multiple Uvicorn processes and service configurations.
- Maintaining independent environments across a microservices architecture.

These challenges highlighted the importance of dependency management, environment consistency, proper error handling, and systematic debugging when developing full-stack AI applications.

---
## 15. Conclusion

Travora demonstrates how Generative AI and modern backend technologies can be combined to build an intelligent travel planning application.

By integrating RAG, semantic search, Pinecone, Groq LLM, AWS DynamoDB, and FastAPI microservices, the application transforms user travel preferences into personalized day-by-day itineraries.

The project provides practical experience in AI application development, vector databases, cloud integration, backend engineering, and full-stack system design.
