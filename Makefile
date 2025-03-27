# Paths
BACKEND_DIR=backend
FRONTEND_DIR=frontend-react

PYTHON=python3
PIP=pip3

# ========================
# 📦 INSTALLATION
# ========================

install:
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	cd $(FRONTEND_DIR) && npm install

# ========================
# 🚀 DEVELOPMENT MODE
# ========================

run-backend:
	cd $(BACKEND_DIR) && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd $(FRONTEND_DIR) && npm start

dev:
	make -j2 run-backend run-frontend

# ========================
# 🏗️ PRODUCTION BUILD
# ========================

build:
	cd $(FRONTEND_DIR) && npm run build


# ========================
# 🚦 TEST FULL STACK
# ========================

start:
	make -j2 run-backend run-frontend



# ========================
# 🧹 CLEANING
# ========================



clean:
	find . -name "__pycache__" -type d -exec rm -r {} +
	rm -rf $(FRONTEND_DIR)/node_modules
	rm -rf $(FRONTEND_DIR)/build
	rm -rf .pytest_cache

# ========================
# 📝 ENV EXAMPLE
# ========================

env-example:
	@echo "AZURE_OPENAI_ENDPOINT=your-endpoint" > .env.example
	@echo "AZURE_OPENAI_KEY=your-key" >> .env.example
	@echo "AZURE_OPENAI_DEPLOYMENT=gpt-4" >> .env.example
	@echo "REACT_APP_SPEECH_KEY=your-speech-key" >> .env.example
	@echo "REACT_APP_SPEECH_REGION=westeurope" >> .env.example
