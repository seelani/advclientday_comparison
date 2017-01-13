#Script for pointing out inconsistent backup usage
#Dependency: Apache Libcloud
#Author: Seelan

import os
from datetime import datetime
from datetime import timedelta
import ast

##Opening the file required for output
outputfile = open('output.csv','w+')

##CREATE A CREDENTIALS FILE NAME "credentials.txt", CONTENTS AS FOLLOWS: ['$USERNAME','$PASSWORD']
##THE PROGRAM SHOULD HAVE NO ISSUE READING THE CREDENTIALS FILE.

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

outputfile.write(i_location)
outputfile.write('\n')
outputfile.write('Date Range: ')
lineoutput = (i_startdate+","+i_enddate)
outputfile.write(lineoutput)
outputfile.write('\n')

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
#print (diffin) # debug line

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
outputfile.write(',,Backup,,,Summary\n')
lineoutput = ('Date,Advanced,Essentials,Enterprise,Advanced,Essentials,Enterprise\n')
outputfile.write(lineoutput)
k = 0
while k < len(backupdays):
	listday = datetime.strptime(backupdays[k], '%Y-%m-%d')
	listday = datetime.date(listday)
	listday = listday + timedelta(days = 2)
	newday = str(listday)
	lineoutput = (newday +',' + str(backup_a[k]) + ',' + str(backup_es[k]) + ',' + str(backup_en[k]) + ',' + str(sum_a[k]) + ',' + str(sum_es[k]) + ',' + str(sum_en[k]))
	print (newday , '		' , backup_a[k] , '		' , backup_es[k] , '		' , backup_en[k] , '				' , sum_a[k] , '		' , sum_es[k] , '			' , sum_en[k] )
	outputfile.write(lineoutput)
	outputfile.write('\n')
	k+=1

#========================================================#
# So we everything prints out a-ok. Lets try comparing each storage type.
#========================================================#
print ('\n')
outputfile.write('\n')
# Essentials!
k = 0
errordates_es = list()
while k < len(backupdays):
	if backup_es[k] != sum_es[k]:
		listday = datetime.strptime(backupdays[k], '%Y-%m-%d')
		listday = datetime.date(listday)
		listday = listday + timedelta(days = 2)
		newday = str(listday)
		errordates_es.append(newday)
	k+=1
if len(errordates_es) != 0:
	print ("The values in summary report and backup report for essential backup hours for the following days are incorrect: ")
	print (errordates_es)
	outputfile.write("The values in summary report and backup report for essential backup hours for the following days are incorrect: \n")
	v = 0
	aline = ''
	while v < len(errordates_es):
		aline = aline +','
		aline = aline + errordates_es[v]
		v+=1
	outputfile.write(aline)
	outputfile.write('\n')


# Advanced!
k = 0
errordates_a = list()
while k < len(backupdays):
	if backup_a[k] != sum_a[k]:
		listday = datetime.strptime(backupdays[k], '%Y-%m-%d')
		listday = datetime.date(listday)
		listday = listday + timedelta(days = 2)
		newday = str(listday)
		errordates_a.append(newday)
	k+=1

if len(errordates_a) != 0:
	print ("The values in summary report and backup report for advanced backup hours for the following days are incorrect: ")
	print (errordates_a)
	outputfile.write("The values in summary report and backup report for advanced backup hours for the following days are incorrect:")
	v = 0
	aline = ''
	while v < len(errordates_a):
		aline = aline + ","
		aline = aline + errordates_a[v]
		v+=1
	outputfile.write(aline)	
	outputfile.write('\n')
# Enterprise!
k = 0
errordates_en = list()
while k < len(backupdays):
	if backup_en[k] != sum_en[k]:
		listday = datetime.strptime(backupdays[k], '%Y-%m-%d')
		listday = datetime.date(listday)
		listday = listday + timedelta(days = 2)
		newday = str(listday)
		errordates_en.append(newday)
	k+=1

if len(errordates_en) != 0:
	print ("The values in summary report and backup report for enterprise backup hours for the following days are incorrect: ")
	print (errordates_en)
	outputfile.write("The values in summary report and backup report for enterprise backup hours for the following days are incorrect: \n")
	v = 0
	aline = ''
	while v < len(errordates_en):
		aline = aline +','
		aline = aline + errordates_en[v]
		v+=1
	outputfile.write(aline)
	outputfile.write('\n')

if 	len(errordates_en) != 0 or len(errordates_a) != 0 or len(errordates_es) != 0:
	print ('Do double check these values with your billing to ensure no undercharge/overcharge.')
	outputfile.write('Do double check these values with your billing to ensure no undercharge/overcharge.\n\n')
#=====================================#
#Time to check adv_client dates as well.
#=====================================#
clientdays_b_es = [0]*diffin
clientdays_b_a = [0]*diffin
clientdays_b_en = [0]*diffin

clientdays_sum_es = [0]*diffin
clientdays_sum_a = [0]*diffin
clientdays_sum_en = [0]*diffin

i = 1
j = 0
while i  < len(apvalue):
	newline = apvalue[i]
	if newline[1] == i_location:
		clientdays_sum_es[j] = int(newline[19])
		clientdays_sum_a[j] = int(newline[20])
		clientdays_sum_en[j]= int(newline[21])
		j+=1
	i+=1
	
