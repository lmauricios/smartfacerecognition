# Facial Recognition System

A complete facial recognition system with Python backend, using FastAPI, OpenCV, and face_recognition.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Structure

```
backend/
├── api/               # API Endpoints
├── core/             # Core facial recognition logic
├── data_access/      # Database access layer
├── face_detector/    # Pre-trained facial detection models
├── models/           # Data schemas and models
├── services/         # Service layer
├── terraform/        # Infrastructure configurations
└── utils/            # Utilities and configurations
```

## Main Features

- Facial detection using OpenCV DNN
- Facial recognition using face_recognition
- REST API with FastAPI
- Video streaming support
- Face storage in PostgreSQL
- Face mask detection
- Graphical interface for testing (v1 and v2 versions)
- Detailed operation logging
- Facial similarity metrics
- Infrastructure as code with Terraform

## Requirements

```python
fastapi==0.111.0
uvicorn[standard]==0.29.0
psycopg2-binary==2.9.9
opencv-python-headless==4.9.0.80
numpy==1.26.4
dlib==19.24.4
face_recognition==1.3.0
python-dotenv==1.0.1
pydantic==2.7.1
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env` file:
   ```env
   DB_HOST=localhost
   DB_NAME=facial_recognition
   DB_USER=my_user
   DB_PASS=your_password
   ```

3. Ensure facial detection models are present in `face_detector/`:
   - deploy.prototxt
   - res10_300x300_ssd_iter_140000.caffemodel

## Usage

### REST API

The system exposes REST endpoints for:
- Registering new people
- Facial identification in images
- Real-time video streaming recognition

### Video Streaming

1. Start the streaming server:
   ```bash
   python video_stream_server.py
   ```

2. Run the recognition client:
   ```bash
   python facial_recognition.py
   ```

### Graphical Interface

For interactive testing, use the GUI versions:
```bash
python adm/facial_recognition-v1.py
# or
python adm/facial_recognition-v2.py
```

## Architecture

### Core

- `FaceProcessor`: Main class for facial processing
  - Detection using OpenCV DNN
  - Feature extraction using face_recognition
  - Facial similarity calculation

### API

- REST endpoints using FastAPI
- Authentication and data validation
- Automatic documentation (OpenAPI/Swagger)

### Database

- PostgreSQL for storing:
  - Personal data
  - Facial encodings
  - Reference images

### Infrastructure

- GCP configuration with Terraform
- Cloud Run for deployment
- Cloud SQL for database
- Cloud Storage for image storage

## Technical Features

- Detection confidence threshold: 0.5
- Facial recognition tolerance: 0.6
- Configurable minimum similarity
- Support for facial landmarks
- Adaptation for mask recognition
- Detailed operation logging

## Development

The project follows a layered architecture:
- API (Routes and Controllers)
- Services (Business Logic)
- Core (Image Processing)
- Data Access (Database)
- Utils (Configurations and Helpers)

## Database Structure

The system uses PostgreSQL as its database. Here's the main table structure:

### Table: pessoas (people)

```sql
CREATE TABLE pessoas (
    id SERIAL PRIMARY KEY,
    nome_pessoa VARCHAR(100) UNIQUE NOT NULL,
    face_encoding BYTEA NOT NULL,
    imagem_path VARCHAR(255)
);
```

Field descriptions:
- `id`: Auto-incrementing primary key
- `nome_pessoa`: Person's name (unique identifier)
- `face_encoding`: Binary storage of facial features (128-dimensional vector)
- `imagem_path`: Optional path to the stored image file (used by CRUD interface)

### Database Configuration

1. Create the database:
   ```sql
   CREATE DATABASE reconhecimento_facial;
   ```

2. Create the user and grant permissions:
   ```sql
   CREATE USER meu_usuario WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE reconhecimento_facial TO meu_usuario;
   ```

3. Connect to the database and create the table:
   ```sql
   \c reconhecimento_facial
   
   CREATE TABLE pessoas (
       id SERIAL PRIMARY KEY,
       nome_pessoa VARCHAR(100) UNIQUE NOT NULL,
       face_encoding BYTEA NOT NULL,
       imagem_path VARCHAR(255)
   );
   ```

4. Grant table permissions:
   ```sql
   GRANT ALL PRIVILEGES ON TABLE pessoas TO meu_usuario;
   GRANT USAGE, SELECT ON SEQUENCE pessoas_id_seq TO meu_usuario;
   ```

### Important Notes:
- The `face_encoding` field stores a 128-dimensional vector as binary data
- Each face encoding is generated using the face_recognition library
- The system uses these encodings for facial comparison and recognition
- The `imagem_path` field is used by the CRUD interface to store reference images

## Contributing

1. Fork the project
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
