import random
import string

class MarkovChain:
    def __init__(self, filename=None, memory=5):
        self.paraLen = 300
        self.dict = {}
        self.memory = memory

        if not isinstance(memory, int) or memory < 1:
            raise Exception("Invalid memory size requested")

        # Read the input file and generate the Markov dartboard.
        prev = ""
        with open(filename, "r", encoding="utf-8") as f:
            seedtext = f.read()

        # By re-adding the first few charaxters to the
        # end, we can guarantee that generate() will
        # always have an option for the next char.
        # and this saves a test in its loop iteration.
        # So we scan twice and, on the second scan, break
        # out as soon as we see a "prev" that's already
        # been seen.

        skip = False
        for scan in range(2):
            for c in seedtext:
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

                # Break out ASAP on the second pass
                if scan==1 and prev in self.dict:
                    break

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

        paragraphs = []
        length = 0

        while True:
            c = rng.choice(self.dict[prev])
            text.append(c)
            if c == ".":
                if numchars == 0:
                    # numchars = 0 means return one sentence.
                    paragraphs.append(text)
                    break
                else:
                    plen = len(text)
                    if plen > self.paraLen:
                        paragraphs.append(text)
                        length += plen

                        # numchars > 0 means return paragraphs until
                        # numchars is exceeded.
                        if length > numchars:
                            break

                        text = []
            prev = prev[1:] + c

        # Make each paragraph array into a string.
        paragraphs = [ "".join(p) for p in paragraphs ]

        if numchars == 0:
            return paragraphs[0]
        return paragraphs

if __name__ == "__main__":
    # Benchmark with the following details.
    seconds = 2
    memory = 8
    length = 20000
    rndseed = 42
    textseed = "Sherlock"

    import time
    random.seed(rndseed)
    mc = MarkovChain("markov_input.txt", memory=memory)
    print(f"Benchmarking memory={memory}, length={length} for {seconds} seconds")
    n = 0
    chars = 0
    start = time.time()
    while True:
        page = mc.generate(length, textseed)
        n += 1
        end = time.time()
        if end - start >= seconds:
            break
    print(page[0])
    print(len("".join(page)))
    seconds = end-start
    print(f"\n{n/seconds:.2f} texts per second, ~{n*length/seconds:.0f} chars per second")
