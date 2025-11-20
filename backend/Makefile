# ================================
# Variables
# ================================
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

DB_NAME := hackathon
DB_USER := hackathon
DB_HOST := localhost
DB_PORT := 5432

SQL_SEED := seed.sql

# ================================
# Cible par défaut
# ================================
all: venv install db seed

# ================================
# 1. Création du venv
# ================================
venv:
	test -d $(VENV) || python3 -m venv $(VENV)

# ================================
# 2. Installation des dépendances
# ================================
install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# ================================
# 3. Création de la base PostgreSQL
# ================================
db:
	@echo "Création de la base PostgreSQL..."
	@psql -U $(DB_USER) -h $(DB_HOST) -p $(DB_PORT) -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='$(DB_NAME)';" | grep -q 1 || \
		psql -U $(DB_USER) -h $(DB_HOST) -p $(DB_PORT) -d postgres -c "CREATE DATABASE $(DB_NAME);"
	@echo "Base créée ou déjà existante : $(DB_NAME)"

# ================================
# 4. Peuple la base via SQL externe
# ================================
seed:
	@echo "Peuplement de la base avec $(SQL_SEED)..."
	@psql -U $(DB_USER) -h $(DB_HOST) -p $(DB_PORT) -d $(DB_NAME) -f $(SQL_SEED)
	@echo "Base peuplée."

# ================================
# Nettoyage
# ================================
clean:
	rm -rf $(VENV)
	@echo "Suppression du venv (la base PostgreSQL n'est pas supprimée)."

.PHONY: all venv install db seed clean
