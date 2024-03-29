#!/usr/bin/env python3
import socket
import time
import json
from PySide2.QtWidgets import QApplication
from PySide2.QtQuick import QQuickView
from PySide2.QtCore import QUrl,QObject, Slot, Signal, Property
from PySide2.QtQuick import QQuickView
import base64
import os,subprocess,sys
sys.path.insert(1, '/usr/lib/python3/dist-packages/appconfig')
import n4dCredentialsBox as login
import logging

import gettext
import getpass
_ = gettext.gettext

QString=type("")
N4D=True
import n4d.client 
import n4d.responses
USERNOTALLOWED_ERROR=-10

class appConfigN4d(QObject):
	onCredentials=Signal(dict)
	def __init__(self,n4dmethod="",n4dclass="",n4dparms="",username='',password='',server='localhost'):
		super(appConfigN4d, self).__init__()
		self.dbg=True
		logging.basicConfig(format='%(message)s')
		self.launchQueue={}
		#No more global vars for credentials or methods, etc but server
		self.server=server
		self.key=''
		self.username=username
		self.password=password
		self.query=''
		self.n4dClass="VariablesManager"
		self.n4dMethod=''
		self.n4dParms=''
		self.retval=0
		self.n4dAuth=None
		self.n4dClient=None
		self.n4dMaster=None
		self.varName=''
		self.uptime=0
	#def __init__

	def _debug(self,msg):
		if self.dbg:
			logging.debug("appConfigN4d: {}".format(msg))

	def error(self,msg):
		logging.debug("appConfigN4d: {}".format(msg))
	#def error

	def writeConfig(self,n4dparms):
		#DEPRECATED
		self.retval=True
		return(self.retval)
	#def writeConfig
	
	def readConfig(self,n4dparms,exclude=[]):
		if self.n4dClient==None:
			self.n4dClient=self._n4d_connect()
		self.retval=0
		tmp=n4dparms.split(",")
		self.varName=tmp[0].upper()
		self.varData=""
		self.varDepends=[]
		self.n4dParms=n4dparms
		self.n4dMethod="get_variable"
		try:
			ret=self.n4dClient.get_variable(self.varName)
		except:
			return({})
		if ret['status']!=0:
			return{}
		tmpStr=ret
		if isinstance(ret,str):
			tmpStr=ret.replace("'","\"")
		if ret==None:
			tmpStr=""
		if "False" in tmpStr:
			if "False," in tmpStr:
				tmpStr=tmpStr.replace("False,","\"False\",")
			elif "False}" in tmpStr:
				tmpStr=tmpStr.replace("False}","\"False\"}")
		if "True" in tmpStr:
			if "True," in tmpStr:
				tmpStr=tmpStr.replace("True,","\"True\",")
			elif "True}" in tmpStr:
				tmpStr=tmpStr.replace("True}","\"True\"}")
		try:
			data=json.loads(tmpStr)
		except Exception as e:
			self._debug("Error reading n4d values: %s"%e)
			self._debug("Dump: %s"%tmpStr)
			data={}
		for excludeKey in exclude:
			self._debug("Search exclude %s in %s"%(excludeKey,data.keys()))
			if excludeKey in list(data.keys()):
				del data[excludeKey]
		self.varName=''
		return(data)
	#def readConfig(self,n4dparms):

	def setCredentials(self,tickets=[],n4dkey=''):
		client=None
		master=None
		if n4dkey:
			self.n4dClient=self._n4d_connect(n4dkey=n4dkey)
			return

		if not self.key in self.launchQueue.keys():
			return
		for ticket in tickets:
			if not 'localhost' in str(ticket) and not self.server_ip in str(ticket):
				self._debug("Discard ticket {} for {}".format(ticket,self.server_ip))
				continue
			n4dProxy=self._n4d_connect(ticket,self.server_ip)
			self._debug("N4d client: {}".format(n4dProxy))
			self._debug("N4d old client: {}".format(self.n4dClient))
			if 'localhost:' in str(ticket):
				self._debug("Relaunching n4dMethod on client")
				oldProxy=self.n4dClient
				self.n4dClient=n4dProxy
			elif self.server_ip in str(ticket):
				self._debug("Relaunching n4dMethod on master")
				oldProxy=self.n4dMaster
				self.n4dMaster=n4dProxy
			data=self.launchQueue.get(self.key,None)
			if not data:
				continue
			del(self.launchQueue[self.key])
			#Update all n4dcalls
			delKeys=[]
			for key in self.launchQueue.keys():
				if key.startswith(str(oldProxy)):
					delKeys.append(key)
			for delKey in delKeys:
				a=delKey
				a=a.replace(str(oldProxy),str(n4dProxy))
				self.launchQueue[a]=self.launchQueue.pop(delKey)
				self.launchQueue[a]['client']=n4dProxy
			key=self.key.replace(str(oldProxy),str(n4dProxy))
			self.launchQueue[key]={'client':n4dProxy,'n4dClass':data['n4dClass'],'n4dMethod':data['n4dMethod'],'args':data['args'],'kwargs':data.get('kwargs','')}
		if self.launchQueue:
			self.onCredentials.emit(self.launchQueue)
	#def setCredentials

	def n4dQuery(self,n4dClass,n4dMethod,*args,**kwargs):
		client=""
		server_ip="localhost"
		self._debug("Kwargs: {}".format(kwargs))
		self._debug("Query: {}.{}".format(n4dClass,n4dMethod))
		if kwargs:
			server_ip=kwargs.get('ip','server')
			self._debug("Received server: {}".format(server_ip))
			username=kwargs.get('username',self.username)
			self.n4dCLient=None
			self.username=username
			
		result={'status':-1,'return':''}
		if server_ip=='localhost' and self.n4dClient==None:
			self._debug("Creating client connection")
			self.n4dClient=self._n4d_connect(server=server_ip)
		elif self.n4dMaster==None or (self.n4dMaster!=None and server_ip not in self.n4dMaster.address):
			self._debug("Creating server connection")
			self.n4dMaster=self._n4d_connect(server=server_ip)

		#Launch and pray. If there's validation error ask for credentials
		try:
			if server_ip and server_ip!='localhost':
				self._debug("Launching n4dMethod on master")
				key="{}:{}:{}".format(str(self.n4dMaster),n4dClass,n4dMethod)
				result=self._launch(self.n4dMaster,n4dClass,n4dMethod,*args)
			else:
				self._debug("Launching n4dMethod on client")
				key="{}:{}:{}".format(str(self.n4dClient),n4dClass,n4dMethod)
				result=self._launch(self.n4dClient,n4dClass,n4dMethod,*args)
			if key in self.launchQueue.keys():
				del(self.launchQueue[key])
		except n4d.client.UserNotAllowedError as e:
			#User not allowed, ask for credentials and relaunch
			result={'status':-1,'code':USERNOTALLOWED_ERROR}
			if server_ip and server_ip!='localhost':
				self.launchQueue[key]={'client':self.n4dMaster,'n4dClass':n4dClass,'n4dMethod':n4dMethod,'args':list(args),'kwargs':kwargs}
			else:
				self.launchQueue[key]={'client':self.n4dClient,'n4dClass':n4dClass,'n4dMethod':n4dMethod,'args':list(args),'kwargs':kwargs}
			self.key=key
			#Get credentials
			self.server_ip=server_ip
			self._debug("Registering to server: {}".format(server_ip))
			if os.environ.get('DISPLAY') and os.environ.get('SUDO_USER','')=='':
				self.onCredentials.connect(self.launchN4dQueue)
				credentials=login.n4dCredentials(server_ip)
				self.loginBox=credentials.dialog
				self.loginBox.onTicket.connect(self.setCredentials)
				if self.loginBox.exec():
					result={'status':0,'code':USERNOTALLOWED_ERROR}
					result=self.result
			elif os.environ.get('SUDO_USER'):
				print("N4d Username: ")
				print("N4d Password: ")
		except n4d.client.InvalidServerResponseError as e:
			self._debug("Response: {}".format(e))
		except Exception as e:
			self._debug('Error: {}'.format(e))
		self._debug("N4d response: {}".format(result))
		return(result)
	#def n4dQuery(self,n4dclass,n4dmethod,*args):
	
	def launchN4dQueue(self,launchQueue):
		self._debug("Launch: {}".format(self.launchQueue))
		self.result=[]
		launch=self.launchQueue.copy()
		for client,callData in launch.items():
			self._debug("Exec: {}".format(callData))
			try:
				self.result=self._launch(callData['client'],callData['n4dClass'],callData['n4dMethod'],*callData['args'])
			except:
				pass
	#def launchN4dQueue(self,launchQueue):

	def n4dGetVar(self,client=None,var=''):
		return(self.get_variable(client,var))
	#def n4dGetVar

	def get_variable(self,client=None,var=''):
		if not client:
			if not self.n4dClient:
				self.n4dClient=self._n4d_connect()
			client=self.n4dClient
		result={'status':-1,'return':''}
		#Launch and pray. If there's validation error ask for credentials
		try:
			result=client.get_variable(var)
		except n4d.client.InvalidServerResponseError as e:
			print("Response: {}".format(e))
		except Exception as e:
			print(e)
		return(result)
	#def n4dGetVar

	def n4dSetVar(self,client=None,var='',val={}):
		return(self.set_variable(client,var,val))
	#def n4dGetVar

	def set_variable(self,client=None,var='',val={}):
		if not client:
			if not self.n4dClient:
				self.n4dClient=self._n4d_connect()
			client=self.n4dClient
		result={'status':-1,'return':''}
		#Launch and pray. If there's validation error ask for credentials
		try:
			result=client.set_variable("{}".format(var),val)
		except n4d.client.InvalidServerResponseError as e:
			print("Response: {}".format(e))
		except Exception as e:
			print(e)
		return(result)
	#def n4dSetVar
	
	def n4dDelVar(self,client=None,var=''):
		return(self.delete_variable(client,var))
	#def n4dGetVar

	def delete_variable(self,client=None,var=''):
		if not client:
			if not self.n4dClient:
				self.n4dClient=self._n4d_connect()
			client=self.n4dClient
		result={'status':-1,'return':''}
		#Launch and pray. If there's validation error ask for credentials
		try:
			result=client.delete_variable("{}".format(var))
		except n4d.client.InvalidServerResponseError as e:
			print("Response: {}".format(e))
		except Exception as e:
			print(e)
		return(result)
	#def n4dSetVar

	def _launch(self,n4dClient,n4dClass,n4dMethod,*args):
		proxy=n4d.client.Proxy(n4dClient,n4dClass,n4dMethod)
		if "{}:{}:{}".format(str(n4dClient),n4dClass,n4dMethod) in self.launchQueue.keys():
			del(self.launchQueue["{}:{}:{}".format(str(n4dClient),n4dClass,n4dMethod)])
		try:
			self._debug("Call client: {}".format(n4dClient))
			self._debug("Call class: {}".format(n4dClass))
			self._debug("Call method: {}".format(n4dMethod))
			if len(args):
				self._debug("Call Args: {}".format(*args))
				result=proxy.call(*args)
			else:
				result=proxy.call()
		except Exception as e:
			self._debug(e)
			raise e
		self._debug("Launch Result: {}".format(result))
		return result
	#def _launch

	def _n4d_connect(self,ticket='',server='localhost',n4dkey=''):
		if server=='localhost':
			if self.server:
				server=self.server
		self._debug("Connecting to n4d at {} -> {}".format(server,ticket))
		client=""
		if ticket:
			ticket=ticket.replace('##U+0020##',' ').rstrip()
			tk=n4d.client.Ticket(ticket)
			client=n4d.client.Client(ticket=tk)
			self._debug("N4d Object2: {}".format(client.credential.auth_type))
		elif n4dkey:
			n4dkey=n4d.client.Key(n4dkey)
			client=n4d.client.Client(key=n4dkey)
			self._debug("N4d Object2: {}".format(client.credential.auth_type))
		if client=='':
			try:
				socket.gethostbyname(server)
			except:
				#It could be an ip
				try:
					socket.inet_aton(server)
				except Exception as e:
					self.error(e)
					self.error("No server found. Reverting to localhost")
					self.server='https://localhost:9779'
			if not server.startswith("http"):
				server="https://{}".format(server)
			if len(server.split(":")) < 3:
				server="{}:9779".format(server)
				
			if self.username:
				self.error("USER: {} SERVERi self {} other {}".format(self.username,self.server,server))
				client=n4d.client.Client(server,self.username,self.password)
				sw_tk=False
				try:
					tk=client.create_ticket()
					sw_tk=True
				except:
					self.error("Using localhost as main server")
					client=n4d.client.Client(self.server,self.username,self.password)
					try:
						tk=client.create_ticket()
						sw_tk=True
					except Exception as e:
						self.error(e)
						tk=""
				if sw_tk:
					client=n4d.client.Client(ticket=tk)
			else:
				client=n4d.client.Client(server)
		self._debug("N4d Object2: {}".format(client.credential.auth_type))
		return(client)
	#def _n4d_connect

