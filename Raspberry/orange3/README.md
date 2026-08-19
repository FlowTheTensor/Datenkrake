<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Orange3

Interaktive Orange3-Umgebung fuer den Unterricht zum Vergleich von ML-Modellen. Der Zugriff erfolgt per Browser ueber noVNC auf Port `6080`.

Es gibt kein offizielles `biolab/orange3`-Image auf Docker Hub - nur nicht vertrauenswuerdige Drittanbieter-Images. Das Image wird deshalb hier lokal aus einem eigenen Dockerfile gebaut: Ubuntu-Basis mit Orange3 (per `pip` in einem venv installiert) sowie Xvfb, x11vnc und noVNC fuer den Browserzugriff.
