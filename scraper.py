import requests
import bs4
import re
from datetime import date, timedelta, datetime

from config import *
from model import *

def log_things(text):
    if DEBUG:
        print('DEBUG: {}'.format(text))

def get_date_list():
    datelist = ['Today', 'Yesterday']

    for days_ago in range(2, DAYS_AGO_TO_CHECK):
        datediff = date.today()-timedelta(days=days_ago)
        datestr = datediff.strftime('%b') + ' ' + datediff.strftime('%d').lstrip('0')
        datelist.append(datestr)

    # For debugging. Known date that has valid reports
    #datelist.append('Sep 8')

    return datelist

def run_scraper():
    # Init the database
    create_tables()

    log_things("Dates I'm going to check: {}".format(get_date_list()))

    with requests.Session() as session:
        # Get the login page, and remember the cookies it set
        login_url = BASE_URL + '/Index.page'
        session.get(login_url)
        cookies = {}
        for c in session.cookies:
            cookies[c.name] = c.value

        # Login to the site
        login_params = {
            'screenName': USERNAME,
            'kclq': PASSWORD,
            'submitEvent': '1',
            'TCNK': 'authenticationEntryComponent',
            'enterClicked': 'true',
        }
        session.post(login_url, data=login_params, cookies=cookies, headers={'Referer': BASE_URL})

        # Soupify the school homepage once we are logged in, and get the school name
        result = session.get(SCHOOL_URL)
        home_soup = bs4.BeautifulSoup(result.text, 'html.parser')
        school_name = home_soup.find('span', id='edlHomePageDocBoxAreaTitleSpan').text

        # Now that one kid doesn't have enough classes to trigger the "More Classes..." link, we have to get to the classes a different way.
        # Default is to use the "More Classes..." link.
        # Skip userShortcuts0 because it not a student with classes in my usual case.
        for class_links in home_soup.find_all('div', id=re.compile('^userShortcuts[123456789]')):
            found_more = False
            for more_link in class_links.find_all('div', id='myClassesMore'):
                found_more = True

                # Get the action and params from the div attrs
                action, event, event_params, junk = re.split('[,()]', re.sub('[\' ]', '', more_link.attrs['action']))
                child_id = re.search('targetViewAsUserEntid=(\d+)', event_params).group(1)

                # Go to the more classes page for each child
                post_params = {
                    'ajaxRequestKeySuffix': '0',
                    'eventParms': event_params,
                    'invokeEvent': event,
                    'sessionHardTimeoutSeconds': '1200',
                    'sessionIgnoreInitialActivitySeconds': '90',
                    'sessionRenewalEnabled': 'yes',
                    'sessionRenewalIntervalSeconds': '300',
                    'sessionRenewalMaxNumberOfRenewals': '25',
                }
                result = session.post(BASE_URL + '/post/GroupHome.page', data=post_params, cookies=cookies,
                                      headers={'Referer': SCHOOL_URL})

                log_things('Child ID = {}'.format(child_id))

                # Find all the classes and go to them...
                classes_soup = bs4.BeautifulSoup(result.text, 'html.parser')
                for class_link in classes_soup.find_all('a', href=re.compile('^javascript:rlViewItm')):
                    class_name = class_link.find(text=True).strip()

                    # Ignore the link back to the school page...
                    if re.match('^' + re.escape(school_name), class_name) is None:
                        class_id = re.search('javascript:rlViewItm\(\'(\d+)', class_link['href']).group(1)
                        log_things('    {}-{}'.format(class_name, class_id))

                        # Go to the class page
                        post_params = {
                            'resourceViewEvent': '1',
                            'targetResEntid': class_id,
                        }
                        result = session.post(BASE_URL + '/post/ResourceList.page', data=post_params,
                                              cookies=cookies, headers={'Referer': SCHOOL_URL})

                        # Go to the contents page
                        post_params = {
                            'ajaxRequestKeySuffix': '0',
                            'eventParms': 'TCNK=contentsBoxComponent',
                            'invokeEvent': 'showMore',
                            'sessionHardTimeoutSeconds': '1200',
                            'sessionIgnoreInitialActivitySeconds': '90',
                            'sessionRenewalEnabled': 'yes',
                            'sessionRenewalIntervalSeconds': '300',
                            'sessionRenewalMaxNumberOfRenewals': '25',
                        }
                        result = session.post(BASE_URL + '/post/GroupHome.page', data=post_params,
                                              cookies=cookies, headers={'Referer': SCHOOL_URL})

                        iterate_items_save_results(result, session, cookies, class_name)


            # This is the case where the "More Classes..." link isn't found, and we have to visit the class pages a little differently.
            if not found_more:
                for class_link in class_links.find_all('div', action=re.compile('^\/pages')):
                    class_name = class_link['title']
                    class_url = BASE_URL + class_link['action']
                    result = session.get(class_url, cookies=cookies, headers={'Referer': SCHOOL_URL})

                    # Go to the contents page
                    post_params = {
                        'ajaxRequestKeySuffix': '0',
                        'eventParms': 'TCNK=contentsBoxComponent',
                        'invokeEvent': 'showMore',
                        'sessionHardTimeoutSeconds': '1200',
                        'sessionIgnoreInitialActivitySeconds': '90',
                        'sessionRenewalEnabled': 'yes',
                        'sessionRenewalIntervalSeconds': '300',
                        'sessionRenewalMaxNumberOfRenewals': '25',
                    }

                    result = session.post(BASE_URL + '/post/GroupHome.page', data=post_params,
                                          cookies=cookies, headers={'Referer': SCHOOL_URL})

                    iterate_items_save_results(result, session, cookies, class_name)


