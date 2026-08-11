# Local Setup Instructions - Bedrock POC

**Time to Setup:** ~15 minutes  
**Difficulty:** Easy

---

## **PREREQUISITES**

Before starting, you need:

- ✅ Python 3.8 or higher
- ✅ Git installed
- ✅ AWS Account with Bedrock access
- ✅ AWS credentials configured
- ✅ Text editor (VS Code, Sublime, etc.)

### **Check Python Version**

```bash
python --version
# Expected: Python 3.9.x or higher
```

---

## **STEP 1: Clone the Repository**

### **Option A: From GitHub**

```bash
# Clone the repo
git clone https://github.com/YOUR-USERNAME/bedrock-poc.git

# Navigate into it
cd bedrock-poc
```

### **Option B: From Local Files**

```bash
# Copy project folder
cd C:\Users\YourName\Downloads\bedrock-poc\bedrock-poc

# Verify you see these files:
ls -la
# Should show: app.py, cli.py, requirements.txt, bedrock_poc/, etc.
```

---

## **STEP 2: Create Virtual Environment**

A virtual environment isolates Python packages for this project.

### **On Windows (PowerShell/CMD):**

```bash
# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate

# Expected: (venv) should appear in your prompt
```

### **On macOS/Linux:**

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Expected: (venv) should appear in your prompt
```

---

## **STEP 3: Install Dependencies**

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E "streamlit|pydantic|boto3"
```

**Expected output:** Should show all 3 packages ✅

---

## **STEP 4: Configure AWS Credentials**

You need AWS access to use Bedrock.

### **Option A: AWS CLI Configuration** (Recommended)

```bash
# Configure AWS
aws configure

# Enter when prompted:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region: us-east-1
# Default output format: json
```

### **Option B: Environment Variables**

```bash
# On Windows (PowerShell):
$env:AWS_ACCESS_KEY_ID = "your-access-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-key"
$env:AWS_REGION = "us-east-1"

# On macOS/Linux:
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

### **Option C: Create .env File**

Create file: `.env` in project root

```bash
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

---

## **STEP 5: Verify Bedrock Access**

Test your AWS credentials work:

```bash
# Test AWS CLI
aws bedrock list-foundation-models --region us-east-1

# Expected: Should list available models without error
```

If you get an error, check:
- [ ] AWS credentials are correct
- [ ] IAM user has Bedrock permissions
- [ ] Claude 3.5 Sonnet model is enabled in your region

---

## **STEP 6: Run the Application**

### **Option A: Streamlit Web UI** (Recommended for first-time)

```bash
# Make sure venv is activated
# (venv) should be in your prompt

# Run Streamlit
streamlit run app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Browser will open automatically. If not, go to: `http://localhost:8501`

### **Option B: Command-Line Interface (CLI)**

#### **Chat (Interactive)**
```bash
python cli.py chat

# Then type messages:
you> Hello, what can you do?
bot> I'm a helpful assistant running on Amazon Bedrock...
```

#### **Summarize Document**
```bash
python cli.py summarize --file large_document.txt

# Output: Summary will be printed to console
```

#### **Ask Question About Document**
```bash
python cli.py ask --file large_document.txt --question "What is Bedrock?"

# Output: Answer based on the document
```

#### **Parse Resume**
```bash
python cli.py parse --file resume.pdf

# Output: JSON with name, email, skills, experience, education
```

#### **Q&A with RAG** (For large documents)
```bash
python cli.py ask --file large_document.txt --question "What are key features?" --use-rag

# Output: Answer retrieved from most relevant sections
```

---

## **STEP 7: Test All Features**

### **Using Streamlit Web UI** (Easiest)

Open browser at: `http://localhost:8501`

#### **Test 1: Chat Tab**
1. Click "Chat" tab
2. Type: "What are your capabilities?"
3. Verify: Response appears ✅

#### **Test 2: Summarize Tab**
1. Click "Summarize" tab
2. Paste or upload text (at least 100 words)
3. Click "Summarize"
4. Verify: Summary appears ✅

