#!/usr/bin/python
###########################################################
#	PYTHIA
#	Matthew Martz 
#		version 0.2 : 2009
#		version 0.3 : 10-09-2010
#		version 0.4 : 3-17-2011
#	http://mutaku.com/
#
# Invoked as:
#   python pythia.py    <---This is the normal mode
#   python pythia.py [debug, menu]
#
#   normal mode:  Works with things in instances and without verbosity
#		auto-updates email list by a check interval variable
#				*no menu capabilities to open emails [yet]
#   debug mode:  Writes to a file in /tmp and is more verbose
#		doesn't run in a loop and will generally let you catch most errors
#				*Doesn't auto-update
#   menu mode:  Works with a raw_input() menu to let you type in email numbers and they open in your browser
#		also has other features like a refresh which updates email display
#				*Doesn't auto-update
###########################################################
import urllib2, time, os, sys, string, getpass, shutil
from configobj import ConfigObj
from xml.dom import minidom
try:
	import pynotify
except:
	pass

# setup the colors for the console display
GREEN = "\033[1;32m"
BLUE = "\033[1;36m"
RED = "\033[1;31m"
LILAC = "\033[1;35m"
YELLOW = "\033[1;33m"
OFF = "\033[1;0m"

# some other variables for title printing etc
CHARS = OFF+"="*10
TITLE = CHARS+YELLOW+' Pythia  '+CHARS
VERSION_NUM = "0.4"
VERSION_DATE = "March 2011"

# setup login information and other global variables
PROTO = "https://"
SERVER = "mail.google.com"
PATH = "/gmail/feed/atom"
BROWSER = ''
USERNAME = ''
PASSWORD = ''
STARTUP = ''
CHECKINTERVAL = ''

# Get user home and append to python path so we can acccess the config module in home dir
HOME = os.getenv("HOME")
# CONFIGFILE = HOME+'/.pythia'
CONFIGFILE = HOME+'/.pythia'
# Icon image
PYNOT_IMG = HOME+"/pythia-icon.png"

# debug mail checker... used if program called as: "pythia.py debug" or "python pythia.py debug"
def debug():
	# Runs pythia in debug mode writing to a temp file and any other operations that are needed when debugging or adding features
	checker()
	# Write contents of page instance into a file at FILENAME
	FILENAME = '/tmp/mails.xml'
	temp = open(FILENAME, 'w')
	# Print FILENAME contents to console screen for debugging
	for line in page:
		temp.write(line)
	temp.close()
	reader = open(FILENAME, 'r')
	for line in reader:
		print line
	reader.close()
	# Setup the XML version of FILENAME by parsing it
	xml = minidom.parse(FILENAME)
	# Find out if there is new mail and take appropriate actions
	count = xml.getElementsByTagName('fullcount')[0].firstChild.data
	print count
	LINKS = {}
	# If there is mail... go ahead and parse and print it
	if int(count) > 0:
		# Split up each email entry and then parse each
		emails = xml.getElementsByTagName('entry')
		print
		print BLUE+'New email from:'+OFF
		#print
		N = 1
		# Setup the links dictionary for opening emails in browser
		LINKS = {}
		for email in emails:
			# Print each entry as XML to console screen for debugging
			print email.toxml()
			# Parse each email and setup the information to display with colors
			NUM = BLUE+'('+str(N)+') '+OFF
			# Use in try to handle empty subject
			try:
				ETITLE = RED+email.getElementsByTagName('title')[0].firstChild.data+OFF
			except:
				ETITLE = '[no subject]'
			# Cuts off after first 50 characters and adds '...' in default console color
			try:
				CONTENT = GREEN+email.getElementsByTagName('summary')[0].firstChild.data[:50]+OFF+'...'+OFF
			except:
				CONTENT = '[no content in body]'
			# Date is ugly so we use some ugly code to get it into the format we like e.g. 23:43:52    25-25-2008
			PREDATE = email.getElementsByTagName('modified')[0].firstChild.data.replace('T', ' ').replace('Z', ' ')
			POSTDATE = PREDATE.split(' ')
			TIME = POSTDATE[1]
			PREDAY = POSTDATE[0].split('-')
			DAY = PREDAY[2]+'-'+PREDAY[2]+'-'+PREDAY[0]
			DATE = OFF+TIME+'    '+DAY+OFF
			# Use try to handle empty author name (not sure if this will happen or not) if not name then we use email
			try:
				FROM = LILAC+email.getElementsByTagName('author')[0].getElementsByTagName('name')[0].firstChild.data+OFF
			except:
				FROM = LILAC+email.getElementsByTagName('author')[0].getElementsByTagName('email')[0].firstChild.data+OFF
			# Setup the link for opening this email entry in browser
			EMAILLINK = email.getElementsByTagName('link')[0].attributes['href'].value
			# Make sure we are putting key as int else we mess up later when handling opening with menu
			LINKS[int(N)] = EMAILLINK
			print EMAILLINK
			#Now we finally display the information from each email entry
			print '  '+NUM+FROM+'      '+DATE
			print '      '+ETITLE
			print '          '+CONTENT+OFF
			print
			print
			N += 1
		print LINKS
	else:
		# What to do if now new emails
		print
		print BLUE+'No new gmail messages.'+OFF
		print
	openmenu(LINKS, REFERER='debug')


