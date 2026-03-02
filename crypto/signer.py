import win32com.client
import pythoncom
from PyQt5.QtCore import QObject, pyqtSignal

class CryptoSigner(QObject):
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self._initialize_com()

    def _initialize_com(self):
        pythoncom.CoInitialize()

    def get_certificates(self):
        try:
            store = win32com.client.Dispatch("CAdESCOM.Store")
            store.Open(1, 0)  # CAPICOM_CURRENT_USER_STORE

            certs = store.Certificates
            result = []

            for i in range(1, certs.Count + 1):
                cert = certs.Item(i)
                cert_info = {
                    'thumbprint': cert.Thumbprint,
                    'subject': cert.GetInfo(1),  # CAPICOM_CERT_INFO_SUBJECT_SIMPLE_NAME
                    'issuer': cert.GetInfo(2),   # CAPICOM_CERT_INFO_ISSUER_SIMPLE_NAME
                    'valid_from': cert.ValidFromDate,
                    'valid_to': cert.ValidToDate,
                    'has_private_key': cert.HasPrivateKey()
                }
                result.append(cert_info)

            store.Close()
            return result

        except Exception as e:
            print(f"Ошибка получения сертификатов: {e}")
            return []

    def sign_xml(self, xml_path, cert_thumbprint, output_path=None):
        try:
            self.progress_updated.emit(10, "Инициализация...")

            store = win32com.client.Dispatch("CAdESCOM.Store")
            store.Open(1, 0)

            certs = store.Certificates.Find(8, cert_thumbprint)  # 8 = CAPICOM_CERTIFICATE_FIND_SHA1_HASH
            if certs.Count == 0:
                raise Exception("Сертификат не найден")

            cert = certs.Item(1)

            self.progress_updated.emit(30, "Сертификат загружен")

            signed_data = win32com.client.Dispatch("CAdESCOM.SignedData")

            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()

            signed_data.Content = content

            self.progress_updated.emit(60, "Вычисление подписи...")

            signer = win32com.client.Dispatch("CAdESCOM.Signer")
            signer.Certificate = cert

            signature = signed_data.Sign(signer, False, 0)  # 0 = CAPICOM_ENCODE_BASE64

            self.progress_updated.emit(90, "Сохранение...")

            if output_path is None:
                output_path = xml_path + ".sig"

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(signature)

            store.Close()

            self.progress_updated.emit(100, "Готово!")
            self.operation_completed.emit(True, f"Подпись сохранена: {output_path}")
            return True

        except Exception as e:
            self.operation_completed.emit(False, f"Ошибка: {str(e)}")
            return False

    def verify_signature(self, xml_path, signature_path):
        pass