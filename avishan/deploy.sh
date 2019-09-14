#!/bin/bash
# todo interactive shell
virtualenv venv

. venv/bin/activate

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py avishan_init

deactivate


[[ "$UID" -eq 0 ]] || exec sudo "$0" "$@"

sudo touch /etc/systemd/system/gunicorn_$1.service

sudo echo "[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=afshari9978
Group=www-data
WorkingDirectory=/home/afshari9978/workspace/$1
ExecStart=/home/afshari9978/workspace/$1/venv/bin/gunicorn \
          --timeout 90 \
          --access-logfile - \
          --workers 1 \
          --bind unix:/home/afshari9978/workspace/$1/gunicorn.sock \
          $1.wsgi:application

[Install]
WantedBy=multi-user.target" >> /etc/systemd/system/gunicorn_$1.service

echo "sudo systemctl start gunicorn_$1.service"

echo "sudo systemctl enable gunicorn_$1.service"

echo "echo \"alias $2pull='pushd /home/afshari9978/workspace/$1/; git pull https://afshari9978:moriaf1050137354%40Gitlab@gitlab.com/afshari9978/$1.git master; pushd avishan/; git pull https://afshari9978:moriaf1050137354%40Gitlab@gitlab.com/afshari9978/avishan.git master; popd; popd'
alias $2reload='sudo systemctl restart gunicorn_$1.service; pushd /home/afshari9978/workspace/$1/; source venv/bin/activate; python manage.py makemigrations; python manage.py migrate; deactivate; popd'
alias $2log='sudo journalctl -n 100 -fu gunicorn_$1.service'\" >> ~/.bashrc"

sudo touch /etc/nginx/sites-available/$2.coleo.ir

sudo echo "server {
    listen 80;
    server_name $2.coleo.ir;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/afshari9978/workspace/$1;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/afshari9978/workspace/$1/gunicorn.sock;
    }
}" > /etc/nginx/sites-available/$2.coleo.ir

sudo ln -s /etc/nginx/sites-available/$2.coleo.ir /etc/nginx/sites-enabled/

sudo systemctl restart nginx