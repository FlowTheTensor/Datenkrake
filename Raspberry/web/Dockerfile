FROM php:8.2-apache

# Installiere mysqli-Erweiterung für MySQL-Verbindung
RUN docker-php-ext-install mysqli

# Kopiere die Webseite (Build-Context ist die Repo-Wurzel, siehe compose/docker-compose.yml)
COPY Raspberry/web/index.php /var/www/html/
COPY leitstand.html /var/www/html/

# Setze Berechtigungen
RUN chown -R www-data:www-data /var/www/html