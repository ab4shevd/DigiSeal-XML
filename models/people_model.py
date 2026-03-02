from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex
import json
import os

class PeopleModel(QAbstractListModel):
    def __init__(self, config_path=None):
        super().__init__()
        self.people = []  # список словарей [{'name': '...', 'thumbprint': '...'}]

        if config_path is None:
            app_data = os.path.join(os.path.expanduser("~"), ".digiseal")
            os.makedirs(app_data, exist_ok=True)
            self.config_path = os.path.join(app_data, "people.json")
        else:
            self.config_path = config_path

        self.load()

    def rowCount(self, parent=QModelIndex()):
        return len(self.people)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.people):
            return None

        person = self.people[index.row()]

        if role == Qt.DisplayRole:
            return person['name']
        elif role == Qt.UserRole:
            return person['thumbprint']

        return None

    def add_person(self, name, thumbprint):
        self.beginInsertRows(QModelIndex(), len(self.people), len(self.people))
        self.people.append({'name': name, 'thumbprint': thumbprint})
        self.endInsertRows()
        self.save()

    def remove_person(self, index):
        if 0 <= index < len(self.people):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.people[index]
            self.endRemoveRows()
            self.save()

    def get_thumbprint(self, index):
        """Получить отпечаток сертификата по индексу"""
        if 0 <= index < len(self.people):
            return self.people[index]['thumbprint']
        return None

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.people, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.people = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")