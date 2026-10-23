from pymodbus.client import ModbusRtuClient

def test_modbus():
    # RTU კლიენტის კონფიგურაცია
    client = ModbusRtuClient(
        port="/dev/ttyUSB0",   # შეცვალე შენი პორტით (Windows-ზე COM3)
        baudrate=19200,
        timeout=2
    )

    if client.connect():
        print("✅ კავშირი დამყარდა")

        # რეგისტრების კითხვა (Holding Registers)
        result = client.read_holding_registers(address=0, count=4, unit=1)

        if not result.isError():
            print("📊 მიღებული მონაცემები:", result.registers)
        else:
            print("❌ შეცდომა:", result)

        client.close()
    else:
        print("❌ ვერ მოხერხდა კავშირის დამყარება")