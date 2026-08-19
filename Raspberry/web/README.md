<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Weboberflaeche

Dieser Ordner enthaelt die Apache/PHP-Weboberflaeche mit Leitstand sowie getrennten Audio- und PLC-Uebersichten.

Der Dienst wird ueber Docker Compose gestartet und ist auf Port `80` erreichbar. `index.html` ist die Startseite, `audiodaten.php` und `plcdaten.php` sind die Datenuebersichten. Die Endpunkte liegen unter `api/`, die gemeinsame Datenbankverbindung unter `includes/db.php`.