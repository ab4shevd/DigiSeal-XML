from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QPushButton, QLabel, QLineEdit,
                             QMessageBox, QDialogButtonBox, QAbstractItemView)
from PyQt5.QtCore import Qt

from crypto.signer import CryptoSigner


class PeopleDialog(QDialog):
    def __init__(self, people_model, parent=None):
        super().__init__(parent)
        self.people_model = people_model
        self.signer = CryptoSigner()
        self.setWindowTitle("Управление подписантами")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Список сертификатов из системы
        layout.addWidget(QLabel("📜 Доступные сертификаты (из КриптоПро):"))
        self.cert_list = QListWidget()
        self.cert_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.cert_list)

        # Кнопка обновить список сертификатов
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self.load_certificates)
        layout.addWidget(refresh_btn)

        # Поле для ввода имени
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Имя подписанта:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите отображаемое имя")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Кнопка добавить
        add_btn = QPushButton("➕ Добавить в список подписантов")
        add_btn.clicked.connect(self.add_person)
        layout.addWidget(add_btn)

        # Разделитель
        layout.addWidget(QLabel("📋 Текущие подписанты:"))

        # Список уже добавленных подписантов
        self.current_list = QListWidget()
        self.current_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.current_list)

        # Кнопка удалить выбранного
        remove_btn = QPushButton("❌ Удалить выбранного")
        remove_btn.clicked.connect(self.remove_person)
        layout.addWidget(remove_btn)

        # Кнопки OK/Отмена
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Загружаем данные
        self.load_certificates()
        self.refresh_current_list()

    def load_certificates(self):
        """Загрузить список сертификатов из КриптоПро"""
        self.cert_list.clear()
        certs = self.signer.get_certificates()
        for cert in certs:
            # Формируем строку с информацией о сертификате
            text = f"{cert['subject']}\n  Отпечаток: {cert['thumbprint']}\n  Действителен до: {cert['valid_to']}"
            if not cert['has_private_key']:
                text += "\n  ⚠️ Нет закрытого ключа (не подойдёт для подписи)"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, cert['thumbprint'])
            item.setData(Qt.UserRole + 1, cert['has_private_key'])
            self.cert_list.addItem(item)

    def refresh_current_list(self):
        """Обновить список подписантов из модели"""
        self.current_list.clear()
        for i in range(self.people_model.rowCount()):
            idx = self.people_model.index(i)
            name = self.people_model.data(idx, Qt.DisplayRole)
            thumbprint = self.people_model.data(idx, Qt.UserRole)
            item = QListWidgetItem(f"{name} [{thumbprint[:8]}...]")
            item.setData(Qt.UserRole, i)  # сохраняем индекс в модели
            self.current_list.addItem(item)

    def add_person(self):
        """Добавить выбранный сертификат как подписанта"""
        current = self.cert_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Предупреждение", "Выберите сертификат из списка")
            return

        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Предупреждение", "Введите имя подписанта")
            return

        thumbprint = current.data(Qt.UserRole)
        has_private_key = current.data(Qt.UserRole + 1)
        if not has_private_key:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "У выбранного сертификата нет закрытого ключа. Подпись таким сертификатом невозможна. Всё равно добавить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Добавляем в модель
        self.people_model.add_person(name, thumbprint)
        self.refresh_current_list()
        self.name_edit.clear()

    def remove_person(self):
        """Удалить выбранного подписанта из модели"""
        current = self.current_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Предупреждение", "Выберите подписанта для удаления")
            return

        index_in_model = current.data(Qt.UserRole)
        self.people_model.remove_person(index_in_model)
        self.refresh_current_list()