def normalcheck(menubased='no'):
	# Clear the buffer of the terminal screen and reprint the header portion
	os.system("clear")
	print TITLE
	print RED+'   '+time.ctime()
	print CHARS*3
	# Grab the email instance
	checker()
	# Parse the instance into xml form
	xml = minidom.parse(page)
	LINKS = {}
	# Check to see if there is new mail and act appropriately
	global count
	count = xml.getElementsByTagName('fullcount')[0].firstChild.data
	if int(count) > 0:
		if int(count) == 1:
			MESS = 'message'
		else:
			MESS = 'messages'
		print
		print GREEN+'You have '+RED+str(count)+GREEN+' new gmail '+MESS+OFF
		print
		emails = xml.getElementsByTagName('entry')
		N = 1
		LINKS = {}
		for email in emails:
			# Parse each email and setup the information to display with colors
			NUM = BLUE+'('+str(N)+') '+OFF
			# Use in try to handle empty subject
			try:
				ETITLE = RED+email.getElementsByTagName('title')[0].firstChild.data+OFF
			except:
				ETITLE = '[no subject]'
			# Cuts off after first 50 characters and adds '...' in default console color
			# also use in a try to handle empty body
			try:
				CONTENT = GREEN+email.getElementsByTagName('summary')[0].firstChild.data[:50]+OFF+'...'+OFF
			except:
				CONTENT = '[no content in body]'
			# Date is ugly so we use some ugly code to get it into the format we like e.g. 23:43:52    25-25-2008
			PREDATE = email.getElementsByTagName('modified')[0].firstChild.data.replace('T', ' ').replace('Z', ' ')
			POSTDATE = PREDATE.split(' ')
			TIME = POSTDATE[1]
			PREDAY = POSTDATE[0].split('-')
			DAY = PREDAY[2]+'-'+PREDAY[2]+'-'+PREDAY[0]
			DATE = OFF+TIME+'    '+DAY+OFF
			# Use try to handle empty author name (not sure if this will happen or not) if not name then we use email
			try:
				FROM = LILAC+email.getElementsByTagName('author')[0].getElementsByTagName('name')[0].firstChild.data+OFF
			except:
				FROM = LILAC+email.getElementsByTagName('author')[0].getElementsByTagName('email')[0].firstChild.data+OFF
			# Setup the link for opening this email entry in browser
			EMAILLINK = email.getElementsByTagName('link')[0].attributes['href'].value
			# Make sure we are putting key as int else we mess up later when handling opening with menu
			LINKS[int(N)] = EMAILLINK
			#Now we finally display the information from each email entry
			print '  '+NUM+FROM+'      '+DATE
			print '      '+ETITLE
			print '          '+CONTENT+OFF
			print
			print
			N += 1
	else:
		# What to1 do if no new emails
		print
		print BLUE+'No new gmail messages.'+OFF
		print
	if menubased == 'yes':
		openmenu(LINKS, REFERER='menubased')


