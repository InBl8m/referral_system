source myenv/bin/activate

python manage.py makemigrations

python manage.py migrate

python manage.py runserver 0.0.0.0:8000

celery -A referral_system worker --loglevel=info

celery -A referral_system flower

