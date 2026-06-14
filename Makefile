.PHONY: setup setup-backend setup-frontend generate-data generate-ev-data train evaluate dev dev-backend dev-frontend test clean

# Full setup
setup: setup-backend setup-frontend generate-data train

setup-backend:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r backend/requirements.txt

setup-frontend:
	cd frontend && npm install

# Data generation and model training
generate-data:
	.venv/bin/python3 backend/scripts/generate_data.py

generate-ev-data:
	.venv/bin/python3 backend/scripts/generate_ev_data.py

train:
	.venv/bin/python3 backend/scripts/train_models.py

evaluate:
	.venv/bin/python3 backend/scripts/evaluate_models.py

# Development servers
dev: dev-backend dev-frontend

dev-backend:
	.venv/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

# Testing
test:
	.venv/bin/python3 -m pytest backend/tests/ -v

clean:
	rm -rf backend/data/*.csv backend/artifacts/*.joblib .venv frontend/node_modules frontend/.next
