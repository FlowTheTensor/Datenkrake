FROM php:8.2-apache

# Installiere mysqli-Erweiterung für MySQL-Verbindung
RUN docker-php-ext-install mysqli

# Kopiere die Webseite (Build-Context ist die Repo-Wurzel, siehe compose/docker-compose.yml)
COPY Raspberry/web/audiodaten.php /var/www/html/
COPY Raspberry/web/plcdaten.php /var/www/html/
COPY Raspberry/web/index.html /var/www/html/
COPY Raspberry/web/index.css /var/www/html/index.css
COPY Raspberry/web/index.js /var/www/html/index.js
COPY Raspberry/web/content-loader.js /var/www/html/content-loader.js
COPY Raspberry/web/content /var/www/html/content
COPY Images/DatenbankAkustik.jpg /var/www/html/DatenbankAkustik.jpg
COPY Images/DatenbankPLC.jpg /var/www/html/DatenbankPLC.jpg
COPY Images/krake_klein.jpg /var/www/html/krake_klein.jpg
COPY Images/krake_klein.png /var/www/html/krake_klein.png
COPY Images/crisp-dm.svg /var/www/html/crisp-dm.svg
COPY Raspberry/web/api /var/www/html/api
COPY Raspberry/web/includes /var/www/html/includes

# datenkrake.local soll standardmäßig den Leitstand ausliefern.
RUN printf "DirectoryIndex index.html audiodaten.php\n" > /etc/apache2/conf-available/datenkrake.conf \
 && a2enconf datenkrake

# Setze Berechtigungen
RUN chown -R www-data:www-data /var/www/html