from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QPushButton, QLabel, QSplitter,
                             QFileDialog, QMessageBox, QStatusBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DigiSeal-XML - Подпись XML файлов")
        self.setMinimumSize(900, 600)

        # Центральный виджет и основной layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Верхняя панель с заголовком (опционально)
        title_label = QLabel("🔏 DigiSeal-XML")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Основная область: сплиттер для двух списков
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)  # растягивается

        # Левая панель - список файлов
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.setContentsMargins(0, 0, 0, 0)

        files_label = QLabel("📄 Файлы для подписи")
        files_label.setObjectName("SectionLabel")
        files_layout.addWidget(files_label)

        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.ExtendedSelection)
        files_layout.addWidget(self.files_list)

        # Кнопки для файлов
        files_buttons_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("➕ Добавить файлы")
        self.clear_files_btn = QPushButton("🗑 Очистить список")
        files_buttons_layout.addWidget(self.add_files_btn)
        files_buttons_layout.addWidget(self.clear_files_btn)
        files_layout.addLayout(files_buttons_layout)

        splitter.addWidget(files_widget)

        # Правая панель - список подписантов
        people_widget = QWidget()
        people_layout = QVBoxLayout(people_widget)
        people_layout.setContentsMargins(0, 0, 0, 0)

        people_label = QLabel("👤 Сотрудники")
        people_label.setObjectName("SectionLabel")
        people_layout.addWidget(people_label)

        self.people_list = QListWidget()
        self.people_list.setSelectionMode(QListWidget.SingleSelection)
        people_layout.addWidget(self.people_list)

        # Кнопки для подписантов
        people_buttons_layout = QHBoxLayout()
        self.manage_people_btn = QPushButton("⚙️ Управление")
        people_buttons_layout.addWidget(self.manage_people_btn)
        # Можно добавить кнопку удаления, но пока оставим управление через диалог
        people_layout.addLayout(people_buttons_layout)

        splitter.addWidget(people_widget)

        # Устанавливаем пропорции (левая панель шире)
        splitter.setSizes([500, 300])

        # Нижняя панель с кнопкой подписать и статусом
        bottom_layout = QHBoxLayout()

        self.sign_btn = QPushButton("✍️ Подписать выбранные")
        self.sign_btn.setObjectName("SignButton")
        self.sign_btn.setEnabled(False)  # будет активироваться, когда есть файлы и подписант

        bottom_layout.addStretch()
        bottom_layout.addWidget(self.sign_btn)
        bottom_layout.addStretch()

        main_layout.addLayout(bottom_layout)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        # Подключение сигналов (пока заглушки)
        self.add_files_btn.clicked.connect(self.on_add_files)
        self.clear_files_btn.clicked.connect(self.on_clear_files)
        self.manage_people_btn.clicked.connect(self.on_manage_people)
        self.files_list.itemSelectionChanged.connect(self.update_sign_button)
        self.people_list.itemSelectionChanged.connect(self.update_sign_button)

    # Слоты (временно просто выводят сообщение)
    def on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите XML файлы", "", "XML файлы (*.xml);;Все файлы (*.*)"
        )
        if files:
            self.files_list.addItems(files)
            self.status_bar.showMessage(f"Добавлено {len(files)} файлов")
            self.update_sign_button()

    def on_clear_files(self):
        self.files_list.clear()
        self.status_bar.showMessage("Список файлов очищен")
        self.update_sign_button()

    def on_manage_people(self):
        # Позже откроем диалог управления
        QMessageBox.information(self, "Управление", "Здесь будет диалог управления подписантами")

    def update_sign_button(self):
        # Активируем кнопку подписи, если есть хотя бы один файл и выбран подписант
        files_selected = len(self.files_list.selectedItems()) > 0
        person_selected = len(self.people_list.selectedItems()) > 0
        self.sign_btn.setEnabled(files_selected and person_selected)