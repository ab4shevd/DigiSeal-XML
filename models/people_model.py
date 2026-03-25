from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex
import json
import os


class PeopleModel(QAbstractListModel):
    def __init__(self, config_path=None):
        super().__init__()
        self.people = []  # каждый элемент: {'name': str, 'thumbprint': str, 'type': str, 'pfx_path': str, 'pfx_password': str}

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

    def add_person(self, name, thumbprint, cert_type='store', pfx_path='', pfx_password=''):
        self.beginInsertRows(QModelIndex(), len(self.people), len(self.people))
        self.people.append({
            'name': name,
            'thumbprint': thumbprint,
            'type': cert_type,
            'pfx_path': pfx_path,
            'pfx_password': pfx_password
        })
        self.endInsertRows()
        self.save()

    def remove_person(self, index):
        if 0 <= index < len(self.people):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.people[index]
            self.endRemoveRows()
            self.save()

    def get_signer_data(self, index):
        """
        Возвращает (thumbprint, cert_object) для использования в подписи.
        Для сертификата из хранилища: (thumbprint, None)
        Для сертификата из PFX: (None, cert_object)
        """
        person = self.people[index]
        if person['type'] == 'store':
            return person['thumbprint'], None
        else:
            # Загружаем сертификат из PFX
            from crypto.signer import CryptoSigner
            signer = CryptoSigner()
            cert_obj = signer.load_cert_from_pfx(person['pfx_path'], person['pfx_password'])
            return None, cert_obj

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