import lgpio

class GPIO_Device:
    def __init__(self, board, pin):
        self._pin = pin
        self._board = board

    def get_pin(self):
        return self._pin
    
    def get_board(self):
        return self._board
    
    