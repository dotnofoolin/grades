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
* Bower
* Edline configured (meaning you have an account, you activated your codes, you can see grades, etc). 
* It is highly suggested that you run this using virtualenv.

Install:
--------
1. git clone https://github.com/dotnofoolin/grades.git
2. virtualenv --python=/usr/bin/python3 --no-site-packages grades
3. cd grades && source bin/activate
4. pip install -r requirements.txt
5. bower install
6. Copy config.py.dist to config.py and edit appropriately
7. python scraper.py
8. python app.py
9. http://localhost:5000