######################################################
# Adapted from: script developed by Ricardo Pereira.
######################################################
import smtplib
import string
import random
import sys
import lxml.etree as ET
from xml.dom import minidom


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def get_info(past_users):
    '''read and put info into a list'''
    users = []
    accounts = []
    lines = [line.rstrip('\n') for line in open(sys.argv[1])]
    for i in range(0, len(lines)):
        username = lines[i].split(' ')[0]
        '''Condition to check if the user is not already at XML file'''
        if username not in past_users:
            users = users+[username]
            accounts = accounts+[lines[i].split(' ')[1]]
    return users, accounts


def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com:587'):
    header = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message

    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login, password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()
    return problems


def createXMLdata(filename, users, passwords, emails):
    tree = ET.parse(filename)
    root = tree.getroot()

    for i in range(0, len(users)):
        passwords = passwords + [id_generator()]
        user = ET.Element('user')
        user.set('username', users[i])
        user.set('password', passwords[i])
        user.set('roles', 'WingsUser')

        root.append(user)
        indent(root)

    with open(filename, 'w') as f:
        f.write(ET.tostring(root,
                            pretty_print=True,
                            xml_declaration=True,
                            encoding='utf-8'))
    return passwords


def writeEmail(accounts, passwords):
    for i in range(0, len(accounts)):
        sendemail(from_addr='insert_your_email',
                  to_addr_list=[accounts[i]],
                  cc_addr_list=[''],
                  subject='New Python Password',
                  message='This is your new password,' + passwords[i],
                  login='insert_your_email',
                  password='insert_your_pass')


if __name__ == '__main__':
    past_users = []
    users = []
    emails = []
    passwords = []
    filename_xml = sys.argv[2]
    try:
        send_email = sys.argv[3]
    except:
        send_email = ''

    mydoc = minidom.parse(filename_xml)
    old_users = mydoc.getElementsByTagName('user')

    for elem in old_users:
        past_users = past_users + [elem.attributes['username'].value]

    info = get_info(past_users)
    passwords = createXMLdata(filename_xml, info[0], passwords, info[1])

    if send_email == "--send_email":
        print("sending email ######")
        if len(passwords) > 0:
            writeEmail(info[1], passwords)
