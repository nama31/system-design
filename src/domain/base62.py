class Base62Encoder:
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    BASE = len(ALPHABET)

    @classmethod
    def encode(cls, number: int) -> str:
        if number < 0:
            raise ValueError("Cannot encode a negative number")
        if number == 0:
            return cls.ALPHABET[0]

        encoded = []
        while number > 0:
            number, remainder = divmod(number, cls.BASE)
            encoded.append(cls.ALPHABET[remainder])

        return "".join(reversed(encoded))

    @classmethod
    def decode(cls, short_code: str) -> int:
        if not short_code:
            raise ValueError("Short code cannot be empty")

        number = 0
        for char in short_code:
            index = cls.ALPHABET.find(char)
            if index == -1:
                raise ValueError("Short code contains invalid Base62 characters")
            number = number * cls.BASE + index

        return number
