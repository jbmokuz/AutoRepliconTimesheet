import sys, json, requests, datetime


if len(sys.argv) < 3:
    comment = 'auto comment'
else:
    comment = sys.argv[2]

if len(sys.argv) < 2:
    hoursWorked = 8
else:
    try:
        hoursWorked = int(sys.argv[1])
    except:
        hoursWorked = 8

today = datetime.datetime.now()
f=open('creds.txt').readlines()

#Make sure to have trailing newline
companyKey = f[0][:-1]
loginName = f[1][:-1]
password = f[2][:-1]

headers = {'content-type':'application/json'}
 
# Finding Swimlane
swimlaneFinderUrl = 'https://global.replicon.com/DiscoveryService1.svc/GetTenantEndpointDetails'
swimlaneFinderJsonBody = {}
tenant = {}
tenant['companyKey'] = companyKey
swimlaneFinderJsonBody['tenant'] = tenant
 
swimlaneInfo = None
 
# Getting the Swimlane information of the Company Key
try:
    swimlaneFinder = requests.post(swimlaneFinderUrl, headers = headers, data = json.dumps(swimlaneFinderJsonBody))
    swimlaneFinder = swimlaneFinder.json()
    if swimlaneFinder.get('error'):
        print 'Error: {0}'.format(swimlaneFinder.get('error'))
        sys.exit(1)
    else:
        swimlane = swimlaneFinder['d']['applicationRootUrl']
except Exception, e:
    print 'Error: {0}'.format(e)
    sys.exit(1)
 
def sendRequest(service,data):
    data = json.dumps(data)
    try:
        url = swimlane + 'services/' + service
        ret = requests.post(url, headers = headers, data=data, auth = (companyKey+'\\'+loginName, password))
        ret = ret.json()
        if ret.get('error'):
            print 'Error: {0}'.format(ret.get('error'))
            sys.exit(1)
        else:
            return ret
    except Exception, e:
        print 'Error: {0}'.format

# Get user uri
ret = sendRequest('UserService1.svc/GetEnabledUsers','')
userUri = ret['d'][0]['uri']

# Get timesheet uri
data = {}
data['userUri'] = userUri
data['date'] = {'year':today.year,'month':today.month,'day':today.day}
ret = sendRequest('TimesheetService1.svc/GetTimesheetForDate2',data)
sheetUri = ret['d']['timesheet']['uri']

# Get timesheet
data = {}
data['timesheetUri']=sheetUri
sheet =  sendRequest('TimesheetService1.svc/GetStandardTimesheet2',data)

# Insert hours into rows
rows = ''
for i,row in enumerate (sheet['d']['rows']):
    if row['activity']['displayText'] == 'Direct - MA' and row['task']['displayText'] == 'Core SW Dev':
        sheet['d']['rows'][i]['cells'].append({u'customFieldValues':
[], u'date': {u'year': today.year, u'day': today.day, u'month': today.month},
u'duration': {u'hours': hoursWorked, u'seconds': 0, u'minutes': 0,
u'milliseconds': 0, u'microseconds': 0}, u'comments':comment})
        rows = sheet['d']['rows']
        break

if rows == '':
    print 'Could not get rows'
    sys.exit(0)

# Post new timesheet!    
data = {}
data['timesheet'] = {}
data['timesheet']['noticeExplicitlyAccepted'] = False
data['timesheet']['rows'] = rows
data['timesheet']['target'] = {'uri':sheetUri,'user':None,'date':None}
data['timesheet']['customFields'] = []
data['timesheet']['bankedTime'] = None
ret = sendRequest('TimesheetService1.svc/PutStandardTimesheet2',data)
print ret
