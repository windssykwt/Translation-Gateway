# Translation API Gateway

Modular Flask application for handling translation requests via Cloud or Local APIs with auto-switching capabilities.

## Features

- **Dual Mode Operation**: Switch between Cloud and Local translation APIs
- **Auto-Failover**: Automatic switching to backup API if primary fails
- **Background Monitoring**: Constant health checks for API availability
- **Context Buffer**: Maintains translation context for better consistency
- **MORT Format Support**: Specialized formatting for game localization
- **Secure Configuration**: Environment-based configuration with .env files
- **Modular Architecture**: Clean separation of concerns with organized folder structure

## Project Structure

```
Custom Cloud/
├── .env                    # Environment variables (API keys, config)
├── .env.example           # Configuration template
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── main.py               # Application entry point
├── README.md             # This documentation
├── src/                  # Source code
│   ├── __init__.py
│   ├── app.py           # Flask application factory
│   ├── config.py        # Configuration management
│   ├── translators/     # Translation engines
│   │   ├── __init__.py
│   │   ├── cloud_translator.py
│   │   └── local_translator.py
│   ├── routes/          # API endpoints
│   │   ├── __init__.py
│   │   ├── translation.py
│   │   └── health.py
│   └── utils/           # Utility functions
│       ├── __init__.py
│       ├── validators.py
│       └── formatters.py
├── logs/                # Log files directory
└── tests/               # Unit tests
    └── __init__.py
```

## Installation

### Method 1: With Virtual Environment (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/windssykwt/Translation-Gateway
   cd "Translation-Gateway"
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and preferences
   ```

6. **Create logs directory:**
   ```bash
   mkdir logs
   ```

7. **Start the application:**
   ```bash
   python main.py
   ```

8. **Deactivate when done:**
   ```bash
   deactivate
   ```

### Method 2: Without Virtual Environment (Quick Test)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/windssykwt/Translation-Gateway
   cd "Translation-Gateway"
   ```

2. **Install dependencies directly:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and preferences
   ```

4. **Create logs directory:**
   ```bash
   mkdir logs
   ```

5. **Start the application:**
   ```bash
   python main.py
   ```

### Virtual Environment Troubleshooting

**Common Issues:**

1. **"python is not recognized" (Windows):**
   - Use `py` instead of `python`: `py -m venv venv`
   - Ensure Python is installed and added to PATH

2. **"activate script not found":**
   - Verify venv folder was created
   - Use correct activation script for your OS:
     - Windows: `venv\Scripts\activate`
     - Linux/Mac: `source venv/bin/activate`

3. **Permission denied:**
   ```bash
   # Linux/Mac - fix permissions
   chmod +x venv/bin/activate
   ```

4. **Virtual environment already exists:**
   ```bash
   # Remove and recreate
   rm -rf venv
   python -m venv venv
   ```

5. **Dependencies installation fails:**
   ```bash
   # Upgrade pip first
   pip install --upgrade pip
   # Then install requirements
   pip install -r requirements.txt
   ```

**Why Use Virtual Environment?**
- ✅ Isolates project dependencies from system Python
- ✅ Prevents version conflicts between projects
- ✅ Easy deployment to different environments
- ✅ Team collaboration consistency
- ✅ Better security and stability

## Configuration

### Environment Variables (.env)

```env
# Main operation mode
ACTIVE_MODE=Cloud  # Options: Cloud, Local

# Logging
ENABLE_CONTROL_LOG=False

# Primary Cloud API
PRIMARY_CLOUD_URL=https://api.intelligence.io.solutions/api/v1/chat/completions
PRIMARY_CLOUD_KEY=your_primary_api_key_here
PRIMARY_CLOUD_MODEL=meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
PRIMARY_CLOUD_TEMPERATURE=0.7
PRIMARY_CLOUD_ENABLE_CONTEXT=True

# Secondary Cloud API (Backup)
SECONDARY_CLOUD_URL=https://api.intelligence.io.solutions/api/v1/chat/completions
SECONDARY_CLOUD_KEY=your_secondary_api_key_here
SECONDARY_CLOUD_MODEL=Qwen/Qwen3-Next-80B-A3B-Instruct
SECONDARY_CLOUD_TEMPERATURE=0.7
SECONDARY_CLOUD_ENABLE_CONTEXT=True

