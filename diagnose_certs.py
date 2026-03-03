import sys
import win32com.client
import pythoncom


def diagnose_certificates():
    print("=" * 60)
    print("ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К КРИПТОПРО")
    print("=" * 60)

    # Проверка разрядности Python
    print(f"\n🐍 Python: {sys.version}")
    print(f"Разрядность: {'64-bit' if sys.maxsize > 2 ** 32 else '32-bit'}")

    try:
        # Инициализация COM
        pythoncom.CoInitialize()
        print("\n✅ COM инициализирован")

        # Пробуем разные варианты открытия хранилища
        print("\n📦 Пробуем открыть хранилища:")

        # Вариант 1: Простое открытие
        try:
            store = win32com.client.Dispatch("CAdESCOM.Store")
            store.Open()  # Без параметров
            certs = store.Certificates
            print(f"  Вариант 1 (Open без параметров): {certs.Count} сертификатов")
            store.Close()
        except Exception as e:
            print(f"  Вариант 1 ошибка: {e}")

        # Вариант 2: Явное указание хранилища (CURRENT_USER, MY)
        try:
            store = win32com.client.Dispatch("CAdESCOM.Store")
            store.Open(1, 0)  # CAPICOM_CURRENT_USER_STORE, CAPICOM_MY_STORE
            certs = store.Certificates
            print(f"  Вариант 2 (Open(1,0)): {certs.Count} сертификатов")

            # Если есть сертификаты, покажем их
            if certs.Count > 0:
                print("\n📜 Найденные сертификаты:")
                for i in range(1, min(certs.Count, 5) + 1):  # Первые 5
                    cert = certs.Item(i)
                    print(f"\n  {i}. {cert.GetInfo(1)}")  # Простое имя
                    print(f"     Отпечаток: {cert.Thumbprint}")
                    print(f"     Закрытый ключ: {'✅ есть' if cert.HasPrivateKey() else '❌ нет'}")
                    print(f"     Действителен до: {cert.ValidToDate}")
            store.Close()
        except Exception as e:
            print(f"  Вариант 2 ошибка: {e}")

        # Вариант 3: С флагами максимального доступа
        try:
            store = win32com.client.Dispatch("CAdESCOM.Store")
            # CAPICOM_CURRENT_USER_STORE, CAPICOM_MY_STORE, CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED
            store.Open(1, 0, 2)
            certs = store.Certificates
            print(f"  Вариант 3 (Open с флагами): {certs.Count} сертификатов")
            store.Close()
        except Exception as e:
            print(f"  Вариант 3 ошибка: {e}")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

    print("\n" + "=" * 60)
    print("\n💡 Рекомендации:")
    print("1. Если ни один вариант не нашёл сертификаты, проверь разрядность Python")
    print("2. Если сертификаты нашлись в одном варианте, но не в другом — нужно исправить параметры Open в коде")
    print("3. Если сертификаты есть, но у них нет закрытого ключа — они не подойдут для подписи")


if __name__ == "__main__":
    diagnose_certificates()