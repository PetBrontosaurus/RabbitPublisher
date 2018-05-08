import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import pika
import time
import win32evtlog
import sys

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "EventPuller"
    _svc_display_name_ = "EventPuller"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
		

    def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                          servicemanager.PYS_SERVICE_STARTED,
                          (self._svc_name_,''))
        self.main()


    def main(self):

		
	#Goal: loop searching event log for new events every minute or so,
	#      and kicking it out to rabbitMQ
		rc = None  
          
        # # if the stop event hasn't been fired keep looping  
		while rc != win32event.WAIT_OBJECT_0:
			eventHandle = win32evtlog.OpenEventLog(None, "Application")
			flags = win32evtlog.EVENTLOG_FORWARDS_READ|win32evtlog.EVENTLOG_SEEK_READ

			try:
				file = open("PATH_TO_TXT_FILE_CONTAINING_DESIRED_START_INDEX", "r") 
				indexString = file.readline()
				eventIndex = int(indexString)
			except:
				eventIndex = 32500

			#TODO: move var declarations outside while loop, hide details inside function.
			messageList = []
			messageString = ""
			batchLimit = 10 
			batchCounter = 0
			eventLimit = 10
			eventCounter = 0
			while batchCounter < batchLimit:
				events = win32evtlog.ReadEventLog(eventHandle,flags,eventIndex)
				if events:
					eventCounter = 0
					for event in events:
						messageString += 'Event Category: ' + str(event.EventCategory) + "\r\n"
						messageString += 'Time Generated: ' + str(event.TimeGenerated) + "\r\n"
						messageString += 'Source Name: ' +  str(event.SourceName) + "\r\n"
						messageString += 'Event ID: ' + str(event.EventID) + "\r\n"
						messageString += 'Event Type: ' +  str(event.EventType) + "\r\n"
						data = event.StringInserts
						if data:
							messageString += 'Event Data:'
							for msg in data:
								messageString += msg + "\r\n"
						messageList.append(messageString)
						messageString = ""
						eventCounter += 1
						if eventCounter >= eventLimit:
							break
				batchCounter += 1
					
			connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
			channel = connection.channel()
			channel.queue_declare(queue='EventLog')
			
			for message in messageList:
				channel.basic_publish(exchange='',
					routing_key='EventLog',
					body=message)
			connection.close()
			rc = win32event.WaitForSingleObject(self.hWaitStop, 30000)

	
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)

	
	
	
	
	
	
	
	
# Example of proper way to stop/start services
# from http://www.chrisumbel.com/article/windows_services_in_python
	
# import win32service  
# import win32serviceutil  
# import win32event  
  
# class PySvc(win32serviceutil.ServiceFramework):  
    # # you can NET START/STOP the service by the following name  
    # _svc_name_ = "PySvc"  
    # # this text shows up as the service name in the Service  
    # # Control Manager (SCM)  
    # _svc_display_name_ = "Python Test Service"  
    # # this text shows up as the description in the SCM  
    # _svc_description_ = "This service writes stuff to a file"  
      
    # def __init__(self, args):  
        # win32serviceutil.ServiceFramework.__init__(self,args)  
        # # create an event to listen for stop requests on  
        # self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)  
      
    # # core logic of the service     
    # def SvcDoRun(self):  
        # import servicemanager  
          
        # f = open('test.dat', 'w+')  
        # rc = None  
          
        # # if the stop event hasn't been fired keep looping  
        # while rc != win32event.WAIT_OBJECT_0:  
            # f.write('TEST DATA\n')  
            # f.flush()  
            # # block for 5 seconds and listen for a stop event  
            # rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)  
              
        # f.write('SHUTTING DOWN\n')  
        # f.close()  
      
    # # called when we're being shut down      
    # def SvcStop(self):  
        # # tell the SCM we're shutting down  
        # self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)  
        # # fire the stop event  
        # win32event.SetEvent(self.hWaitStop)  
          
# if __name__ == '__main__':  
    # win32serviceutil.HandleCommandLine(PySvc) 
	
	
	
	
# install it with:  
# C:\Dev\Projects\PySvc> python.exe .\PySvc.py install
