import random
import string

class MarkovChain:
    def __init__(self, filename=None, memory=5):
        self.paraLen = 300
        self.lineLen = 62
        self.dict = {}
        self.memory = memory

        if not isinstance(memory, int) or memory < 1:
            raise Exception("Invalid memory size requested")

        # Read the input file and generate the Markov dartboard.
        prev = ""
        with open(filename, "r", encoding="utf-8") as f:
            skip = False
            while True:
                c = f.read(1)
                if not c:
                    break

                if c.isalnum():
                    skip = False
                elif c.isspace():
                    c = " "
                    skip = False
                elif skip:
                    continue
                elif c in string.punctuation:
                    skip = True
                else:
                    skip = True
                    c = " "

                if len(prev) == self.memory:
                    if prev in self.dict:
                        self.dict[prev] += c
                    else:
                        self.dict[prev] = c
                    prev = prev[1:]
                prev = prev + c

        # Make the "starters" dartboard. We look for things that
        # look like the starts of sentences, and we make a dartboard
        # out of it.
        self.starters = []
        if self.memory == 1:
            # Have to handle the 1 character memory option separately.
            for k, v in self.dict.items():
                if k.isalpha() and k == k.upper():
                    self.starters += [k] * len(v)
        else:
            # Multi-character memory allows more subtle checking.
            for k, v in self.dict.items():
                if k[0].isalpha() and k[0] == k[0].upper() and k[1].isalpha() and k[1] == k[1].lower():
                    self.starters += [k] * len(v)
                elif k[0] == "I" and k[1] in (" '"):
                    self.starters += [k] * len(v)
                elif k[0:1] == "A ":
                    self.starters += [k] * len(v)

    # The Python random number generator isn't thread-safe. This makes
    # things complicated in a Flask app, where we want to see the random
    # number generator. So the generate() method now has a "rng" variable,
    # which, if supplied can be a thread-local instance of random.Random().
    def generate(self, numchars, seed_text=None, rng=random):
        text = []

        if seed_text is None:
            prev = rng.choice(self.starters)
            text.append(prev)
        else:
            seed_len = len(seed_text)
            text.append(seed_text)
            if seed_len >= self.memory:
                prev = seed_text[-self.memory:]
                if prev not in self.dict:
                    prev = rng.choice(self.starters)
                    text.append(" " + prev)
            else:
                # Expensive
                possibles = [s for s in self.dict.keys() if s[0:seed_len] == seed_text]
                if len(possibles) == 0:
                    prev = rng.choice(self.starters)
                    text.append(" " + prev)
                else:
                    prev = rng.choice(possibles)
                    text.append(prev[seed_len:])

        choices = {}

        linePos = 0
        paraPos = 0

        while True:
            if prev in self.dict:
                c = rng.choice(self.dict[prev])
                if c.isspace() and linePos > self.lineLen:
                    linePos = 0
                    text.append("\n")
                elif c == ".":
                    text.append(". ")
                    if numchars == 0:
                        # numchars = 0 means return one sentence.
                        break
                    elif paraPos > self.paraLen:
                        # numchars > 0 means return paragraphs until
                        # numchars is exceeded.
                        text.append("\n\n")
                        paraPos = 0
                        linePos = 0
                        if len(text) > numchars:
                            break
                else:
                    linePos += 1
                    paraPos += 1
                    text.append(c)
                    if c in """,".!?:)""":
                        text.append(" ")
                        linePos += 1
                prev = prev + c
            else:
                prev = rng.choice(list(self.dict.keys()))

            if len(prev) > self.memory:
                prev = prev[1:]
        return "".join(text).strip().replace(" i ", " I ").replace(" i'", " I'")

if __name__ == "__main__":
    import time
    random.seed(42)
    mc = MarkovChain("markov_input.txt", memory=8)
    start = time.time()
    for i in range(100):
        page = mc.generate(20000, "pict")
    print(page[:200])
    end = time.time()
    print((end-start)/100)

