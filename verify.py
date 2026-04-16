import win32com.client
import sys

def verify_signature(xml_path, sig_path):
    signed_data = win32com.client.Dispatch("CAdESCOM.CadesSignedData")
    with open(xml_path, 'rb') as f:
        content = f.read().decode('utf-8')
    signed_data.Content = content
    with open(sig_path, 'r', encoding='utf-8') as f:
        signature = f.read()
    try:
        signed_data.Verify(signature, True)  # True = отделённая подпись
        print("✅ Подпись верна")
        return True
    except Exception as e:
        print(f"❌ Подпись неверна: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) == 3:
        verify_signature(sys.argv[1], sys.argv[2])
    else:
        verify_signature("C:/Users/TBG/Desktop/test.xml", "C:/Users/TBG/Desktop/test.xml.sig")