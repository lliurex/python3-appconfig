#!/usr/bin/env python3
from PyQt5.QtWidgets import QWidget,QHBoxLayout,QPushButton
from PyQt5.QtCore import pyqtSignal,Qt
from PyQt5 import QtGui
from edupals.ui import QAnimatedStatusBar
import gettext
#_ = nullTrans.gettext
_=gettext.gettext
QString=type("")

class appConfigStack(QWidget):
	message=pyqtSignal("PyQt_PyObject","PyQt_PyObject")
	def __init__(self,stack):
		super().__init__()
		self.dbg=False
		self.default_icon='shell'
		self.menu_description=(_("Configure stack"))
		self.description=(_("Configure custom stack"))
		self.icon=('org.kde.plasma.quicklaunch')
		self.tooltip=(_("From here you can configure something"))
		self.index=1
		self.enabled=True
		self.sw_changes=False
		self.level='user'
		self.appConfig=None
		self.config={}
		self.changes=False
		self.add_events=False
		self.refresh=False
		self.stack=stack
		self.textdomain=''
		self.btn_ok=QPushButton(_("Apply"))
		self.btn_cancel=QPushButton(_("Undo"))
		self.__init_stack__()
		self.writeConfig=self.writeDecorator(self.writeConfig)
	#def __init__

	def __init_stack__(self):
		raise NotImplementedError()
	#def __init_stack__
	
	def _debug(self,msg):
		if self.dbg:
				print("Stackdbg: %s: %s"%(self.description,msg))
	#def _debug

	def initScreen(self):
		self._debug("No init values")

	def setAppConfig(self,appconfig):
		self.appConfig=appconfig
	#def setAppConfig

	def translate(self,msg=""):
		return(gettext.dgettext(self.textdomain,msg))

	def setTextDomain(self,textDomain):
		gettext.textdomain(textDomain)
	#def set_textDomain(self,textDomain):
	
	def applyParms(self,app):
		self._debug("Set parm %s"%app)
		self.app=app
	#def apply_parms(self,app):

	def getConfig(self,level=None,exclude=[]):
		self._debug("Getting config for level %s"%level)
		self._debug("Exclude keys: %s"%exclude)
		cursor=QtGui.QCursor(Qt.WaitCursor)
		self.setCursor(cursor)
		data={'system':{},'user':{},'n4d':{}}
		self._debug("Refresh: %s"%self.refresh)
		self._debug("Changes: %s"%self.changes)
		if self.refresh or self.changes:
			if level:
				data=self.appConfig.getConfig(level,exclude)
			else:
				data=self.appConfig.getConfig('system',exclude)
