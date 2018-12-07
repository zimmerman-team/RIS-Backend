DEBUG=False
DJANGO_SETTINGS_MODULE='ris.settings'
RIS_CACHES_DEFAULT_BACKEND='redis_cache.RedisCache'
RIS_CACHES_DEFAULT_LOCATION='redis:6379'
RIS_DB_CONN_MAX_AGE=500
RIS_DB_ENGINE='django.db.backends.postgresql'
RIS_DB_HOST='' # postgres db host name; 'localhost' | 'postgres'
RIS_DB_NAME='' # postgres db name
RIS_DB_PASSWORD='' # postgres db password
RIS_DB_PORT=5432 # postgres db port
RIS_DB_USER='' # postgres db user
RIS_EMAIL_HOST_PASSWORD='SECRET_CODE'
RIS_EMAIL_HOST_USER='zimmermanzimmermantest@gmail.com'
RIS_EMAIL_HOST='smtp.gmail.com'
RIS_EMAIL_PORT=587
RIS_EMAIL_USE_TLS=True
RIS_SITE_ID=3
MAILGUN_ACCOUNT='' # use your own mailgun account
MAILGUN_KEY='' # use your own mailgun key
MAILGUN_MAIL='' # use your own mailgun email
FRONTEND_URL='http://localhost:3000/' # frontend url that uses this backend app
ACCOUNT_EMAIL_CONFIRMATION_URL = FRONTEND_URL + 'verify-email/{}'
ACCOUNT_PASSWORD_RESET_CONFIRM = FRONTEND_URL + 'wachtwoord-reset/bevestigen/'
RIS_RQ_REDIS_URL='redis://redis:6379/0'
RIS_MUNICIPALITY='' # Almere | Utrecht | Rotterdam
COLOR={
    'Rotterdam': '#00AC5B',
    'Almere': '#018FB3',
    'Utrecht': '#CC0200',
}
