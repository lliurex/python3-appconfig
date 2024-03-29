import os
import tempfile
from PySide2.QtWidgets import QWidget, QPushButton,QScrollArea,QVBoxLayout,QLabel,QHBoxLayout,QDialog,QScroller,QScrollerProperties,QTableWidget,QLineEdit,QListWidget,QHeaderView,QAbstractItemView,QGridLayout,QComboBox,QTableWidgetItem,QDesktopWidget
from PySide2 import QtGui
from PySide2.QtCore import Qt,Signal,QEvent,QThread,QSize,QPointF,QRectF,QRect
import gettext
import requests
import hashlib
_ = gettext.gettext

i18n={
	"PRESSKEY":_("Press keys"),
	"SEARCH":_("Search..."),
	"FILTERS":_("Filters"),
	"APPLY":_("Apply")
}

class loadScreenShot(QThread):
	imageLoaded=Signal("PyObject")
	def __init__(self,*args):
		super().__init__()
		self.img=args[0]
		self.cacheDir=None
		if len(args)>1:
			self.setCacheDir(args[1])
	#def __init__

	def _debug(self,msg):
		print("{}".format(msg))
	
	def setCacheDir(self,cacheDir):
		sureDirs=["/tmp/.cache",os.path.join(os.environ.get('HOME',''),".cache")]
		if isinstance(cacheDir,str)==False:
			cacheDir=''
		for sure in sureDirs:
			if sure in cacheDir:
				sureDirs=[]
				break
		if sureDirs:
			return
		if isinstance(cacheDir,str)==False:
			cacheDir=""
		if os.path.exists(cacheDir)==False:
			try:
				os.makedirs(cacheDir)
			except Exception as e:
				print("mdkdir {0} failed: {1}".format(cacheDir,e))
		if os.path.isdir(cacheDir)==True:
			self.cacheDir=cacheDir
		self._debug("Cache set to {}".format(self.cacheDir))
	#def setCacheDir

	def run(self,*args):
		img=None
		md5Name=""
		md5Name=hashlib.md5(self.img.encode())
		icn=QtGui.QIcon.fromTheme("image-x-generic")
		pxm=icn.pixmap(512,512)
		if self.cacheDir:
			fPath=os.path.join(self.cacheDir,str(md5Name.hexdigest()))#self.img.split('/')[-1])
			if os.path.isfile(fPath)==True:
				pxm=QtGui.QPixmap()
				try:
					pxm.load(fPath)
					img=True
				except Exception as e:
					print("Loading cache pixmap: {}".format(e))
		if img==None:
			try:
				img=requests.get(self.img)
				pxm.loadFromData(img.content)
			except Exception as e:
				img=None
				print("request: {}".format(e))
		if img:
			if self.cacheDir:
				fPath=os.path.join(self.cacheDir,str(md5Name.hexdigest()))
				if os.path.exists(fPath)==False:
					pxm=pxm.scaled(256,256,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
					p=pxm.save(fPath,"PNG")#,quality=5)
		self.imageLoaded.emit(pxm)
		return True
	#def run

class QCheckableComboBox(QComboBox):
	clicked=Signal()
	closed=Signal()
	def __init__(self,parent=None):
		QComboBox.__init__(self, parent)
		self.view().pressed.connect(self._checked)
		self.setModel(QtGui.QStandardItemModel(self))
		self.checked=False
		self.addItem("")
	#def __init__

	def _checked(self, index):
		self.checked=True
		if index.row()==0:
			return
		item = self.model().itemFromIndex(index)
		if item.checkState() == Qt.Checked:
			item.setCheckState(Qt.Unchecked)
		else:
			item.setCheckState(Qt.Checked)
		self.clicked.emit()
		return(False)
	#def _checked

	def setText(self,text):
		if self.count()==0:
			self.addItem("")
		item=self.model().item(0)
		item.setText(text)
	#def setText

	def hidePopup(self,*args,close=False):
		self.setCurrentIndex(0)
		if close==False and self.checked==True:
			self.checked=False
			self.closed.emit()
			return close
		super().hidePopup()
	#def hidePopup

	def addItem(self,*args,state=True):
		super().addItem(args[0])
		item=self.model().item(self.count()-1)
		if self.count()>1:
			if state==True:
				item.setCheckState(Qt.Checked)
			else:
				item.setCheckState(Qt.Unchecked)
	#	rect=self.view().sizeHint()
	#	Xpos=0
	#	Ypos=rect.height()
	#	self.btn.move(Xpos,Ypos)
	#def addItem

	def getItems(self,*args):
		items=[]
		for i in range(0,self.count()):
			item=self.model().item(i)
			items.append(item)
		return(items)
	#def getItems

	def setState(self,idx,state):
		item=self.model().item(idx)
		if state==True:
			item.setCheckState(Qt.Checked)
		else:
			item.setCheckState(Qt.Unchecked)
	#def setState
#class QCheckableComboBox

class QSearchBox(QWidget):
	clicked=Signal()
	editingFinished=Signal()
	returnPressed=Signal()
	textChanged=Signal()
	def __init__(self,parent=None):
		QWidget.__init__(self, parent)
		lay=QHBoxLayout()
		self.setStyleSheet('QPushButton{margin-left:1px;} QLineEdit{margin-right:0px;}')
		lay.setContentsMargins(0, 0, 0, 0)
		lay.setSpacing(0)
		self.txtSearch=QLineEdit()
		self.txtSearch.editingFinished.connect(self._emitEdit)
		self.txtSearch.returnPressed.connect(self._emitReturn)
		self.txtSearch.textChanged.connect(self._emitChange)
		self.txtSearch.setPlaceholderText(i18n.get("SEARCH"))
		lay.addWidget(self.txtSearch)
		self.btnSearch=QPushButton()
		icn=QtGui.QIcon.fromTheme("search")
		self.btnSearch.clicked.connect(self._emitClick)
		self.btnSearch.setIcon(icn)
		lay.addWidget(self.btnSearch)
		self.setLayout(lay)
	#def __init__

	def _emitClick(self):
		self.clicked.emit()
	#def _emitClick

	def _emitEdit(self):
		self.editingFinished.emit()
	#def _emitEdit

	def _emitReturn(self):
		self.returnPressed.emit()
	#def _emitEdit

	def _emitChange(self):
		self.textChanged.emit()
	#def _emitEdit

	def text(self):
		return(self.txtSearch.text())
	#def text

	def setText(self,text):
		self.txtSearch.setText(text)
	#def setText

	def setPlaceholderText(self,text):
		self.txtSearch.setPlaceholderText(text)
	#def setPlaceholderText
#class QSearchBox

class QTableTouchWidget(QTableWidget):
	def __init__(self,parent=None):
		QTableWidget.__init__(self, parent)
		self.scroller=QScroller()
		self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
#		sp=self.scroller.scrollerProperties()
#		sp.setScrollMetric(QScrollerProperties.DragVelocitySmoothingFactor,0.6)
#		sp.setScrollMetric(QScrollerProperties.MinimumVelocity,0.0)
#		sp.setScrollMetric(QScrollerProperties.MaximumVelocity,0.5)
#		sp.setScrollMetric(QScrollerProperties.AcceleratingFlickMaximumTime,0.4)
#		sp.setScrollMetric(QScrollerProperties.AcceleratingFlickSpeedupFactor,1.2)
#		sp.setScrollMetric(QScrollerProperties.SnapPositionRatio,0.2)
#		sp.setScrollMetric(QScrollerProperties.MaximumClickThroughVelocity,0)
#		sp.setScrollMetric(QScrollerProperties.DragStartDistance,0.001)
#		sp.setScrollMetric(QScrollerProperties.MousePressEventDelay,0.5)
		self.scroller.grabGesture(self.viewport(),self.scroller.LeftMouseButtonGesture)
	#def __init__
#class QTableTouchWidget

class QHotkeyButton(QPushButton):
	keybind_signal=Signal("PyObject")
	hotkeyAssigned=Signal("PyObject")
	def __init__(self,text="",parent=None):
		QPushButton.__init__(self, parent)
		self.installEventFilter(self)
		self.keymap={}
		for key,value in vars(Qt).items():
			if isinstance(value, Qt.Key):
				self.keymap[value]=key.partition('_')[2]
		self.modmap={
					Qt.ControlModifier: self.keymap[Qt.Key_Control],
					Qt.AltModifier: self.keymap[Qt.Key_Alt],
					Qt.ShiftModifier: self.keymap[Qt.Key_Shift],
					Qt.MetaModifier: self.keymap[Qt.Key_Meta],
					Qt.GroupSwitchModifier: self.keymap[Qt.Key_AltGr],
					Qt.KeypadModifier: self.keymap[Qt.Key_NumLock]
					}
		self.processed=False
		self.setText(text)
		self.originalText=text
	#def __init__

	def setIconSize(self,*args):
		pass
	#def setIconSize(self,*args):

	def mousePressEvent(self, ev):
		self.originalText=self.text()
		self.setText(i18n.get("PRESSKEY"))
		self.processed=False
		self._grab_alt_keys()
	#def mousePressEvent

	def eventFilter(self,source,event):
		sw_mod=False
		keypressed=[]
		if (event.type()==QEvent.KeyPress):
			for modifier,text in self.modmap.items():
				if event.modifiers() & modifier:
					sw_mod=True
					keypressed.append(text)
			key=self.keymap.get(event.key(),event.text())
			if key not in keypressed:
				if sw_mod==True:
					sw_mod=False
				keypressed.append(key)
			if sw_mod==False:
				self.keybind_signal.emit("+".join(keypressed))
		if (event.type()==QEvent.KeyRelease):
			self.releaseKeyboard()
			if self.processed==False:
				action=self.getSettingForHotkey()
				retVal={"hotkey":self.text(),"action":action}
				self.hotkeyAssigned.emit(retVal)
			self.processed=True

		return False
	#def eventFilter

	def _grab_alt_keys(self,*args):
		self.keybind_signal.connect(self._set_config_key)
		self.grabKeyboard()
	#def _grab_alt_keys

	def _set_config_key(self,keypress):
		keypress=keypress.replace("Control","Ctrl")
		self.setText(keypress)
	#def _set_config_key

	def getSettingForHotkey(self):
		hotkey=self.text()
		kfile="kglobalshortcutsrc"
		action=""
		sourceFolder=os.path.join(os.environ.get('HOME',"/usr/share/acccessibility"),".config")
		kPath=os.path.join(sourceFolder,kfile)
		with open(kPath,"r") as f:
			lines=f.readlines()
		for line in lines:
			if len(line.split(","))>2:
				if hotkey.lower()==line.split(",")[-2].lower():
					action=line.split(",")[-1]
					break
				elif line.startswith("_launch"):
					if hotkey.lower()==line.replace("_launch=","").split(",")[0].lower():
						action=line.split(",")[-1]
						break
		return(action.replace("\n",""))
	#def getSettingForHotkey

	def revertHotkey(self):
		self.setText(self.originalText)
	#def revertHotkey
#class QHotkeyButton

class QScrollLabel(QScrollArea):
	def __init__(self,text="",parent=None):
		QScrollArea.__init__(self, parent)
		self.setWidgetResizable(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		content = QWidget(self)
		self.setWidget(content)
		lay = QVBoxLayout(content)
		self.label = QLabel(content)
		self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
		self.label.setWordWrap(True)
		lay.addWidget(self.label)
		self.label.setText(text)
		self.label.adjustSize()
#		self.setFixedWidth(self.label.sizeHint().width())
#		self.setFixedHeight(self.label.sizeHint().height()/2)
	#def __init__

	def setText(self,text):
		self.label.setText(text)
#		self.setFixedWidth(self.label.sizeHint().width())
#		self.setFixedHeight(self.label.sizeHint().height())
		self.label.adjustSize()
	#def setText

	def setWordWrap(self,boolWrap):
		self.label.setWordWrap(boolWrap)
	#def setWordWrap

	def adjustWidth(self,width):
		if self.width()<width-50:
			self.setFixedWidth(width-50)
	#def adjustWidth

	def adjustHeight(self,height):
		if self.height()<height-50:
			self.setFixedHeight(height-50)
	#def adjustHeight
#class QScrollLabel

class QScreenShotContainer(QWidget):
	def __init__(self,parent=None):
		QWidget.__init__(self, parent)
		self.widget=QWidget()
		self.lay=QHBoxLayout()
		self.outLay=QHBoxLayout()
		self.scroll=QScrollArea()
		self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.scroll.setWidgetResizable(True)
		self.scroll.setWidget(self.widget)
		self.outLay.addWidget(self.scroll)
		self.setLayout(self.outLay)
		self.widget.setLayout(self.lay)
		self.cacheDir=None
		self.th=[]
		self.btnImg={}
		self.destroyed.connect(lambda: self._cleanThreads())
	#def __init__

	def setCacheDir(self,cacheDir):
		if os.path.exists(cacheDir)==False:
			try:
				os.makedirs(cacheDir)
			except Exception as e:
				print("mdkdir {0} failed: {1}".format(cacheDir,e))
		if os.path.isdir(cacheDir)==True:
			self.cacheDir=cacheDir
	#def setCacheDir

	def eventFilter(self,source,qevent):
		if isinstance(qevent,QEvent):
			if qevent.type()==QEvent.Type.MouseButtonPress:
				self._carrousel(source)
		return(False)
	#def eventFilter

	def _carrousel(self,btn="",w=0,h=0):
		dlg=QDialog()	
		dlg.setModal(True)
		if (w==0) or (h==0):
			sizeObject = QDesktopWidget().screenGeometry(-1)
			w=int(sizeObject.width()/2)
			h=int(sizeObject.height()/2)
		xSize=w
		ySize=h
		#widget=QWidget()
		self.widget=QTableTouchWidget()
		self.widget.setRowCount(1)
		self.widget.setShowGrid(True)
		self.widget.verticalHeader().hide()
		self.widget.horizontalHeader().hide()
		#widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.widget.setRowCount(1)
		mainLay=QGridLayout()
		mainLay.setHorizontalSpacing(0)
		selectedImg=""
		arrayImg=[]
		for btnImg,img in self.btnImg.items():
			lbl=QLabel()
			lbl.setPixmap(img.scaled(xSize,ySize,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
			if btnImg==btn:	
				selectedImg=lbl
			else:
				arrayImg.append(lbl)
		if selectedImg:
			self.widget.setColumnCount(self.widget.columnCount()+1)
			container=QWidget()
			lay=QHBoxLayout()
			container.setLayout(lay)
			container.setFixedSize(QSize(xSize,ySize))
			lay.addStretch()
			lay.addWidget(selectedImg)
			lay.addStretch()
			self.widget.setCellWidget(0,self.widget.columnCount()-1,container)
			self.widget.setItem(0,self.widget.columnCount()-1,QTableWidgetItem())
			self.widget.setColumnWidth(self.widget.columnCount()-1,xSize)
			self.widget.setRowHeight(self.widget.rowCount()-1,ySize)

		for lbl in arrayImg:
			self.widget.setColumnCount(self.widget.columnCount()+1)
			container=QWidget()
			container.setFixedSize(QSize(xSize,ySize))
			lay=QHBoxLayout()
			container.setLayout(lay)
			lay.addStretch()
			lay.addWidget(lbl)
			lay.addStretch()
			self.widget.setCellWidget(0,self.widget.columnCount()-1,container)
			self.widget.setItem(0,self.widget.columnCount()-1,QTableWidgetItem())
			self.widget.setColumnWidth(self.widget.columnCount()-1,xSize)
			self.widget.setRowHeight(self.widget.rowCount()-1,ySize)
		icn=QtGui.QIcon.fromTheme("window-close")
		btnClose=QPushButton()
		btnClose.setIcon(icn)
		btnClose.setIconSize(QSize(24,24))
		icn=QtGui.QIcon.fromTheme("go-previous")
		btnPrev=QPushButton()
		btnPrev.setIcon(icn)
		btnPrev.setIconSize(QSize(24,24))
		icn=QtGui.QIcon.fromTheme("go-next")
		btnNext=QPushButton()
		btnNext.setIcon(icn)
		btnNext.setIconSize(QSize(24,24))
		fontSize=btnPrev.font().pointSize()
		btnClose.clicked.connect(dlg.reject)
		btnPrev.clicked.connect(lambda x:self._scrollContainer("left"))
		btnNext.clicked.connect(lambda x:self._scrollContainer("right"))
		mainLay.addWidget(btnPrev,0,0,1,1,Qt.AlignRight)
		mainLay.addWidget(self.widget,0,1,1,1)
		mainLay.addWidget(btnClose,0,2,1,1,Qt.AlignTop|Qt.AlignRight)
		mainLay.addWidget(btnNext,0,2,1,1,Qt.AlignLeft)
		dlg.setLayout(mainLay)
		dlg.setFixedSize(xSize+(0.1*xSize),ySize+(0.1*ySize))
		dlg.exec()
	#def carrousel
	
	def _scrollContainer(self,*args):
		if len(args)==0:
			return
		visible = self.widget.itemAt(20, 20)
		column=1
		if visible is not None:
			column=visible.column()
		if args[0]=="left":
			if column<=0:
				column=self.widget.columnCount()
			self.widget.scrollToItem(self.widget.item(visible.row(), column-1))
		elif args[0]=="right":
			if column>=self.widget.columnCount()-1:
				column=-1
			self.widget.scrollToItem(self.widget.item(visible.row(), column+1))
	#def scrollContainer(self,*args):
	
	def addImage(self,img):
		scr=loadScreenShot(img,self.cacheDir)
		self.th.append(scr)
		scr.imageLoaded.connect(self._load)
		scr.start()
	#def addImage

	def _load(self,*args):
		img=args[0]
		if isinstance(img,QtGui.QPixmap):
			if img.isNull()==False:
				btnImg=QPushButton()
				self.lay.addWidget(btnImg)
				self.btnImg[btnImg]=img
				icn=QtGui.QIcon(img)
				btnImg.setIcon(icn)
				btnImg.setIconSize(QSize(128,128))
				self.scroll.setFixedHeight(btnImg.sizeHint().height()+32)
				btnImg.installEventFilter(self)
				btnImg.show()
	#def load

	def clear(self):
		for i in reversed(range(self.lay.count())): 
			self.lay.itemAt(i).widget().setParent(None)
		self.btnImg={}
	#def clear

	def _cleanThreads(self):
		for th in self.th:
			th.quit()
			th.wait()
	#def _cleanThreads
#class QScreenShotContainer