def openmenu(LINKS, REFERER=''):
	# Print out the menu deal for opening an email in browser if program run with menu option
	global OPENEMAIL
	print "Enter email number to open in browser. ('q' to quit, 'r' to refresh, 'c' to rerun config)"
	OPENEMAIL = raw_input(BLUE+'#: '+OFF)
	if OPENEMAIL:
		if OPENEMAIL == 'q' or OPENEMAIL == 'Q':
			exiter()
		elif OPENEMAIL == 'r' or OPENEMAIL == 'R':
			# Respawn check instance with menubased option again since no timers involved
			if REFERER == 'debug':
				debug()
			elif REFERER == 'menubased':
				normalcheck(menubased='yes')
		elif OPENEMAIL == 'c' or OPENEMAIL == 'C':
			configmenu(SENDER=REFERER)
		else:
			if int(OPENEMAIL) in LINKS:
				try:
					# Call system to open the selected link in the browser
					OPENLINK = BROWSER+' "'+LINKS[int(OPENEMAIL)]+'"'
					os.system(OPENLINK)
					# Sleep here briefly to try and allow time for browser to open mail so as not to regrab as still new
					time.sleep(4)
				except:
					print 'Sorry, problem opening link in browser %s .' % BROWSER
			else:
				print 'Sorry, '+str(OPENEMAIL)+' is not a valid email choice'
			# Respawn check instance with menubased option again since no timers involve
			if REFERER == 'debug':
				debug()
			elif REFERER == 'menubased':
				normalcheck(menubased='yes')

def checker():
	# Does the actual grab of the information and puts in page instance
	global page
	# Added try around this because if couldn't connect in time would exit program and no error was generated either
	try:
		passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
		passman.add_password(None, SERVER, USERNAME, PASSWORD)
		authhandler = urllib2.HTTPBasicAuthHandler(passman)
		opener = urllib2.build_opener(authhandler)
		urllib2.install_opener(opener)
		page = urllib2.urlopen(PROTO + SERVER + PATH)
	except:
		# if we have a connection issue print error and wait the normal mail check interval and then run self again
		print RED+"		error connecting to gmail servers..."+OFF
		time.sleep(CHECKINTERVAL)
		checker()

def welcome(TYPE='normal'):
	# Displays the welcome message when started for X seconds
	os.system("clear")
	print
	print BLUE+'   Welcome to '+YELLOW+'PYTHIA'+OFF
	print GREEN+'		A python based console GMAIL checker'+OFF
	print
	print LILAC+'		Version : %s  %s' % (VERSION_NUM, VERSION_DATE)+OFF
	print
	print '	To quit press '+RED+'cntrl-c'+OFF+' at anytime.'
	print
	print
	# After showing the welcome header lets prompt for the password (like when making the config) if they have chosen not to store password
	if PASSWORD == "":
		PROMPT = LILAC+'[%s]'+BLUE+' #: '+OFF
		PROMPTo = BLUE+' #: '+OFF
		print 
		print "You have not stored your password in the config file. Please enter it now for this session."
		def printpass():
			global CPASS1, CPASS2
			print
			print
			print "What is your GMAIL password?"
			CPASS1 = getpass.getpass(PROMPT % hider(CONFIG['password']))
			print 'Please enter your password again to confirm.'
			CPASS2 = getpass.getpass(PROMPT % hider(CONFIG['password']))
			print
			checkpass()
		def checkpass():
			global CPASS1, CPASS2, PASSWORD
			if not CPASS1 or CPASS1 != CPASS2:
				print 'Your passwords do not match. Please try again.'
				printpass()
			PASSWORD = CPASS1
		printpass()
		
	# Here we check to see how we are run and if normal display and sleep and go on
	if TYPE == 'normal':
		X = 4
		time.sleep(X)
	else:
		# If run in alternative mode sleep then display that we are entering that particular mode and then sleep again and go on
		# mode from TYPE sent in by function... normal by default
		X, Y = 2, 2
		time.sleep(X)
		print
		print
		print OFF+'	......... ENTERING '+RED+TYPE.upper()+OFF+' MODE .........'
		print
		print
		time.sleep(Y)

