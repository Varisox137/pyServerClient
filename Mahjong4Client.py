def handle_status(status: str):
    if status:
        print('Status:\n'+status)
        return input('Decision ?=\n')
