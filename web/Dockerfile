FROM php:8.2-apache

# Installiere mysqli-Erweiterung für MySQL-Verbindung
RUN docker-php-ext-install mysqli

# Kopiere die Webseite
COPY index.php /var/www/html/

# Setze Berechtigungen
RUN chown -R www-data:www-data /var/www/html