def exiter():
	# Sets up the actions to do on quitting or accidental failures to prevent loop issues and show exit message
	# This will wipe the screen and display our goodbye message when someone kills it e.g. w/ control-c
	#     also if we don't do this we get an ugly exception error during the CHECKTIME sleep if killed
	os.system("clear")
	print
	print BLUE+"	THANKS FOR USING "+YELLOW+"PYTHIA"+OFF
	print
	print BLUE+"	GOODBYE!"+OFF
	print
	sys.exit()

def getconfig():
	global BROWSER, USERNAME, PASSWORD, STARTUP, CHECKINTERVAL, CONFIG
	# lets first check to make sure the config file has the proper permissions 0600
	try:
		os.chmod(CONFIGFILE,0600)
	except:
		print 'Problem correcting permissions on config file %s . Please set to 0600.' % CONFIGFILE
	try:
		CONFIG = ConfigObj(CONFIGFILE)
	except:
		print 'Problem opening config file %s for parsing.' % CONFIGFILE
	try:
		BROWSER = CONFIG['browser']
		USERNAME = CONFIG['username']
		PASSWORD = CONFIG['password']
		STARTUP = CONFIG['startup']
		CHECKINTERVAL = float(CONFIG['checkinterval'])
	except:
		print 'Error parsing the config file.'

def hider(HIDEPASS):
	HIDDEN = ''
	for char in HIDEPASS:
		HIDDEN += '*'
	return HIDDEN

def checknum(NUM, X=None, Y=None):
	if X == None and Y == None:
		if float(NUM) or int(NUM):
			return True
		else:
			return False
	else:
		if float(NUM) in range(X,Y) or int(NUM) in range(X,Y):
			return True
		else:
			return False

