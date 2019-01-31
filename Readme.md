[![License: AGPLv3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://github.com/zimmerman-zimmerman/ris-backend/blob/master/License.md)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/be81450219f44b509fabcf7918af9b5c)](https://www.codacy.com/app/zimmerman-zimmerman/RIS-Backend?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=zimmerman-zimmerman/RIS-Backend&amp;utm_campaign=Badge_Grade)

# Raads Informatie Portaal (RIS) - Back-end
--------

NL | Het Raads informatie Portaal (RIS) levert open-source software voor Nederlandse Gemeente om alle besluiten die door de raad worden genomen te volgen. Nederlandse griffies kunnen gebruik maken van de de online agenda om vergaderingen te organiseren. Burgers kunnen alle besluiten en agende punten volgen en inloggen om zo hun eigen dossier aan te maken en te volgen. Raadsdocumenten kunnen worden ontsloten en via de zoekmachine zijn deze voor iederen vindbaar en inzichtelijk. Alle data welke reeds is ontsloten via Ibabs of Notubiz wordt automatisch ingelezen. RIS is een iniatief van de <a href="https://gemeenteraad.almere.nl/" target="_blank">Gemeente Almere</a>. Je hebt de <a href="https://github.com/zimmerman-zimmerman/Raads-Informatie-Portaal-RIS" target="_blank">Raads-Informatie-Portaal-RIS</a> front-end nodig om deze back-end in te zetten of je kunt zelf een front-end bouwen op deze API.

UK | The local council information Portal (RIS) is open-source software that can be used by Dutch municipalities to track decisions made by the council. Registrars to the dutch municipalities ('griffie') are able to setup agenda's for the council. Civil society is able to track all information published by the municipality and is able to create Dossiers to track specific subjects handled by the municipality. All files published by the municipality are indexed and made available using a search engine. RIS is an iniative by the <a href="https://gemeenteraad.almere.nl/" target="_blank">municipality of Almere</a>. You require <a href="https://github.com/zimmerman-zimmerman/Raads-Informatie-Portaal-RIS" target="_blank">Raads-Informatie-Portaal-RIS</a> front-end to use this back-end or you could build your custom front-end UI on top of this API.

## About the project
--------
* Authors: <a href="https://www.zimmermanzimmerman.nl/" target="_blank">Zimmerman & Zimmerman</a>
* Municipalities: <a href="https://gemeenteraad.almere.nl/" target="_blank">Municipality of Almere</a>
* License: AGPLv3 (see included <a href="https://github.com/zimmerman-zimmerman/ris-backend/blob/master/License.md" target="_blank">LICENSE</a> file for full license)
* Github Repo: <a href="https://github.com/zimmerman-zimmerman/ris-backend/" target="_blank">github.com/zimmerman-zimmerman/ris-backend/</a>
* Bug Tracker: <a href="https://github.com/zimmerman-zimmerman/ris-backend/issues" target="_blank">github.com/zimmerman-zimmerman/ris-backend/issues</a>

## Requirements
--------

| Name                   | Recommended version |
| ---                    | ---       |
| Python                 | 2.7       |
| pip                    | latest    |
| PostgreSQL             | 9.6       |
| Redis                  | 4.0.x     |
| virtualenv             | latest    |
| textract               | 1.6.1     |

 `sudo apt-get install libpulse-dev`
 
### Create database
--------

    sudo su - postgres
    psql template1
    CREATE USER <user> WITH PASSWORD '<password>';
    CREATE DATABASE <database name> OWNER <user>;
    \c <database name>
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO <user>;
  
### Create virtualenv & install requirements
--------

From the root folder

    virtualenv .env
    source .env/bin/activate
    cd src
    pip install -r requirements.txt
  
### Municipality configuration
--------

Copy `src/ris/local_settings.sample.py` and rename to `src/ris/local_settings.py`

Adjust the following variables:

    RIS_DB_NAME=<database name>
    RIS_DB_PASSWORD=<password>
    RIS_DB_USER=<user>
    RIS_MUNICIPALITY=<Almere>

### Create DB model migrations & apply them
--------

From the `src` folder

Create database models migrations: `./manage.py makemigrations`

If the command returns `No changes detected` on a fresh new database then you need to run the command for every app:
    
    ./manage.py makemigrations accounts
    ./manage.py makemigrations dossier
    ./manage.py makemigrations favorite
    ./manage.py makemigrations generics
    ./manage.py makemigrations query
    ./manage.py makemigrations subscriptions

Apply migrations: `./manage.py migrate`

Generate static files: `./manage.py collectstatic`
    
### Import data
--------

**Note**: Importing data will take some time!

From the `src` folder

1. `./manage.py import_speakers` - imports people speaking in videos (applies only for Notubiz)
2. `./manage.py import_public_dossiers` - imports public dossiers (applies only for Notubiz)
3. `./manage.py import_data` - data scraper script extracting municipality's data
4. `./manage.py import_notubiz_modules` - data scraper script for notubiz municipalities (applies only for Notubiz)
- Note: before executing the next command, create `src/files` folder
5. `./manage.py import_document_files` - script for downloading, scanning and indexing document content

### Run
--------

From the `src` folder

`./manage.py runserver`


App should be running on <http://localhost:8000/>


## Tests
--------

TBD (this is in project's roadmap)


## Can I contribute?
--------

Yes please! We are mainly looking for coders to help on the project. If you are a coder feel free to *Fork* the repository and send us Pull requests!

## How should I contribute?

Python already has clear <a href="https://www.python.org/dev/peps/pep-0008/" target="_blank">PEP 8</a> code style guidelines, so it's difficult to add something to it, but there are certain key points to follow when contributing:

* <a href="https://www.python.org/dev/peps/pep-0008/" target="_blank">PEP 8</a> code style guidelines should _always_ be followed
* When making commits, in the first line try to summarize changes (in around 50 characters or less) and in the message body (if needed) try to explain _what_ you did, and, most importantly, _why_. Try to avoid commit messages like "Fixed bugs". Other developers should be able to understand _why_ the change was made!
* Always try to reference issues ("related to #614", "closes #619" and etc.)
* Avoid huge code commits where the difference can not even be rendered by browser based web apps (Github for example). Smaller commit make it much easier to understand why the change was made, why (if) it resulted in certain bugs and etc
* When developing new feature, write at least some basic tests for it. This helps not to break other things in the future
* If there's a reason to commit code that is commented out (there usually should be none), always leave a "FIXME" or "TODO" comment so it's clear for other developers _why_ this was done
* When using external dependencies that are not in PyPI (from Github for example), stick to a particular commit (i. e. `git+https://github.com/Supervisor/supervisor@ec495be4e28c694af1e41514e08c03cf6f1496c8#egg=supervisor`), so if the library is updated, it doesn't break everything
* These rules are to be extended