# Local API (Ollama)
LOCAL_API_URL=http://localhost:11434/v1/chat/completions
LOCAL_API_KEY=
LOCAL_API_MODEL=zongwei/gemma3-translator:4b
LOCAL_API_TEMPERATURE=0.0
LOCAL_API_ENABLE_CONTEXT=False

# MORT Format Separator
SAFE_SEPARATOR=//////
```

## Usage

### Starting the Application

```bash
python main.py
```

The server will start on `http://localhost:5000` by default.

### API Endpoints

#### 1. Translation Endpoint
**POST** `/translate`

Request body:
```json
{
    "text": "Hello world\n//////\nHow are you?",
    "source": "en",
    "target": "id"
}
```

Response:
```json
{
    "result": ["Halo dunia\n//////\nApa kabar?"],
    "errorCode": "0",
    "errorMessage": ""
}
```

#### 2. Health Check Endpoint
**GET** `/health`

Response:
```json
{
    "status": "healthy",
    "mode": "Cloud",
    "cloud_primary_available": true,
    "cloud_secondary_available": true
}
```

#### 3. Configuration Endpoint
**GET** `/config`

Response:
```json
{
    "active_mode": "Cloud",
    "control_log_enabled": false,
    "safe_separator": "//////",
    "cloud_primary": {
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "temperature": 0.7,
        "context_enabled": true,
        "has_key": true
    },
    "cloud_secondary": {
        "model": "Qwen/Qwen3-Next-80B-A3B-Instruct",
        "temperature": 0.7,
        "context_enabled": true,
        "has_key": true
    },
    "local": {
        "model": "zongwei/gemma3-translator:4b",
        "temperature": 0.0,
        "context_enabled": false,
        "url": "http://localhost:11434/v1/chat/completions"
    }
}
```

## Features Explanation

### Auto-Failover System
- **Primary API**: Main translation service
- **Secondary API**: Backup service that activates when primary fails
- **Background Monitoring**: Constant health checks with automatic recovery

### Context Buffer
- Maintains last 2 translation segments for context
- Improves consistency in dialog translations
- Configurable per API

### MORT Format Support
- Specialized separator format for game localization
- Automatic validation and formatting
- Preserves structure and line breaks

### Logging System
- Configurable detailed logging
- Request/response tracking
- Error categorization
- Background monitoring logs

## Development

### Adding New Translators

1. Create new translator class in `src/translators/`
2. Implement required methods:
   - `__init__(config)`
   - `handle_request(data, request_id, app_logger)`

3. Update configuration in `src/config.py`
4. Register in `src/app.py`

### Adding New Routes

1. Create route file in `src/routes/`
2. Define Flask routes
3. Register in `src/app.py`

### Testing

```bash
# Run tests (when implemented)
python -m pytest tests/

# Test API endpoints
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello","source":"en","target":"es"}'
```

## Security

- **Environment Variables**: Sensitive data stored in .env files
- **Input Validation**: Request validation and sanitization
- **Error Handling**: Secure error responses without information leakage
- **Logging**: No sensitive information logged

## Dependencies

### Core Dependencies (requirements.txt)
- **Flask 2.3.3**: Web framework
- **Requests 2.31.0**: HTTP client for API calls
- **python-dotenv 1.0.0**: Environment variable management

### Optional Development Dependencies
- **pytest 7.4.2**: Testing framework
- **pytest-flask 1.2.0**: Flask testing utilities
- **black 23.7.0**: Code formatter
- **flake8 6.0.0**: Linter

Install optional dependencies:
```bash
pip install pytest pytest-flask black flake8
```

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Check .env file for correct API keys
   - Ensure .env is in the same directory as main.py

2. **Import Errors**:
   - Verify all dependencies are installed
   - Check Python path includes src directory

3. **Permission Errors**:
   - Ensure logs directory exists and is writable
   - Check file permissions for .env

4. **Connection Errors**:
   - Verify API URLs are accessible
   - Check network connectivity for cloud APIs
   - Ensure Ollama is running for local mode

### Debug Mode

Enable detailed logging by setting:
```env
ENABLE_CONTROL_LOG=True
```

This will provide:
- Request/response logging
- API communication details
- Background monitoring status
- Translation context tracking

## License

This project is part of the MORT (Modular Open Translation) system for game localization.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files in `logs/` directory
3. Verify configuration in .env file

4. Test individual API endpoints