#### **Test 3: Q&A (Non-RAG)**
1. Click "Q&A" tab
2. Upload or paste `large_document.txt`
3. **Uncheck** "Use RAG" checkbox
4. Type question: "What is Amazon Bedrock?"
5. Click "Ask"
6. Verify: Answer appears ✅

#### **Test 4: Q&A (RAG-Enhanced)**
1. Keep "Q&A" tab open
2. Same document uploaded
3. **Check** "Use RAG" checkbox ✅
4. Same question: "What is Amazon Bedrock?"
5. Click "Ask"
6. Verify: 
   - Info message appears: "Using RAG mode..."
   - Answer appears
   - May take slightly longer (normal) ✅

#### **Test 5: Parse Resume**
1. Click "Parse Resume" tab
2. Paste or upload resume text
3. Click "Parse Resume"
4. Verify: Structured data displays
   - Name, Email, Skills, Experience, Education ✅
5. Click "View Raw JSON" to see JSON output ✅

---

## **TROUBLESHOOTING**

### **Error: "No module named 'streamlit'"**

```bash
# Make sure venv is activated
# (venv) should be in prompt

# Reinstall dependencies
pip install streamlit
```

### **Error: "No module named 'dotenv'"**

```bash
pip install python-dotenv
```

### **Error: "Failed to connect to AWS"**

```bash
# Check AWS credentials
aws configure

# Test connection
aws bedrock list-foundation-models --region us-east-1

# If error, verify:
# 1. AWS credentials are correct
# 2. Region is us-east-1
# 3. IAM user has bedrock:InvokeModel permission
```

### **Error: "Model access denied"**

Go to AWS Bedrock Console:
1. Click "Model access" (left sidebar)
2. Enable: "Claude 3.5 Sonnet"
3. Enable: "Titan Text Embeddings v2"
4. Wait 5 minutes for activation

### **Port 8501 Already in Use**

```bash
# Run on different port
streamlit run app.py --server.port 8502
```

### **Streamlit Blank Page**

```bash
# Clear cache and restart
# Press Ctrl+C to stop
# Delete .streamlit folder:
rm -rf .streamlit

# Run again
streamlit run app.py
```

---

## **PROJECT STRUCTURE**

```
bedrock-poc/
├── bedrock_poc/                 # Core package
│   ├── __init__.py
│   ├── client.py               # Bedrock API wrapper
│   ├── use_cases.py            # Business logic
│   ├── models.py               # Data models
│   └── vector_store.py         # RAG engine
├── app.py                      # Streamlit web UI
├── cli.py                      # CLI commands
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── large_document.txt         # Test document
├── README.md                  # Project overview
├── LOCAL_SETUP.md             # This file
└── screenshots/               # Feature demos
    ├── 01-chat.png
    ├── 02-summarize.png
    ├── 03-resume.png
    ├── 04-qa-no-rag.png
    └── 05-qa-with-rag.png
```

---

## **ENVIRONMENT VARIABLES** (Optional)

Create `.env` file in project root:

```bash
# Optional: Override default model
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Optional: Override default region
AWS_REGION=us-east-1
```

---

## **QUICK START SUMMARY**

```bash
# 1. Clone/navigate to project
cd bedrock-poc

# 2. Create and activate venv
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure AWS
aws configure  # Enter your credentials

# 5. Run the app
streamlit run app.py

# 6. Open browser
# http://localhost:8501
```

---

## **GETTING HELP**

**If something doesn't work:**

1. Check error message carefully
2. Try troubleshooting section above
3. Verify:
   - [ ] Python version is 3.8+
   - [ ] Virtual environment is activated
   - [ ] All dependencies installed: `pip list`
   - [ ] AWS credentials configured: `aws sts get-caller-identity`
   - [ ] Bedrock models enabled in AWS console

---

## **NEXT STEPS**

Once running locally, you can:
- Explore different models (edit `client.py`)
- Customize prompts (edit `use_cases.py`)
- Modify UI (edit `app.py`)
- Add new features (new functions in `use_cases.py`)

---

**Questions?** Check `README.md` for more details or contact support.

Happy testing! 🚀
