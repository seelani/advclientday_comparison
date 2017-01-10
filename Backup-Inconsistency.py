#Script for pointing out inconsistent backup usage
#Dependency: Apache Libcloud
#Author: Seelan

import os
from datetime import datetime
from datetime import timedelta
import ast

fileCredentials = open("credentials.txt","r")
credentialList = fileCredentials.read()
fileCredentials.close()
credentialList = ast.literal_eval(credentialList)

username = credentialList[0]
password = credentialList[1]

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
cls = get_driver(Provider.DIMENSIONDATA)
apdriver = cls(username, password , region='dd-ap')

i_location = input("Please input which datacenter you would like to check (AP3/AP5) ")
i_startdate = input("Please input the start date for the range that you would like checked in the following format (YYYY-MM-DD) ")
i_enddate = input("Please input the end date for the range that you would like checked in the following format (YYYY-MM-DD) ")

#For Summary Report Date Start Date is exact End Date need to increase by one day
#For Backup Report, first i need to shift by 2 days in reverse.
#The startdate provides a date prior, enddate is increased by one day
#As such to meet the 2 days in reverse we will perform the following operations

b_startdate = datetime.strptime(i_startdate, '%Y-%m-%d')
b_startdate = datetime.date(b_startdate)
b_startdate = b_startdate + timedelta(days= -1)

b_enddate = datetime.strptime(i_enddate, '%Y-%m-%d')
b_enddate = datetime.date(b_enddate)
r_enddate = b_enddate + timedelta(days = -1) # to get the report for the end date it must be one day in advance
b_enddate = b_enddate + timedelta(days= -2)

s_enddate = datetime.strptime(i_enddate, '%Y-%m-%d')
s_enddate = datetime.date(s_enddate)
s_enddate = s_enddate + timedelta(days = 1)


#finding number of days given in the range.
difference = (b_enddate - b_startdate)
difference = difference + timedelta(days=2) #need to add 2 days to include start and end dates as well.
diffin = int(difference.days)
print (diffin) # debug line

#debug print (can be commented out)
#print ('The requested start date is ' + str(i_startdate) + ' The requested end ate is: ' + str(i_enddate)) 
#print ('-----')																								
#print ('The adjusted start date is: ' + str(b_startdate) + ' The adjusted end date is: ' + str(b_enddate))

#create a list of the given size to include each day
backupdays = ['']*diffin
backup_a = [0]*diffin
backup_es = [0]*diffin
backup_en = [0]*diffin

#now we want to pull the backup report using the API, first date goes into backupdays list
backuplist = apdriver.ex_backup_usage_report(str(b_startdate),str(r_enddate),i_location)

#print (backuplist) #debug line
backuplist_headers = backuplist[0]
templine = backuplist[1]	#first line
firstdate = templine[0]		#getting the first date from the first line
backupdays[0] = firstdate	#first date goes into the backupdays LIST

j = 1
bd = 0
#print (len(backuplist))
while j < len(backuplist):
	newline = backuplist[j]
	if newline[0] == backupdays[bd]:
		backup_es[bd]+=int(newline[5])
		backup_a[bd]+=int(newline[6])
		backup_en[bd]+=int(newline[7])
	else:
		bd+=1
		backupdays[bd] = newline[0]
		backup_es[bd]+=int(newline[5])
		backup_a[bd]+=int(newline[6])
		backup_en[bd]+=int(newline[7])
	j+=1

#print (backupdays)
#print (backup_a)
#print (backup_es)
#print (backup_en)

apvalue = apdriver.ex_summary_usage_report(i_startdate,str(s_enddate))
headers = apvalue[0]
sum_es = [0]*diffin
sum_a = [0]*diffin
sum_en = [0]*diffin

#When traversing the list you wanna skip index[0]-headers and index[last]-total

#print ("Entire length: "+str(len(apvalue))+"\n")
i = 1
icount = 0
while i < len(apvalue):
	nxline = apvalue[i]
	if nxline[1] == i_location:
		sum_es[icount] = int(nxline[22])
		sum_a[icount] = int(nxline[23])
		sum_en[icount] = int(nxline[24])
		icount+=1
	i+=1
#print ("Stopped at: "+ str(i) +"\n")
#print (sum_a)
#print (sum_es)
#print (sum_en)

print ("Adjusted Values")
print ("===============")
print ("|Date|		|Advanced(B)|	|Essentials(B)|	  |Enterprise(B)|		|Advanced(S)|	|Essentials(S)|	  |Enterprise(S)|")

#print (backupdays)

k = 0
while k < len(backupdays):
	listday = datetime.strptime(backupdays[k], '%Y-%m-%d')
	listday = datetime.date(listday)
	listday = listday + timedelta(days = 2)
	newday = str(listday)
	print (newday , '		' , backup_a[k] , '		' , backup_es[k] , '		' , backup_en[k] , '				' , sum_a[k] , '		' , sum_es[k] , '			' , sum_en[k] )
	k+=1