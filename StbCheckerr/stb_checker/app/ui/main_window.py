import asyncio
from datetime import datetime

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QSplitter, QListWidget,
                               QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QListWidgetItem)
from PySide6.QtCore import Qt, QSize
from qasync import asyncSlot

from app.network.mock_provider import MockSubscriptionProvider
from app.player.vlc_player import VLCPlayerWidget
from app.storage.history import HistoryManager
from app.models import UserStatus

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STB/Portal Checker (Manual)")
        self.resize(1000, 700)
        
        # Iniciar proveedor y gestor de historial
        self.provider = MockSubscriptionProvider()
        self.history_manager = HistoryManager()
        
        self.init_ui()
        self.load_history()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 1. Top Bar (Portal, MAC, Buttons)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Portal:"))
        self.portal_input = QLineEdit("http://mi-servidor.example/c/")
        top_layout.addWidget(self.portal_input)
        
        top_layout.addWidget(QLabel("MAC:"))
        self.mac_input = QLineEdit("00:1A:79:D5:5B:01")
        top_layout.addWidget(self.mac_input)
        
        self.btn_connect = QPushButton("CONECTAR / CARGAR")
        self.btn_connect.clicked.connect(self.on_connect)
        top_layout.addWidget(self.btn_connect)
        
        self.btn_disconnect = QPushButton("DESCONECTAR")
        self.btn_disconnect.clicked.connect(self.on_disconnect)
        top_layout.addWidget(self.btn_disconnect)
        
        layout.addLayout(top_layout)
        
        # 2. Status Area
        self.lbl_status = QLabel("Estado: ⚪ ESPERANDO")
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lbl_status)
        
        # 3. Main Splitter (Left: content/history, Right: Player)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left Panel (History + Content)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["Portal", "MAC", "Estado"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.itemDoubleClicked.connect(self.on_history_double_clicked)
        left_layout.addWidget(QLabel("Historial Reciente (Doble clic para rellenar):"))
        left_layout.addWidget(self.history_table)
        
        self.categories_list = QListWidget()
        self.categories_list.itemClicked.connect(self.on_category_clicked)
        left_layout.addWidget(QLabel("Categorías:"))
        left_layout.addWidget(self.categories_list)
        
        self.content_list = QListWidget()
        self.content_list.itemClicked.connect(self.on_content_clicked)
        left_layout.addWidget(QLabel("Contenido:"))
        left_layout.addWidget(self.content_list)
        
        splitter.addWidget(left_panel)
        
        # Right Panel (Player)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.player = VLCPlayerWidget()
        self.player.setMinimumSize(QSize(640, 480))
        right_layout.addWidget(self.player)
        
        # Player Controls
        controls_layout = QHBoxLayout()
        btn_play = QPushButton("▶ Play")
        btn_play.clicked.connect(lambda: self.player.media_player.play())
        btn_pause = QPushButton("⏸ Pausa")
        btn_pause.clicked.connect(self.player.pause)
        btn_stop = QPushButton("⏹ Stop")
        btn_stop.clicked.connect(self.player.stop)
        
        controls_layout.addWidget(btn_play)
        controls_layout.addWidget(btn_pause)
        controls_layout.addWidget(btn_stop)
        controls_layout.addStretch()
        right_layout.addLayout(controls_layout)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])
        
        # 4. Logs
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(100)
        self.log_output.setReadOnly(True)
        layout.addWidget(QLabel("Logs:"))
        layout.addWidget(self.log_output)

    def log(self, message: str):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{time_str}] {message}")
        # Auto-scroll
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    @asyncSlot()
    async def on_connect(self):
        portal = self.portal_input.text().strip()
        mac = self.mac_input.text().strip()
        
        if not portal or not mac:
            QMessageBox.warning(self, "Error", "Portal y MAC son obligatorios.")
            return

        self.btn_connect.setEnabled(False)
        self.player.stop()
        
        # Limpiar sesión/UI anterior antes de la nueva conexión
        await self.provider.disconnect()
        self.categories_list.clear()
        self.content_list.clear()
        
        self.log(f"Conectando a {portal} con MAC {mac}...")
        self.lbl_status.setText("Estado: ⏳ CONECTANDO...")
        self.lbl_status.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        
        try:
            status: UserStatus = await self.provider.connect(portal, mac)
            
            if status.is_valid:
                exp_text = f" | Expiración: {status.expiration_date}" if status.expiration_date else ""
                self.lbl_status.setText(f"Estado: 🟢 CONECTADO{exp_text}")
                self.lbl_status.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
                self.log("Usuario autorizado. Cargando categorías...")
                self.history_manager.add_entry(portal, mac, "🟢")
                await self.load_categories()
            else:
                self.history_manager.add_entry(portal, mac, "🔴")
                if status.status_code == "BLOCKED":
                    self.lbl_status.setText(f"Estado: 🔴 STB BLOQUEADO\nMensaje del servidor: {status.message}")
                    self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
                    self.log(f"STB Bloqueado: {status.message}")
                elif status.status_code == "EXPIRED":
                    self.lbl_status.setText(f"Estado: 🟠 SUSCRIPCIÓN CADUCADA\nMensaje: {status.message}")
                    self.lbl_status.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
                    self.log("Suscripción caducada.")
                elif status.status_code == "ERROR":
                    self.lbl_status.setText(f"Estado: ⚠️ TIMEOUT / ERROR DE CONEXIÓN")
                    self.lbl_status.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
                    self.log(f"Error de red: {status.message}")
                else:
                    self.lbl_status.setText(f"Estado: ⚪ {status.message}")
                    self.lbl_status.setStyleSheet("color: gray; font-weight: bold; font-size: 14px;")
                    self.log(f"Error de acceso: {status.message}")
                    
        except Exception as e:
            self.lbl_status.setText(f"Estado: ⚠️ ERROR DE CONEXIÓN")
            self.lbl_status.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
            self.log(f"Excepción: {str(e)}")
        finally:
            self.btn_connect.setEnabled(True)
            self.load_history()

    @asyncSlot()
    async def on_disconnect(self):
        self.log("Desconectando y limpiando datos de sesión...")
        await self.provider.disconnect()
        self.player.stop()
        self.categories_list.clear()
        self.content_list.clear()
        self.lbl_status.setText("Estado: ⚪ DESCONECTADO")
        self.lbl_status.setStyleSheet("color: black; font-weight: bold; font-size: 14px;")

    @asyncSlot()
    async def load_categories(self):
        categories = await self.provider.get_categories()
        self.categories_list.clear()
        for cat in categories:
            self.categories_list.addItem(cat)
        self.log(f"Se cargaron {len(categories)} categorías de forma segura.")

    @asyncSlot()
    async def on_category_clicked(self, item):
        category = item.text()
        self.log(f"Cargando contenido para la categoría: {category}...")
        self.content_list.clear()
        
        contents = await self.provider.get_content(category)
        
        for content in contents:
            list_item = QListWidgetItem(content.name)
            list_item.setData(Qt.UserRole, content.id)
            self.content_list.addItem(list_item)
            
        self.log(f"Se cargaron {len(contents)} elementos en la categoría {category}.")

    @asyncSlot()
    async def on_content_clicked(self, item):
        content_id = item.data(Qt.UserRole)
        self.log(f"Obteniendo recurso de reproducción legítimo para: {content_id}...")
        try:
            url = await self.provider.get_playback_resource(content_id)
            self.log(f"Iniciando reproducción en VLC...")
            self.player.play_url(url)
        except Exception as e:
            self.log(f"Error al cargar stream: {e}")

    def load_history(self):
        self.history_table.setRowCount(0)
        history = self.history_manager.get_history()
        for i, (portal, mac, status) in enumerate(history):
            self.history_table.insertRow(i)
            self.history_table.setItem(i, 0, QTableWidgetItem(portal))
            self.history_table.setItem(i, 1, QTableWidgetItem(mac))
            
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(i, 2, status_item)

    def on_history_double_clicked(self, item):
        row = item.row()
        portal = self.history_table.item(row, 0).text()
        mac = self.history_table.item(row, 1).text()
        self.portal_input.setText(portal)
        self.mac_input.setText(mac)
        self.log(f"Autocompletado desde el historial: {mac} (Pulsa CONECTAR manualmente)")