def configmenu(FIRSTSTART='no', WELCOME='no', SENDER='main'):
	# Runs the initial config menu and can be run later to alter configuration
	# Setup some variables
	DF = 0
	if FIRSTSTART == 'yes':
		WELCOME = 'yes'
		DF = 1
		# Create the config file since it is first run... careful this will wipe out an existing one if it is there
		CONFIG = ConfigObj()
		CONFIG.filename = CONFIGFILE
		CONFIG['browser'] = ''
		CONFIG['username'] = ''
		CONFIG['password'] = ''
		CONFIG['startup'] = ''
		CONFIG['checkinterval'] = 60

	else:
		CONFIG = ConfigObj(CONFIGFILE)

	PROMPT = LILAC+'[%s]'+BLUE+' #: '+OFF
	PROMPTo = BLUE+' #: '+OFF

	os.system("clear")
	print
	# If this is the first run, display a little welcome message with a pause then wipe and continue
	if WELCOME == 'yes':
		print '''
			%sWelcome to %sPYTHIA%s

It seems that this is your first startup or that you have removed your configuration file.
Therefore, let's go ahead and setup a new configuration file and get on to the email.
Good luck and enjoy!%s''' % (GREEN, YELLOW, BLUE, OFF)
		time.sleep(3)
		os.system("clear")
		print
	print GREEN+"		PYTHIA CONFIGURATION EDITOR"+OFF
	print
	# Start menu configuration operations
	# basic setup is:
	# def print*     - prints out the prompt and grabs user input
	# def check*   - checks that the input is there and proper else loops back onto print*
	def printuser():
		global CUSER
		print
		print BLUE+'''If you have run this before and are updating...
you can accept the default values (listed in the prompt in %spurple%s)
by simply pressing %senter%s.''' % (LILAC, BLUE, YELLOW, OFF)
		print
		print
		print '''What is your GMAIL username?
(e.g. 'john.doe@gmail.com' as just 'john.doe' without quotes)'''
		CUSER = raw_input(PROMPT % CONFIG['username'])
		print
		checkuser()
	def checkuser():
		global CUSER
		if not CUSER and DF == 1:
			print 'Please enter your username.'
			printuser()
		elif not CUSER:
			CUSER = CONFIG['username'].rstrip('@gmail.com')

	def printpassgo():
		global PASSGO
		print
		print
		print '''How would you like to handle your password
WARNING: PYTHIA stores this password in the config file with permissions as ^00.
You could alternatively type in the password each time PYTHIA is launched.'''
		print
		print '''1) continue and store password in restricted file (600)
2) don't store password'''
		PASSGO = raw_input(PROMPTo)
		print
		checkpassgo()
	def checkpassgo():
		global CPASS1
		if not PASSGO or not checknum(PASSGO,1,3):
			print "Please confirm how you would like to handle your password."
			printpassgo()
		elif PASSGO and int(PASSGO) == 2:
			CPASS1 = ''
		else:
			printpass()

	def printpass():
		global CPASS1, CPASS2
		print
		print
		print "What is your GMAIL password?"
		CPASS1 = getpass.getpass(PROMPT % hider(CONFIG['password']))
		print 'Please enter your password again to confirm.'
		CPASS2 = getpass.getpass(PROMPT % hider(CONFIG['password']))
		print
		checkpass()
	def checkpass():
		global CPASS1, CPASS2
		if not CPASS1 and DF == 1 or CPASS1 != CPASS2:
			print 'Your passwords do not match. Please try again.'
			printpass()
		elif not CPASS1:
			CPASS1 = CPASS2 = CONFIG['password']

	def printbrowser():
		global CBROWSER
		print
		print
		print '''What browser should PYTHIA use for email opening function?
	(enter full path e.g. /usr/bin/firefox)'''
		CBROWSER = raw_input(PROMPT % CONFIG['browser'])
		print
		checkbrowser()
	def checkbrowser():
		global CBROWSER
		if not CBROWSER and DF == 1:
			print "Please enter a browser"
			printbrowser()
		elif not os.path.exists(CBROWSER) and DF == 1:
			print "Browser %s%s%s does not seem to be valid. Please try again." % (GREEN, CBROWSER, OFF)
			printbrowser()
		elif not CBROWSER:
			CBROWSER = CONFIG['browser']

	def printinterval():
		global CCHECK
		print
		print
		print '''Enter how often you would like PYTHIA to check mail in normal model.
(in minutes e.g. 5 for 5 min or 1.5 for 1min30sec)'''
		CCHECK = raw_input(PROMPT % (int(CONFIG['checkinterval'])/60.0))
		print
		checkinttime()
	def checkinttime():
		global CCHECK
		if not CCHECK and DF == 1:
			print "Please enter a time (in minutes)"
			printinterval()
		elif not checknum(CCHECK) and DF == 1:
			print "Please enter a number value in minutes"
			printinterval()
		elif not CCHECK:
			CCHECK = float(CONFIG['checkinterval'])/60

	def printstartup():
		global CSTARTUP
		print
		print
		print '''You can choose your default startup mode now. Choose a number:
1) NORMAL - regular non-menu mode with autochecking
2) MENU - menu-based without autochecking but ability to open emails in browser, check on demand,
		and access this configuration menu
3) DEBUG - why is this even an option - you've been warned'''
		CSTARTUP = raw_input(PROMPT % CONFIG['startup'])
		print
		checkstartup()
	def checkstartup():
		global CSTARTUP
		if not CSTARTUP and DF == 1 or not checknum(CSTARTUP,1,4) and DF == 1:
			print "Please enter a valid choice (i.e. 1-3)"
			printstartup()
		elif not CSTARTUP:
			CSTARTUP = CONFIG['startup']

	# Show the prompts and run it all
	printuser()
	printpassgo()
	printbrowser()
	printinterval()
	printstartup()

	# Print out the changes to be committed and then make/alter the config file
	# User prompted to enter minutes so here we convert to seconds which is what time.sleep uses
	CCHECKadj = str(float(CCHECK)*60)
	CPASS = CPASS1
	CUSERadj = CUSER+'@gmail.com'

	# config file name : name from menu
	#	BROWSER	:	CBROWSER
	#	USERNAME	:	CUSER
	#	PASSWORD:	CPASS
	#	STARTUP	:	CSTARTUP
	#	CHECKINTERVAL:CCHECKINTERVAL
	MENUVARS = {'browser': CBROWSER, 'username': CUSERadj, 'password': CPASS,
		'startup': CSTARTUP, 'checkinterval': CCHECKadj}
	HIDEPASS = ''
	for char in CPASS:
		HIDEPASS += '*'


	os.system("clear")
	print
	print BLUE+'	Editing your configuration file ....'+OFF
	print
	print
	time.sleep(1)

	for var in MENUVARS:
		if var == 'password':
			showvar = hider(CPASS)
			confvar = hider(CONFIG[var])
		else:
			showvar = MENUVARS[var]
			confvar = CONFIG[var]
		if var in CONFIG.keys():
			if CONFIG[var] == MENUVARS[var]:
				print '%sNot changing %s%s:%s %s%s' % (GREEN, BLUE, var, LILAC, confvar, OFF)
			elif CONFIG[var] != MENUVARS[var]:
				print '%sChanging %s%s (%s%s%s) %s--------> %s%s%s' % (RED, BLUE, var,LILAC, confvar, BLUE, RED, YELLOW, showvar, OFF)
				CONFIG[var] = MENUVARS[var]
		else:
			print '%sCreating %s%s:%s %s%s' % (GREEN, BLUE, var, LILAC, showvar, OFF)
			CONFIG[var] = MENUVARS[var]
		time.sleep(1)
	CONFIG.write()
	print
	print LILAC+'	Reparsing new configuration.'+OFF
	getconfig()
	time.sleep(1)
	print
	print BLUE+'	Configuration complete!'+OFF
	time.sleep(2)

	if SENDER != 'main':
		if SENDER == 'debug':
			debug()
		elif SENDER == 'menu':
			normalcheck(menubased='yes')
