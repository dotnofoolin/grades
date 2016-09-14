Grades App
==========

Scrapes grades from your schools Edline page for each child in your account. 
Displays these grades in an aggregated, quick access, beautiful interface.

Author:
-------
* Josh Burks
* dotnofoolin@gmail.com

Requirements:
-------------
* Python 3
* pip
* npm
* Bower
* Edline configured (meaning you have an account, you activated your codes, you can see grades, etc). 
* It is highly suggested that you run this using virtualenv.

Install:
--------
1. git clone https://github.com/dotnofoolin/grades.git
2. virtualenv --python=/usr/bin/python3 --no-site-packages grades
3. cd grades && source bin/activate
4. pip install -r requirements.txt
5. npm install -g bower-npm-resolver
6. bower install
7. Copy config.py.dist to config.py and edit appropriately
8. python scraper.py
9. python app.py
10. http://localhost:5000