a = 1
summaryDates = list()
while a < len(apvalue):
	anline = apvalue[a]
	if anline[1] == i_location:
		summaryDates.append(anline[0])
	a+=1

#print (summaryDates, '\n')
#print (clientdays_sum_es)
#print (clientdays_sum_a)
#print (clientdays_sum_en)
#print ('\n')

bc = 1
bn = 0
while bc < len(backuplist):
	bline = backuplist[bc]
	if bline [0] == backupdays[bn]:
		if int(bline[5]) != 0:
			clientdays_b_es[bn]+=1
		if int(bline[6]) != 0:
			clientdays_b_a[bn]+=1
		if int(bline[7]) != 0:
			clientdays_b_en[bn]+=1	
	else:
		bn+=1
		if int(bline[5]) != 0:
			clientdays_b_es[bn]+=1
		if int(bline[6]) != 0:
			clientdays_b_a[bn]+=1
		if int(bline[7]) != 0:
			clientdays_b_en[bn]+=1
	bc+=1

#avalue = sum(clientdays_b_es)
#bvalue = sum(clientdays_b_a)
#cvalue = sum (clientdays_b_en)
#print (clientdays_b_es)
#print (avalue)
#print (clientdays_b_a)
#print (bvalue)
#print (clientdays_b_en)
#print (cvalue)

#Okay we can assume that something is wrong somewhere?
#We want to compare whats on the summary report against what is on the backup report.

#loop through summary and get the value per day and compare
errordates_adv_es = list()
errordates_adv_a = list()
errordates_adv_en = list()

i = 0
while i < len(summaryDates):
	if clientdays_sum_es[i] != clientdays_b_es[i]:
		errordates_adv_es.append(summaryDates[i])
	if clientdays_sum_a[i] != clientdays_b_a[i]:
		errordates_adv_a.append(summaryDates[i])
	if clientdays_sum_en[i] != clientdays_b_en[i]:
		errordates_adv_en.append(summaryDates[i])
	i+=1
print ('==========================')
print ('The following essential client dates are incorrect: ', errordates_adv_es)
print ('The following advanced client dates are incorrect: ',errordates_adv_a)
print ('The following enterprise client dates are incorrect: ',errordates_adv_en)

v = 0
aline = 'The following essential client dates are incorrect: '
while v < len(errordates_adv_es):
	aline = aline + ','
	aline = aline + errordates_adv_es[v]
	v+=1

v = 0
bline = 'The following advanced client dates are incorrect: '
while v < len(errordates_adv_a):
	bline = bline + ','
	bline = bline + errordates_adv_a[v]
	v+=1

v = 0
cline = 'The following enterprise client dates are incorrect: '
while v < len(errordates_adv_es):
	cline = cline + ','
	cline = cline + errordates_adv_es[v]
	v+=1

outputfile.write(aline)
outputfile.write('\n')
outputfile.write(bline)
outputfile.write('\n')
outputfile.write(cline)

outputfile.write('\n\nA review of the administrative logs show that the following actions pertaining to backup were performed: \n')
print ('\nA review of the administrative logs show that the following actions pertaining to backup were performed: \n')

compiled_errordates_adv = errordates_adv_es + errordates_adv_a + errordates_adv_en
compiled_errordates_adv = set(compiled_errordates_adv)
compiled_errordates_adv = list(compiled_errordates_adv)
compiled_errordates_adv.sort()
<<<<<<< HEAD

print (compiled_errordates_adv)

=======
print (compiled_errordates_adv)
>>>>>>> 34f151839656816df263bbf3d4b4b7e058548697
adminvalues = apdriver.ex_audit_log_report(i_startdate,i_enddate)
finaloutput =list()
i = 1

while i < len(adminvalues):
	adminline = adminvalues[i]
	admindate = adminline[1]
	admindate = admindate[:10]
	j = 0
	while j < len(compiled_errordates_adv):
		if admindate == compiled_errordates_adv[j]:
			devicename = adminline [7]
			newdevname=''
			#This strips device name of the IP address
			k = 0
			while k < len(devicename):
				if devicename[k] == '[':
					break
				else:
					newdevname = newdevname + devicename[k]
				k+=1
			if 'Backup' in adminline[8] or 'backup' in adminline[8]:
				tempstring = "['"+admindate+"','" +adminline[2]+"','"+newdevname+"','"+adminline[8]+"']" 
				#tempstring = ast.literal_eval(tempstring)
				finaloutput.append(tempstring)

		j+=1
	i+=1

finaloutput = set(finaloutput)
finaloutput = list(finaloutput)

#convert the finaloutput values to lists to make nested list
lastCount = 0
while lastCount <len(finaloutput):
	templine = finaloutput[lastCount]
	templine = ast.literal_eval(templine)
	finaloutput[lastCount] = templine
	lastCount+=1

outputfile.write('Date,User,Server,Action\n')
outputline = ''
lastCount = 0
while lastCount < len (finaloutput):
	lastline = finaloutput[lastCount]
	outputline = lastline[0] + "," + lastline[1] + "," + lastline[2] + "," + lastline[3] + "\n"
	outputfile.write(outputline)
	print (lastline[0], lastline[1], lastline[2], lastline[3])
	#print (finaloutput[lastCount])
	lastCount+=1
