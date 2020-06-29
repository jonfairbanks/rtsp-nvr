# rtsp-nvr
RTSP NVR

python .\manage.py db init
python .\manage.py migrate
python .\manage.py db upgrade
python .\__main__.py --ip 0.0.0.0 --port 8000