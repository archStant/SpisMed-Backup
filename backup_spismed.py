import requests
from bs4 import BeautifulSoup
#import re
import os
import datetime
import sys
from pathlib import Path
from getpass import getpass
import configparser

Config = configparser.ConfigParser()

kitchen, email, password = '', '', ''

# Is this universal? TODO: Find out.
headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/71.0.3578.98 Chrome/71.0.3578.98 Safari/537.36'
}

login_data = {'utf8': '✓',
              'authenticity_token': '',
              'user[email]': email,
              'user[password]': password,
              'button': ''
              }

helpstring = '''Usage: backup_spismed [OPTIONS]
Options:
    -h:          Print this help message
    -p:          Print the standings without saving to a file
    -l:          List the current backups
    -c:          Clean the backups directory leaving only the 10 latest backups
    -d "DST":    Saves the backup in the supplied destination
    --configure: Runs the configuration wiz
All options are mutually exclusive.'''

# regex = r"<strong><a href=\"/accounts/.*\">(?P<name>.*)</a>(.*\n){3}(?P<month>.*)(.*\n){4}(?P<total>.*)"

home = str(Path.home())
config_folder = os.path.join(home, '.backup_spismed')
config_file = os.path.join(config_folder, 'config.ini')

if not (os.path.isdir(config_folder)):
    print('Making directory "%s"' % config_folder)
    os.mkdir(config_folder)


def takeInput(question):
    x = input(question)
    if not x:
        print('Error: exiting')
        sys.exit(0)
    else:
        return x


def writeconf():
    global kitchen, email, password
    kitchen = takeInput('Køkkennummer:\t')
    email = takeInput('Din email:\t')
    password = getpass('Dit password:\t')  # takeInput('Dit password:\t')
    cfgfile = open(config_file, 'w+')
    Config.add_section('backup_spismed')
    Config.set('backup_spismed', 'kitchen_number', str(kitchen))
    Config.set('backup_spismed', 'email', email)
    Config.set('backup_spismed', 'password', password)
    Config.write(cfgfile)
    cfgfile.close()


if '--configure' in sys.argv:
    writeconf()
    sys.exit()

if not os.path.isfile(config_file):
    print('Not yet configured, run "backup_spismed --configure"')
    sys.exit(0)
else:
    Config.read(config_file)
    kitchen = Config.get('backup_spismed', 'kitchen_number')
    email = Config.get('backup_spismed', 'email')
    password = Config.get('backup_spismed', 'password').strip()
    login_data['user[email]'] = email
    login_data['user[password]'] = password

#print(kitchen, email, password)
foldername = os.path.join(home, 'spismed_backups')

# Choose directory
if '-d' in sys.argv:
    theIndex = sys.argv.index('-d')
    if len(sys.argv) < (theIndex + 2):
        print('You need to supply a destination for the backup.\n\nIdiot...')
        sys.exit(0)
    foldername = os.path.abspath(sys.argv[theIndex + 1])

# Print help
if '-h' in sys.argv:
    print(helpstring)
    sys.exit(0)

# Erase old backups
if '-c' in sys.argv:
    print('Cleaning...')
    backups = sorted(os.listdir(foldername))[:-10]
    if input('About to delete %d files, continue? [y/N]\n' % len(backups)).upper() == 'Y':
        for i in backups:
            os.remove(os.path.join(foldername, i))
    else:
        print('Aborting')
    sys.exit(0)

# List current backups
if '-l' in sys.argv:
    backups = sorted(os.listdir(foldername))
    print('Current backups:')
    for i in backups:
        print(i)
    print('(Located in "%s")' % foldername)
    sys.exit(0)

print('Kitchen:\t%s\nEmail:\t\t%s\n' % (kitchen, email))

# The main logic
with requests.Session() as s:
    url = 'https://spismed.nu/users/sign_in'
    regnskaburl = 'https://spismed.nu/kitchens/%s/edit/accounting' % kitchen
    r = s.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    a_token = soup.find('input', attrs={'name': 'authenticity_token'})['value']
    login_data['authenticity_token'] = a_token
    r = s.post(url, data=login_data, headers=headers)
    r = s.get(regnskaburl, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    tmp = soup.find('tbody', id='accounts')
    if tmp is None:
        print('Something went wrong. Check you internet connection or configuration')
        sys.exit(1)
    theTable = (tmp).text

# Sanitize data
a = theTable.replace('\n'*5, '\n')
a = a.replace('\n'*4, '\t')
a = a.replace('\n'*3, ':\t')[2:-1]

b = [x.split('\t') for x in a.split('\n')]
for i in range(int(len(b)/2)):
    b.remove([''])


now = datetime.datetime.now()
filename = os.path.join(foldername, ('spismed_backup_%s.txt' % now.strftime("%Y-%m-%d-%H-%M")))

# Print to screen
if '-p' in sys.argv:
    print('Navn%sSidste måned\t Total udestående\n%s' % (' '*20, '-'*60))
    for i in b:
        print('%s %s\t%s' % (i[0].ljust(20), i[1].rjust(15), i[2].rjust(15)))
# Write to file
else:
    if not (os.path.isdir(foldername)):
        print('Making directory "%s"' % foldername)
        os.mkdir(foldername)

    with open(filename, 'w') as file:

        file.write('Navn%sSidste måned\t Total udestående\n%s\n' % (' '*20, '-'*60))
        for i in b:
            file.write('%s %s\t%s\n' % (i[0].ljust(20), i[1].rjust(15), i[2].rjust(15)))
        file.write('\n\n%s' % now.strftime("%Y-%m-%d %H:%M"))

    print('Writing to "%s"' % filename)
    count = len(os.listdir(foldername))
    print('Current number of backups: %d' % count)
    os.system('/usr/bin/notify-send "Backed up Spismed.nu"')
