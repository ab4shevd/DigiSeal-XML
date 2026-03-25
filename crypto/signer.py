import win32com.client
import pythoncom
import traceback
import os
from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import logger


class CryptoSigner(QObject):
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        logger.debug("Инициализация CryptoSigner")
        self._initialize_com()
        self._init_objects()

    def _initialize_com(self):
        try:
            pythoncom.CoInitialize()
            logger.debug("COM инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации COM: {e}")

    def _init_objects(self):
        try:
            self.store = win32com.client.Dispatch("CAdESCOM.Store")
            self.hashed_data = win32com.client.Dispatch("CAdESCOM.HashedData")
            self.signer = win32com.client.Dispatch("CAdESCOM.CPSigner")
            logger.debug("COM-объекты успешно созданы")
        except Exception as e:
            logger.error(f"Ошибка создания COM-объектов: {e}")
            raise

    def get_certificates(self):
        logger.debug("Запрос списка сертификатов")
        try:
            self.store.Open()
            certs = self.store.Certificates
            result = []
            for i in range(1, certs.Count + 1):
                try:
                    cert = certs.Item(i)
                    cert_info = {
                        'thumbprint': cert.Thumbprint,
                        'subject': cert.GetInfo(1),
                        'issuer': cert.GetInfo(2),
                        'valid_from': str(cert.ValidFromDate),
                        'valid_to': str(cert.ValidToDate),
                        'has_private_key': cert.HasPrivateKey()
                    }
                    result.append(cert_info)
                except Exception as e:
                    logger.error(f"Ошибка обработки сертификата {i}: {e}")
            self.store.Close()
            return result
        except Exception as e:
            logger.error(f"Ошибка получения сертификатов: {e}")
            return []

    def load_cert_from_pfx(self, pfx_path, password):
        """Загрузить сертификат из PFX-файла и вернуть COM-объект Certificate."""
        try:
            if not os.path.exists(pfx_path):
                raise Exception(f"Файл не найден: {pfx_path}")
            store = win32com.client.Dispatch("CAdESCOM.Store")
            # CAPICOM_MEMORY_STORE = 2
            store.Open(2, pfx_path, 0, password)
            if store.Certificates.Count == 0:
                raise Exception("PFX не содержит сертификатов")
            cert = store.Certificates.Item(1)
            store.Close()
            logger.info(f"Сертификат загружен: {cert.GetInfo(1)}")
            return cert
        except Exception as e:
            logger.error(f"Ошибка загрузки сертификата из PFX: {e}")
            raise

    def sign_xml(self, xml_path, cert_thumbprint=None, cert_obj=None, output_path=None):
        """
        Подписать XML-файл (создать CMS-подпись в отдельном файле)
        """
        logger.info(f"Начало подписи файла: {xml_path}")

        try:
            self.progress_updated.emit(10, "Загрузка сертификата...")

            # ----- Получение сертификата -----
            if cert_obj is None and cert_thumbprint is not None:
                self.store.Open()
                found_cert = None
                for i in range(1, self.store.Certificates.Count + 1):
                    cert = self.store.Certificates.Item(i)
                    if cert.Thumbprint == cert_thumbprint:
                        found_cert = cert
                        break
                if not found_cert:
                    raise Exception("Сертификат не найден в хранилище")
                cert_obj = found_cert
            elif cert_obj is None:
                raise Exception("Не указан сертификат для подписи")

            # Проверка наличия закрытого ключа
            if not cert_obj.HasPrivateKey():
                logger.warning("Сертификат не имеет закрытого ключа! Подпись невозможна.")
                raise Exception("У сертификата отсутствует закрытый ключ. Проверьте установку PFX.")

            self.progress_updated.emit(30, "Чтение файла...")

            if not os.path.exists(xml_path):
                raise Exception(f"Файл не найден: {xml_path}")

            with open(xml_path, 'rb') as f:
                content_bytes = f.read()
            if not content_bytes:
                raise Exception("Файл пуст")

            self.progress_updated.emit(50, "Подписание документа...")
            content_str = content_bytes.decode('utf-8')

            signed_data = win32com.client.Dispatch("CAdESCOM.CadesSignedData")
            signed_data.Content = content_str

            # Настройка подписчика
            signer = win32com.client.Dispatch("CAdESCOM.CPSigner")
            signer.Certificate = cert_obj
            signer.CheckCertificate = False
            signer.Options = 0
            signer.TSAAddress = ""  # отключаем TSA

            # ----- Создание подписи -----
            import base64

            if hasattr(signed_data, 'SignCades'):
                # CADESCOM_CADES_BES = 1, отделённая подпись, EncodingType = 0 (бинарные)
                signature_bin = signed_data.SignCades(signer, 1, True, 0)
                # Если результат — строка (BSTR), преобразуем в байты, используя latin-1
                if isinstance(signature_bin, str):
                    signature_bytes = signature_bin.encode('latin-1')
                else:
                    signature_bytes = signature_bin
                # Кодируем в Base64 и получаем строку ASCII
                signature = base64.b64encode(signature_bytes).decode('ascii')
                logger.debug("Подпись создана через SignCades (CADES_BES) и закодирована в Base64")
            else:
                # Старый метод Sign – ожидаем строку Base64 (EncodingType=1)
                signature = signed_data.Sign(signer, True, 1)
                # На всякий случай проверяем, что это ASCII
                if not signature.isascii():
                    # Если нет – пробуем преобразовать
                    try:
                        signature_bytes = signature.encode('latin-1')
                        signature = base64.b64encode(signature_bytes).decode('ascii')
                        logger.debug("Подпись из Sign перекодирована в Base64")
                    except Exception as e:
                        logger.warning(f"Не удалось перекодировать подпись: {e}")
                logger.debug("Подпись создана через Sign (старый метод)")

            self.progress_updated.emit(90, "Сохранение подписи...")

            if output_path is None:
                output_path = xml_path + ".sig"

            # Записываем подпись в бинарном режиме, используя ASCII (Base64)
            with open(output_path, 'wb') as f:
                f.write(signature.encode('ascii'))

            if cert_thumbprint is not None:
                self.store.Close()

            self.progress_updated.emit(100, "Готово!")
            self.operation_completed.emit(True, f"Подпись сохранена: {output_path}")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка подписи: {error_msg}")
            logger.error(traceback.format_exc())
            self.operation_completed.emit(False, f"Ошибка: {error_msg}")
            return False