##############################################################
## MAIN - start everything here
##############################################################

# If no config file exists, it is first run or file has been moved so rerun the config menu setup else roll as normal
if not os.path.exists(CONFIGFILE):
	configmenu(FIRSTSTART='yes')

# Setup the config file using ConfigObj... setup here as access (won't make new config)
getconfig()

# Test to see if there is a debug argument from command line and run that else run loop as normal
if "debug" in sys.argv[1:]:
	welcome(TYPE='debug')
	debug()
else:
	# This will just keep looping to check and then wait few mins and check again until terminated
	# Here we can drop into a menu driven version...similar to debug but fuctional for user
	if "menu" in sys.argv[1:]:
		welcome(TYPE='menu')
		try:
			normalcheck(menubased='yes')
		except:
			exiter()
	elif "config" in sys.argv[1:]:
		welcome(TYPE='config')
		#try:
		configmenu(SENDER='menu')
		#except:
		#	print 'oops'
			#exiter()
		try:
			normalcheck(menubased='yes')
		except:
			exiter()
	else:
		welcome()
		while 1:
			try:
				# Check mail the normal route
				normalcheck()
				# Throw up the notifcation if there are messages
				MSG_STATUS = 'close'
				if pynotify.init("Pythia"):
					if int(count) == 0:
						pass
					else:
						NOTER_BODY = "You have %s new gmail messages." % str(count)
						NOTER = pynotify.Notification("Pythia Gmail Checker", NOTER_BODY, PYNOT_IMG)
						NOTER.set_urgency(pynotify.URGENCY_NORMAL)
						NOTER.set_timeout(pynotify.EXPIRES_NEVER)
						NOTER.show()
						MSG_STATUS = 'open'
				# Wait until check interval time is up and run loop again
				time.sleep(CHECKINTERVAL)
				# Now close it so we can run again and not have them pile up
				if MSG_STATUS == 'open':
					NOTER.close()
				else:
					pass
			except:
				exiter()
