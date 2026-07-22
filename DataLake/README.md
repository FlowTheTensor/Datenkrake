# Data Lake (MinIO, Nessie, Spark/Jupyter)

Ein **Lakehouse** ergänzt die bisherigen Speicherorte (MariaDB, InfluxDB)
um eine dritte, andersartige Ebene: statt Daten in einer Datenbank-Engine
einzusperren, landen sie als offene Parquet-Dateien in einem
S3-kompatiblen Objektspeicher (**MinIO**) – nutzbar von jedem Werkzeug,
das das offene [Apache-Iceberg](https://iceberg.apache.org/)-Tabellenformat
spricht (Spark, Trino, DuckDB, ...). **Nessie** legt darüber eine
Git-artige Versionierung: Tabellen lassen sich branchen, committen,
zusammenführen – "Git für Daten". **Spark/Jupyter** ist die
Verarbeitungsebene, in der Notebooks genau das zeigen.

## ⚠️ Bewusst NICHT auf dem Raspberry Pi

Dieser Stack ist deutlich ressourcenhungriger als der IoT-Stack unter
`../Raspberry/` (Spark allein will mehrere GB RAM). Er läuft deshalb als
**eigener, unabhängiger Compose-Stack** auf einem separaten Rechner
(Schulserver, Lehrer-PC) – nicht auf dem Pi. Einzige Voraussetzung:
Netzzugriff auf `datenkrake.local` (bzw. die IP des Pi), um die
Telemetriedaten aus der MariaDB zu laden.

## Setup

```bash
cd DataLake/compose
docker compose up -d
```

Die drei Dienste bauen aufeinander auf und brauchen etwas Zeit (`nessie`
wartet auf `minio`, `spark-notebook` auf `nessie`). Erster Blick nach dem
Start:

| Dienst | URL | Zugangsdaten |
|---|---|---|
| Jupyter | http://localhost:8888 | Token: siehe `JUPYTER_TOKEN` in `docker-compose.yml` |
| MinIO-Konsole | http://localhost:9001 | siehe `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` |
| Nessie-API | http://localhost:19120/api/v2/config | keine (siehe Sicherheitshinweis) |

Dann `notebooks/01_lakehouse_intro.ipynb` öffnen und Zelle für Zelle
durchgehen.

## Woher die Konfiguration stammt

Die MinIO/Nessie/Spark-Verdrahtung ist **nicht geraten**, sondern direkt
aus dem offiziellen Nessie-Repository
([`docker/catalog-auth-s3/docker-compose.yml`](https://github.com/projectnessie/nessie/blob/main/docker/catalog-auth-s3/docker-compose.yml))
übernommen und vereinfacht – dort läuft dieselbe Kombination inklusive
Keycloak-Authentifizierung. Für den Unterricht im geschützten Schulnetz
habe ich die Auth-Schicht bewusst weggelassen (siehe Sicherheitshinweis
unten), Grundkonfiguration und Versionsstände (Nessie 0.108.2) stammen
von dort.

## ⚠️ Sicherheitshinweis

**Kein Dienst in diesem Stack hat eine Anmeldung** (Nessie-API, Jupyter
nur mit einem einfachen Token, MinIO mit einem einzigen Root-Nutzer). Für
den Unterricht im geschützten Schulnetz vertretbar, für den
Dauerbetrieb oder ein Netz mit weniger Vertrauen unbedingt nachrüsten:

- Nessie: [Authentifizierung via Keycloak/OIDC](https://github.com/projectnessie/nessie/blob/main/docker/catalog-auth-s3/docker-compose.yml) (das Original-Beispiel, von dem dieser Stack abgeleitet ist)
- MinIO: zusätzliche, eingeschränkte Nutzer statt des Root-Kontos für den täglichen Zugriff
- Jupyter: `JUPYTER_TOKEN` durch ein starkes, geheimes Token ersetzen

## Persistenz

Der Nessie-Katalog läuft mit `IN_MEMORY`-Version-Store: **Branches und
Commit-Historie gehen bei jedem Neustart des `nessie`-Containers
verloren** (die Parquet-Dateien selbst bleiben in MinIO erhalten, nur die
Nessie-eigene Versionierung nicht). Für Dauerbetrieb einen persistenten
Store konfigurieren, siehe [Nessie-Konfiguration](https://projectnessie.org/nessie-latest/configuration/)
(z. B. JDBC/Postgres, wie im `all-in-one`-Beispiel des Nessie-Repos).

## Bekannte Einschränkungen

- Alle Zugangsdaten (`changeMeDatalake` etc.) sind Platzhalter wie bei
  den übrigen Diensten in diesem Repo.
- Die Paketversionen im Notebook (`nessie-spark-extensions`,
  `iceberg-spark-runtime`, `iceberg-aws-bundle`) müssen zur im
  `jupyter/pyspark-notebook:latest`-Image tatsächlich installierten
  Spark-Version passen. Das Notebook prüft das in der ersten Code-Zelle;
  bei einer Abweichung dort die Versionszahl in den Paket-Koordinaten
  anpassen (Anleitung dort verlinkt).
- Kein JDBC-Connector für den MariaDB-Import – bewusst über
  `pandas`/`pymysql` gelöst, um einen weiteren versionssensitiven
  Baustein zu vermeiden. Für sehr große Datenmengen ist ein echter
  JDBC-Connector performanter (Hinweis dazu am Ende des Notebooks).
