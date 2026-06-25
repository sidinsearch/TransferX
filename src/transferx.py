import sys
import pyperclip
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QSpacerItem, QSizePolicy, QTabWidget
)
from PyQt5.QtGui import QPixmap, QImage, QMovie, QCursor, QDragEnterEvent, QDropEvent, QIcon
from PyQt5.QtCore import QSize, Qt, QFileInfo, QThread, pyqtSignal, QMimeData
import qrcode
import os
import asyncio
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription
import ctypes

NETLIFY_SITE = "https://p2pxrelay.netlify.app/.netlify/functions/relay"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB in bytes

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class TransferX(QWidget):

    def __init__(self):
        super().__init__()
        self.download_link = ""
        self.share_id = ""
        self.file_path = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle("TransferX")
        self.setWindowIcon(QIcon(resource_path('icon.ico')))
        self.setFixedSize(400, 410)
        self.setAcceptDrops(True)  # Enable drag and drop for the main window

        self.tabWidget = QTabWidget(self)
        self.tabWidget.setFixedSize(400, 410)

        self.TransferXTab = QWidget()
        self.initTransferXTab()
        self.tabWidget.addTab(self.TransferXTab, "Quick Share")

        self.aboutTab = QWidget()
        self.initAboutTab()
        self.tabWidget.addTab(self.aboutTab, "About")

        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(self.tabWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("""
        QWidget {
            font-family: 'Google Sans', sans-serif;
            background-color: #f0f0f0;
        }
        QLabel {
            font-size: 14px;
            margin-bottom: 5px;
        }
        QLineEdit {
            padding: 8px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        QPushButton {
            font-size: 14px;
            padding: 8px;
            border: none;
            border-radius: 5px;
        }
        QPushButton#browseButton {
            background-color: #FFD700;
            color: black;
        }
        QPushButton#uploadButton {
            background-color: #45a049;
            color: white;
        }
        QPushButton#clearButton {
            background-color: #ff4d4d;
            color: white;
        }
        QPushButton#browseButton:hover,
        QPushButton#uploadButton:hover,
        QPushButton#clearButton:hover {
            opacity: 0.8;
        }""")

    def initTransferXTab(self):
        self.TransferXTab.setAcceptDrops(True)

        self.label = QLabel("📁 Click to Browse or Drag & Drop Your File Here! 🚀")
        self.filePathLineEdit = QLineEdit()
        self.browseButton = QPushButton("Browse")
        self.uploadButton = QPushButton("Share")
        self.clearButton = QPushButton("Clear")

        self.logoLabel = QLabel()
        logoPixmap = QPixmap(resource_path("main.png"))
        logoPixmap = logoPixmap.scaled(QSize(311, 202), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logoLabel.setPixmap(logoPixmap)
        self.logoLabel.setAlignment(Qt.AlignCenter)
        self.logoLabel.setScaledContents(True)

        self.fileSizeLimitLabel = QLabel("⚠️ NOTE: MAX FILE SIZE ALLOWED IS 20MB")
        self.fileSizeLimitLabel.setStyleSheet("QLabel { color: black; font-size: 11px; }")
        self.fileSizeLimitLabel.setAlignment(Qt.AlignCenter)

        self.scanMeLabel = QLabel("📱 Scan QR Code to Download the File")
        self.scanMeLabel.setStyleSheet("QLabel { color: black; font-size: 13px; }")
        self.scanMeLabel.setAlignment(Qt.AlignCenter)
        self.scanMeLabel.hide()

        self.qrCodeLabel = QLabel()
        self.qrCodeLabel.setAlignment(Qt.AlignCenter)
        self.qrCodeLabel.setStyleSheet("""
        QLabel {
            background-color: white;
            border: 1px solid #333333;
            padding: 10px;
        }""")
        self.qrCodeLabel.hide()
        self.qrCodeLabel.setCursor(QCursor(Qt.PointingHandCursor))
        self.qrCodeLabel.mousePressEvent = self.copyLinkToClipboard

        self.clickInfoLabel = QLabel("👆 Click on QR Code to Copy the Download Link")
        self.clickInfoLabel.setStyleSheet("QLabel { color: black; font-size: 12px; }")
        self.clickInfoLabel.setAlignment(Qt.AlignCenter)
        self.clickInfoLabel.hide()

        self.loadingLabel = QLabel(self.TransferXTab)
        self.loadingMovie = QMovie(resource_path("loading.gif"))
        self.loadingMovie.setScaledSize(QSize(100, 100))
        self.loadingLabel.setMovie(self.loadingMovie)
        self.loadingLabel.setAlignment(Qt.AlignCenter)
        self.loadingLabel.setFixedSize(100, 100)
        self.loadingLabel.hide()

        self.quoteLabel = QLabel()
        self.quoteLabel.setStyleSheet("QLabel { color: #333; font-size: 14px; font-style: italic; }")
        self.quoteLabel.setAlignment(Qt.AlignCenter)
        self.quoteLabel.setWordWrap(True)
        self.quoteLabel.setFixedWidth(380)
        self.quoteLabel.hide()

        mainLayout = QVBoxLayout(self.TransferXTab)
        mainLayout.addWidget(self.label)
        mainLayout.addWidget(self.filePathLineEdit)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.browseButton)
        buttonLayout.addWidget(self.uploadButton)
        buttonLayout.addWidget(self.clearButton)
        mainLayout.addLayout(buttonLayout)

        mainLayout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        mainLayout.addWidget(self.logoLabel, 0, Qt.AlignHCenter)

        scanMeQRLayout = QVBoxLayout()
        scanMeQRLayout.addWidget(self.scanMeLabel)
        scanMeQRLayout.addWidget(self.qrCodeLabel, 0, Qt.AlignHCenter)
        scanMeQRLayout.addWidget(self.clickInfoLabel)
        mainLayout.addLayout(scanMeQRLayout)

        mainLayout.addSpacerItem(QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))

        loadingLayout = QVBoxLayout()
        loadingLayout.addStretch(1)
        loadingLayout.addWidget(self.loadingLabel, 0, Qt.AlignCenter)
        loadingLayout.addWidget(self.quoteLabel, 0, Qt.AlignCenter)
        loadingLayout.addStretch(1)
        mainLayout.addLayout(loadingLayout)

        mainLayout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        mainLayout.addWidget(self.fileSizeLimitLabel)

        self.browseButton.setObjectName("browseButton")
        self.uploadButton.setObjectName("uploadButton")
        self.clearButton.setObjectName("clearButton")
        self.browseButton.clicked.connect(self.browseFile)
        self.uploadButton.clicked.connect(self.uploadFile)
        self.clearButton.clicked.connect(self.clearAll)

    def initAboutTab(self):
        aboutLayout = QVBoxLayout(self.aboutTab)
        aboutLayout.setContentsMargins(20, 20, 20, 20)
        aboutLayout.setSpacing(10)

        titleLabel = QLabel("About TransferX")
        titleLabel.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        titleLabel.setAlignment(Qt.AlignCenter)

        aboutText = QLabel(
            """<p><strong>TransferX</strong> is a cutting-edge file sharing application utilizing Peer-to-Peer technology for secure and fast transfers.</p>
            <p>Key Features:</p>
            <ul>
                <li>💾 File Size Limit: 20MB</li>
                <li>🔐 Enhanced Security with P2P</li>
                <li>🖥️ Simple, Intuitive Interface</li>
            </ul>
            <p>Built on the <a href='https://github.com/sidinsearch/P2PxRelay'>P2PxRelay</a> project.</p>
            <p><strong>Why P2P?</strong> Enhanced privacy and security by avoiding central servers.</p>
            <p><strong>Version:</strong> 1.0</p>"""
        )
        aboutText.setWordWrap(True)
        aboutText.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        aboutText.setStyleSheet("font-size: 13px; color: #444; line-height: 1.3;")
        aboutText.setOpenExternalLinks(True)
        aboutText.setTextFormat(Qt.RichText)

        developerLabel = QLabel("Built with 💻 by <a href='https://github.com/sidinsearch'>sidinsearch</a>")
        developerLabel.setStyleSheet("font-size: 13px; color: #666;")
        developerLabel.setAlignment(Qt.AlignCenter)
        developerLabel.setOpenExternalLinks(True)

        aboutLayout.addWidget(titleLabel)
        aboutLayout.addWidget(aboutText)
        aboutLayout.addStretch(1)
        aboutLayout.addWidget(developerLabel)
        pass

    def clearAll(self):
        self.filePathLineEdit.clear()
        self.download_link = ""
        self.showInitialScreen()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.filePathLineEdit.setText(files[0])

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def browseFile(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if filePath:
            self.filePathLineEdit.setText(filePath)

    def uploadFile(self):
        self.file_path = self.filePathLineEdit.text()
        if self.file_path:
            fileInfo = QFileInfo(self.file_path)
            fileSize = fileInfo.size()
            if fileSize <= MAX_FILE_SIZE:
                self.showLoadingScreen()
                self.uploadThread = UploadThread(self.file_path)
                self.uploadThread.uploadFinished.connect(self.onUploadFinished)
                self.uploadThread.start()
            else:
                QMessageBox.warning(self, "Warning", "Selected file is above 20MB. Please select a smaller file.")
        else:
            QMessageBox.information(self, "Info", "Please Select File To Share.")

    def showLoadingScreen(self):
        for widget in self.TransferXTab.findChildren(QWidget):
            widget.hide()
        self.loadingLabel.show()
        self.quoteLabel.show()
        self.loadingMovie.start()
        self.showRandomQuote()

    def onUploadFinished(self, share_id, download_link):
        self.loadingMovie.stop()
        self.loadingLabel.hide()
        self.quoteLabel.hide()
        if share_id and download_link:
            self.share_id = share_id
            self.download_link = download_link
            self.showQRCodeScreen(download_link)
            self.startFileTransferThread()
        else:
            QMessageBox.critical(self, "Error", "File upload failed. Check your internet connection or try again.")
            self.showInitialScreen()

    def showQRCodeScreen(self, download_link):
        self.generateQRCode(download_link)
        self.label.show()
        self.filePathLineEdit.show()
        self.browseButton.show()
        self.uploadButton.show()
        self.clearButton.show()
        self.scanMeLabel.show()
        self.qrCodeLabel.show()
        self.clickInfoLabel.show()
        self.logoLabel.hide()
        self.fileSizeLimitLabel.hide()

    def showInitialScreen(self):
        self.label.show()
        self.filePathLineEdit.show()
        self.browseButton.show()
        self.uploadButton.show()
        self.clearButton.show()
        self.logoLabel.show()
        self.fileSizeLimitLabel.show()
        self.scanMeLabel.hide()
        self.qrCodeLabel.hide()
        self.clickInfoLabel.hide()

    def generateQRCode(self, download_link):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(download_link)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save('qrcode.png')
        qrCodeImage = QImage('qrcode.png')
        fixedSize = QSize(150, 150)
        qrCodeImage = qrCodeImage.scaled(fixedSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.qrCodeLabel.setPixmap(QPixmap.fromImage(qrCodeImage))
        self.qrCodeLabel.setFixedSize(fixedSize)

    def copyLinkToClipboard(self, event):
        if event.button() == Qt.LeftButton and self.download_link:
            pyperclip.copy(self.download_link)
            QMessageBox.information(self, "Link Copied", "Download link has been copied to clipboard!")

    def showRandomQuote(self):
        quotes = [
            "Sharing is caring in the digital world too.",
            "Your files, your rules. Share responsibly.",
            "In the age of information, privacy is power.",
            "Encrypt your world, one file at a time.",
            "Share with care, protect with passion.",
            "The internet remembers. Share wisely.",
            "Digital footprints last longer than you think.",
            "Convenience is good, but security is better.",
            "Your data is your digital DNA. Guard it well.",
            "In a world of open networks, be a firewall."
        ]
        self.quoteLabel.setText(random.choice(quotes))

# ... [Previous TransferX class code remains the same]

    def startFileTransferThread(self):
        self.fileTransferThread = FileTransferThread(self.share_id, self.file_path)
        self.fileTransferThread.start()

class UploadThread(QThread):
    uploadFinished = pyqtSignal(str, str)

    def __init__(self, filePath):
        super().__init__()
        self.filePath = filePath

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            share_id, download_link = loop.run_until_complete(self.announce_file())
            self.uploadFinished.emit(share_id, download_link)
        except Exception as e:
            print(f"Error uploading file: {e}")
            self.uploadFinished.emit("", "")

    async def announce_file(self):
        file_name = os.path.basename(self.filePath)
        file_size = os.path.getsize(self.filePath)
        
        metadata = {
            "fileName": file_name,
            "fileSize": file_size
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{NETLIFY_SITE}/create-share", json={"metadata": metadata}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["shareId"], data["link"]
        return None, None

class FileTransferThread(QThread):
    def __init__(self, share_id, file_path):
        super().__init__()
        self.share_id = share_id
        self.file_path = file_path

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.handle_connections())

    async def handle_connections(self):
        while True:
            await self.handle_new_connection()

    async def handle_new_connection(self):
        pc = await self.create_peer_connection()
        dc = pc.createDataChannel('file_transfer')
        offer = await self.create_offer(pc)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{NETLIFY_SITE}/add-offer/{self.share_id}", json={"offer": {"sdp": offer.sdp, "type": offer.type}}) as response:
                data = await response.json()
                connection_id = data["connectionId"]
        
        # Wait for answer
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{NETLIFY_SITE}/get-answer/{self.share_id}/{connection_id}") as response:
                    if response.status == 200:
                        answer = await response.json()
                        await self.set_remote_description(pc, answer['answer'])
                        break
                    await asyncio.sleep(1)
        
        print(f"New connection established. Connection ID: {connection_id}")
        await self.send_file(dc)
        
        # Remove connection after file transfer
        async with aiohttp.ClientSession() as session:
            await session.post(f"{NETLIFY_SITE}/remove-connection/{self.share_id}/{connection_id}")

    async def create_peer_connection(self):
        return RTCPeerConnection()

    async def create_offer(self, pc):
        await pc.setLocalDescription(await pc.createOffer())
        return pc.localDescription

    async def set_remote_description(self, pc, answer):
        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer['sdp'], type=answer['type']))

    async def send_file(self, dc):
        print("Waiting for data channel to open...")
        while dc.readyState != "open":
            await asyncio.sleep(0.1)
        print("Data channel opened.")

        with open(self.file_path, "rb") as file:
            while True:
                data = file.read(16384)
                if not data:
                    break
                dc.send(data)
                await asyncio.sleep(0.01)  # Small delay to prevent flooding
        
        dc.send("EOF")
        print("File transfer completed")

if __name__ == '__main__':
    myappid = 'com.transferx.app.1.0'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    ex = TransferX()
    ex.show()
    sys.exit(app.exec_())