def iterate_items_save_results(raw_html, session, cookies, class_name):
    # Iterate through the item list table...
    items = {}
    items_names = {}
    items_soup = bs4.BeautifulSoup(raw_html.text, 'html.parser')
    try:
        items_table = items_soup.find('table', id='directoryList')
        for row in items_table.find_all('tr', attrs={'class': 'ed-compactTableRow'}):
            cols = row.find_all('td', attrs={'class': 'ed-userListCellBody'})
            try:
                item_link = cols[1].find_all('a', href=re.compile('^javascript:submitEvent'))[0]
                item_name = item_link.text.strip()
                item_id = re.search('folderEntid=(\d+)', item_link['href']).group(1)
            except:
                log_things('        Non-grades link found. Skipping')

            item_date = cols[2].find('span').text

            # Only look for things updated within the last few days.
            if item_date in get_date_list():
                items[item_id] = item_date
                items_names[item_id] = item_name

                log_things('        {}-{}'.format(item_date, item_id))

    except AttributeError:
        log_things('        No items found!')
        pass

    log_things('        {} items to check'.format(str(len(items))))

    # Iterate through the found items and retrieve the contents...
    for id, desc in items.items():
        item_name = items_names[id]
        # Go to the item page
        post_params = {
            'ajaxRequestKeySuffix': '0',
            'eventParms': 'folderEntid=' + id,
            'invokeEvent': 'viewFolder',
            'sessionHardTimeoutSeconds': '1200',
            'sessionIgnoreInitialActivitySeconds': '90',
            'sessionRenewalEnabled': 'yes',
            'sessionRenewalIntervalSeconds': '300',
            'sessionRenewalMaxNumberOfRenewals': '25',
        }
        result = session.post(BASE_URL + '/post/ResourceList.page', data=post_params, cookies=cookies,
                              headers={'Referer': SCHOOL_URL})

        # The actual report is in an iframe. Find it and the actual URL of the report.
        report_soup = bs4.BeautifulSoup(result.text, 'html.parser')
        for report in report_soup.find_all('iframe', id='docViewBodyFrame'):
            result = session.get(report['src'])

            # The report is contained in a pre tag.
            final_soup = bs4.BeautifulSoup(result.text, 'html.parser')
            final_pre = final_soup.find('pre')

            # Parse out the child name.
            child_name = re.search('Progress Report for (.+)', final_pre.text).group(1).strip()

            # Parse out the grade letter. Look at the Term line at the bottom of the report
            try:
                grade_letter = None
                # Terms are listed oldest to newest, so overwritting grade_average through the loop will get us the newest one
                for match in re.findall('Term #\d.*\d+\s+([ABCDF])', final_pre.text):
                    grade_letter = match.strip()
            except AttributeError:
                log_things('CANNOT FIND GRADE LETTER FOR {} -- {}'.format(child_name, class_name))
                break

            # Parse out the grade average. Look at the Term line at the bottom of the report
            try:
                grade_average = None
                # Terms are listed oldest to newest, so overwritting grade_average through the loop will get us the newest one
                for match in re.findall('Term #\d.*\s+(\d+)\s+[ABCDF]', final_pre.text):
                    grade_average = match.strip()
            except AttributeError:
                log_things('CANNOT FIND GRADE AVERAGE FOR {} -- {}'.format(child_name, class_name))
                break

            # Here's the final results!
            log_things('{}-{}-{}-{}-{}-{}'.format(child_name, class_name, grade_letter, grade_average, desc, item_name))

            # Format 'Today' and 'Yesterday' to expected MMM D format, for conversion to date object later
            if desc == 'Today':
                today = datetime.today()
                desc = today.strftime('%b') + ' ' + today.strftime('%d').lstrip('0')

            if desc == 'Yesterday':
                yesterday = date.today() - timedelta(days=1)
                desc = yesterday.strftime('%b') + ' ' + yesterday.strftime('%d').lstrip('0')

            # Persist the results to the database, but only if we have a valid grade letter
            if grade_letter != '**' and grade_letter != None and grade_average != None:
                save_report(
                    child_name=child_name,
                    class_name=class_name,
                    grade_letter=grade_letter,
                    grade_average=grade_average,
                    post_date=datetime.strptime(desc + ' ' + str(datetime.today().year), '%b %d %Y').date(),
                    post_desc=item_name,
                    report_text=final_pre.text,
                )

if __name__ == '__main__':
    run_scraper()

    print("Completed at {}".format(datetime.now()))



