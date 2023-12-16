# Kubernetes-commands
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot "/var/www/html/moodle"
    ServerName domainname.com

    <Directory "/var/www/html/moodle">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    <Directory "/var/moodledata">
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    <IfModule mod_dir.c>
        DirectoryIndex index.php
    </IfModule>

    ErrorLog ${APACHE_LOG_DIR}/moodle_error.log
    CustomLog ${APACHE_LOG_DIR}/moodle_access.log combined
</VirtualHost>
