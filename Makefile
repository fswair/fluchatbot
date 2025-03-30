clean:
	@rm -f ./database/*.lock
	@rm -f ./sessions/*.session-journal
	@rm -rf ./__pycache__
	@rm -rf ./config/__pycache__
	@rm -f ./logs/*.log

	@echo "Cleaned up the project directory."

	@mkdir -p ./database
	@mkdir -p ./sessions
	@mkdir -p ./logs

	@echo "Created the database and sessions directories (if they didn't exist)."
	@echo "Created the env file (if it didn't exist)."
	@touch ./config/.env.sample

	@echo "# database directory to store database files" > ./database/blank.md
	@echo "# sessions directory to store telegram sessions" > ./sessions/blank.md

drop:
	@make clean
	@rm -f ./database/*.lock ./database/*.json
	@rm -f ./sessions/*.session-journal ./sessions/*.session
	@rm -rf ./__pycache__
	@rm -rf ./config/__pycache__ 
	@echo "Database has dropped."

build:
	make clean
	@echo "Building the project..."
	@echo "Installing dependencies..."
	@if [ "$(shell uname)" = "Darwin" ]; then \
		python3 -m pip install -r requirements.txt; \
	elif [ "$(shell uname)" = "Linux" ]; then \
		python3 -m pip install -r requirements.txt; \
	else \
		python -m pip install -r requirements.txt; \
	fi

clear:
	@cls || clear