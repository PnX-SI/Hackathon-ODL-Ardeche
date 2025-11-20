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

GPKG := data.gpkg
DB_CONN := "host=$(DB_HOST) port=$(DB_PORT) dbname=$(DB_NAME) user=$(DB_USER) password=$(DB_PASSWORD)"

SQL_SEED := migrations/create_tables.sql

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

	@echo "Activation de PostGIS dans $(DB_NAME)..."
	# Active les extensions PostGIS, seulement si elles ne le sont pas déjà
	@psql -U postgres -h $(DB_HOST) -p $(DB_PORT) -d $(DB_NAME) -c "CREATE EXTENSION IF NOT EXISTS postgis;"
	@psql -U postgres -h $(DB_HOST) -p $(DB_PORT) -d $(DB_NAME) -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
	@echo "PostGIS activé dans $(DB_NAME) !"

# ================================
# 4. Peuple la base via SQL externe
# ================================
seed:
	@echo "Peuplement de la base avec $(SQL_SEED)..."
	@psql -U $(DB_USER) -h $(DB_HOST) -p $(DB_PORT) -d $(DB_NAME) -f $(SQL_SEED)
	@echo "Base peuplée."

import_gpkg:
	@echo "Import du GeoPackage dans PostgreSQL..."
	ogr2ogr -f PostgreSQL PG:$(DB_CONN) $(GPKG) -nln building_data batiments -overwrite
	@echo "Import terminé."

# ================================
# Nettoyage
# ================================
clean:
	rm -rf $(VENV)
	@echo "Suppression du venv (la base PostgreSQL n'est pas supprimée)."

.PHONY: all venv install db seed clean