#				self._debug("Data: %s"%data)
				self.level=data['system'].get('config','user')
				if self.level!='system':
					data=self.appConfig.getConfig(self.level,exclude)
					level=data[self.level].get('config','n4d')
					if level!=self.level:
						self.level=level
						data=self.appConfig.getConfig(level,exclude)
						data[self.level]['config']=self.level
		else:
			if self.config[self.level]:
				data[self.level]=self.config[self.level].copy()
		self._debug("Read level from config: %s"%self.level)
		self.refresh=False
		cursor=QtGui.QCursor(Qt.PointingHandCursor)
		self.setCursor(cursor)
		return (data)
	#def get_default_config

	def setConfig(self,config):
		if self.config and self.config==config:
			self.refresh=False
		else:
			if self.config:
				self.refresh=True
			self.config=config.copy()
	#def setConfig

	def setLevel(self,level):
		self.level=level
	#def setLevel
	
	def _reset_screen(self):
		self.updateScreen()
		self.setChanged('',False)
	#def _reset_screen

	def updateScreen(self):
		print("updateScreen method not implemented in this stack")
		raise NotImplementedError()
	#def updateScreen

	def saveChanges(self,key,data,level=None):
		cursor=QtGui.QCursor(Qt.WaitCursor)
		self.setCursor(cursor)
		retval=False
		if not level:
			self.getConfig()
			level=self.level
		self._debug("Saving to level %s"%level)
		retval=True
		if not self.appConfig.write_config(data,level=level,key=key):
			self.btn_ok.setEnabled(True)
			self.btn_cancel.setEnabled(True)
			self.refresh=False
			self.changes=True
			retval=False
			self.showMsg("Failed to write config")
		cursor=QtGui.QCursor(Qt.PointingHandCursor)
		self.setCursor(cursor)
		return retval
	#def saveChanges
	
	def writeDecorator(self,func):
		def states():
			cursor=QtGui.QCursor(Qt.WaitCursor)
			self.setCursor(cursor)
			func()
			self.btn_ok.setEnabled(False)
			self.btn_cancel.setEnabled(False)
			self.refresh=True
			self.changes=False
			cursor=QtGui.QCursor(Qt.PointingHandCursor)
			self.setCursor(cursor)
		return states
	#def writeDecorator

	def writeConfig(self):
		print("writeConfig method not implemented in this stack")
		raise NotImplementedError()
	#def writeConfig

	def showEvent(self,event):
		def recursive_add_events(layout):

			def recursive_explore_widgets(widget):
					if widget==None:
						return
					if "QCheckBox" in str(widget):
						widget.stateChanged.connect(lambda x:self.setChanged(widget))
					elif "QComboBox" in str(widget):
						widget.currentIndexChanged.connect(lambda x:self.setChanged(widget))
					elif "QLineEdit" in str(widget):
						widget.textChanged.connect(lambda x:self.setChanged(widget))
					elif "QPushButton" in str(widget):
						if widget.menu():
							widget.menu().triggered.connect(lambda x:self.setChanged(widget))
						else:
							widget.clicked.connect(lambda x:self.setChanged(widget))
					elif 'dropButton' in str(widget):
							widget.drop.connect(lambda x:self.setChanged(widget))
					elif "Table" in str(widget):
						for x in range (0,widget.rowCount()):
							for y in range (0,widget.columnCount()):
								tableWidget=widget.cellWidget(x,y)
								recursive_explore_widgets(tableWidget)
					elif widget.layout():
						recursive_add_events(widget.layout())

			for idx in range(0,layout.count()):
				widget=layout.itemAt(idx).widget()
				if widget:
					recursive_explore_widgets(widget)

				elif layout.itemAt(idx).layout():
					recursive_add_events(layout.itemAt(idx).layout())

		if self.add_events==False:
			self.add_events=True
			layout=self.layout()
			if layout:
				recursive_add_events(layout)
				box_btns=QHBoxLayout()
				self.btn_ok.clicked.connect(self.writeConfig)
				self.btn_ok.setFixedWidth(100)
				self.btn_cancel.clicked.connect(self._reset_screen)
				self.btn_cancel.setFixedWidth(100)
				box_btns.addWidget(self.btn_ok,1,Qt.AlignRight)
				box_btns.addWidget(self.btn_cancel,Qt.AlignRight)
				try:
					layout.addLayout(box_btns,Qt.Alignment(0))
				except:
					layout.addLayout(box_btns,layout.rowCount(),0,1,layout.columnCount())
		self.btn_ok.setEnabled(False)
		self.btn_cancel.setEnabled(False)
		try:
			self.updateScreen()
			self.setChanged("",False)
		except:
			print("updateScreen method is not implemented in this stack")
	#def showEvent

	def hideControlButtons(self):
		self.btn_ok.hide()
		self.btn_cancel.hide()
	#def hideControlButtons(self):

	def setChanged(self,widget,state=True):
		self._debug("State: %s"%state)
		if self.btn_ok.isHidden()==False:
			self.btn_ok.setEnabled(state)
			self.btn_cancel.setEnabled(state)
		else:
			state=False
		self.changes=state
	#def setChanged

	def getChanges(self):
		return self.changes
	#def getChanges

	def setParms(self,parms):
		return
	#def setParms

	def showMsg(self,msg,state=None):
		self._debug("Sending %s"%msg)
		self.message.emit(msg,state)
	#def showMsg

	def n4dQuery(self,n4dclass,n4dmethod,n4dparms=''):
		return(self.appConfig.n4dQuery(n4dclass,n4dmethod,n4dparms))
	#def n4dQuery

#class appConfigStack
