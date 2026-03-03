import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QPushButton, QLabel, QSplitter,
                             QFileDialog, QMessageBox, QStatusBar, QListView)
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QIcon

from models.people_model import PeopleModel
from crypto.signer import CryptoSigner
from gui.people_dialog import PeopleDialog


class SignWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, file_paths, thumbprint):
        super().__init__()
        self.file_paths = file_paths
        self.thumbprint = thumbprint
        self.signer = CryptoSigner()
        self.signer.progress_updated.connect(self.progress)

    def run(self):
        try:
            for i, file_path in enumerate(self.file_paths):
                self.progress.emit(i * 100 // len(self.file_paths),
                                   f"Подпись файла {i+1} из {len(self.file_paths)}")
                success = self.signer.sign_xml(file_path, self.thumbprint)
                if not success:
                    self.finished.emit(False, f"Ошибка при подписи {file_path}")
                    return
            self.finished.emit(True, f"Успешно подписано {len(self.file_paths)} файлов")
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DigiSeal-XML - Подпись XML файлов")
        self.setMinimumSize(900, 600)

        # Центральный виджет и основной layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Верхняя панель с заголовком
        title_label = QLabel("🔏 DigiSeal-XML")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Основная область: сплиттер для двух списков
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

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

        people_label = QLabel("👤 Подписанты")
        people_label.setObjectName("SectionLabel")
        people_layout.addWidget(people_label)

        self.people_list = QListView()
        self.people_list.setSelectionMode(QListView.SingleSelection)
        self.people_model = PeopleModel()
        self.people_list.setModel(self.people_model)
        people_layout.addWidget(self.people_list)

        # Кнопки для подписантов
        people_buttons_layout = QHBoxLayout()
        self.manage_people_btn = QPushButton("⚙️ Управление")
        people_buttons_layout.addWidget(self.manage_people_btn)
        people_layout.addLayout(people_buttons_layout)

        splitter.addWidget(people_widget)

        # Устанавливаем пропорции (левая панель шире)
        splitter.setSizes([500, 300])

        # Нижняя панель с кнопкой подписать и статусом
        bottom_layout = QHBoxLayout()

        self.sign_btn = QPushButton("✍️ Подписать выбранные")
        self.sign_btn.setObjectName("SignButton")
        self.sign_btn.setEnabled(False)

        bottom_layout.addStretch()
        bottom_layout.addWidget(self.sign_btn)
        bottom_layout.addStretch()

        main_layout.addLayout(bottom_layout)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        # Подключение сигналов
        self.add_files_btn.clicked.connect(self.on_add_files)
        self.clear_files_btn.clicked.connect(self.on_clear_files)
        self.manage_people_btn.clicked.connect(self.on_manage_people)
        self.files_list.itemSelectionChanged.connect(self.update_sign_button)
        self.people_list.selectionModel().selectionChanged.connect(self.update_sign_button)
        self.sign_btn.clicked.connect(self.on_sign_clicked)

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
        dialog = PeopleDialog(self.people_model, self)
        dialog.exec_()

    def update_sign_button(self):
        files_selected = len(self.files_list.selectedItems()) > 0
        person_selected = len(self.people_list.selectionModel().selectedIndexes()) > 0
        self.sign_btn.setEnabled(files_selected and person_selected)

    def on_sign_clicked(self):
        selected_files = [item.text() for item in self.files_list.selectedItems()]
        if not selected_files:
            return

        indexes = self.people_list.selectionModel().selectedIndexes()
        if not indexes:
            return
        index = indexes[0]
        thumbprint = self.people_model.get_thumbprint(index.row())

        # Блокируем интерфейс
        self.sign_btn.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.manage_people_btn.setEnabled(False)

        # Создаём поток
        self.thread = QThread()
        self.worker = SignWorker(selected_files, thumbprint)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_sign_finished)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.status_bar.showMessage("Подписание...")

    def update_progress(self, percent, message):
        self.status_bar.showMessage(message)

    def on_sign_finished(self, success, message):
        # Разблокируем интерфейс
        self.sign_btn.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.manage_people_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.critical(self, "Ошибка", message)
        self.status_bar.showMessage(message)